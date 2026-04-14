import pandas as pd

# Chọn màu bạn muốn xem thử (ví dụ: Lông đen)
file_path = "/mnt/d/darwins_dogs_genetic_set/output/GWAS_Results/Trích_Xuất_SNP_Q243_black_coat_color.txt"

try:
    # 1. Đọc file chứa các SNP đã lọt qua vòng loại
    df = pd.read_csv(file_path, sep='\t')
    
    # 2. Sắp xếp SNP có tác động từ LỚN NHẤT đến NHỎ NHẤT 
    # (Tác động càng lớn thì P_value càng nhỏ, nên ta xếp tăng dần)
    df_sorted = df.sort_values(by='P_value', ascending=True).reset_index(drop=True)
    
    print(f"🎉 TỔNG KẾT: Có {len(df_sorted)} SNP thực sự quyết định màu lông này!")
    
    print("\n🏆 DANH SÁCH TOP 15 SNP CÓ TÁC ĐỘNG MẠNH MẼ NHẤT:")
    # In ra 15 SNP xịn nhất
    print(df_sorted.head(15).to_string())
    
except FileNotFoundError:
    print("❌ Không tìm thấy file. Bạn hãy kiểm tra xem script Bash đã chạy xong chưa nhé!")
except Exception as e:
    print(f"Lỗi: {e}. File có thể trống vì không có SNP nào đủ mạnh vượt qua ngưỡng 5e-8.")