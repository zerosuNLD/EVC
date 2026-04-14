#!/bin/bash
set -e

# ==========================================
# CẤU HÌNH ĐẦU VÀO (Configuration)
# ==========================================
THREADS=8
INPUT_BFILE="/mnt/d/darwins_dogs_genetic_set/DarwinsDogs_2024_N-3277_canfam4_gp-0.70_biallelic"
OUTPUT_DIR="/mnt/d/darwins_dogs_genetic_set/output"
MIN_AF=0.0016

mkdir -p $OUTPUT_DIR

echo "=========================================="
echo "BẮT ĐẦU CHẠY LỌC DỮ LIỆU (HARD FILTERS)"
echo "=========================================="

# ------------------------------------------------------------------------------
# HARD FILTER 1: Chỉ giữ SNP + Biallelic (2 alen)
# ------------------------------------------------------------------------------
echo ""
echo ">>> BƯỚC 1: Lọc SNP và Biallelic"

plink2 --bfile $INPUT_BFILE \
       --dog \
       --snps-only \
       --max-alleles 2 \
       --make-pgen \
       --out $OUTPUT_DIR/DarwinsDogs_SNP_filtered \
       --threads $THREADS

# ------------------------------------------------------------------------------
# Tính toán thống kê tần số trước khi lọc MAF
# ------------------------------------------------------------------------------
echo ""
echo ">>> Đang tính toán tần số alen (pre-MAF)..."

plink2 --pfile $OUTPUT_DIR/DarwinsDogs_SNP_filtered \
       --dog \
       --freq \
       --out $OUTPUT_DIR/DarwinsDogs_SNP_filtered_info \
       --threads $THREADS

# ------------------------------------------------------------------------------
# HARD FILTER 2: Lọc theo tần số alen phụ (MAF)
# ------------------------------------------------------------------------------
echo ""
echo ">>> BƯỚC 2: Lọc MAF"

plink2 --pfile $OUTPUT_DIR/DarwinsDogs_SNP_filtered \
       --dog \
       --min-af $MIN_AF \
       --make-pgen \
       --out $OUTPUT_DIR/DarwinsDogs_MAF_filtered \
       --threads $THREADS

# ------------------------------------------------------------------------------
# Tính toán thống kê tần số sau khi lọc MAF
# ------------------------------------------------------------------------------
echo ""
echo ">>> Đang tính toán tần số alen (post-MAF)..."

plink2 --pfile $OUTPUT_DIR/DarwinsDogs_MAF_filtered \
       --dog \
       --freq \
       --out $OUTPUT_DIR/DarwinsDogs_MAF_filtered_info \
       --threads $THREADS

# ------------------------------------------------------------------------------
# Tổng kết (Summary)
# ------------------------------------------------------------------------------
echo ""
echo "=========================================="
echo "QUÁ TRÌNH LỌC ĐÃ HOÀN TẤT"
echo "=========================================="
echo ""
echo "Số lượng variants:"
echo -n "  Sau khi lọc SNP/biallelic: "
grep -v "^#" $OUTPUT_DIR/DarwinsDogs_SNP_filtered.pvar | wc -l

echo -n "  Sau khi lọc MAF:           "
grep -v "^#" $OUTPUT_DIR/DarwinsDogs_MAF_filtered.pvar | wc -l
echo ""
