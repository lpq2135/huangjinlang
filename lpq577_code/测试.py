import requests
import json

headers = {
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
    'cookie': '_ga=GA1.1.745819872.1718200119; _ts_id=20240612200723212747.1718200118; _fbp=fb.2.1721286008777.586727973816170188; _ts_session=hkm8m4neqx; cf_clearance=2J8rjzx4fpO3ABYOwaKzwPCouklLgi8UGGCQqsq7z_4-1737080009-1.2.1.1-bOYp5ih16m9BQliKycrEVtEBHHRr3e2UMnzcGSygxm72hL32r_Wj0ZhSoo9Gocx.HZU3z.Yzx0woxOO2lIImjm2jSFHEW.r7qczMp1Jlp31aVc_3q.S0Ipji_uW0JvAVUUfnlc48wtrXSX9dUiNgQfQqYKufBak2s.03HX0p5S.dk9z3tIqu5JQrSIT0eFgTFIo7BHNab1HRFYG0q91kv7RidhxnyQqvZ0eXfkScf7FVDr1SzH3hr4c9wG2Sk.96DWxEjaTPQ5pJui8LH4HGovP9hKzQJwtuwA.MGItE7MXGVu7drrWnnteTiU1vF.EIJjchrKVtTTI0aUgABnOwdQ; bid_member=dLWvGqw%2FRwCUHeuB3uK9zRAVCjBeBajq66v%2FG2n2YAVoDuO2NXcf5nIiAZ9uB9%2BgC7rCd5kX8pP85s5ixeSvGWC2ln%2FGvjFJrpz6569jGd2e4SG%2BERR5TCLkkL1mDZxYHIliBVvi3BszC%2BRwVOIjOUqy3Eodkc9a7tJiMYJQF4K7j8Ei6gbxp1J4J5QaGi4QYeS%2B6wT2eqlrwFTMKmtkYqXfYs2HbSV%2F2XF0V7ds%2BGcqswOXWPdOr3K%2BmIr0UXwBldzkhh5B3wBMhtDqhcZQxm3xSvE9PbAq6qTPAlL2upPGSqdaF6oYEtwT36v9pAQAktm9pNlx8dP6CDklERaBZDl5vuTCZ0nRdPpSdpsYBRSTJZo%3D; bid_rid=20035208; bid_nick=5353275647e65786; IS_HRU=N; login=1; login_status_code=1; rt_header_info=eyJ1c2VyX25pY2siOiJodW50ZXI1NSIsImxhc3RfbG9naW5fdGltZSI6bnVsbCwibGFzdF9sb2dpbl9jaGVjayI6ZmFsc2V9; _cfuvid=M1BX1jDqwry2z4mNL8dpLNqrjguqU0h9VE5B4dT31fk-1739195061563-0.0.1.1-604800000; _clck=1td8f8r%7C2%7Cftb%7C0%7C1783; _ga_2VP4WXLL56=GS1.1.1739195062.14.1.1739195069.53.0.0; _clsk=1ladv8x%7C1739195070301%7C2%7C1%7Ck.clarity.ms%2Fcollect; _ts_session_spent=34990'
}
# 获取 ck 值
url_initial = "https://mybidu.ruten.com.tw/upload/item_initial.php"
response_initial = requests.get(url_initial, headers=headers)
ck_value = response_initial.url.split('ck=')[1]  # 获取 ck 值
# 提交表单数据
url_action = f"https://mybidu.ruten.com.tw/upload/item_action.php?ck={ck_value}"
form_data = {
    # 将spec_info字段转为JSON字符串
    "new_spec_name": 'None',
    "shop_id": "00020049",
    "g_name": "適用於12~20款高爾夫7 9.7寸車載汽車中控安卓導航一體機",
    "g_mode": "B",
    "g_direct_price": "199",
    "item_detail_price_0": 5310,
    "item_detail_count_0": 0,
    "item_detail_price_1": 5310,
    "item_detail_count_1": 274,
    "item_detail_price_2": 5310,
    "item_detail_count_2": 0,
    "item_detail_price_3": 5470,
    "item_detail_count_3": 291,
    "item_detail_price_4": 5310,
    "item_detail_count_4": 0,
    "item_detail_price_5": 5630,
    "item_detail_count_5": 284,
    "level": "2",
    "structure.temp_17819902.temp_31179065": "[]",
    "structure.temp_20339872.temp_38876675": "[]",
    "structure.temp_12938457.temp_40909425": "[]",
    "specs.temp_17819902.spec_id": "temp_17819902",
    "specs.temp_17819902.parent_id": "0",
    "specs.temp_17819902.spec_name": "1+32G（carplay）",
    "specs.temp_17819902.spec_num": "0",
    "specs.temp_17819902.spec_price": "5310",
    "specs.temp_17819902.spec_status": "Y",
    "specs.temp_17819902.spec_ext": "[]",
    "specs.temp_17819902.childs.temp_31179065": "[]",
    "specs.temp_17819902.spec_ori_price": "5310",
    "specs.temp_31179065.spec_id": "temp_31179065",
    "specs.temp_31179065.parent_id": "244276680709139",
    "specs.temp_31179065.spec_name": "9.7英寸",
    "specs.temp_31179065.spec_num": "274",
    "specs.temp_31179065.spec_price": "5310",
    "specs.temp_31179065.spec_status": "Y",
    "specs.temp_31179065.spec_ext": "[]",
    "specs.temp_31179065.childs": "[]",
    "specs.temp_31179065.spec_ori_price": "5310",
    "specs.temp_20339872.spec_id": "temp_20339872",
    "specs.temp_20339872.parent_id": "0",
    "specs.temp_20339872.spec_name": "2+32G（carplay）",
    "specs.temp_20339872.spec_num": "0",
    "specs.temp_20339872.spec_price": "5310",
    "specs.temp_20339872.spec_status": "Y",
    "specs.temp_20339872.spec_ext": "[]",
    "specs.temp_20339872.childs.temp_38876675": "[]",
    "specs.temp_20339872.spec_ori_price": "5310",
    "specs.temp_38876675.spec_id": "temp_38876675",
    "specs.temp_38876675.parent_id": "244276680709162",
    "specs.temp_38876675.spec_name": "9.7英寸",
    "specs.temp_38876675.spec_num": "291",
    "specs.temp_38876675.spec_price": "5470",
    "specs.temp_38876675.spec_status": "Y",
    "specs.temp_38876675.spec_ext": "[]",
    "specs.temp_38876675.childs": "[]",
    "specs.temp_38876675.spec_ori_price": "5470",
    "specs.temp_12938457.spec_id": "temp_12938457",
    "specs.temp_12938457.parent_id": "0",
    "specs.temp_12938457.spec_name": "2+64G（carplay）",
    "specs.temp_12938457.spec_num": "0",
    "specs.temp_12938457.spec_price": "5310",
    "specs.temp_12938457.spec_status": "Y",
    "specs.temp_12938457.spec_ext": "[]",
    "specs.temp_12938457.childs.temp_40909425": "[]",
    "specs.temp_12938457.spec_ori_price": "5310",
    "specs.temp_40909425.spec_id": "temp_40909425",
    "specs.temp_40909425.parent_id": "244276680709207",
    "specs.temp_40909425.spec_name": "9.7英寸",
    "specs.temp_40909425.spec_num": "284",
    "specs.temp_40909425.spec_price": "5630",
    "specs.temp_40909425.spec_status": "Y",
    "specs.temp_40909425.spec_ext": "[]",
    "specs.temp_40909425.childs": "[]",
    "specs.temp_40909425.spec_ori_price": "5630",

    "show_num": "199",
    "item_detail_note_0": "",
    "goods_no": "",
    "is_goods_sale": "0",
    "sale_start_time": "",
    "sale_end_time": "",
    "g_condition": "B",
    "stock_status": "1",
    "customized_ship_date": "",
    "pre_order_ship_date": "202502",
    "text2": "<p>gfhgfhgf</p>",
    "g_flag": "6_1",
    "g_location": "台北市",
    "g_ship": "D",
    "g_pay_way": "PAYLINK,SELF_FAMI_COD,SELF_SEVEN_COD,SELF_HILIFE_COD",
    "g_deliver_way": "{SELF_FAMI_COD:60,SELF_SEVEN_COD:60,SELF_HILIFE_COD:45,HOUSE:100,ISLAND:300,FAMI:60,SEVEN:60,HILIFE:45}"
}
response_action = requests.post(url_action, headers=headers, data=form_data)

# 预览页面
# url_preview = f"https://mybidu.ruten.com.tw/upload/item_preview.php?ck={ck_value}"
# response_preview = requests.get(url_preview, headers=headers)

# 提交最终化请求
url_finalize = f"https://mybidu.ruten.com.tw/upload/item_finalize.php?ck={ck_value}"
response_finalize = requests.post(url_finalize, headers=headers)

# 完成上架
# response_finish = requests.get(response_finalize.url, headers=headers)

print(response_finalize.text)  # 输出上架完成后的响应内容
