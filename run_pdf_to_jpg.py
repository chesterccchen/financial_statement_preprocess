import os
from pdf2image import convert_from_path

# --- 設定路徑 ---
pdf_folder = ""
output_folder ="" 
# 確保最外層的輸出資料夾存在
os.makedirs(output_folder, exist_ok=True)

# --- 使用 os.walk() 遍歷所有子資料夾 ---
for root, dirs, files in os.walk(pdf_folder):
    # 計算對應的輸出子資料夾路徑
    # 例如，如果 root 是 '.../pdf/現金流量表', rel_path 就是 '現金流量表'
    rel_path = os.path.relpath(root, pdf_folder)
    # 建立對應的輸出子資料夾，例如 '.../output/現金流量表'
    out_dir = os.path.join(output_folder, rel_path)
    os.makedirs(out_dir, exist_ok=True)

    # --- 處理目前資料夾中的所有檔案 ---
    for filename in files:
        if filename.lower().endswith(".pdf"):
            # 建立完整的 PDF 檔案輸入路徑
            pdf_path = os.path.join(root, filename)
            # 取得不含副檔名的檔名
            base_name = os.path.splitext(filename)[0]

            print(f"正在處理: {pdf_path}")

            try:
                # 執行 PDF 轉換 這邊grayscale可以決定是否輸出灰階圖片
                images = convert_from_path(pdf_path, fmt='jpg', dpi=200,grayscale=True)

                # 如果 PDF 只有一頁
                if len(images) == 1:
                    output_path = os.path.join(out_dir, f"{base_name}.jpg")
                    images[0].save(output_path, 'JPEG')
                    print(f" -> 已儲存: {output_path}")
                # 如果 PDF 有多頁
                else:
                    for i, img in enumerate(images, start=1):
                        # 檔名加上頁碼，例如 "report_1.jpg", "report_2.jpg"
                        output_path = os.path.join(out_dir, f"{base_name}_{i}.jpg")
                        img.save(output_path, "JPEG")
                        print(f" -> 已儲存: {output_path}")

            except Exception as e:
                print(f"處理檔案 {pdf_path} 時發生錯誤: {e}")

print("所有 PDF 轉換完成。")
