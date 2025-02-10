import requests
import re
import time

# 1?? 创建会话 (保持 cookies)
session = requests.Session()

# 2?? 请求 `item_initial.php` 获取 `ck`
initial_url = "https://mybidu.ruten.com.tw/upload/item_initial.php"
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36",
    "cookie": "_ga=GA1.1.745819872.1718200119; _ts_id=20240612200723212747.1718200118; bid_totp=j1pHBnRgLAuTaXDHYMYoJzY4Yn1DumPw7WhbEUp%2FOhZyBaqLoZnhmRRBdoc0vCQBzL0lGT6BVUz7p%2BJsvn8lLF%2BOgEkkws0IM2sAC81agXs8RKQ%2FdECeksOiZ7FOpwM%2FrTxjwk1%2FtWJEv8cHeuZdLH%2B6brcsB%2F2ZhrfxiPCFmn8afkI%2BKQrc5QDlNJC1oEHQHeE%2BZ20%3D; _fbp=fb.2.1723430307477.523152985603678383; cf_clearance=BkIarvYQmlZEP7fvb1joBwH9ZtwKt36CBZshV_6dvjM-1728632429-1.2.1.1-cqKH._1E8cZ_htpM.pS_9qWBAgZZpJk289hUM7mB379lBj9A5afJVthX_q42wlv3PmrqRbueKr545YfEAPpo4e6NhgxkTrOQ0MyoLvZ6itOFVVFsvxlkHSN5PWD8rjJ6sYZH8TuirPo1tiLGfhN0iI.JHSs.rpsOYFAYeJ1oqubga1X9iw1P1hNM_UjO0eAupKozm1GAdufRCnHStjMzJp.vakAYLsNM13R2C9lqkZ7ZO.rOcxoRL8hRIaXwNPiUJmiIcPyr4YvvIGdr2hQi243t0n3xVrHm3YWhyfXBDJswDacY6CFIBzBhM6Owtoq8ge6.ZNjL8hdjcHqed5F7FHtbn9xVu9F5Q7svxy64cwm8hmtWHIlmWj7yIy0H.xK_CMixmOu.luYUDi7qOMmHNzusSs8IYpm2337HC51DbDhYVJSbYTtrSPxOHja.iKHz; bid_rid=20024183; bid_nick=23331686472716d6; bid_member=OtDeVUPvVqN0r8wqiql%2B5OqBsBak9y5RvBZcQ68FUthDTMuofkza3cEjwXBiYtPiuFC74jdb37B3UDst7827VVOHEUND9pKO6748%2Fyu5YLccef%2F6uGIc0BENVocfjYlu3BHJgB53o0n8bkBwy8shKf4VYc%2FtWbJI6bhlZ%2F7kvtSvZefHnuL%2F4seoVOc05si%2BzHlJuglC8G%2FyX%2BgZP5gQAPcj7ulZB6gtZ%2F1tArVFHiVXPAtpM4qjtNKxTC0fOXE%2BTsiK%2B4yZ%2FSDvZnruWQ3tKgd31de88%2FkTZziBnH9rePbPFD3oPj84y%2BUPWeyY2YVKw%2FglQhMeThFqICfLYp6pGVPW7E2gQQUbnycgQas%2FG97yxN0%3D; _cfuvid=jWpeFbBW4PGjZqvi7JrJfgEoWR7QM3FxcPnyBNHd5LE-1737445399086-0.0.1.1-604800000; rt_header_info=eyJ1c2VyX25pY2siOiJtYXJ0aGEzMiIsImxhc3RfbG9naW5fdGltZSI6bnVsbCwibGFzdF9sb2dpbl9jaGVjayI6ZmFsc2V9; _ts_session=v1d33ioq05; _clck=fyz7wb%7C2%7Cfsr%7C0%7C1847; itemUploadOtpUrl=https%3A%2F%2Fmybidu.ruten.com.tw%2Fupload%2Fitem_initial.php; itemUploadOtpCookieRecords=j8BnzFuG5GI%2FF82QPUZDNb9DK0gGwT4IjkWlFdVYC7XWix8odHyUeEROSCrW8cx5nURV3AGZUOF9BMkVSXnKps%2BE8TCHfT1mG4QQ2OU%2FobcNhhaeAhxCYs%2FrTH7nKhVBnZKSafxnaUtoRUtkAMQQQUUAIke2veINMpB1oYYRO0gzAxyFWL5IfO%2BZt5Y%2BKgx8LIxW%2FMnxIGaglqlYWc16J%2BWFvfh15ITT47A%3D; _clsk=f3aa5y%7C1737445566807%7C3%7C0%7Cu.clarity.ms%2Fcollect; _ga_2VP4WXLL56=GS1.1.1737445399.6.1.1737445568.39.0.0; _ts_session_spent=156864",
}

response = session.get(initial_url, headers=headers)

# 解析 `ck`
ck_match = re.search(r"ck=([\w\d]+)", response.url)
if not ck_match:
    print("? 未找到 ck，终止流程")
    exit()
ck = ck_match.group(1)
print(f"? 获取 ck 成功: {ck}")

# 3?? 发送商品信息到 `item_action.php`
post_url = f"https://mybidu.ruten.com.tw/upload/item_action.php?ck={ck}"

data = {
    "shop_id": "00150006",
    "g_name": "ghgf",
    "user_class_select": "6416213",
    "g_mode": "B",
    "g_direct_price": "199",
    "show_num": "199",
    "g_buyer_limit_num": "0",
    "new_spec_name": "",
    "goods_no": "",
    "is_goods_sale": "0",
    "sale_start_time": "",
    "sale_end_time": "",
    "g_condition": "B",
    "stock_status": "1",
    "customized_ship_date": "",
    "pre_order_ship_date": "202502",
    "text2": "<p>zhgjgj</p>",
    "g_flag": "",
    "g_location": "台北市",
    "g_ship": "A",
    "g_pay_way": "PAYLINK,SELF_FAMI_COD,SELF_SEVEN_COD,SELF_HILIFE_COD",
    "g_deliver_way": "{SELF_FAMI_COD:60,SELF_SEVEN_COD:60,SELF_HILIFE_COD:40,HOUSE:100,ISLAND:300,FAMI:60,SEVEN:60,HILIFE:45}",
    "g_accept_shiprule": "1"
}

response = session.post(post_url, headers=headers, data=data, allow_redirects=True)
print(f"?? 商品提交状态码: {response.status_code}")

# 4?? 访问 `item_preview.php` 预览页面
preview_url = f"https://mybidu.ruten.com.tw/upload/item_preview.php?ck={ck}"
response = session.get(preview_url, headers=headers)
print(f"? 预览页面访问状态码: {response.status_code}")

# 5?? 发送 `item_finalize.php` 确认上架
finalize_url = f"https://mybidu.ruten.com.tw/upload/item_finalize.php?ck={ck}"
response = session.post(finalize_url, headers=headers)
print(f"?? 确认上架请求状态码: {response.status_code}")

# 6?? 访问 `item_finish.php` 确认上架成功
finish_url = f"https://mybidu.ruten.com.tw/upload/item_finish.php?g_no=22507733730605&ck={ck}"
response = session.get(finish_url, headers=headers)
print(f"? 最终上架状态码: {response.status_code}")

# 7?? 检查是否成功
if "成功" in response.text or response.status_code == 200:
    print("?? 商品成功上架！")
else:
    print("? 商品上架失败，请检查数据")
