1. Clone github:
git clone https://github.com/zerosuNLD/EVC.git
cd EVC

2. Setup enviroment
conda create -n aisnp --file spec-file.txt
conda activate aisnp
pip install pandas numpy scipy scikit-learn xgboost matplotlib seaborn tqdm statsmodels requests

3. Thiết lập dường dẫn dữ liệu đầu vào
run_hard_filters.sh:
  - INPUT_BFILE: đường dẫn tới dữ liệu của input: chứa thông tin mã gen của từng dog_id ( file: darwins_dogs_genetic_set/DarwinsDogs_2024_N-3277_canfam4_gp-0.70_biallelic .bim, .bam, .bed)
  - OUTPUT_DIR: đường dẫn đầu ra sau bước hard_filters để lọc bớt các snp ( ví dụ: darwins_dogs_genetic_set/output/ )

run_situational_filters.sh:
  - INPUT_BFILE: đường dẫn tới file DarwinsDogs_MAF_filtered dữ liệu đầu ra sau bước hard_filters ( ví dụ: darwins_dogs_genetic_set/output/DarwinsDogs_MAF_filtered )
  - OUTPUT_DIR: đường dẫn đầu ra sau bước situational_filters (ví dụ: darwins_dogs_genetic_set/output)

run_gwas_colors.sh:
  - INPUT_PFILE: đường dẫn tới file DarwinsDogs_FINAL_READY sau bước situational_filters.sh
  - PHENOTYPE_FILE: đường dẫn chứa file label (plink_pheno_coat_color.txt)
  - OUTPUT_DIR: đường dẫn đầu ra sau bước gwas_colors

create_csv.py:
  - prefix: đường dẫn tới file DarwinsDogs_Analysis_Ready sau bước situational_filters
  - pheno_path: đường dẫn từ file label (plink_pheno_coat_color.txt)
  - gwas_result_dir:  đường dẫn tới file GWAS_Results sau bước gwas_color
  - output_dir: đường dẫn sau bước tạo các file csv để chuẩn bị dữ liệu dùng để train

optimize_pvalue.py:
  - prefix: đường dẫn tới file DarwinsDogs_Analysis_Ready sau bước situational_filters
  - pheno_path: đường dẫn từ file label (plink_pheno_coat_color.txt)
  - gwas_result_dir:  đường dẫn tới file GWAS_Results sau bước gwas_color
  - output_plot: đường dẫn tới output đắt đồ thị vẽ ra sau bước chọn ra p value tốt nhất

train_model.py:
  - dataset_dir: folder dẫn tới output sau bước create_csv.py
  - output_plot: đường dẫn tới hình ảnh so sánh, đánh giá hiệu suất các mô hình
    
3. Chạy:

B1: Chạy hard filters:
   ./run_hard_filters.sh
   
B2: Chạy situational filters:
   ./run_situational_filters.sh
   
B3: Tìm ra ngưỡng p_value tốt nhất
   python optimize_pvalue.py

B4: Thiết lập giá trị ngưỡng P_value trong file run_gwas_color.sh: 
    PVAL_THRESHOLD = ....

B5: Chạy gwas:
    ./run_gwas_colors.sh
    
B6: Tạo các file csv tương ứng dùng đẻ train
    python create_csv.py

B7: Train mô hình và đánh giá 
    python train_model.py

    
