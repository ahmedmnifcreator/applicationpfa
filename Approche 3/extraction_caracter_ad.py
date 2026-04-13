import os
import pandas as pd
import numpy as np
import re

# ══════════════════════════════════════════════════════
# PATHS
# ══════════════════════════════════════════════════════

BASE_DIR = r"C:\Users\ahmed\OneDrive\Bureau\pfa_nthif"
FASTSURFER_DIR = os.path.join(BASE_DIR, "fastsurfer", "output")
CLINICAL_CSV   = os.path.join(BASE_DIR, "CN.csv")  # <-- ton CSV CN

OUTPUT_DIR = os.path.join(BASE_DIR, "Approche 3")
os.makedirs(OUTPUT_DIR, exist_ok=True)

OUTPUT_FILE = os.path.join(OUTPUT_DIR, "Dataset_CN_ALL_VISITS.csv")

# ══════════════════════════════════════════════════════
# NORMALISATION ID
# ══════════════════════════════════════════════════════

def normalize_subject_id(s):
    s = str(s).strip()
    s = s.replace(".nii", "")
    s = re.sub(r'[a-zA-Z]$', '', s)
    return s

# ══════════════════════════════════════════════════════
# EXTRACTION FASTSURFER
# ══════════════════════════════════════════════════════

def extract_volumes(stats_file):
    vols = {'eTIV': None, 'Hippo_L': None, 'Hippo_R': None}
    try:
        with open(stats_file, 'r', encoding='utf-8') as f:
            for line in f:
                if "Measure Mask, MaskVol, Mask Volume" in line:
                    parts = line.split(',')
                    vols['eTIV'] = float(parts[-2].strip())
                if "Left-Hippocampus" in line:
                    vols['Hippo_L'] = float(line.split()[3])
                if "Right-Hippocampus" in line:
                    vols['Hippo_R'] = float(line.split()[3])
        return vols
    except:
        return vols

# ══════════════════════════════════════════════════════
# LOAD CSV CLINIQUE
# ══════════════════════════════════════════════════════

print("Chargement CSV clinique...")

df = pd.read_csv(CLINICAL_CSV)

# Garder les colonnes nécessaires
df = df[["Subject", "Age", "Sex", "Group", "Visit"]]
df = df.rename(columns={"Subject": "Subject_ID"})

# Normaliser les IDs
df["Subject_ID"] = df["Subject_ID"].apply(normalize_subject_id)

# Filtrer uniquement les sujets CN
df = df[df["Group"] == "CN"]

print(f"Groupes trouvés dans CSV : {df['Group'].unique().tolist()}")
print(f"Nombre lignes CN : {len(df)}")
print(f"Sujets CN uniques : {df['Subject_ID'].nunique()}")

# ══════════════════════════════════════════════════════
# INDEX FASTSURFER
# ══════════════════════════════════════════════════════

print("\nIndexation FastSurfer...")

scan_map = {}

for folder in os.listdir(FASTSURFER_DIR):
    full_path = os.path.join(FASTSURFER_DIR, folder)
    if not os.path.isdir(full_path):
        continue

    sid = normalize_subject_id(folder)
    stats_path = os.path.join(full_path, "stats", "aseg+DKT.stats")

    if os.path.exists(stats_path):
        scan_map.setdefault(sid, []).append((folder, stats_path))

# Tri pour garder l'ordre a,b,c...
for sid in scan_map:
    scan_map[sid].sort()

print(f"Sujets FastSurfer trouvés : {len(scan_map)}")

# ══════════════════════════════════════════════════════
# EXTRACTION — TOUTES LES VISITES
# ══════════════════════════════════════════════════════

print("\nExtraction biomarqueurs CN (toutes visites)...")

rows = []
missing_subjects = 0

for _, row in df.iterrows():
    sid = row["Subject_ID"]
    visit = row["Visit"]

    if sid not in scan_map:
        missing_subjects += 1
        continue

    # Parcourir tous les scans du sujet
    for folder, stats_path in scan_map[sid]:
        v = extract_volumes(stats_path)

        if v['Hippo_L'] is None or v['Hippo_R'] is None:
            continue

        total = v['Hippo_L'] + v['Hippo_R']
        mean  = total / 2
        ratio_icv = total / v['eTIV'] if v['eTIV'] else np.nan
        asym_pct  = abs(v['Hippo_L'] - v['Hippo_R']) / mean * 100
        asym_idx  = (v['Hippo_L'] - v['Hippo_R']) / mean

        rows.append({
            "Subject_ID": sid,
            "Visit": visit,
            "Scan_ID": folder,
            "Hippo_L": v['Hippo_L'],
            "Hippo_R": v['Hippo_R'],
            "Total_Hippo": total,
            "Hippo_Mean": mean,
            "eTIV": v['eTIV'],
            "Hippo_Ratio_ICV": round(ratio_icv, 6),
            "Hippo_Asymmetry_Pct": round(asym_pct, 2),
            "Hippo_Asym_Index": round(asym_idx, 4),
            "Hippo_L_R_Ratio": round(v['Hippo_L'] / v['Hippo_R'], 4) if v['Hippo_R'] else np.nan,
            "Hippo_L_Norm": round(v['Hippo_L'] / v['eTIV'], 8) if v['eTIV'] else np.nan,
            "Hippo_R_Norm": round(v['Hippo_R'] / v['eTIV'], 8) if v['eTIV'] else np.nan,
            "Group": row["Group"],
            "Sex": row["Sex"],
            "Age": row["Age"]
        })

# ══════════════════════════════════════════════════════
# DATAFRAME FINAL
# ══════════════════════════════════════════════════════

df_final = pd.DataFrame(rows)

# Supprimer doublons possibles
df_final = df_final.drop_duplicates(subset=["Subject_ID", "Scan_ID"])

# ══════════════════════════════════════════════════════
# SAVE
# ══════════════════════════════════════════════════════

df_final.to_csv(OUTPUT_FILE, index=False)

print("\n✅ DATASET CN COMPLET CRÉÉ")
print(f"Nombre total lignes : {len(df_final)}")
print(f"Sujets manquants    : {missing_subjects}")
print(f"Fichier sauvegardé  : {OUTPUT_FILE}")

print("\nAperçu :")
print(df_final.head())

print("\nStatistiques rapides :")
print(df_final.groupby("Subject_ID").size().describe())