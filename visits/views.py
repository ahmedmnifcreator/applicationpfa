from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Visit
from patients.models import Patient
from datetime import date
import os
import zipfile

from analytics.pipeline import run_mri_pipeline_async

@login_required
def mri_upload(request):
    if request.method == 'POST':
        patient_id = request.POST.get('patient')
        exam_date  = request.POST.get('date') or str(date.today())
        patient    = get_object_or_404(Patient, pk=patient_id)

        # Determine what was uploaded
        dicom_files = request.FILES.getlist('mri_files')   # multiple .dcm
        single_file = request.FILES.get('mri_file')        # .zip / .nii / .nii.gz

        visit = None

        # ── Case 1: Multiple DICOM files ──────────────────────────────────
        if dicom_files:
            visit = Visit.objects.create(
                patient=patient, date=exam_date,
                mri_format='dicom', file_count=len(dicom_files), status='pending'
            )
            # Save each .dcm to media/mri_scans/visit_<id>/
            from django.conf import settings
            folder_rel = f"mri_scans/visit_{visit.pk}/"
            folder_abs = os.path.join(settings.MEDIA_ROOT, folder_rel)
            os.makedirs(folder_abs, exist_ok=True)
            for f in dicom_files:
                dest = os.path.join(folder_abs, os.path.basename(f.name))
                with open(dest, 'wb') as out:
                    for chunk in f.chunks():
                        out.write(chunk)
            visit.mri_folder = folder_rel
            visit.save()

        # ── Case 2: ZIP archive ───────────────────────────────────────────
        elif single_file and single_file.name.lower().endswith('.zip'):
            visit = Visit.objects.create(
                patient=patient, date=exam_date,
                mri_format='zip', status='pending'
            )
            from django.conf import settings
            folder_rel = f"mri_scans/visit_{visit.pk}/"
            folder_abs = os.path.join(settings.MEDIA_ROOT, folder_rel)
            os.makedirs(folder_abs, exist_ok=True)
            # Extract zip
            with zipfile.ZipFile(single_file, 'r') as zf:
                zf.extractall(folder_abs)
                visit.file_count = len(zf.namelist())
            visit.mri_folder = folder_rel
            visit.mri_format = 'dicom'   # assume contents are DICOM
            visit.save()

        # ── Case 3: Single NIfTI file ─────────────────────────────────────
        elif single_file:
            visit = Visit.objects.create(
                patient=patient, date=exam_date,
                mri_file=single_file, mri_format='nifti',
                file_count=1, status='pending'
            )

        else:
            messages.error(request, "Veuillez sélectionner au moins un fichier IRM.")
            return redirect('visits:upload')

        # Launch async pipeline
        run_mri_pipeline_async(visit.pk)

        messages.success(request, f"IRM de {patient.name} soumis avec succès ({visit.file_count} fichier(s)).")
        return redirect('visits:status', visit_id=visit.pk)

    # GET – show upload form
    patients = Patient.objects.all().order_by('name')
    selected_patient_id = request.GET.get('patient', '')
    today = str(date.today())
    return render(request, 'visits/upload.html', {
        'patients': patients,
        'selected_patient_id': selected_patient_id,
        'today': today,
    })


@login_required
def mri_status(request, visit_id):
    visit = get_object_or_404(Visit, pk=visit_id)
    return render(request, 'visits/status.html', {'visit': visit})


@login_required
def mri_list(request):
    visits = Visit.objects.all().order_by('-created_at').select_related('patient')
    return render(request, 'visits/list.html', {'visits': visits})
