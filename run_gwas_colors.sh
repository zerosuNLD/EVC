#!/bin/bash
set -e

# ==========================================
# CẤU HÌNH ĐƯỜNG DẪN
# ==========================================
THREADS=8
INPUT_PFILE="/mnt/d/darwins_dogs_genetic_set/output/DarwinsDogs_FINAL_READY"
PHENOTYPE_FILE="/mnt/d/darwins_dogs_genetic_set/output/plink_pheno_coat_color.txt"
OUTPUT_DIR="/mnt/d/darwins_dogs_genetic_set/output/GWAS_Results"

PVAL_THRESHOLD="0.05" 

mkdir -p $OUTPUT_DIR

# Danh sách các cột màu lông trong file Phenotype
COLORS=(
    "Q243_black_coat_color"
    "Q243_liver_or_brown_coat_color"
    "Q243_white_coat_color"
    "Q243_red_coat_color"
    "Q243_yellow_coat_color"
    "Q243_grey_or_blue_coat_color"
    "Q243_tan_coat_color"
    "Q243_cream_coat_color"
)

echo "=========================================="
echo "BẮT ĐẦU CHẠY GWAS CHO TỪNG MÀU LÔNG"
echo "=========================================="

# Chạy vòng lặp cho từng màu
for COLOR in "${COLORS[@]}"; do
    echo ""
    echo ">>> Đang phân tích màu: $COLOR"

    # 1. Chạy GWAS bằng PLINK2
    plink2 --pfile $INPUT_PFILE \
           --dog \
           --pheno $PHENOTYPE_FILE \
           --pheno-name $COLOR \
           --1 \
           --glm allow-no-covars hide-covar \
           --out $OUTPUT_DIR/GWAS_$COLOR \
           --threads $THREADS > /dev/null # Ẩn bớt log cho đỡ rối màn hình

    # 2. Tìm file kết quả vừa tạo (thường có đuôi .glm.logistic.hybrid)
    RESULT_FILE=$(ls $OUTPUT_DIR/GWAS_${COLOR}.${COLOR}.glm.* 2>/dev/null | head -n 1)
    
    # 3. Trích xuất SNP xịn vào file riêng
    SIG_SNP_FILE="$OUTPUT_DIR/Trích_Xuất_SNP_${COLOR}.txt"

    if [[ -f "$RESULT_FILE" ]]; then
        # Lệnh AWK: Quét file, tìm cột "P", giữ lại các dòng có P < PVAL_THRESHOLD
        awk -v p_thresh=$PVAL_THRESHOLD '
            NR==1 {
                for(i=1;i<=NF;i++) if($i=="P") p_col=i;
                print "SNP_ID\tP_value" > "'"$SIG_SNP_FILE"'"
            }
            NR>1 {
                if ($p_col != "NA" && $p_col < p_thresh) {
                    print $3 "\t" $p_col >> "'"$SIG_SNP_FILE"'"
                }
            }
        ' "$RESULT_FILE"

        # Đếm xem trích xuất được bao nhiêu SNP
        COUNT=$(tail -n +2 "$SIG_SNP_FILE" | wc -l)
        echo "    ✅ Hoàn tất! Lọc được $COUNT SNP quyết định màu lông này."
        echo "    📁 Đã lưu vào: $SIG_SNP_FILE"
    else
        echo "    ❌ Lỗi: Không tìm thấy file kết quả GWAS."
    fi
done

echo ""
echo "=========================================="
echo "HOÀN TẤT TOÀN BỘ QUÁ TRÌNH!"
echo "Tất cả file trích xuất nằm trong: $OUTPUT_DIR"
echo "=========================================="