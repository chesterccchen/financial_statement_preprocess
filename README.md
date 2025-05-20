# 財報狗財報爬蟲與前處理

本專案自動化登入 [財報狗](https://statementdog.com/)，下載指定公司最新年度第四季合併及個體財報（PDF），並進行四大報表擷取與紅色印章去除等前處理。

---

## 專案流程總覽

1. **登入並取得 Cookies**
2. **下載公司財報 PDF**
3. **擷取四大報表 PDF**
4. **PDF 轉 JPG 圖片**
5. **去除紅色印章**

---

## 主要腳本說明

| 檔案名稱                      | 功能簡述                                      |
|------------------------------|-----------------------------------------------|
| `get_statementdog_cookies.py` | 自動登入財報狗並儲存 Cookies                  |
| `crawer_statementdog.py`      | 下載指定公司第四季財報 PDF                    |
| `gemini_extract_statement.py` | 擷取財報中的四大報表 PDF                      |
| `run_pdf_to_jpg.py`           | 將四大報表 PDF 轉為 JPG 圖片                  |
| `remove_red_stamp.py`         | 去除 JPG 圖片中的紅色印章                     |

---

## 環境需求

- **Python 3.6+**
- **Google Chrome**（用於 Selenium WebDriver）
- **財報狗帳號**（需登入下載財報）
- 需自訂公司名稱清單（於 `crawer_statementdog.py` 的 `companies` 變數）

### 安裝必要套件

```bash
pip install selenium webdriver-manager requests
```

---

## 使用步驟

### 1. 取得 Cookies

```bash
python get_statementdog_cookies.py
```

### 2. 開始爬取財報

```bash
python crawer_statementdog.py
```

> **注意：**  
> - 一個帳號一天約只能爬 20 間公司。  
> - 可能遇到廣告或下載頻率限制，導致部分公司財報漏抓。  
> - 若需完整抓取所有公司，建議額外設計重試與錯誤處理邏輯。

### 3. 擷取四大報表 PDF

```bash
python gemini_extract_statement.py
```

- 透過gemini自動偵測 PDF 目錄位置，根據目錄頁碼跳轉至四大報表。
- 檢查這些頁碼和pdf實際頁數是否相同，如果不同就捨去(如果不同可能導致頁數位移，將資產負債表判定成綜合損益表)
- 被捨去的情況通常是第三頁與第五頁中間穿插了4-1、4-2，會導致頁碼第五頁實際是第六頁pdf

### 4. 將四大報表 PDF 轉為 JPG

```bash
python run_pdf_to_jpg.py
```

### 5. 去除紅色印章

```bash
python remove_red_stamp.py
```

- 會將圖片轉為 HSV 色彩空間，去除亮度高於 120 的紅色區域。
- 也可用 `auto_thresh = np.percentile(red_v, N)` 取前 N% 亮度紅色去除。

---

## 處理效果展示

| 原始圖片 | 去除紅章後 |
|:---:|:---:|
| <img src="https://github.com/user-attachments/assets/f68b39c1-6cd7-4929-b50e-a63ef158704d" width="300"/> | <img src="https://github.com/user-attachments/assets/2cc05b37-a1b1-4d16-916c-1cebbb923a23" width="300"/> |

> **注意：**  
> 有些財報印章會完全蓋住文字，無法還原，如下圖所示：

![image](https://github.com/user-attachments/assets/7a4a10dc-4199-455a-9830-b277043344a9)

---
