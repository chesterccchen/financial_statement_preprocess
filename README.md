# 財報狗財報爬蟲與前處理

本專案包含多個 Python 腳本，用於自動化登入 [財報狗](https://statementdog.com/) 下載指定公司最新年份的第四季合併及個體財報（PDF 格式），並進行四大報表擷取與印章去除

- **`get_statementdog_cookies.py`**：負責登入財報狗並儲存必要的 Cookies，以便後續爬取財報。
- **`crawer_statementdog.py`**：使用儲存的 Cookies 搜尋並下載指定公司的第四季財報 PDF 檔案。

## 環境要求

在執行腳本之前，請確保滿足以下條件：

- **Python 3.6 或更高版本**已安裝。
- 擁有有效的**財報狗帳號**（需要登入才能下載財報）。
- 已安裝 **Google Chrome** 瀏覽器（用於 Selenium WebDriver）。
- 已準備好要爬取的公司名稱清單（可在 `crawer_statementdog.py` 中的 `companies` 變數自訂）。

### 必要 Python 套件

使用 pip 安裝以下 Python 套件：

```bash
pip install selenium webdriver-manager requests
```

### 獲取cookies:
```bash
python get_statementdog_cookies.py
```
### 開始爬蟲:
```bash
python crawer_statementdog.py
```
### 注意! 一個帳號一天約只能爬10~20間公司，並且爬蟲過程有些時候會跳出廣告，或是提醒下載太過頻繁，因此可能導致部分公司財報漏抓，如果需非常嚴謹的抓下每間公司的所有資料，要再額外設定一些邏輯判斷


### 接下來是將每間公司財報pdf中的四大報表抓取下來，可以從pdf中的目錄得知四大報表的位置，然而目錄的位置並不固定，並且目錄導向財報的pdf頁數有可能是錯的，因為pdf頁碼有可能與公司的財報頁碼不相同(例如第三頁與第五頁中間穿插了4-1、4-2，會導致頁碼第五頁實際是第六頁pdf)，處理方式如下: 透過gemini api掃過每個財報的前10頁，尋找目錄位置，再跳轉到財報位置


### 將四大報表pdf轉jpg
```bash
python run_pdf_to_jpg.py #記得先設定inputfile和outputfile path
```

### 將四大報表轉成jpg後，要進行紅印章去除，可以發現每個財報上的印章亮紅色部份表示沒有被文字覆蓋，暗紅色表示印章上參雜文字，因此可以透過remove_red_stamp.py，將圖片轉成hsv空間，將亮紅色部分去除(實測結果是將亮度>120的紅色去除效果最佳，也可以透過auto_thresh = np.percentile(red_v, N)取前N%亮度的紅色去除 )
```bash
python remove_red_stamp.py #記得先設定inputfile和outputfile path
```
<div style="overflow: hidden;">
  <img src="https://github.com/user-attachments/assets/f68b39c1-6cd7-4929-b50e-a63ef158704d" style="float: left; width: 45%; margin-right: 5%;" alt="左邊圖片">
  <img src="https://github.com/user-attachments/assets/2cc05b37-a1b1-4d16-916c-1cebbb923a23" style="float: right; width: 45%;" alt="右邊圖片">
</div>

然而有些照片本身印章就已經將字完全蓋住，因此無法還原，如下圖:
![image](https://github.com/user-attachments/assets/7a4a10dc-4199-455a-9830-b277043344a9)


