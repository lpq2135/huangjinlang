import requests
import base64
import logging
import re
import time
import io
import json
import random

from datetime import datetime
from lxml import html


def request_function(url, method='GET', headers=None, data=None, proxies=None, files=None, timeout=30):
    # 创建通用请求函数
    for attempt in range(5):
        try:
            if method.upper() == 'POST':
                response = requests.post(url, headers=headers, data=data, files=files, timeout=timeout, proxies=proxies)
            else:
                response = requests.get(url, headers=headers, files=files, timeout=timeout, proxies=proxies)
            # 检查响应状态码
            response.raise_for_status()  # 如果响应状态码不是 2xx，将抛出异常
            return response
        except requests.exceptions.RequestException as e:
            logging.warning(f"请求错误 ({method}-{url}): {e}. 重试中... ({attempt + 1}/5)")
            time.sleep(2)

def generate_random_number(length):
    # 第一个数字为 1-9，后续数字为 0-9
    first_digit = random.randint(1, 9)  # 生成第一位数字 (1-9)
    remaining_digits = ''.join(str(random.randint(0, 9)) for _ in range(length - 1))  # 生成剩余的数字 (0-9)
    return str(first_digit) + remaining_digits

def get_all_keys(d):
    # 获取所有的键
    keys = []
    if isinstance(d, dict):  # 如果是字典
        for key, value in d.items():
            keys.append(key)  # 添加键
            if isinstance(value, dict):  # 如果值还是字典，递归调用
                for key1 in value.keys():
                    keys.append(key1)
    return keys

def replace_key_value(structure_list, d):
    # 创建一个结构字典，存储结构列表与随机键的映射
    structure_dict = {i: 'temp_' + generate_random_number(8) for i in structure_list}
    specs_new_dict = {}
    structure_new_dict = {}
    # 替换specs中的键
    for key, value in d['specs'].items():
        new_key = structure_dict[key]  # 获取新的键
        # 替换specs字典中的键
        specs_new_dict[new_key] = value.copy()
        # 替换spec_id
        specs_new_dict[new_key]['spec_id'] = new_key
        # 替换childs中的键（如果有childs并且是字典）
        if isinstance(specs_new_dict[new_key]['childs'], dict):
            for child_key in list(specs_new_dict[new_key]['childs'].keys()):
                new_child_key = structure_dict[child_key]
                # 替换childs中的键
                specs_new_dict[new_key]['childs'][new_child_key] = specs_new_dict[new_key]['childs'].pop(child_key)
    for key, value in d['structure'].items():
        new_key = structure_dict[key]
        # 替换structure字典中的键
        structure_new_dict[new_key] = value.copy()
        # 替换childs中的键（如果有childs并且是字典）
        if isinstance(structure_new_dict[new_key], dict):
            for structure_key in list(structure_new_dict[new_key].keys()):
                new_structure_key = structure_dict[structure_key]
                structure_new_dict[new_key][new_structure_key] = structure_new_dict[new_key].pop(structure_key)

    return specs_new_dict, structure_new_dict


def flatten_dict(d, parent_key='', sep='.'):
    # 递归扁平化嵌套字典，将嵌套的字段使用 dot notation 连接，
    items = []
    for k, v in d.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, dict):
            items.extend(flatten_dict(v, new_key, sep=sep).items())
        elif isinstance(v, list):
            # 如果是列表，将列表转换成字符串，表示空列表 "[]"
            items.append((new_key, str(v) if v else '[]'))
        else:
            # 将值转换成字符串，None 转换为空字符串 ""
            items.append((new_key, "" if v is None else str(v)))
    return dict(items)


class Ruten:
    def __init__(self, store):
        self.store = store
        self.proxies = {
            'http': 'http://brd-customer-hl_8240a7b6-zone-ruten_remove:g4w5c685daes@brd.superproxy.io:33335',
            'https': 'https://brd-customer-hl_8240a7b6-zone-ruten_remove:g4w5c685daes@brd.superproxy.io:33335',
        }
        self.headers = {
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
            'cookie': self.get_cookie_by_api()}
        self.ck = None
        self.current_month = datetime.now().strftime("%Y%m")

    def get_product_package(self, product_id):
        # 获取商品数据包
        url = f'https://www.ruten.com.tw/item/show?{product_id}'
        response = request_function(url, headers=self.headers, proxies=self.proxies)
        match = re.search(r'(?<=RT\.context\ =\ ).*(?=;)', response.text)
        if match:
            return match.group(0)
        else:
            print(f'获取商品数据包失败-{product_id}')
            return None

    def get_cookie_by_api(self):
        # 通过本地接口获取cookie
        local_url = 'http://127.0.0.1:8802/get_user_by_name'
        data = {'store': self.store}
        response = request_function(local_url, method='POST', data=data)
        if response is None:
            logging.error(f"无法获取{self.store}的cookie")
            return None
        try:
            return response.json()['cookie']
        except ValueError as e:
            logging.error(f"解析{self.store}参数数据失败: {e}")
            return None

    def upload_main_images(self, img_url):
        # 上传主图
        url = f'https://upload.ruten.com.tw/item/image.php?ck={self.ck}'
        image_result = request_function(img_url, headers=self.headers)
        files = {'image': (img_url.split('/')[-1], io.BytesIO(image_result.content), 'image/jpeg')}
        response = request_function(url, method='POST', headers=self.headers, files=files)
        return response.text

    def get_pagination_product_id(self, page):
        # 获取分页的商品ID
        url = f'https://mybid.ruten.com.tw/master/my.php?p={page}&l_type=sel_selling&p_size=30&o_sort=asc&o_column=post_time'
        response = request_function(url, headers=self.headers)
        tree = html.fromstring(response.text)
        product_num = re.findall(r'"real_total":(.*?)}', response.text)[0]
        if product_num:
            id_list = tree.xpath('//tr[@class="row-odd" or @class="row-even"]/@data-gno')
            new_list = []
            for i in id_list:
                product_data = {
                    'product_id': i,
                    'title': tree.xpath(f'//tr[@data-gno="{i}"]/td[3]/a/text()')[0],
                    'price': tree.xpath(f'//tr[@data-gno="{i}"]/td[4]/div/@data-price-min')[0],
                    'stock': tree.xpath(f'//tr[@data-gno="{i}"]/td[5]/text()')[0].replace('(', '').strip(),
                    'sales': tree.xpath(f'//tr[@data-gno="{i}"]/td[6]/a/text()')[0],
                    'click': tree.xpath(f'//tr[@data-gno="{i}"]/td[7]/text()')[0],
                    'cart': tree.xpath(f'//tr[@data-gno="{i}"]/td[8]/text()')[0],
                    'upduct_time': tree.xpath(f'//tr[@data-gno="{i}"]/td[10]/text()')[0].strip(),
                }
                new_list.append(product_data)
            return new_list

    def get_description(self, description_url):
        response = request_function(description_url, headers=self.headers)
        return response.text

    def process_upload_data(self, product_id):
        # 处理上货数据
        product_data = json.loads(self.get_product_package(product_id))
        upload_data = {
            'name': product_data['item']['name'],
            'mode': product_data['item']['mode'],
            'main_images': [i['original'] for i in product_data['item']['images']],
            'category_id': product_data['item']['class'],
            'direct_price': product_data['item']['directPrice'],
            'remain_num': product_data['item']['remainNum'],
            'spec_info': product_data['item']['specInfo'],
            'descriptionUrl': '111'
        }
        return upload_data

    def process_category_id(self):
        # 处理类目编号
        pass

    def process_main_img(self):
        # 处理主图
        pass

    def process_title(self):
        # 处理标题
        pass

    def process_user_class(self):
        # 处理后台分类
        pass

    def process_item_detail(self, spec_info):
        # 处理 item_detail
        num = 0
        item_detail_dict = {'new_spec_name': None}
        # 处理 item_detail
        for key, value in spec_info.items():
            item_detail_dict[f'item_detail_price_{num}'] = value['spec_price']
            item_detail_dict[f'item_detail_count_{num}'] = value['spec_num']
            num += 1
        # 处理扁平化 spec_info

        return item_detail_dict

    def process_details(self):
        # 处理详情
        pass

    def upload_products(self, product_id):
        # 上传产品总流程

        # 获取上传所需ck值
        url_initial = 'https://mybidu.ruten.com.tw/upload/item_initial.php'
        response_initial = request_function(url_initial, headers=self.headers)
        self.ck = response_initial.url.split('ck=')[1]

        # 获取处理好的商品数据
        upload_data = self.process_upload_data(product_id)

        # 处理sku参数-单规格或双规格
        if upload_data['spec_info']:
            structure_list = get_all_keys(upload_data['spec_info']['structure'])
            specs_dict, structure_dict = replace_key_value(structure_list, upload_data['spec_info'])
            upload_data['spec_info']['specs'] = specs_dict  # 替换原始 specs 数据
            upload_data['spec_info']['structure'] = structure_dict
            flatten_spec_info = flatten_dict(upload_data['spec_info'])
            item_detail_dict = self.process_item_detail(specs_dict)
            item_detail_dict.update(flatten_spec_info)
        else:
            # 无规格 item_detail 参数
            item_detail_dict = {
                'new_spec_name': '',
                'item_detail_price_0': upload_data['direct_price'],
                'item_detail_count_0': upload_data['remain_num'],
                'item_detail_note_0': '',
            }

        # 开始处理图片上传并组装格式
        main_images = []
        for i in upload_data['main_images']:
            result = json.loads(self.upload_main_images(i))
            image = {"img_name": result['content']['file_name'], "storage": result['content']['storage']}
            main_images.append(image)

        data_dict = {
            'shop_id': upload_data['category_id'],    # 类目id
            'process_img': main_images,    # 主图数据包
            'g_name': upload_data['name'],    # 标题
            'user_class_select': '',    # 后台自自定义分类编码
            'g_mode': 'B',    # mode
            'g_direct_price': upload_data['direct_price'],   # sku数据包
            'show_num': upload_data['remain_num'],    # 总库存数量
            'is_goods_sale': '0',    # 銷售時間設定 0: 立即销售  1: 指定销售时间
            'sale_start_time': '',    # 銷售時間設定-开始时间(如果is_goods_sale=1,此参数必填)
            'sale_end_time': '',    # 銷售時間設定-结束时间，不填则表示无限
            'g_condition': 'B',    # 物品新旧 B: 全新
            'stock_status': '1',    # 备货状态 3: 24h内出货  1: 3天内出货  4: 7天内出货  0: 21天内出货  6: 较长备货  2: 预售商品
            'customized_ship_date': '',    # 较长备货的天数 22-90天
            'pre_order_ship_date': self.current_month,    # 预计出货时间
            'text2': '0002004',    # 详情
            'g_flag': '',    # 特别醒目标签
            'g_location': '台北市',    # 物品所在地
            'g_buyer_limit_value': '',    # 买家下标限制-评价总分
            'g_buyer_limit_nega': '',    # 买家下标限制-差劲评分
            'g_buyer_limit_abandon': '',    # 买家下标限制-近半年弃单次数
            'g_ship': 'B',    # 运费规定 A: 买家自付  B: 免运费
            'g_pay_way': 'PAYLINK,SELF_FAMI_COD,SELF_SEVEN_COD,SELF_HILIFE_COD',    # 付款方式
            'g_deliver_way': '{SELF_FAMI_COD:60,SELF_SEVEN_COD:60,SELF_HILIFE_COD:45,HOUSE:100,ISLAND:300,FAMI:60,SEVEN:60,HILIFE:45}',    # 运输方式
        }

        data_dict.update(item_detail_dict)

        # 第一次请求进入预览页面
        url_action = f'https://mybidu.ruten.com.tw/upload/item_action.php?ck={self.ck}'
        response_action = request_function(url_action, 'POST', headers=self.headers, data=json.dumps(data_dict))

        # 完成最终的上架请求
        url_finalize = f"https://mybidu.ruten.com.tw/upload/item_finalize.php?ck={ck_value}"
        response_finalize = request_function(url_finalize, headers=self.headers)

        return response


if __name__ == '__main__':
    reten = Ruten('martha32')
    result = reten.upload_products('22442980164912')
    print(result)

s = 3
# sa