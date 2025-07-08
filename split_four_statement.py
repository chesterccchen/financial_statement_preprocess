import os
import shutil

# 1. 設定來源資料夾路徑
# 請確保路徑是正確的。使用 r"..." 可以避免 Windows 路徑的反斜線問題。
source_folder = r"C:\Users\chester\Desktop\commeet\後137公司四大報表_jpg_去除紅色印章_dpi_300"

# 2. 定義四種報表類型和對應的資料夾名稱
# 字典的 "鍵" (key) 是檔名中要尋找的關鍵字
# 字典的 "值" (value) 是要建立/移入的資料夾名稱
statement_map = {
    "資產負債表": "資產負債表",
    "綜合損益表": "綜合損益表",
    "現金流量表": "現金流量表",
    "權益變動表": "權益變動表"
}

# 3. 建立目標資料夾 (如果不存在)
print("--- 步驟 1: 正在檢查並建立目標資料夾 ---")
for folder_name in statement_map.values():
    # 使用 os.path.join 來組合完整的資料夾路徑
    target_path = os.path.join(source_folder, folder_name)
    # os.makedirs 可以建立多層資料夾，exist_ok=True 表示如果資料夾已存在也不會報錯
    os.makedirs(target_path, exist_ok=True)
    print(f"資料夾 '{folder_name}' 已準備就緒。")

print("\n--- 步驟 2: 開始分類並移動檔案 ---")

# 4. 遍歷來源資料夾中的所有項目
for filename in os.listdir(source_folder):
    source_path = os.path.join(source_folder, filename)

    # A. 跳過資料夾，只處理檔案
    if os.path.isdir(source_path):
        continue

    # B. 檢查檔名包含哪種報表關鍵字
    file_moved = False
    for keyword, folder_name in statement_map.items():
        if keyword in filename:
            # 找到對應的資料夾，準備移動
            destination_folder = os.path.join(source_folder, folder_name)
            destination_path = os.path.join(destination_folder, filename)

            # 執行移動
            shutil.move(source_path, destination_path)
            
            print(f"已移動: '{filename}'  ->  資料夾 '{folder_name}'")
            file_moved = True
            break # 找到後就跳出內層迴圈，處理下一個檔案

    # C. 如果檔案沒有匹配任何關鍵字，可以印出提示 (可選)
    if not file_moved:
        # 這個判斷式可以幫助你找出是否有未被分類的檔案
        if filename.lower().endswith(".jpg"): # 只提示圖片檔
             print(f"注意: 檔案 '{filename}' 未匹配任何分類，被忽略。")


print("\n--- 所有檔案分類完成！ ---")