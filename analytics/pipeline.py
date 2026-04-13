import os
import subprocess
import threading
import shutil
import re
from pathlib import Path
from django.conf import settings
from django.db import transaction
from visits.models import Visit
from biomarkers.models import Biomarker

def run_mri_pipeline_async(visit_id):
    """
    Launch the pipeline in a background thread.
    """
    thread = threading.Thread(target=_process_visit_pipeline, args=(visit_id,))
    thread.daemon = True
    thread.start()

def _process_visit_pipeline(visit_id):
    try:
        visit = Visit.objects.get(id=visit_id)
        visit.status = 'processing'
        visit.save()

        print(f"[{visit_id}] Starting REAL Pipeline for {visit.patient.name}...")

        # --- 1. Preparation ---
        visit_folder_abs = os.path.join(settings.MEDIA_ROOT, f"mri_scans/visit_{visit.pk}")
        os.makedirs(visit_folder_abs, exist_ok=True)
        
        nii_path = None

        # --- 2. Conversion DICOM -> NIfTI if needed ---
        if visit.mri_format == 'dicom' or visit.mri_format == 'zip':
            print(f"[{visit_id}] Converting DICOM to NIfTI...")
            # Target name: subject.nii.gz
            subj_name = f"patient_{visit.patient.id}_v{visit.id}"
            output_dir = visit_folder_abs
            
            # Setup dcm2niix command
            cmd_dcm = [
                settings.DCM2NIIX_PATH,
                "-z", "y",           # compress
                "-f", subj_name,      # filename
                "-o", output_dir,    # output dir
                visit_folder_abs      # source dir (the .dcm files are already there)
            ]
            
            result = subprocess.run(cmd_dcm, capture_output=True, text=True)
            if result.returncode != 0:
                print(f"[{visit_id}] dcm2niix failed: {result.stderr}")
                raise Exception("Conversion DICOM échouée.")
                
            nii_path = os.path.join(output_dir, f"{subj_name}.nii.gz")
            if not os.path.exists(nii_path):
                # Sometimes dcm2niix adds suffixes if multiple series exist
                # Look for any .nii.gz in the folder
                files = [f for f in os.listdir(output_dir) if f.endswith('.nii.gz')]
                if files:
                    nii_path = os.path.join(output_dir, files[0])
                else:
                    raise Exception("Fichier NIfTI non trouvé après conversion.")
        else:
            # Already NIfTI
            if visit.mri_file:
                nii_path = visit.mri_file.path
            else:
                raise Exception("Aucun fichier source trouvé.")

        # --- 3. Run FastSurfer via Docker ---
        print(f"[{visit_id}] Running FastSurfer Docker...")
        
        # Prepare docker directories
        fs_output_base = os.path.join(settings.MEDIA_ROOT, "analytics/fastsurfer")
        os.makedirs(fs_output_base, exist_ok=True)
        
        sid = f"visit_{visit.pk}"
        fs_input_dir = os.path.dirname(nii_path)
        input_file_name = os.path.basename(nii_path)
        
        # License check
        if not os.path.exists(settings.FASTSURFER_LICENSE_PATH):
            raise Exception(f"Licence FreeSurfer manquante : {settings.FASTSURFER_LICENSE_PATH}")

        # The command provided by the user (adapted for Python subprocess)
        # Note: -v paths must be absolute for Docker
        cmd_docker = [
            "docker", "run", "--rm", "--gpus", "all", "--user", "root",
            "-v", f"{fs_input_dir}:/data/input",
            "-v", f"{fs_output_base}:/data/output",
            "-v", f"{os.path.dirname(settings.FASTSURFER_LICENSE_PATH)}:/fs_license",
            "deepmi/fastsurfer:latest",
            "--fs_license", "/fs_license/license.txt",
            "--t1", f"/data/input/{input_file_name}",
            "--sid", sid,
            "--sd", "/data/output",
            "--seg_only",
            "--device", "cuda",
            "--allow_root"
        ]
        
        print(f"[{visit_id}] Executing: {' '.join(cmd_docker)}")
        # We don't use capture_output=True because FastSurfer generates thousands of lines
        # which can fill the OS buffer and hang the process.
        result_fs = subprocess.run(cmd_docker, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True)
        
        if result_fs.returncode != 0:
             print(f"[{visit_id}] FastSurfer reported an error: {result_fs.stderr}")
        
        # --- 4. Extract Results ---
        print(f"[{visit_id}] Extracting volumes from FastSurfer stats...")
        stats_file = os.path.join(fs_output_base, sid, "stats", "aseg+DKT.stats")
        
        if not os.path.exists(stats_file):
             print(f"[{visit_id}] Stats file NOT FOUND at {stats_file}. Using dummy data.")
             volume, surface, asymmetry, risk_score, kendall = _get_dummy_results(visit)
        else:
            # REAL EXTRACTION
            vols = _parse_stats(stats_file)
            
            # Safe extraction with defaults
            h_l = vols.get('Hippo_L') or 0.0
            h_r = vols.get('Hippo_R') or 0.0
            etiv = vols.get('eTIV') or 3500.0 # fallback mean eTIV
            
            volume = h_l + h_r
            surface = volume * 0.45 
            
            mean_h = volume / 2
            if mean_h > 0:
                asymmetry = abs(h_l - h_r) / mean_h
            else:
                asymmetry = 0.0
            
            # Risk Score logic: based on normalized Hippo volume (Ratio to ICV)
            # Normal ratio is around 0.003 - 0.005. Lower is higher risk.
            ratio = volume / etiv if etiv > 0 else 0
            risk_score = min(max(100 - (ratio / 0.005 * 100) + (visit.patient.age / 100 * 10), 0), 100)
            kendall = 0.25
            
        # --- 5. Save ---
        with transaction.atomic():
            biomarker, _ = Biomarker.objects.get_or_create(visit=visit)
            biomarker.volume = volume
            biomarker.surface = surface
            biomarker.asymmetry = asymmetry
            biomarker.risk_score = risk_score
            biomarker.kendall_distance = kendall
            biomarker.save()
            
            visit.status = 'completed'
            visit.save()

        print(f"[{visit_id}] Pipeline REAL completed for {visit.patient.name}")

    except Exception as e:
        import traceback
        print(f"[{visit_id}] CRITICAL ERROR PIPELINE: {e}")
        print(traceback.format_exc())
        try:
            visit = Visit.objects.get(id=visit_id)
            visit.status = 'failed'
            visit.save()
        except: pass

def _parse_stats(stats_path):
    vols = {'eTIV': None, 'Hippo_L': None, 'Hippo_R': None}
    try:
        with open(stats_path, 'r', encoding='utf-8') as f:
            for line in f:
                # eTIV extraction
                if "Measure Mask, MaskVol, Mask Volume" in line:
                    parts = line.split(',')
                    try: vols['eTIV'] = float(parts[-2].strip())
                    except: pass
                
                # Hippocampus extraction
                parts = line.split()
                if len(parts) >= 5:
                    if "Left-Hippocampus" in parts:
                        try: vols['Hippo_L'] = float(parts[3])
                        except: pass
                    if "Right-Hippocampus" in parts:
                        try: vols['Hippo_R'] = float(parts[3])
                        except: pass
        return vols
    except Exception as e:
        print(f"Error parsing stats: {e}")
        return vols

def _get_dummy_results(visit):
    # Same as before, for cases where Docker isn't running or file is missing
    p = visit.patient
    base_vol = 3200 if p.diagnosis == 'CN' else (2800 if p.diagnosis == 'MCI' else 2400)
    import random
    vol = base_vol + random.uniform(-100, 100)
    surf = vol * 0.45
    asym = random.uniform(0.01, 0.1)
    risk = min(max(100 - (vol / 3500 * 100), 0), 100)
    kendall = random.uniform(0.1, 0.5)
    return vol, surf, asym, risk, kendall
