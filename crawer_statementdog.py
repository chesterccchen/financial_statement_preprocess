#此程式碼是為了爬取財報狗的公司第四季個體和合併財報，需先執行 get_statementdog_cookies.py 得到cookies檔，再執行此程式

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
import time
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import requests
import os
import json

output_dir = "" #你要輸出的資料夾位置

# 公司名稱清單

COOKIE_FILE = "statementdog_cookies.json"  #需先執行 get_statementdog_cookies.py 得到cookies檔
START_URL = "https://statementdog.com/analysis/3711/e-report" # 財報狗網站


#你要爬取的公司名稱，可以從 https://www.taifex.com.tw/cht/9/futuresQADetail 取得
companies=[ "台灣精銳", "京城銀", "大成", "信邦", "喬山", "智易", "中保科", "佳世達", "巨大", "台肥", "復盛應用", "東和鋼鐵", "智原", "崇越", "遠雄", "國產", "宏全", "慧洋-KY", "世紀鋼", "裕民", "潤弘", "漢翔", "永豐餘"]

# Selenium 初始化
options = Options()

options.add_argument('--start-maximized')
options.add_argument('--disable-blink-features=AutomationControlled') # 隱藏自動化特徵
options.add_experimental_option("excludeSwitches", ["enable-automation"])
options.add_experimental_option('useAutomationExtension', False)
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
print("嘗試載入 Cookies...")
if not os.path.exists(COOKIE_FILE):
    print(f"錯誤：找不到 Cookie 檔案 '{COOKIE_FILE}'。請先執行儲存 Cookie 的腳本。")
    driver.quit()
    exit()
time.sleep(3)

driver.get("https://statementdog.com/") 

time.sleep(10) 


try:
    with open(COOKIE_FILE,'r') as f:
        cookies=json.load(f)
    print(f"從{COOKIE_FILE}載入{len(cookies)}個Cookies")

    print("正在添加Cookies到瀏覽器")
    for cookie in cookies:
        if 'expiry' in cookie and isinstance(cookie['expiry'],float):
            cookie['expiry']=int(cookie['expiry'])

        if 'domain' in cookie and cookie['domain'].startswith('.'):
            cookie['domain']=cookie['domain'][1:]
        try:
            driver.add_cookie(cookie)
        except Exception as e:
            print(f"警告:無法添加cookie'{cookie.get('name','N/A')}'.錯誤:{e}")
    print("Cookies添加完成")
    print(f"重新載入頁面或導航至目標頁面:{START_URL}")
    driver.get(START_URL)
    time.sleep(3)
except Exception as e:
    print(f"處理 Cookies 時發生錯誤: {e}")
    driver.quit()
    exit()

driver.get("https://statementdog.com/analysis/3711/e-report")
time.sleep(3)  # 等待頁面載入
for company in companies:
    # 搜尋公司
    search_input = WebDriverWait(driver, 10).until(
      EC.presence_of_element_located((By.CLASS_NAME, "search-form-input"))
  )
    search_input.clear()
    search_input.send_keys(company)
    time.sleep(1)
    search_button = driver.find_element(By.CLASS_NAME, "search-form-button")
    search_button.click()
    time.sleep(3)

    # 找到最新一年度有第4季財報的那一列
    try:
        row = driver.find_element(By.XPATH, "//table//tr[td[2]//a[contains(text(), '第 4 季財務報告書')]]")
        year = row.find_element(By.XPATH, "./td[1]").text.strip()
    except Exception as e:
        print(f"{company} 找不到有第4季財報的年度: {e}")
        continue

    # 合併財報（第2欄）
    try:
        merge_link = row.find_element(By.XPATH, "./td[2]//a[contains(text(), '第 4 季財務報告書')]")
        merge_link.click()
        WebDriverWait(driver, 10).until(lambda d: len(d.window_handles) > 1)
        driver.switch_to.window(driver.window_handles[1])
        try:
            pdf_link = WebDriverWait(driver, 15).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "a[href$='.pdf']"))
            )
            pdf_url = pdf_link.get_attribute("href")
            file_name = f"{company}_{year}_合併.pdf"
            file_path = os.path.join(output_dir, file_name)
            response = requests.get(pdf_url)
            with open(file_path, "wb") as f:
                f.write(response.content)
            print(f"下載完成: {file_name}")
        except Exception as e:
            print(f"{company} {year} 合併財報 PDF 下載失敗: {e}")
        finally:
            driver.close()  # 關閉 PDF 視窗
            driver.switch_to.window(driver.window_handles[0])  # 切回主視窗
            time.sleep(5)
    except Exception as e:
        print(f"{company} {year} 沒有合併第4季財報: {e}")

    # 個體財報（第3欄）
    try:
        individual_link = row.find_element(By.XPATH, "./td[3]//a[contains(text(), '第 4 季財務報告書')]")
        individual_link.click()
        WebDriverWait(driver, 10).until(lambda d: len(d.window_handles) > 1)
        driver.switch_to.window(driver.window_handles[1])
        try:
            pdf_link = WebDriverWait(driver, 15).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "a[href$='.pdf']"))
            )
            pdf_url = pdf_link.get_attribute("href")
            file_name = f"{company}_{year}_個體.pdf"
            file_path = os.path.join(output_dir, file_name)
            response = requests.get(pdf_url)
            with open(file_path, "wb") as f:
                f.write(response.content)
            print(f"下載完成: {file_name}")
        except Exception as e:
            print(f"{company} {year} 個體財報 PDF 下載失敗: {e}")
        finally:
            driver.close()  # 關閉 PDF 視窗
            driver.switch_to.window(driver.window_handles[0])  # 切回主視窗
            time.sleep(5)
    except Exception as e:
        print(f"{company} {year} 沒有個體第4季財報: {e}")
# 關閉瀏覽器
driver.quit()