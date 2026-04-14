import os
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import f1_score, accuracy_score
from tqdm import tqdm

# Các thuật toán cơ bản
from sklearn.svm import SVC
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier

from xgboost import XGBClassifier
from sklearn.neural_network import MLPClassifier

# --- 1. CẤU HÌNH ĐƯỜNG DẪN ---
dataset_dir = "/mnt/d/darwins_dogs_genetic_set/output/ML_Datasets"
output_plot = "/mnt/d/darwins_dogs_genetic_set/output/Model_Comparison_Chart.png"

IGNORE_LABELS = [
    "Q243_white_or_cream_coat_color",
    "Q243_red_or_liver_or_brown_or_tan_coat_color"
]

models = {
    "SVM (Linear)": SVC(kernel='linear', C=1.0, random_state=42),
    "Logistic Regression": LogisticRegression(max_iter=1000, random_state=42),
    "Random Forest": RandomForestClassifier(n_estimators=100, random_state=42),
    "Gradient Boosting": GradientBoostingClassifier(n_estimators=100, random_state=42),
    "XGBoost": XGBClassifier(eval_metric='logloss', random_state=42),    
    "Neural Net (1 Layer)": MLPClassifier(hidden_layer_sizes=(100,), max_iter=1000, random_state=42)
}

results = []

# Lọc danh sách các file hợp lệ trước để thanh tiến độ biết tổng số lượng
valid_files = [f for f in os.listdir(dataset_dir) if f.startswith("Dataset_") and f.endswith(".csv")]

print(f"🏁 Bắt đầu quá trình huấn luyện cho các màu lông 🏁\n")

# --- 2. QUÉT TẤT CẢ CÁC FILE VỚI THANH TIẾN ĐỘ (tqdm) ---
for file in tqdm(valid_files, desc="Tiến độ tổng thể", unit=" màu"):
    color_name = file.replace("Dataset_", "").replace(".csv", "")
    
    # KỂM TRA XEM CÓ NẰM TRONG DANH SÁCH BỎ QUA KHÔNG
    if color_name in IGNORE_LABELS:
        tqdm.write(f"⏭️ Bỏ qua {color_name}: Nằm trong danh sách loại trừ.")
        continue
        
    file_path = os.path.join(dataset_dir, file)
    df = pd.read_csv(file_path)
    
    # Nếu cột nhãn không có trong df (lỗi dữ liệu), bỏ qua
    if color_name not in df.columns:
        tqdm.write(f"⚠️ Bỏ qua {color_name}: Không tìm thấy cột nhãn.")
        continue
        
    X = df.drop(columns=['dog_id', color_name])
    y = df[color_name]
    
    # Kiểm tra xem dữ liệu có đủ 2 loại (Có màu/Không màu) không
    if y.nunique() < 2:
        tqdm.write(f"⚠️ Bỏ qua {color_name}: Chỉ có 1 loại nhãn (Không thể train).")
        continue

    # Chia tập và chuẩn hóa
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)
    
    # Huấn luyện 6 mô hình
    for model_name, model in models.items():
        # Do Mạng Nơ-ron chạy có thể tốn thời gian hơn một chút với gen, tqdm vẫn sẽ giữ mượt
        model.fit(X_train_scaled, y_train)
        y_pred = model.predict(X_test_scaled)
        
        # Tính F1-Score
        f1 = f1_score(y_test, y_pred, average='weighted', zero_division=0)
        acc = accuracy_score(y_test, y_pred)
        
        # Lưu kết quả
        results.append({
            "Color": color_name.replace("Q243_", "").replace("_coat_color", ""), 
            "Model": model_name,
            "F1_Score": f1,
            "Accuracy": acc
        })
            
print("\n✅ Đã huấn luyện xong toàn bộ 6 mô hình!")

# --- 3. VẼ BIỂU ĐỒ VÀ LƯU ẢNH ---
if len(results) > 0:
    print("🎨 Đang vẽ biểu đồ so sánh...")
    df_results = pd.DataFrame(results)

    # Thiết lập kích thước ảnh
    plt.figure(figsize=(16, 8))
    sns.set_theme(style="whitegrid")

    # Vẽ biểu đồ cột nhóm
    chart = sns.barplot(
        data=df_results, 
        x="Color", 
        y="F1_Score", 
        hue="Model",
        palette="Set2" 
    )

    # Trang trí biểu đồ
    plt.title("So sánh hiệu suất các mô hình trên từng màu lông (F1-Score)", fontsize=16, fontweight='bold')
    plt.xlabel("Đặc điểm Màu Lông", fontsize=12)
    plt.ylabel("Điểm F1-Score ", fontsize=12)
    plt.ylim(0, 1.1) 
    plt.xticks(rotation=45, ha="right") 

    # Chuyển bảng chú giải ra ngoài để không che lấp đồ thị
    plt.legend(title="Mô hình", bbox_to_anchor=(1.01, 1), loc='upper left')
    plt.tight_layout()

    # Lưu thành file PNG
    plt.savefig(output_plot, dpi=300)
    print(f"🎉 HOÀN TẤT! Biểu đồ đã được lưu tại: {output_plot}")

    # In thêm một bảng text ngắn gọn ra Terminal
    print("\n--- Trung bình F1-Score của các mô hình ---")
    avg_results = df_results.groupby("Model")["F1_Score"].mean().sort_values(ascending=False)
    for model, score in avg_results.items():
        print(f"🥇 {model}: {score:.4f}")
else:
    print("⚠️ Không có dữ liệu hợp lệ nào được huấn luyện để vẽ biểu đồ.")