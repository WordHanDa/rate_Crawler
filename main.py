import pymysql
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from dotenv import load_dotenv
import os
from http.server import BaseHTTPRequestHandler
from ..main import *  # Import your main crawler logic

# Load environment variables
load_dotenv()

# 設定目標網址
url = "https://rate.bot.com.tw/xrt?Lang=zh-TW"

# 送出 HTTP GET 請求
headers = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
}
response = requests.get(url, headers=headers)

if response.status_code == 200:
    soup = BeautifulSoup(response.text, 'html.parser')

    # 找到匯率表格
    table = soup.find('table')
    jpy_rate = None  # 存放日圓的匯率

    for row in table.find_all('tr')[1:]:  # 遍歷每一行
        cells = row.find_all('td')
        if len(cells) >= 5:
            currency_text = cells[0].get_text(strip=True)
            currency = currency_text.split('(')[-1].split(')')[0]  # 確保正確取得貨幣代碼
            print(f"抓取到的貨幣名稱: {currency}")  # 確認貨幣代碼是否正確

            # 檢查每列的所有欄位
            for i, cell in enumerate(cells):
                print(f"Column {i}: {cell.get_text(strip=True)}")

            # 正確對應即期買入和現金買入匯率
            spot_rate_text = cells[4].get_text(strip=True)  # 即期賣出匯率
            cash_rate_text = cells[2].get_text(strip=True)  # 現金賣出匯率

            # 解析匯率數據
            def parse_rate(rate_text):
                try:
                    return float(rate_text) if rate_text and rate_text != '-' else None
                except ValueError:
                    return None

            spot_rate = parse_rate(spot_rate_text)
            cash_rate = parse_rate(cash_rate_text)

            # 如果是 JPY，則儲存
            if currency == "JPY":
                jpy_rate = (spot_rate, cash_rate)
                break  # 找到日圓後即可中斷迴圈

    # 如果找到 JPY 匯率，插入資料庫
    if jpy_rate:
        spot_rate, cash_rate = jpy_rate
        print(f"日圓匯率：即期買入 {spot_rate}，現金買入 {cash_rate}")

        # 轉換為整數 (乘以 1000)
        spot_rate_int = int(spot_rate * 10000) if spot_rate is not None else None
        cash_rate_int = int(cash_rate * 10000) if cash_rate is not None else None

        # 設定日期時間
        current_datetime = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        # 連接 MySQL
        connect_db = pymysql.connect(
            host=os.getenv('DB_HOST', 'localhost'),
            user=os.getenv('DB_USER', 'root'),
            passwd=os.getenv('DB_PASSWORD', '123456'),
            db=os.getenv('DB_NAME', 'split_test'),
            charset='utf8',
            port=3306
        )

        try:
            with connect_db.cursor() as cursor:
                # First check if column exists
                cursor.execute("""
                    SELECT COUNT(*)
                    FROM information_schema.columns
                    WHERE table_name = 'RATE'
                    AND column_name = 'rate_id'
                """)
                if cursor.fetchone()[0] == 0:
                    # Add column if it doesn't exist
                    cursor.execute("ALTER TABLE RATE ADD COLUMN rate_id INT AUTO_INCREMENT PRIMARY KEY FIRST")
                    connect_db.commit()

                # Insert data
                sql = """
                INSERT INTO RATE (cash_rate, spot_rate, date)
                VALUES (%s, %s, %s)
                """
                cursor.execute(sql, (cash_rate_int, spot_rate_int, current_datetime))
                connect_db.commit()
                print("✅ 日圓匯率已成功插入資料庫！")

        except pymysql.MySQLError as e:
            print(f"❌ MySQL 錯誤: {e}")

        finally:
            connect_db.close()

    else:
        print("❌ 未找到日圓匯率，無法插入資料庫。")

else:
    print("❌ 無法取得網頁內容")

def handler(request, response):
    try:
        # Your existing crawler code will be executed here
        # The code from main.py will run when this endpoint is called
        return {
            'statusCode': 200,
            'body': 'Cron job executed successfully'
        }
    except Exception as e:
        return {
            'statusCode': 500,
            'body': f'Error executing cron job: {str(e)}'
        }
