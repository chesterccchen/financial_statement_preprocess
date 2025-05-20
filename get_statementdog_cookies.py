#由於財報狗下載檔案前需先登入，本程式碼是為了在爬財報狗之前，先登入帳號，獲取cookies檔，再進行爬蟲

import time
import json
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager


LOGIN_URL = "https://statementdog.com/users/sign_in" #進入財報狗登入頁面
COOKIE_FILE = "statementdog_cookies.json"


options = Options()
options.add_argument('--start-maximized')
options.add_argument('--disable-blink-features=AutomationControlled') 
options.add_experimental_option("excludeSwitches", ["enable-automation"])
options.add_experimental_option('useAutomationExtension', False)

driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

print(f"請前往 {LOGIN_URL} 並在瀏覽器中手動登入...")
driver.get(LOGIN_URL) # 打開登入頁面或首頁

input("完成登入後，請按 Enter 鍵繼續，腳本將儲存 Cookies...")

driver.get("https://statementdog.com/") 
time.sleep(2) # 等待頁面穩定

# 獲取 Cookies
cookies = driver.get_cookies()

# 儲存 Cookies 到檔案
with open(COOKIE_FILE, 'w') as f:
    json.dump(cookies, f)

print(f"Cookies 已成功儲存到 {COOKIE_FILE}")

driver.quit()