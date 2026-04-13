import pandas as pd
import numpy as np
import os
import matplotlib
matplotlib.use('Agg')  # Permet de sauvegarder les figures sans ouvrir de fenêtre graphique
import matplotlib.pyplot as plt
import seaborn as sns

# --------------------------
# PATHS
# --------------------------
BASE_DIR = r"C:\Users\ahmed\OneDrive\Bureau\pfa_nthif\Approche 3"
INPUT_CSV = os.path.join(BASE_DIR, "Dataset_extract.csv")  # CSV final avec toutes les visites et groupes
OUTPUT_DIR = BASE_DIR

# --------------------------
# LOAD DATA
# --------------------------
df = pd.read_csv(INPUT_CSV)

# Supprimer les lignes avec Age ou Total_Hippo manquant (indispensable pour analyse)
df_clean = df.dropna(subset=['Age', 'Total_Hippo'])

print(f"Total lignes originales : {len(df)}")
print(f"Lignes valides pour analyse : {len(df_clean)}")

# --------------------------
# FIGURE 1 : Corrélation Volume Hippocampique vs Âge
# --------------------------
fig1, ax1 = plt.subplots(figsize=(8, 6))

# Scatter plot : Total_Hippo en fonction de l'âge
ax1.scatter(df_clean['Age'], df_clean['Total_Hippo'], alpha=0.6, color='steelblue', s=50)

# Régression linéaire simple
m, b = np.polyfit(df_clean['Age'], df_clean['Total_Hippo'], 1)
x_line = np.linspace(df_clean['Age'].min(), df_clean['Age'].max(), 200)
y_line = m * x_line + b

# Calculer l'écart type des résidus pour bande d'erreur
residuals = df_clean['Total_Hippo'] - (m * df_clean['Age'] + b)
std_err = np.std(residuals)

# Ajouter ligne de régression et bande d'erreur
ax1.plot(x_line, y_line, color='red', linewidth=2)
ax1.fill_between(x_line, y_line - std_err, y_line + std_err, color='red', alpha=0.15)

ax1.set_xlabel('Âge', fontsize=12)
ax1.set_ylabel('Volume Hippocampique Total', fontsize=12)
ax1.set_title('Corrélation : Volume Hippocampique vs Âge', fontsize=13)
plt.tight_layout()
plt.savefig(os.path.join(OUTPUT_DIR, 'Correlation_Age_Volume.png'), dpi=150)
plt.close(fig1)
print("✅ Figure 1 sauvegardée : Corrélation Volume Hippocampe vs Âge")

# --------------------------
# FIGURE 2 : Heatmap Corrélations Hippocampiques
# --------------------------
features = [
    'Hippo_L', 'Hippo_R', 'Total_Hippo', 'Hippo_Mean',
    'Hippo_Asymmetry_Pct', 'Hippo_Asym_Index', 'Hippo_L_R_Ratio',
    'Hippo_Ratio_ICV', 'Age'
]

# Vérifier que toutes les colonnes existent dans le CSV
features = [f for f in features if f in df.columns]

corr_matrix = df[features].corr()

fig2, ax2 = plt.subplots(figsize=(10, 8))
sns.heatmap(
    corr_matrix,
    annot=True,
    fmt='.2f',
    cmap='RdPu',
    center=0,
    linewidths=0.5,
    ax=ax2,
    annot_kws={"size": 9}
)
ax2.set_title('Heatmap Corrélations Features Hippocampiques', fontsize=13, pad=15)
plt.tight_layout()
plt.savefig(os.path.join(OUTPUT_DIR, 'Heatmap_Correlations.png'), dpi=150)
plt.close(fig2)
print("✅ Figure 2 sauvegardée : Heatmap corrélations hippocampiques")

# --------------------------
# FIGURE 3 : Progression de l'Asymétrie Hippocampique par Groupe
# --------------------------
group_order = ['CN', 'MCI', 'AD']
colors = ['#E8A96A', '#A8788A', '#6A4C8C']

# Calculer moyenne de l'asymétrie par groupe
asym_by_group = df.groupby('Group')['Hippo_Asymmetry_Pct'].mean().reindex(group_order)

fig3, ax3 = plt.subplots(figsize=(7, 6))
bars = ax3.bar(group_order, asym_by_group.values, color=colors, width=0.5)

# Ajouter les valeurs au-dessus des barres
for bar, val in zip(bars, asym_by_group.values):
    ax3.text(
        bar.get_x() + bar.get_width() / 2,
        bar.get_height() + 0.1,
        f'{val:.2f}%',
        ha='center', va='bottom',
        fontsize=11, fontweight='bold'
    )

ax3.set_xlabel('Groupe', fontsize=12)
ax3.set_ylabel("Indice d'Asymétrie Moyen (%)", fontsize=12)
ax3.set_title("Progression de l'Asymétrie Hippocampique", fontsize=13)
ax3.set_ylim(0, asym_by_group.max() * 1.2)
plt.tight_layout()
plt.savefig(os.path.join(OUTPUT_DIR, 'Asymetrie_Par_Groupe.png'), dpi=150)
plt.close(fig3)
print("✅ Figure 3 sauvegardée : Asymétrie par groupe")

# --------------------------
# STATISTIQUES RAPIDES
# --------------------------
print("\n📊 DATASET SUMMARY")
print(f"Total sujets uniques : {df['Subject_ID'].nunique()}")
print(f"Nombre de scans valides : {df['Scan_ID'].notna().sum()}")

print("\nRépartition par groupe :")
print(df['Group'].value_counts())

print("\nAsymétrie moyenne par groupe :")
print(df.groupby('Group')['Hippo_Asymmetry_Pct'].mean().reindex(group_order).round(2))

print(f"\nCorrélation Age / Total_Hippo : {df['Age'].corr(df['Total_Hippo']):.3f}")