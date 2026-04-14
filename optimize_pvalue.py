import os
import glob
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pandas_plink import read_plink
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import f1_score
from tqdm import tqdm

from sklearn.svm import SVC
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from xgboost import XGBClassifier
from sklearn.neural_network import MLPClassifier

prefix = "/mnt/d/darwins_dogs_genetic_set/output/DarwinsDogs_Analysis_Ready"
pheno_path = "/mnt/d/darwins_dogs_genetic_set/output/plink_pheno_coat_color.txt"
gwas_result_dir = "/mnt/d/darwins_dogs_genetic_set/output/GWAS_Results"
output_plot = "/mnt/d/darwins_dogs_genetic_set/output/Pvalue_Optimization_Chart.png"

thresholds = [0.1, 0.05, 0.01, 0.001, 0.0001, 0.00001, 0.000001, 0.0000001]

models = {
    "SVM (Linear)": SVC(kernel='linear', C=1.0, random_state=42),
    "Logistic Regression (L2)": LogisticRegression(penalty='l2', C=0.1, max_iter=1000, random_state=42),
    "Random Forest": RandomForestClassifier(n_estimators=100, n_jobs=-1, random_state=42),
    "Gradient Boosting": GradientBoostingClassifier(n_estimators=100, random_state=42),
    "XGBoost": XGBClassifier(eval_metric='logloss', n_jobs=-1, random_state=42),
    "Neural Net (1 Layer)": MLPClassifier(hidden_layer_sizes=(100,), max_iter=1000, random_state=42),
    "Neural Net (2 Layers)": MLPClassifier(hidden_layer_sizes=(100, 50), max_iter=1000, random_state=42)
}

print("🚀 Đang nạp dữ liệu Gen và Nhãn...")
(bim, fam, bed) = read_plink(prefix, verbose=False)
fam_iids = fam['iid'].astype(str).values

df_pheno = pd.read_csv(pheno_path, sep='\t')
df_pheno['#IID'] = df_pheno['#IID'].astype(str)

all_colors = [c for c in df_pheno.columns[1:] if c not in [
    "Q243_white_or_cream_coat_color", 
    "Q243_red_or_liver_or_brown_or_tan_coat_color"
]]

print("⚡ Đang tải toàn bộ Ma trận kiểu gen vào RAM...")
bed_matrix_ram = bed.compute() 
print(" Tải xong! Dữ liệu đã sẵn sàng trên RAM.")

def evaluate_single_run(p_val, color):
    run_results = []
    
    glm_files = glob.glob(f"{gwas_result_dir}/GWAS_{color}.*.glm.*")
    if not glm_files: return run_results
        
    try:
        df_gwas = pd.read_csv(glm_files[0], sep='\t', usecols=['ID', 'P'])
    except ValueError:
        return run_results
        
    sig_snps = df_gwas[df_gwas['P'] < p_val]['ID'].tolist()
    if len(sig_snps) == 0: return run_results

    snp_indices = bim[bim['snp'].isin(sig_snps)].index.tolist()
    
    if len(snp_indices) == 0: 
        return run_results

    genotype_matrix = bed_matrix_ram[snp_indices, :].T 
    
    df_genotype = pd.DataFrame(genotype_matrix, columns=bim.iloc[snp_indices]['snp'].values)
    df_genotype['IID_key'] = fam_iids
    
    df_final = pd.merge(df_pheno[['#IID', color]], df_genotype, left_on='#IID', right_on='IID_key')
    df_final = df_final.dropna(subset=[color])
    
    X = df_final.drop(columns=['#IID', 'IID_key', color])
    y = df_final[color]
    
    if X.empty or X.shape[1] == 0: 
        return run_results
        
    if y.nunique() < 2: 
        return run_results

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)
    
    for model_name, model in models.items():
        model.fit(X_train_scaled, y_train)
        y_pred = model.predict(X_test_scaled)
        f1 = f1_score(y_test, y_pred, average='weighted', zero_division=0)
        
        run_results.append({
            "Threshold": str(p_val), 
            "P_Value_Num": p_val,
            "Color": color.replace("Q243_", "").replace("_coat_color", ""),
            "Model": model_name,
            "F1_Score": f1,
            "SNP_Count": len(snp_indices) # Lấy số lượng thực tế có trong data
        })
        
    return run_results

tasks = [(p_val, color) for p_val in thresholds for color in all_colors]

print(f"\n🏁 BẮT ĐẦU CHẠY TUẦN TỰ {len(tasks)} NHIỆM VỤ 🏁")

results = []
for p_val, color in tqdm(tasks, desc="Tiến độ (Tuần tự)"):
    run_res = evaluate_single_run(p_val, color)
    results.extend(run_res) # Gộp trực tiếp list kết quả con vào list tổng

print("\n HOÀN TẤT TOÀN BỘ THỬ NGHIỆM!")

print(" Đang vẽ đồ thị tối ưu hóa...")
df_results = pd.DataFrame(results)

df_summary = df_results.groupby(['Threshold', 'P_Value_Num', 'Model'])['F1_Score'].mean().reset_index()

idx_max = df_summary.groupby(['P_Value_Num'])['F1_Score'].idxmax()
df_best_only = df_summary.loc[idx_max].sort_values(by='P_Value_Num', ascending=False)

plt.figure(figsize=(14, 8))
sns.set_theme(style="whitegrid", context="talk")

chart = sns.lineplot(
    data=df_best_only,
    x="Threshold",
    y="F1_Score",
    marker="o",
    linewidth=3.5,
    markersize=12,
    color="#e74c3c" # Màu đỏ nổi bật
)

for _, row in df_best_only.iterrows():
    plt.annotate(
        f"{row['Model']}\n({row['F1_Score']:.3f})", 
        (row['Threshold'], row['F1_Score']),
        textcoords="offset points", 
        xytext=(0,15), 
        ha='center', 
        fontsize=10,
        color='#2c3e50',
        fontweight='bold',
        bbox=dict(boxstyle="round,pad=0.3", fc="white", ec="#bdc3c7", alpha=0.9)
    )

y_max = df_best_only['F1_Score'].max()
y_min = df_best_only['F1_Score'].min()
plt.ylim(y_min - 0.02, y_max + 0.05) 

plt.title("Hiệu Suất Tốt Nhất (Max F1-Score) Tại Từng Ngưỡng P-value", fontsize=18, fontweight='bold', pad=20)
plt.xlabel("Ngưỡng P-value ", fontsize=14)
plt.ylabel("Điểm F1-Score Cao Nhất", fontsize=14)
plt.tight_layout()

plt.savefig(output_plot, dpi=300)
print(f"ĐỒ THỊ ĐÃ ĐƯỢC LƯU TẠI: {output_plot}")

print("\n---  KẾT QUẢ TÓM TẮT ĐỈNH CAO NHẤT  ---")
best_setting = df_best_only.loc[df_best_only['F1_Score'].idxmax()]
print(f"NGƯỠNG TỐT NHẤT: P_value = {best_setting['Threshold']}")
print(f"MÔ HÌNH THẮNG CUỘC: {best_setting['Model']}")
print(f"ĐIỂM F1-SCORE CAO NHẤT: {best_setting['F1_Score']:.4f}")
print("==============================================")