import argparse
import pandas as pd
import numpy as np
from pandas_plink import read_plink
from sklearn.feature_selection import chi2, mutual_info_classif
from sklearn.tree import DecisionTreeClassifier
from scipy.stats import entropy
import warnings
import os

warnings.filterwarnings('ignore')

def main():
    parser = argparse.ArgumentParser(description="Consensus Statistical Tests for SNPs")
    parser.add_argument("--pfile", required=True, help="Prefix của file PLINK (yêu cầu .bed, .bim, .fam)")
    parser.add_argument("--pheno", required=True, help="Đường dẫn file phenotype (TSV)")
    parser.add_argument("--color", required=True, help="Tên cột màu sắc (nhãn)")
    parser.add_argument("--snp_list", required=True, help="File chứa danh sách SNP từ GWAS")
    parser.add_argument("--out", required=True, help="Đường dẫn lưu kết quả (CSV)")
    parser.add_argument("--top_percent", type=float, default=0.5, help="Tỷ lệ % SNP hàng đầu lấy từ mỗi test")
    args = parser.parse_args()

    # 1. Đọc danh sách SNP mục tiêu
    try:
        # Giả định file GWAS có cột 'variant_id' hoặc 'SNP_ID'
        sig_df = pd.read_csv(args.snp_list, sep='\s+')
        id_col = 'variant_id' if 'variant_id' in sig_df.columns else 'SNP_ID'
        sig_snps = sig_df[id_col].unique().tolist()
    except Exception as e:
        print(f"⚠️ Lỗi đọc file SNP: {e}")
        return

    if not sig_snps:
        print(f"⚠️ Không có SNP nào được tìm thấy trong file {args.snp_list}")
        return

    # 2. Đọc dữ liệu Genotype và Phenotype
    # Lưu ý: read_plink cần file .bed
    try:
        (bim, fam, bed) = read_plink(args.pfile, verbose=False)
    except Exception as e:
        print(f"❌ Lỗi đọc file PLINK: {e}. Hãy chắc chắn bạn đã convert pgen sang bed.")
        return

    # Chuẩn hóa ID giữa FAM và Phenotype file
    fam['iid'] = fam['iid'].astype(str)
    df_pheno = pd.read_csv(args.pheno, sep='\t')
    df_pheno['#IID'] = df_pheno['#IID'].astype(str)

    # Lọc các SNP trong danh sách GWAS
    bim_filtered = bim[bim['snp'].isin(sig_snps)]
    if bim_filtered.empty:
        print("⚠️ Không tìm thấy SNP mục tiêu trong file Genotype.")
        return

    snp_indices = bim_filtered.index.tolist()
    valid_snp_names = bim_filtered['snp'].values
    
    # 3. Trích xuất Matrix và Merge
    # Tính toán lười (Lazy compute) thông qua dask, sau đó chuyển sang numpy
    print(f"--- Đang tải matrix cho {len(valid_snp_names)} SNPs...")
    X_matrix = bed[snp_indices, :].compute().T
    
    df_genotype = pd.DataFrame(X_matrix, columns=valid_snp_names)
    df_genotype['IID_key'] = fam['iid'].values

    # Merge với phenotype
    df_final = pd.merge(df_pheno[['#IID', args.color]], df_genotype, left_on='#IID', right_on='IID_key')
    df_final = df_final.dropna(subset=[args.color])
    
    # Xử lý missing values (điền bằng mode - giá trị xuất hiện nhiều nhất của SNP đó)
    X = df_final[valid_snp_names]
    X = X.apply(lambda x: x.fillna(x.mode()[0] if not x.mode().empty else 0), axis=0)
    y = df_final[args.color].values

    if X.shape[1] == 0 or len(np.unique(y)) < 2:
        print("⚠️ Dữ liệu không đủ biến thiên để thực hiện test.")
        return

    # 4. Thực hiện 4 bài Test Thống kê
    k = max(1, int(X.shape[1] * args.top_percent))
    print(f"--- Đang thực hiện 4 bài test (Lấy top {k} SNPs mỗi loại)...")

    # --- TEST 1: Chi-Square ---
    chi2_val, _ = chi2(X, y)
    top_chi2 = set(X.columns[np.argsort(chi2_val)[-k:]])

    # --- TEST 2: Mutual Information (MI) ---
    mi_val = mutual_info_classif(X, y, random_state=42)
    top_mi = set(X.columns[np.argsort(mi_val)[-k:]])

    # --- TEST 3: Information Gain (IG) ---
    dt = DecisionTreeClassifier(criterion='entropy', random_state=42)
    dt.fit(X, y)
    ig_val = dt.feature_importances_
    top_ig = set(X.columns[np.argsort(ig_val)[-k:]])

    # --- TEST 4: KL Divergence (Sự khác biệt phân phối) ---
    kl_val = []
    classes = np.unique(y)
    if len(classes) == 2:
        c0 = X[y == classes[0]]
        c1 = X[y == classes[1]]
        for col in X.columns:
            # Tính xác suất xuất hiện allele (0, 1, 2)
            p = np.histogram(c0[col], bins=[0,1,2,3], density=True)[0] + 1e-9
            q = np.histogram(c1[col], bins=[0,1,2,3], density=True)[0] + 1e-9
            kl_val.append(entropy(p, q))
    else:
        kl_val = [0] * X.shape[1]
    
    top_kl = set(X.columns[np.argsort(kl_val)[-k:]])

    # 5. Tìm Consensus và Xuất file
    consensus_set = top_chi2 & top_mi & top_ig & top_kl
    consensus_list = list(consensus_set)

    # Tạo dataframe kết quả có chứa điểm số để dễ phân tích
    results_summary = pd.DataFrame({
        "SNP_ID": X.columns,
        "Chi2_Score": chi2_val,
        "MI_Score": mi_val,
        "IG_Score": ig_val,
        "KL_Divergence": kl_val
    })
    
    results_summary['Is_Consensus'] = results_summary['SNP_ID'].isin(consensus_list)
    
    # Chỉ lưu các SNP đạt đồng thuận cả 4 test
    final_output = results_summary[results_summary['Is_Consensus'] == True].sort_values(by="Chi2_Score", ascending=False)
    
    final_output.to_csv(args.out, index=False)
    
    print(f"✅ {args.color}: Hoàn tất!")
    print(f"   - Tổng số SNP đầu vào: {X.shape[1]}")
    print(f"   - Số SNP đồng thuận (4/4): {len(consensus_list)}")
    print(f"   - Kết quả lưu tại: {args.out}")

if __name__ == "__main__":
    main()