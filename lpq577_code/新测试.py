# product_data = {
#     'min_price': 349,
#     'max_price': 1001,
#     'click': 99,
#     'cart': 99
# }
#
# min_price = 350
# max_price = 18000
# maximum_views = 100
# maximum_traces = 100
#
# if (int(product_data['min_price']) < min_price and int(product_data['max_price']) > 1000) or (
#                         min_price <= int(product_data['min_price']) <= max_price):
#     print(1)
# else:
#     print(2)
#
# if int(product_data['click']) <= maximum_views and int(product_data['cart']) <= maximum_traces:
#     print(3)
# else:
#     print(4)


# title = '適用無線  m220 靜音滑鼠 辦公滑鼠 對稱滑鼠 帶無線微型接收'
# while '  ' in title:
#     title = title.replace('  ', ' ')
#
# print(title.count(' '))
import requests
url = 'https://rapi.ruten.com.tw/api/items/v2/list?gno=22511914927171&level=simple'
headers = {
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36',
}
result = requests.get(url, headers=headers).json()
if not result['data'][0]['available']:
    print(1)