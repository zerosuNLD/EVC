import pandas as pd
from pandas_plink import read_plink
import os
import matplotlib.pyplot as plt
import seaborn as sns

# --- 1. CẤU HÌNH ĐƯỜNG DẪN ---
prefix = "/mnt/d/darwins_dogs_genetic_set/output/DarwinsDogs_Analysis_Ready"
pheno_path = "/mnt/d/darwins_dogs_genetic_set/output/plink_pheno_coat_color.txt"
gwas_result_dir = "/mnt/d/darwins_dogs_genetic_set/output/GWAS_Results"
output_dir = "/mnt/d/darwins_dogs_genetic_set/output/ML_Datasets"

os.makedirs(output_dir, exist_ok=True)

# --- 2. ĐỌC DỮ LIỆU GEN VÀ NHÃN ---
print("🚀 Đang nạp dữ liệu gen (BED/BIM/FAM)...")
(bim, fam, bed) = read_plink(prefix, verbose=False)
fam['iid'] = fam['iid'].astype(str)

print("🚀 Đang nạp file nhãn (Phenotypes)...")
df_pheno = pd.read_csv(pheno_path, sep='\t')
df_pheno['#IID'] = df_pheno['#IID'].astype(str)

# --- TỰ ĐỘNG LẤY TẤT CẢ CÁC CỘT MÀU LÔNG VÀ LOẠI BỎ 2 MÀU YÊU CẦU ---
exclude_colors = [
    "Q243_white_or_cream_coat_color", 
    "Q243_red_or_liver_or_brown_or_tan_coat_color"
]
all_colors = [c for c in df_pheno.columns[1:] if c not in exclude_colors]

print(f"🔍 Tìm thấy tổng cộng {len(all_colors)} đặc điểm màu lông để xử lý (đã loại trừ 2 màu).")

# Từ điển (Dictionary) để lưu trữ số lượng SNP cho biểu đồ
snp_counts = {}

# --- 3. VÒNG LẶP TẠO FILE CSV ---
for color in all_colors:
    snp_list_file = f"{gwas_result_dir}/Trích_Xuất_SNP_{color}.txt"
    
    if not os.path.exists(snp_list_file):
        print(f"⚠️ Bỏ qua {color} (Không có file SNP trích xuất)")
        continue
        
    df_sig = pd.read_csv(snp_list_file, sep='\t')
    sig_snps = df_sig['SNP_ID'].tolist()
    
    if len(sig_snps) == 0:
        continue

    # LƯU SỐ LƯỢNG SNP (Cắt gọt tên cho biểu đồ bớt rườm rà)
    short_color = color.replace("Q243_", "").replace("_coat_color", "")
    snp_counts[short_color] = len(sig_snps)

    print(f"📦 Đang tạo Dataset cho: {color} ({len(sig_snps)} SNPs)")

    snp_indices = bim[bim['snp'].isin(sig_snps)].index.tolist()
    snp_names = bim.iloc[snp_indices]['snp'].values
    
    genotype_matrix = bed[snp_indices, :].compute().T 
    
    df_genotype = pd.DataFrame(genotype_matrix, columns=snp_names)
    df_genotype['IID_key'] = fam['iid'].values
    
    df_final = pd.merge(df_pheno[['#IID', color]], df_genotype, left_on='#IID', right_on='IID_key')
    df_final = df_final.drop(columns=['IID_key']).rename(columns={'#IID': 'dog_id'})
    
    out_file = f"{output_dir}/Dataset_{color}.csv"
    df_final.to_csv(out_file, index=False)

print("\n🔥 XONG! Toàn bộ các màu lông đã được xuất ra file CSV riêng biệt.")

# --- 4. VẼ BIỂU ĐỒ SỐ LƯỢNG SNP ---
if snp_counts:
    print("🎨 Đang vẽ biểu đồ thống kê số lượng SNP...")
    
    # Chuyển Dictionary thành DataFrame và sắp xếp từ cao xuống thấp
    df_plot = pd.DataFrame(list(snp_counts.items()), columns=['Color', 'SNP_Count'])
    df_plot = df_plot.sort_values(by='SNP_Count', ascending=False)

    plt.figure(figsize=(12, 6))
    sns.set_theme(style="whitegrid")

    # Vẽ biểu đồ cột
    ax = sns.barplot(
        data=df_plot, 
        x='Color', 
        y='SNP_Count', 
        palette="viridis" # Bảng màu chuyển sắc đẹp mắt
    )

    # Hiển thị chính xác con số lên trên đỉnh mỗi cột
    for i in ax.containers:
        ax.bar_label(i, padding=3, fontweight='bold')

    # Trang trí
    plt.title("Số lượng SNP có tác động mạnh theo từng Màu Lông", fontsize=16, fontweight='bold')
    plt.xlabel("Đặc điểm Màu", fontsize=12)
    plt.ylabel("Số lượng SNP", fontsize=12)
    
    # Thêm một chút không gian phía trên trục Y để số không bị cắt mất
    plt.ylim(0, df_plot['SNP_Count'].max() * 1.15) 
    plt.xticks(rotation=45, ha="right")
    plt.tight_layout()

    # Lưu biểu đồ
    plot_path = f"{output_dir}/ThongKe_SoLuong_SNP.png"
    plt.savefig(plot_path, dpi=300)
    print(f"🎉 BIỂU ĐỒ ĐÃ ĐƯỢC LƯU TẠI: {plot_path}")
else:
    print("⚠️ Không có dữ liệu SNP để vẽ biểu đồ.")