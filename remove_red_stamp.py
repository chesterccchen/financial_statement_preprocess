import os
import cv2
import numpy as np

add_file_name = "_去除紅章"
input_folder = ""
output_folder = ""
os.makedirs(output_folder, exist_ok=True)

def remove_red_only(image):
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    lower_red1 = np.array([0, 70, 50])
    upper_red1 = np.array([10, 255, 255])
    lower_red2 = np.array([160, 70, 50])
    upper_red2 = np.array([180, 255, 255])
    mask1 = cv2.inRange(hsv, lower_red1, upper_red1)
    mask2 = cv2.inRange(hsv, lower_red2, upper_red2)
    red_mask = cv2.bitwise_or(mask1, mask2)
    v = hsv[:, :, 2]
    bright_red_mask = cv2.bitwise_and(red_mask, (v > 120).astype(np.uint8) * 255)
    result = image.copy()
    result[bright_red_mask > 0] = [255, 255, 255]
    return result

for root, dirs, files in os.walk(input_folder):
    # 計算對應的 output 子資料夾路徑
    rel_path = os.path.relpath(root, input_folder)
    out_dir = os.path.join(output_folder, rel_path)
    os.makedirs(out_dir, exist_ok=True)
    for filename in files:
        if filename.lower().endswith('.png'):
            input_path = os.path.join(root, filename)
            # 新檔名：原檔名+add_file_name+副檔名
            name, ext = os.path.splitext(filename)
            new_filename = f"{name}{add_file_name}{ext}"
            output_path = os.path.join(out_dir, new_filename)
            img_array = np.fromfile(input_path, dtype=np.uint8)
            image = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
            if image is None:
                print(f"無法讀取圖片: {input_path}")
                continue
            no_red = remove_red_only(image)
            gray = cv2.cvtColor(no_red, cv2.COLOR_BGR2GRAY)
            success, encoded_img = cv2.imencode('.jpg', gray)
            if success:
                encoded_img.tofile(output_path)
                print(f"已處理並儲存: {output_path}")
            else:
                print(f"儲存失敗: {output_path}")

print("全部圖片紅章去除+增強完成！")
