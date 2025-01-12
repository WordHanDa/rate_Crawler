import requests
from bs4 import BeautifulSoup

url = "https://rate.landbank.com.tw/zh-TW/Foreign?mid=35"

response = requests.get(url)

if response.status_code == 200:
    soup = BeautifulSoup(response.text, 'html.parser')
    table = soup.find('table')
    rates = []
    for row in table.find_all('tr')[1:]:
        cells = row.find_all('td')
        if len(cells) >= 3:
            currency = cells[0].get_text(strip=True)
            buy_rate = float(cells[1].get_text(strip=True))
            sell_rate = float(cells[2].get_text(strip=True))
            rates.append((currency, buy_rate, sell_rate))

    print("可用的貨幣代碼：")
    for i, (currency, buy_rate, sell_rate) in enumerate(rates):
        print(f"{i + 1}. {currency} (買入匯率: {buy_rate}, 賣出匯率: {sell_rate})")

    mount = int(input("轉換金額："))
    select = int(input("請輸入貨幣索引號碼：").strip()) - 1

    if 0 <= select < len(rates):
        selected_currency, selected_buy_rate, _ = rates[select]
        print(f"{mount} {selected_currency} = {mount * selected_buy_rate} TWD")
    else:
        print("無效的索引號碼。")
else:
    print("無法取得網頁內容")