#此程式碼是想透過gemini api自動取出每個財務報表中的四大報表

import json
import os
import requests
from typing import Optional, Tuple, Union, Dict, Any
import time
import re
import random
import fitz  # PyMuPDF library
import argparse


pdf_folder = r"C:\Users\chester\Downloads\extract_合併_個體_137之後-20250630T055829Z-1-001\後137大公司原始pdf" #爬取的公司財務報表資料夾
output_folder = r"C:\Users\chester\Desktop\commeet\後137公司四大報表"#輸出的四大報表資料夾
log_file_path = os.path.join(output_folder, "processed_log.txt")


# --- Constants ---
MAX_RETRIES = 20
INITIAL_RETRY_DELAY = 20
MAX_RETRY_DELAY = 130.0

STATUS_SUCCESS = "SUCCESS"
STATUS_API_ERROR = "API_ERROR"
STATUS_RATE_LIMIT = "RATE_LIMIT_EXCEEDED"
STATUS_SERVER_ERROR = "SERVER_ERROR"
STATUS_REQUEST_ERROR = "REQUEST_ERROR"
STATUS_UNEXPECTED_CONTENT = "UNEXPECTED_CONTENT"
STATUS_UNKNOWN_ERROR = "UNKNOWN_ERROR"

def gemini_answer(user_prompt: str, api_key: Optional[str] = None) -> Tuple[str, Union[str, Dict[str, Any]]]:
    api_key = api_key or os.environ.get("GEMINI_API_KEY")   

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={api_key}" #可以自己設定要用甚麼模型
    headers = {"Content-Type": "application/json"}
    payload = {   # "threshold": "BLOCK_NONE"表示不過濾這些騷擾或是仇恨內容，因為財報沒有甚麼有害內容，故不過濾
        "contents": [{"parts": [{"text": user_prompt}]}],
        "generationConfig": {"temperature": 0.0},
        "safetySettings": [
            {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"}
        ]
    }

    current_retry_delay = INITIAL_RETRY_DELAY
    last_exception = None

    for attempt in range(MAX_RETRIES + 1):
        try:
            response = requests.post(url, headers=headers, data=json.dumps(payload), timeout=120)
            if response.status_code == 429 or response.status_code >= 500:
                if attempt < MAX_RETRIES:
                    wait_time = min(current_retry_delay + random.uniform(0, 0.1 * current_retry_delay), MAX_RETRY_DELAY)
                    print(f"    收到錯誤 {response.status_code}. {attempt + 1}/{MAX_RETRIES+1} 次嘗試. 等待 {wait_time:.2f} 秒後重試...")
                    time.sleep(wait_time)
                    current_retry_delay *= 2
                    last_exception = requests.exceptions.HTTPError(f"{response.status_code} {response.reason}", response=response)
                    continue
                else:
                    print(f"    達到最大重試次數 ({MAX_RETRIES}). API 錯誤 {response.status_code} 持續存在。")
                    status = STATUS_RATE_LIMIT if response.status_code == 429 else STATUS_SERVER_ERROR
                    return status, response.text
            elif 400 <= response.status_code < 500:
                print(f"    收到客戶端錯誤 {response.status_code}. 不進行重試。詳細資訊: {response.text}")
                return STATUS_API_ERROR, response.text
            response.raise_for_status()
            result = response.json()
            if "candidates" in result and len(result["candidates"]) > 0:
                candidate = result["candidates"][0]
                if "content" in candidate and "parts" in candidate["content"]:
                    parts = candidate["content"]["parts"]
                    if len(parts) > 0 and "text" in parts[0]:
                        return STATUS_SUCCESS, parts[0]["text"].strip()
            return STATUS_UNEXPECTED_CONTENT, result
        except Exception as e:
            last_exception = e
            if attempt < MAX_RETRIES:
                wait_time = min(current_retry_delay + random.uniform(0, 0.1 * current_retry_delay), MAX_RETRY_DELAY)
                print(f"    發生錯誤: {e}. {attempt + 1}/{MAX_RETRIES+1} 次嘗試. 等待 {wait_time:.2f} 秒後重試...")
                time.sleep(wait_time)
                current_retry_delay *= 2
                continue
            else:
                print(f"    達到最大重試次數 ({MAX_RETRIES}).")
                return STATUS_UNKNOWN_ERROR, str(e)
    return STATUS_UNKNOWN_ERROR, str(last_exception)
def gemini_check_page_number(page_text: str, pdf_page_num: int, api_key: str) -> bool:
    """
    用 Gemini 判斷這一頁的實際頁碼（PDF 物理頁碼）和頁面上標示的頁碼是否一致。
    """
    prompt = (
        f"這是PDF的第{pdf_page_num}頁，請判斷下列頁面內容中，頁面上標示的頁碼是否為{pdf_page_num}？"
        "如果是，請回答'相同'，否則回答'不同'。\n\n"
        f"--- 頁面內容 ---\n{page_text}"
    )
    status, response = gemini_answer(prompt, api_key)
    if status == STATUS_SUCCESS and "相同" in response:
        return True
    return False

def extract_page_numbers(text: str) -> Dict[str, Union[str, list]]:
    page_numbers = {}
    reports_to_find = {
        "資產負債表": "資產負債表",
        "綜合損益表": "綜合損益表",
        "權益變動表": "權益變動表",
        "現金流量表": "現金流量表"
    }
    for report_key, report_name in reports_to_find.items():
        match = re.search(rf"{re.escape(report_name)}\s*:\s*第\s*([\d\s\-到,~]+)\s*頁", text)
        if match:
            pages_str = match.group(1).strip()
            pages = []
            parts = pages_str.split(',')
            for part in parts:
                part = part.strip()
                if not part:
                    continue
                range_separators = ['到', '-', '~']
                is_range = False
                for sep in range_separators:
                    if sep in part:
                        try:
                            start_str, end_str = part.split(sep)
                            start = int(start_str.strip())
                            end = int(end_str.strip())
                            if start <= end:
                                pages.extend(range(start, end + 1))
                            else:
                                pages.extend(range(end, start + 1))
                                pages.reverse()
                            is_range = True
                            break
                        except ValueError:
                            is_range = True
                            break
                if not is_range:
                    try:
                        pages.append(int(part))
                    except ValueError:
                        pass
            pages = sorted(list(set(pages)))
            if pages:
                page_numbers[report_key] = pages
            else:
                page_numbers[report_key] = "無"
        else:
            page_numbers[report_key] = "無"
    return page_numbers

def save_pdf_pages(pdf_path: str, page_numbers: Dict[str, Union[str, list]], output_folder: str):
    if not page_numbers:
        print("沒有提取到任何頁碼資訊，不執行保存。")
        return
    pdf_doc = None
    try:
        pdf_doc = fitz.open(pdf_path)
        base_filename = os.path.splitext(os.path.basename(pdf_path))[0]
        total_original_pages = pdf_doc.page_count
        for report_name, pages in page_numbers.items():
            if isinstance(pages, list) and len(pages) > 0:
                output_filename = os.path.join(output_folder, f"{base_filename}_{report_name}.pdf")
                try:
                    output_doc = fitz.open()
                    for page_num in pages:
                        page_index = page_num - 1
                        if 0 <= page_index < total_original_pages:
                            output_doc.insert_pdf(pdf_doc, from_page=page_index, to_page=page_index)
                        else:
                            print(f"    警告: PDF '{os.path.basename(pdf_path)}' 中，報表 '{report_name}' 頁碼 {page_num} 超出範圍 ({total_original_pages} 頁)。跳過此頁。")
                    output_doc.save(output_filename)
                    print(f"    已保存 '{report_name}' ({len(pages)} 頁) 到 {output_filename}")
                    if not output_doc.is_closed:
                        output_doc.close()
                except Exception as e:
                    print(f"    錯誤: 保存報表 '{report_name}' 的 PDF 時發生錯誤: {e}")
            elif pages == "無":
                print(f"    報表 '{report_name}' 頁碼為 '無'，不保存。")
            else:
                print(f"    報表 '{report_name}' 的頁碼格式異常 ({type(pages)})，不保存。")
    except fitz.FileNotFoundError:
        print(f"    錯誤: PDF 檔案 '{pdf_path}' 未找到。")
    except Exception as e:
        print(f"處理 PDF '{os.path.basename(pdf_path)}' 時發生錯誤: {e}")
    finally:
        if pdf_doc and not pdf_doc.is_closed:
            pdf_doc.close()


def main():
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key or api_key == "YOUR_API_KEY_HERE":
        print("錯誤: 請在程式碼中或環境變數中設定您的 Gemini API 金鑰。")
        return # <--- 如果沒有 API Key 就直接結束

    api_call_delay_per_page = 1.0

    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
        print(f"建立輸出資料夾: {output_folder}")
    
    # <--- 步驟 1: 讀取已處理的檔案紀錄
    processed_files = set()
    if os.path.exists(log_file_path):
        try:
            with open(log_file_path, 'r', encoding='utf-8') as f:
                processed_files = {line.strip() for line in f if line.strip()}
            print(f"已從紀錄檔讀取 {len(processed_files)} 個已處理過的檔案。")
        except Exception as e:
            print(f"警告：讀取紀錄檔 '{log_file_path}' 失敗: {e}。將從頭開始處理。")

    print(f"開始處理 PDF 資料夾: {pdf_folder}")
    print(f"輸出資料夾: {output_folder}")
    print(f"每頁 API 呼叫間隔: {api_call_delay_per_page} 秒")
    # <--- 使用 sorted() 確保每次處理順序一致，方便追蹤
    pdf_files_to_process = sorted(os.listdir(pdf_folder))

    for filename in pdf_files_to_process:
        if not (filename.lower().endswith(".pdf") and os.path.isfile(os.path.join(pdf_folder, filename))):
            continue

        # <--- 步驟 2: 檢查檔案是否已經處理過
        if filename in processed_files:
            print(f"根據紀錄，檔案 '{filename}' 已處理過，跳過。")
            continue
            
        pdf_path = os.path.join(pdf_folder, filename)
        print(f"\n--- 處理新檔案：{filename} ---")
        
        pdf_doc = None
        found_toc_for_this_pdf = False
        try:
            pdf_doc = fitz.open(pdf_path)
            total_pages = pdf_doc.page_count
            print(f"  總頁數: {total_pages}")

            prompt_instruction = """辨識這頁是否為目錄，如果不是目錄就回答"不是目錄"；如果是目錄則尋找"資產負債表"、"綜合損益表"、"權益變動表"、"現金流量表"的頁數
                                 回答範例1:
                                 資產負債表: 第7到9頁
                                 綜合損益表: 第10頁
                                 權益變動表: 無
                                 現金流量表: 第11頁
                                 回答範例2:
                                 不是目錄
                                 """
            max_toc_pages = 10
            for page_index in range(min(total_pages, max_toc_pages)):
                if found_toc_for_this_pdf:
                    break
                page_num = page_index + 1
                print(f"  檢查第 {page_num}/{min(total_pages, max_toc_pages)} 頁是否為目錄...")
                
                try:
                    page = pdf_doc[page_index]
                    page_text = page.get_text()
                    if not page_text.strip(): # 如果頁面是空的，直接跳過
                        print(f"    第 {page_num} 頁為空，跳過。")
                        continue
                        
                    user_prompt = f"{prompt_instruction}\n\n--- 本頁文字內容如下 ---\n{page_text}"
                    status, response_data = gemini_answer(user_prompt, api_key)
                    
                    if status == STATUS_SUCCESS:
                        gemini_response_text = response_data
                        print(f"    API 回應 (前50字): {gemini_response_text.strip()[:50]}...")
                        
                        reports_found_in_response = any(report in gemini_response_text for report in ["資產負債表", "綜合損益表", "權益變動表", "現金流量表"])
                        is_not_toc = "不是目錄" in gemini_response_text
                        
                        if reports_found_in_response and not is_not_toc:
                            print(f"    偵測到第 {page_num} 頁可能是目錄。開始提取與驗證頁碼。")
                            page_numbers = extract_page_numbers(gemini_response_text)
                            print(f"    提取到的報表頁碼: {page_numbers}")

                            # 頁碼驗證邏輯...
                            for report_name, pages in page_numbers.items():
                                if isinstance(pages, list) and len(pages) > 0:
                                    valid_pages = []
                                    for p in pages:
                                        idx = p - 1
                                        if 0 <= idx < total_pages:
                                            page_text_to_check = pdf_doc[idx].get_text()
                                            if gemini_check_page_number(page_text_to_check, p, api_key):
                                                print(f"      [驗證成功] {report_name} 第 {p} 頁頁碼一致。")
                                                valid_pages.append(p)
                                            else:
                                                print(f"      [驗證失敗] {report_name} 第 {p} 頁頁碼不一致，捨棄。")
                                            time.sleep(api_call_delay_per_page)
                                    page_numbers[report_name] = valid_pages
                            
                            save_pdf_pages(pdf_path, page_numbers, output_folder)
                            
                            # <--- 步驟 3: 成功處理後，將檔名寫入紀錄檔
                            try:
                                with open(log_file_path, 'a', encoding='utf-8') as f:
                                    f.write(f"{filename}\n")
                                print(f"    成功！已將 '{filename}' 記錄到處理日誌中。")
                            except Exception as e:
                                print(f"    警告：無法將 '{filename}' 寫入紀錄檔: {e}")

                            found_toc_for_this_pdf = True
                        else:
                            print(f"    第 {page_num} 頁不是目錄。")
                    else:
                        print(f"    API 呼叫時發生錯誤 (頁 {page_num}): {status} - {response_data}")
                except Exception as page_processing_error:
                    print(f"  處理 PDF '{filename}' 第 {page_num} 頁時發生錯誤: {page_processing_error}")
                
                if not found_toc_for_this_pdf and api_call_delay_per_page > 0:
                    time.sleep(api_call_delay_per_page)
            
            if not found_toc_for_this_pdf:
                print(f"  在檢查的前 {min(total_pages, max_toc_pages)} 頁中未找到目錄，將此檔案視為處理失敗，不寫入紀錄。")
                # <--- 也可以在此處寫入一個 "失敗" 的日誌，但目前需求是只記錄成功的
                
        except Exception as pdf_error:
            print(f"處理 PDF 檔案 '{filename}' 時發生嚴重錯誤: {pdf_error}")
        finally:
            if pdf_doc:
                pdf_doc.close()

    print("\n--- 所有 PDF 檔案處理完成 ---")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Process PDFs to find Table of Contents and extract financial reports using Gemini API.")
    parser.add_argument("-i", "--input", help=argparse.SUPPRESS)
    parser.add_argument("-o", "--output", help=argparse.SUPPRESS)
    parser.add_argument("-e", "--errors", help=argparse.SUPPRESS)
    parser.add_argument("--delay", type=float, default=1.0, help=argparse.SUPPRESS)
    args = parser.parse_args()
    main()
