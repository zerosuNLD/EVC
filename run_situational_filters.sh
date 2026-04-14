#!/bin/bash
set -e

# ==============================================================================
# CẤU HÌNH ĐẦU VÀO
# ==============================================================================
THREADS=8
INPUT_PFILE="/mnt/d/darwins_dogs_genetic_set/output/DarwinsDogs_MAF_filtered"
OUTPUT_DIR="/mnt/d/darwins_dogs_genetic_set/output"

# Các thông số lọc (Bạn có thể sửa lại nếu cần)
HWE_THRESHOLD="1e-6"
LD_WINDOW="1000kb"
LD_STEP="1"
LD_R2="0.1"

echo "=========================================="
echo "BẮT ĐẦU CHẠY LỌC SITUATIONAL FILTERS"
echo "=========================================="
echo " Input: $INPUT_PFILE"
echo " HWE threshold: $HWE_THRESHOLD"
echo " LD pruning: ${LD_WINDOW}, step ${LD_STEP}, r2 ${LD_R2}"
echo "=========================================="

# ------------------------------------------------------------------------------
# BƯỚC 1 & 2: Lọc HWE (Hardy-Weinberg Equilibrium)
# ------------------------------------------------------------------------------
echo ""
echo ">>> BƯỚC 1 & 2: Tính toán và Lọc HWE"

plink2 --pfile $INPUT_PFILE \
       --dog \
       --hwe $HWE_THRESHOLD \
       --make-pgen \
       --out $OUTPUT_DIR/DarwinsDogs_HWE_filtered \
       --threads $THREADS

# ------------------------------------------------------------------------------
# BƯỚC 3: Đặt lại tên Variant ID cho chuẩn
# ------------------------------------------------------------------------------
echo ""
echo ">>> BƯỚC 3: Đổi tên Variant IDs (Chuẩn hóa ID)"

plink2 --pfile $OUTPUT_DIR/DarwinsDogs_HWE_filtered \
       --dog \
       --set-all-var-ids @:#[canFam4]\$r,\$a \
       --make-pgen \
       --out $OUTPUT_DIR/DarwinsDogs_HWE_unique_ids \
       --threads $THREADS

# ------------------------------------------------------------------------------
# BƯỚC 4: Tính toán danh sách cắt tỉa LD
# ------------------------------------------------------------------------------
echo ""
echo ">>> BƯỚC 4: Tính toán danh sách LD Pruning"

plink2 --pfile $OUTPUT_DIR/DarwinsDogs_HWE_unique_ids \
       --dog \
       --indep-pairwise $LD_WINDOW $LD_STEP $LD_R2 \
       --out $OUTPUT_DIR/DarwinsDogs_LD_PRUNED \
       --threads $THREADS

# ------------------------------------------------------------------------------
# BƯỚC 5: Áp dụng cắt tỉa LD
# ------------------------------------------------------------------------------
echo ""
echo ">>> BƯỚC 5: Áp dụng cắt tỉa LD để ra bộ dữ liệu cuối cùng"

plink2 --pfile $OUTPUT_DIR/DarwinsDogs_HWE_unique_ids \
       --dog \
       --extract $OUTPUT_DIR/DarwinsDogs_LD_PRUNED.prune.in \
       --make-pgen \
       --out $OUTPUT_DIR/DarwinsDogs_FINAL_READY \
       --threads $THREADS

# ------------------------------------------------------------------------------
# Tổng kết
# ------------------------------------------------------------------------------
echo ""
echo "=========================================="
echo "HOÀN TẤT!"
echo "=========================================="
echo "Dữ liệu cuối cùng của bạn nằm ở:"
echo "  - $OUTPUT_DIR/DarwinsDogs_FINAL_READY.pgen"
echo "  - $OUTPUT_DIR/DarwinsDogs_FINAL_READY.pvar"
echo "  - $OUTPUT_DIR/DarwinsDogs_FINAL_READY.psam"
echo ""
echo "Số lượng SNP còn lại sau khi cắt tỉa LD:"
grep -v "^#" $OUTPUT_DIR/DarwinsDogs_FINAL_READY.pvar | wc -l
