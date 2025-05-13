import requests
import json
import re

# def product_items_v2(product_id):
#     url = f'https://rapi.ruten.com.tw/api/items/v2/list?gno={product_id}&level=simple'
#     headers = {
#         'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36',
#     }
#     result = requests.get(url, headers=headers).json()
#     return result['data'][0]['available']
#
# res = product_items_v2('22430179804426')
# print(res)
# images = [
#       'https://cbu01.alicdn.com/img/ibank/O1CN013Np2c12G5ZDQPX7LD_!!2196368964-0-cib.jpg',
#       'https://cbu01.alicdn.com/img/ibank/O1CN01rQPqrW2G5ZDV2Y5m9_!!2196368964-0-cib.jpg',
#       'https://cbu01.alicdn.com/img/ibank/O1CN01TNW7I92G5ZDZuCDMm_!!2196368964-0-cib.jpg',
#       'https://cbu01.alicdn.com/img/ibank/O1CN016C8vM52G5ZDYlK362_!!2196368964-0-cib.jpg',
#       'https://cbu01.alicdn.com/img/ibank/O1CN01jeCge02G5ZDVXe9La_!!2196368964-0-cib.jpg',
#       'https://cbu01.alicdn.com/img/ibank/O1CN011EDHTc2G5ZDUR5zsV_!!2196368964-0-cib.jpg',
#       'https://cbu01.alicdn.com/img/ibank/O1CN01skcmPn2G5ZDYjO2vE_!!2196368964-0-cib.jpg'
#     ]
#
# print(len(images[1:]))
# product_id_lsit = []
# for product_data in product_id_lsit:
#     print(1)
# print(2)
#
# text = '切菜手殘黨必備 電動切菜機 全自動切菜機 滾筒切菜器 切菜機lhnj'
# # print(len(text))
#
#
# pattern = r'[a-zA-Z0-9]+$'
# result = re.sub(pattern, '', text)
# print(result)

img = 'https://cbu01.alicdn.com/img/ibank/O1CN01iFCKRf2DoxlJf6sI7_!!2588788657-0-cib.jpg'
result = requests.get(img)
print(result.status_code)