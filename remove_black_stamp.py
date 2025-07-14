
import os
import cv2
import numpy as np

# --- 核心處理函式 (不變) ---
def binarize_region(region, threshold_value):
    """對指定的區域(region)進行二值化處理"""
    if region.size == 0:
        return region
    ret, binary_region = cv2.threshold(region, threshold_value, 255, cv2.THRESH_BINARY)
    return binary_region

# --- 新的雙區域處理函式 ---
def process_stamps_in_two_regions(image, threshold_value):
    """
    同時處理頂部中心和底部全寬的印章區域。
    """
    # 建立一個原始圖片的副本，我們將在這個副本上進行修改
    result_image = image.copy()
    height, width = image.shape

    # --- 1. 處理頂部區域 (頂部20%範圍內的中間1/3) ---
    top_y_end = int(height * 0.2)
    top_x_start = int(width / 3)
    top_x_end = int(width * 2 / 3)
    
    # 切片、處理、放回頂部區域
    top_roi = image[0:top_y_end, top_x_start:top_x_end]
    processed_top_roi = binarize_region(top_roi, threshold_value)
    result_image[0:top_y_end, top_x_start:top_x_end] = processed_top_roi
    print(f"已處理頂部區域: Y(0-{top_y_end}), X({top_x_start}-{top_x_end})")

    # --- 2. 處理底部區域 (底部20%的整個寬度) ---
    bottom_y_start = int(height * 0.9) # 從80%的高度開始
    
    # 切片、處理、放回底部區域
    # 注意：這裡 X 軸是整個寬度 (0 到 width)
    bottom_roi = image[bottom_y_start:height, 0:width]
    processed_bottom_roi = binarize_region(bottom_roi, threshold_value)
    result_image[bottom_y_start:height, 0:width] = processed_bottom_roi
    print(f"已處理底部區域: Y({bottom_y_start}-{height}), X(0-{width})")
    
    return result_image

# --- 你的主程式修改版 ---

add_file_name = "_去除印章_灰階"  # 檔名後綴
input_folder = r""  # 請填寫你的輸入資料夾
output_folder = r"" # 請填寫你的輸出資料夾
os.makedirs(output_folder, exist_ok=True)


# 這個閾值將同時應用於頂部和底部區域
STAMP_THRESHOLD = 60

for root, dirs, files in os.walk(input_folder):
    rel_path = os.path.relpath(root, input_folder)
    out_dir = os.path.join(output_folder, rel_path)
    os.makedirs(out_dir, exist_ok=True)
    
    for filename in files:
        if filename.lower().endswith(('.png', '.jpg', '.jpeg')):
            input_path = os.path.join(root, filename)
            
            name, ext = os.path.splitext(filename)
            new_filename = f"{name}{add_file_name}.jpg"
            output_path = os.path.join(out_dir, new_filename)

            # 1. 以灰階模式讀取圖片
            img_array = np.fromfile(input_path, dtype=np.uint8)
            gray_image = cv2.imdecode(img_array, cv2.IMREAD_GRAYSCALE)
            
            if gray_image is None:
                print(f"無法讀取圖片: {input_folder}")
                continue
            
            print(f"\n正在處理檔案: {filename}")

            # 2. 呼叫新的 "雙區域處理" 函式
            clean_image = process_stamps_in_two_regions(gray_image, threshold_value=STAMP_THRESHOLD)

            # 3. 儲存處理後的圖片
            success, encoded_img = cv2.imencode('.png', clean_image)
            if success:
                encoded_img.tofile(output_path)
                print(f"已儲存至: {output_path}")
            else:
                print(f"儲存失敗: {output_path}")

print("\n全部圖片雙區域去章處理完成！")
