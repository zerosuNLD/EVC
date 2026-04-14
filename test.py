import pandas as pd
from pandas_plink import read_plink

# Đường dẫn đến file đã qua tất cả các bước lọc và chuyển đổi
file_prefix = "/mnt/d/darwins_dogs_genetic_set/DarwinsDogs_2024_N-3277_canfam4_gp-0.70_biallelic" 
(bim, fam, bed) = read_plink(file_prefix)
# 1. Thông tin 2 con chó mục tiêu
danh_sach_id = ['117', '95']
thong_tin_cho = fam[fam['iid'].isin(danh_sach_id)]

if thong_tin_cho.empty:
    print("Không tìm thấy chó.")
else:
    vi_tri_cot = thong_tin_cho['i'].tolist()
    ten_cho = thong_tin_cho['iid'].tolist()
    
    # Lấy tổng số SNP thực tế còn lại
    tong_so_snp = bim.shape[0]
    
    # 2. Lấy 20 SNP đầu tiên để xem thử
    so_luong_snp = 20
    ma_tran_gen = bed[:so_luong_snp, vi_tri_cot].compute()
    
    # Lấy tên SNP (lúc này đã được chuẩn hóa Chromosome:Position)
    ten_snp = bim['snp'].iloc[:so_luong_snp].values

    # 3. Tạo bảng kết quả
    df_ket_qua = pd.DataFrame(ma_tran_gen, columns=ten_cho, index=ten_snp)
    
    print(f"--- THÔNG TIN BỘ DỮ LIỆU ĐÃ LỌC SẠCH ---")
    print(f"Tổng số lượng SNP còn lại: {tong_so_snp:,}")
    print(f"Số lượng chó trong file: {fam.shape[0]}")
    print(f"\n--- Kiểu gen của chó {', '.join(ten_cho)} (20 vị trí đầu) ---")
    print(df_ket_qua)