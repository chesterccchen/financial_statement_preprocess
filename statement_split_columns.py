import cv2
import numpy as np
import os
import random
from collections import Counter

line_width=1 #畫線的寬度

input_directory = ""
output_directory = ""


def find_and_draw_column_separators(image_to_draw_on, representative_lines, all_horizontal_lines):
    """
    根據代表性的一列橫線，找出欄位間隙並繪製垂直分隔線。

    Args:
        image_to_draw_on (numpy.ndarray): 要在上面繪圖的影像。
        representative_lines (list): 從表格結構中篩選出的一列橫線 (例如 main_table_lines)。
        all_horizontal_lines (list): 所有合併後的橫線，用來確定表格的垂直範圍。
    """
    if not representative_lines or len(representative_lines) < 2:
        return

    # 1. 根據 x1 座標對代表性橫線進行排序
    sorted_lines = sorted(representative_lines, key=lambda line: line[0])

    # 2. 從所有橫線中確定整個表格的頂部和底部
    all_y_coords = []
    for line in all_horizontal_lines:
        # line 是 [x1, y1, x2, y2]，合併後 y1 和 y2 會很接近
        all_y_coords.append(line[1])
    
    if not all_y_coords:
        return
        
    table_top = min(all_y_coords)   # -10 向上延伸一點
    table_bottom = max(all_y_coords)  # +10 向下延伸一點

    # 3. 計算相鄰線段間隙的中點，並儲存為欄位分隔線的 x 座標
    column_x_coords = []
    for i in range(len(sorted_lines) - 1):
        # 當前線段的終點 x 座標
        end_of_line1 = sorted_lines[i][2]
        # 下一線段的起點 x 座標
        start_of_line2 = sorted_lines[i+1][0]
        
        # 計算間隙的中點
        separator_x = (end_of_line1 + start_of_line2) // 2
        column_x_coords.append(separator_x)


    # 4. 繪製垂直的欄位分隔線
    for x in column_x_coords:
        cv2.line(image_to_draw_on, (x, table_top), (x, table_bottom), (0, 0, 255), line_width)

def filter_rows_by_mode(lines,y_threshold=10):
    if not lines:
        return []
    lines.sort(key=lambda line: line[1])
    rows=[]
    current_row=[lines[0]]
    for i in range(1,len(lines)):
        avg_y_current_row=np.mean( [line[1] for line in current_row])
        if abs(lines[i][1]-avg_y_current_row)<y_threshold:
            current_row.append(lines[i])
        else:
            rows.append(current_row)
            current_row=[lines[i]]
    rows.append(current_row)


    filtered_rows_for_mode_calculation = [row for row in rows if len(row) > 4]

    row_lengths=[len(row) for row in filtered_rows_for_mode_calculation]
    if not row_lengths:
        return []
    counts=Counter(row_lengths)
    mode_length=counts.most_common(1)[0][0]

    filtered_lines=[]
    for row in reversed(rows):
        if len(row)==mode_length:
            filtered_lines.extend(row)
            break

    return filtered_lines

def imread_unicode(path, flags=cv2.IMREAD_COLOR):
    """
    取代 cv2.imread，使其支援包含非 ASCII 字元 (如中文) 的路徑。
    """
    try:
        raw_data = np.fromfile(path, dtype=np.uint8)
        img = cv2.imdecode(raw_data, flags)
        return img
    except Exception as e:

        return None

def imwrite_unicode(path, img):
    """
    取代 cv2.imwrite，使其支援包含非 ASCII 字元 (如中文) 的路徑。
    """
    try:
        ext = os.path.splitext(path)[1]
        result, buffer = cv2.imencode(ext, img)
        if result:
            with open(path, mode='wb') as f:
                f.write(buffer)
            return True
        else:
            return False
    except Exception as e:


        return False

def merge_lines_optimized(lines, y_threshold=5, x_threshold=5):
    """
    Args:
        lines (list or None): HoughLinesP 偵測到的線段列表。
        y_threshold (int): 判定線段是否在同一列的 Y 座標最大容許差值。
        x_threshold (int): 水平方向上，線段間隙或重疊的最大容許值。
        
    Returns:
        list: 最終合併後的線段列表。
    """
    if lines is None or len(lines) < 2:
        return [] if lines is None else [list(l[0]) for l in lines]

    # 1. 預處理：將 (N, 1, 4) 轉為 list of lists，並確保 x1 < x2
    processed_lines = []
    for line in lines:
        x1, y1, x2, y2 = line[0]
        if x1 > x2:
            x1, x2 = x2, x1
        processed_lines.append([x1, y1, x2, y2])

    # 2. 分群：根據 Y 座標將線段分到不同的群組 (rows)
    # 首先根據 y 座標排序，方便分群
    processed_lines.sort(key=lambda line: line[1])
    
    groups = []
    if not processed_lines:
        return []
    
    current_group = [processed_lines[0]]
    for i in range(1, len(processed_lines)):
        # 計算目前群組的平均 y 座標
        avg_y_current_group = np.mean([line[1] for line in current_group])
        
        # 如果當前線段的 y 與群組平均 y 接近，則加入群組
        if abs(processed_lines[i][1] - avg_y_current_group) < y_threshold:
            current_group.append(processed_lines[i])
        else:
            # 否則，目前群組結束，開始一個新群組
            groups.append(current_group)
            current_group = [processed_lines[i]]
    groups.append(current_group) # 加入最後一個群組

    # 3. 在每個群組內進行合併
    final_merged_lines = []
    for group in groups:
        if not group:
            continue
        
        # 根據 x1 座標對群組內的線段進行排序
        group.sort(key=lambda line: line[0])
        
        # 從第一條線開始合併
        merged_line = list(group[0]) # 使用 list() 確保是副本
        
        for i in range(1, len(group)):
            current_line = group[i]
            
            # 檢查當前線段是否與已合併的線段重疊或接近
            if current_line[0] <= merged_line[2] + x_threshold:
                # 若是，則合併：更新 x2 為兩者中較大的值
                merged_line[2] = max(merged_line[2], current_line[2])
                # 可以選擇更新 y 值為平均值，但因為已在同一群組，差異不大
                # merged_line[1] = (merged_line[1] + current_line[1]) // 2
            else:
                # 若否，則上一條合併線段結束，將其加入結果
                final_merged_lines.append(merged_line)
                # 開始一個新的合併線段
                merged_line = list(current_line)
        
        # 將最後一條合併的線段加入結果
        final_merged_lines.append(merged_line)
        
    return final_merged_lines

def detect_and_merge_lines(input_path, output_path):
    image_gray = imread_unicode(input_path, cv2.IMREAD_GRAYSCALE)
    _, thresh = cv2.threshold(image_gray, 200, 255, cv2.THRESH_BINARY_INV)

    #edges = cv2.Canny(image_gray, 50, 150)

    horizontal_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (20, 1))
    #detected_lines_img = cv2.erode(thresh, horizontal_kernel, iterations=2)
    detected_lines_img = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, horizontal_kernel, iterations=1) #先用20*1的kernel侵蝕再膨脹
    kernel = np.ones((3, 3), np.uint8)
    detected_lines_img = cv2.dilate(detected_lines_img, kernel, iterations=1) #用3*3 kernel修補線的寬度
    imwrite_unicode("debug_detected_lines.jpg", detected_lines_img)
    #dilation_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (9, 1))
    #detected_lines_img = cv2.dilate(detected_lines_img, dilation_kernel, iterations=2)
    lines = cv2.HoughLinesP(detected_lines_img, 1, np.pi / 180,  threshold=40, minLineLength=40, maxLineGap=2)

    output_image = cv2.cvtColor(image_gray, cv2.COLOR_GRAY2BGR)

    if lines is not None:


        merged_lines = merge_lines_optimized(lines, y_threshold=10, x_threshold=0)
        

        main_table_lines = filter_rows_by_mode(merged_lines, y_threshold=10)

        #畫出每個column的線
        # for line in merged_lines:
        #     x1, y1, x2, y2 = line
        #     #color = (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))

        #     cv2.line(output_image, (x1, y1), (x2, y2), (0, 0,255), 2)

        # for line in main_table_lines:
        #     x1, y1, x2, y2 = line
        #    # color = (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))

        #     cv2.line(output_image, (x1, y1), (x2, y2), (0, 255,0), 2)
        find_and_draw_column_separators(output_image, main_table_lines, merged_lines)

    imwrite_unicode(output_path, output_image)


# --- 主程式執行區塊 ---
if __name__ == "__main__":
    # 1. 設定輸入和輸出資料夾的路徑
    # 2. 檢查並建立輸出資料夾 (如果它不存在)
    if not os.path.exists(output_directory):
        os.makedirs(output_directory)


    # 3. 獲取輸入資料夾中所有檔案的列表
    try:
        filenames = os.listdir(input_directory)
    except FileNotFoundError:

        filenames = []

    # 4. 遍歷所有檔案
    for filename in filenames:
        # 檢查檔案是否為常見的圖片格式
        if filename.lower().endswith(('.png', '.jpg', '.jpeg')):
            # 組合完整的輸入和輸出檔案路徑
            input_path = os.path.join(input_directory, filename)
            output_path = os.path.join(output_directory, filename)

            detect_and_merge_lines(input_path, output_path)
