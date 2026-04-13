import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats

# -------- 1. Charger dataset --------
path_csv = r"C:\Users\ahmed\OneDrive\Bureau\pfa_nthif\Approche 3\Dataset_extract.csv"
df = pd.read_csv(path_csv)

# Nettoyage colonnes
df.columns = df.columns.str.strip()
print("Colonnes disponibles :", df.columns)

# -------- 2. Vérifications + nettoyage --------
df = df.dropna(subset=['Group', 'Age', 'Total_Hippo'])
df['Group'] = df['Group'].str.strip()
df = df[df["Group"].isin(["CN", "MCI", "AD"])]
print(f"Nombre total lignes après filtrage : {len(df)}")
print("Distribution par groupe :")
print(df['Group'].value_counts())

# -------- 3. Création variable AD binaire --------
df["AD_binary"] = (df["Group"] == "AD").astype(int)

# -------- 4. ANOVA Total_Hippo par groupe --------
if 'Total_Hippo' in df.columns:
    groups = [df[df['Group']==g]['Total_Hippo'].dropna() for g in ['CN','MCI','AD']]
    f_stat, p_val = stats.f_oneway(*groups)
    print("\n--- ANOVA Total_Hippo par groupe ---")
    print(f"F = {f_stat:.2f}, p = {p_val:.4f}")
    print("SIGNIFICATIF" if p_val < 0.05 else "NON SIGNIFICATIF")

# -------- 5. Analyse des features hippocampiques --------
features = [
    "Hippo_L",
    "Hippo_R",
    "Total_Hippo",
    "Hippo_Mean",
    "Hippo_Asymmetry_Pct",
    "Hippo_Asym_Index",
    "Age"
]

features = [f for f in features if f in df.columns]
print("\nFeatures utilisées :", features)

if features:
    fig = plt.figure(figsize=(20, 5 * len(features)))
    fig.suptitle("Analyse Hippocampique par Groupe", fontsize=18)

    for i, feature in enumerate(features):
        # Boxplot
        ax1 = plt.subplot(len(features), 3, i*3 + 1)
        sns.boxplot(data=df, x="Group", y=feature, ax=ax1)
        ax1.set_title(f"Boxplot {feature}")

        # Violin plot
        ax2 = plt.subplot(len(features), 3, i*3 + 2)
        sns.violinplot(data=df, x="Group", y=feature, ax=ax2)
        ax2.set_title(f"Violin {feature}")

        # Histogram
        ax3 = plt.subplot(len(features), 3, i*3 + 3)
        sns.histplot(data=df, x=feature, hue="Group", kde=True, bins=30, ax=ax3)
        ax3.set_title(f"Histogram {feature}")

    plt.tight_layout(rect=[0, 0, 1, 0.96])
    plt.show()