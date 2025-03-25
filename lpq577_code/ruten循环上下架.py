import requests
import base64
import logging
import logging_config
import re
import time
import io
import os
import sys
import json
import random
import string
import pandas as pd
import concurrent.futures

from requests.adapters import HTTPAdapter
from 数据库连接 import MySqlPool
from datetime import datetime
from lxml import html
from bs4 import BeautifulSoup
from threading import Lock
from urllib.parse import urlparse, parse_qs
from concurrent.futures import ThreadPoolExecutor, wait, ALL_COMPLETED, as_completed, TimeoutError
from requests.exceptions import ReadTimeout, RequestException


# code 状态注释
# 0: 成功
# 1: 一般错误，一般直接跳过，无需特殊处理
# 2: 严重错误，做记录
# 3：需处理错误，需记录并处理
# 4：未知错误，需记录并处理


# 将输入列表分成多个子列表，每个子列表最多包含 chunk_size 个元素
def split_list(input_list):
    return [input_list[i:i + 30] for i in range(0, len(input_list), 30)]

# 记录上架成功的商品 id
def record_product_id_listing_status(store, product_id, g_no):
    cnx, cursor = mysql_pool.get_conn()
    try:
        table_name = f'cyclic_on_and_off_record_by_{store}'  # 构建完整的表名
        # 获取当前时间，格式化为字符串（YYYY-MM-DD HH:MM:SS）
        current_time = datetime.now().strftime('%Y-%m-%d')
        query = f"INSERT INTO {table_name} (store, product_id, after_listing_id, remove_status, update_time) VALUES (%s, %s, %s, %s, %s)"
        cursor.execute(query, (store, product_id, g_no, '0', current_time,))
        cnx.commit()

    except Exception as e:
        # 如果发生异常，记录错误日志并回滚事务
        logging.warning('记录商品成功上传信息异常, store: %s, product_id: %s, error: %s', store, product_id, str(e))
        cnx.rollback()  # 回滚事务，避免无效或部分更新的数据

    finally:
        # 关闭数据库连接和游标
        mysql_pool.close_mysql(cnx, cursor)

# 记录无法上架的商品id
def unable_to_list_id_record(store, product_id):
    cnx, cursor = mysql_pool.get_conn()
    try:
        cursor.execute(
            """
            INSERT INTO unable_to_list_id_record (store, product_id)
            VALUES (%s, %s)
            """,
            (store, product_id)
        )
        cnx.commit()

    except Exception as e:
        # 如果发生异常，记录错误日志并回滚事务
        logging.warning('记录商品上传失败信息异常, store: %s, product_id: %s, error: %s', store, product_id, str(e))
        cnx.rollback()  # 回滚事务，避免无效或部分更新的数据

    finally:
        # 关闭数据库连接和游标
        mysql_pool.close_mysql(cnx, cursor)

# 记录上传失败的商品ID
def record_upload_error(store, product_id):
    cnx, cursor = mysql_pool.get_conn()
    try:
        cursor.execute(
            """
            INSERT INTO upload_error (store, product_id)
            VALUES (%s, %s)
            """,
            (store, product_id)
        )
        cnx.commit()

    except Exception as e:
        # 如果发生异常，记录错误日志并回滚事务
        logging.warning('记录商品上传失败信息异常, store: %s, product_id: %s, error: %s', store, product_id, str(e))
        cnx.rollback()  # 回滚事务，避免无效或部分更新的数据

    finally:
        # 关闭数据库连接和游标
        mysql_pool.close_mysql(cnx, cursor)

# 记录上传失败的商品ID
def record_main_image_error(store, product_id):
    cnx, cursor = mysql_pool.get_conn()
    try:
        cursor.execute(
            """
            INSERT INTO main_image_error (store, product_id)
            VALUES (%s, %s)
            """,
            (store, product_id)
        )
        cnx.commit()

    except Exception as e:
        # 如果发生异常，记录错误日志并回滚事务
        logging.warning('记录主图信息异常, store: %s, product_id: %s, error: %s', store, product_id, str(e))
        cnx.rollback()  # 回滚事务，避免无效或部分更新的数据

    finally:
        # 关闭数据库连接和游标
        mysql_pool.close_mysql(cnx, cursor)

# 批量修改 product_id 的状态
def modify_product_status(store, remove_id):
    cnx, cursor = mysql_pool.get_conn()
    try:
        table_name = f'cyclic_on_and_off_record_by_{store}'  # 构建完整的表名
        # 动态生成占位符，用于IN子句
        placeholders = ', '.join(['%s'] * len(remove_id))
        query = f"UPDATE {table_name} SET remove_status = '1' WHERE product_id IN ({placeholders})"
        cursor.execute(query, remove_id)
        cnx.commit()

    except Exception as e:
        # 如果发生异常，记录错误日志并回滚事务
        logging.warning('更新商品下架信息异常, store: %s, product_id_list: %s, error: %s', store, remove_id, str(e))
        cnx.rollback()  # 回滚事务，避免无效或部分更新的数据

    finally:
        # 关闭数据库连接和游标
        mysql_pool.close_mysql(cnx, cursor)

# 获取每日上架数量
def get_the_daily_listing_quantity(store):
    cnx, cursor = mysql_pool.get_conn()
    try:
        table_name = f'cyclic_on_and_off_record_by_{store}'  # 构建完整的表名
        current_time = datetime.now().strftime('%Y-%m-%d')
        query = f"SELECT COUNT(*) FROM {table_name} WHERE store = %s AND update_time = %s"
        cursor.execute(query, (store, current_time,))
        row_count = cursor.fetchone()[0]
        return row_count
    except Exception as e:
        logging.warning("获取当前上货数量异常, store: %s, current_time: %s", store, current_time, str(e))
    finally:
        mysql_pool.close_mysql(cnx, cursor)

#  获取店铺需下架的商品id
def get_id_to_be_removed(store):
    cnx, cursor = mysql_pool.get_conn()
    try:
        table_name = f'cyclic_on_and_off_record_by_{store}'  # 构建完整的表名
        query = f"SELECT product_id FROM {table_name} WHERE remove_status = '0' AND store = %s"
        cursor.execute(query, (store,))
        rows = cursor.fetchall()
        if rows:
            result = [row[0] for row in rows]
            return result
        return None
    except Exception as e:
        logging.warning("获取需下架的商品id异常, store: %s", store, str(e))
    finally:
        mysql_pool.close_mysql(cnx, cursor)

# 获取修改标题也无法上架的id进行过滤
def get_the_id_that_cannot_be_listed(store):
    cnx, cursor = mysql_pool.get_conn()
    try:
        query = f"SELECT product_id FROM unable_to_list_id_record WHERE store = %s"
        cursor.execute(query, (store,))
        rows = cursor.fetchall()
        if rows:
            result = [row[0] for row in rows]
            return result
        return []
    except Exception as e:
        logging.warning("获取无法上架的商品id异常, store: %s", store, str(e))
    finally:
        mysql_pool.close_mysql(cnx, cursor)

class Ruten:
    def __init__(self, store, upload_count):
        self.store = store
        self.proxies = proxies

        # 创建独立的 Session 对象
        self.session = requests.Session()

        cookie = self.get_cookie_by_api()
        if cookie is None:
            raise ValueError(f'{self.store}-获取cookie异常导致此线程结束')
        self.headers = {
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
            'cookie': cookie,
        }
        self.g_pay_way = None
        self.g_deliver_way = None
        if self.get_payment_and_shipping(self.store) is False:
            self.close()
            raise ValueError(f'{self.store}-在数据库找不到店铺的付款运输方式')
        self.upload_count = upload_count
        self.initial_count = 0
        if self.check_store_status(self.store) is False:
            self.close()
            raise ValueError(f'{self.store}-店铺状态异常(线程终止)')
        self.lock = Lock()

    # 显式关闭 Session 对象
    def close(self):
        self.session.close()

    # 创建通用请求函数
    def request_function(self, url, method='GET', headers=None, data=None, proxies=None, files=None, timeout=30):
        for attempt in range(8):
            response = None  # 每次重试时初始化 response
            try:
                # 使用实例的 session 发起请求
                response = self.session.request(
                    url=url,
                    method=method.upper(),
                    headers=headers,
                    data=data,
                    proxies=proxies,
                    files=files,
                    timeout=timeout
                )
                # 检查响应状态码
                response.raise_for_status()  # 如果响应状态码不是 2xx，将抛出异常
                return response
            except ReadTimeout as e:
                # 单独处理超时错误
                logging.warning(f"请求超时 ({method}-{url}): {e}. 重试中... ({attempt + 1}/8)")
                time.sleep(2 ** attempt)  # 指数退避策略
            except RequestException as e:
                # 处理其他请求异常
                if hasattr(e, 'response') and e.response is not None:
                    if e.response.status_code == 404:
                        return e.response
                logging.warning(f"请求错误 ({method}-{url}): {e}. 重试中... ({attempt + 1}/8)")
                time.sleep(2 ** attempt)
            except Exception as e:
                # 处理其他未知异常
                logging.error(f"未知错误 ({method}-{url}): {e}")
                return None
        logging.error(f"请求失败，已重试 8 次: {url}")
        return None

    # 获取店铺对应的付款和运输方式
    def get_payment_and_shipping(self, store):
        cnx, cursor = mysql_pool.get_conn()
        try:
            cursor.execute(
                "SELECT g_pay_way, g_deliver_way FROM payment_and_shipping_methods WHERE store = %s", (store,))
            rows = cursor.fetchall()
            if rows:
                self.g_pay_way = rows[0][0]
                self.g_deliver_way = rows[0][1]
                return True
            return False
        except Exception as e:
            logging.warning("获取店铺物流和运输方式异常: %s", str(e))
        finally:
            mysql_pool.close_mysql(cnx, cursor)

    # 获取当前月份
    @property
    def current_month(self):
        return datetime.now().strftime("%Y%m")

    # 获取商品数据包
    def get_product_package(self, product_id):
        url = f'https://www.ruten.com.tw/item/show?{product_id}'
        cookies = {
            "_cfuvid": "_CH_Nx_bYg9Q3tPA42nSf0rzNshiFWV63ofzzsw7_QQ-1740457574750-0.0.1.1-604800000",
            "x-hng": "lang=zh-CN&domain=www.ruten.com.tw",
            "_ga": "GA1.1.925149236.1740457572",
            "_ts_id": "20250225200792387309.1740457576",
            "_fbp": "fb.2.1740457572410.613730098481646494",
            "_clck": "1mztmfc%7C2%7Cftt%7C0%7C1882",
            "_clsk": "1xvygqj%7C1740729396184%7C4%7C0%7Cn.clarity.ms%2Fcollect",
            "_ts_session": "rtk8anlsmz",
            "adultchk": "ok",
            "_ga_2VP4WXLL56": "GS1.1.1740738889.14.1.1740738902.47.0.0",
            "_ts_session_spent": "23762",
        }
        cookie_str = "; ".join([f"{k}={v}" for k, v in cookies.items()])
        headers = {
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
            'cookie': cookie_str
            }
        response = self.request_function(url, headers=headers)
        match = re.search(r'(?<=RT\.context\ =\ ).*(?=;)', response.text)
        if match:
            try:
                return match.group(0)
            except Exception as e:
                logging.warning(f'获取商品数据包失败-{product_id}, 错误信息: {e}')
        return None

    # 检查店铺状态
    def check_store_status(self, store):
        url = f'https://mybidu.ruten.com.tw/upload/item_initial.php'
        response = self.request_function(url, headers=self.headers)
        if 'item_start' in response.url:
            logging.info(f'{store}-店铺状态正常')
            return True
        elif 'mobile_validation' in response.url:
            logging.warning(f'{store}-请处理OTP验证')
            return False
        elif len(response.history) == 2:
            if 'unpay_lv1' in response.history[1].url:
                logging.warning(f'{store}-请处理计费中心')
                return False
        else:
            logging.warning(f'{store}-未知异常(请检查店铺状态)')
            return False

    # 通过本地接口获取cookie
    def get_cookie_by_api(self):
        local_url = 'http://127.0.0.1:8802/get_user_by_name'
        data = {'store': self.store}
        response = self.request_function(local_url, 'post', data=data)
        if response:
            try:
                return response.json().get('cookie')
            except ValueError as e:
                logging.error(f"{self.store}-cookie数据获取失败, 错误信息: {e}")
        return None

    # 上传主图
    def upload_main_images(self, img_url, ck):
        url = f'https://upload.ruten.com.tw/item/image.php?ck={ck}'
        try:
            image_result = self.request_function(img_url, headers=self.headers, proxies=proxies)
            if image_result.status_code == 404:
                return {'code': 3}
            files = {'image': (img_url.split('/')[-1], io.BytesIO(image_result.content), 'image/jpeg')}
            response = self.request_function(url, method='post', headers=self.headers, files=files, proxies=proxies)
            return {'code': 0, 'data': response.json()}

        except Exception as e:
            logging.warning(f'{self.store}-主图上传失败, 错误信息: {e}')
            return {'code': 1}

    # 获取详情信息
    def get_description(self, product_id, description_url):
        # 请求详情专用请求头，需要带 referer
        headers = {
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36',
            'referer': f'https://www.ruten.com.tw/item/show?{product_id}'
        }
        html_data = self.request_function(description_url, headers=headers).text
        html_add = """<p><span style="font-size: 24pt; background-color: #ff0000;"><strong><span style="color: #000000;">溫馨提示：</span></strong></span></p>
                        <p><span style="color: #800000; font-size: 14pt;"><strong><span style="background-color: #ccffff;">1️⃣本店所屬</span></strong></span><span style="background-color: #ccffff;"><span style="color: #800000;" color="#800000"><span style="font-size: 18.6667px;"><b></b></span></span></span><strong style="color: #800000; font-size: 14pt;"><span style="background-color: #ccffff;">公司長期運營，品質第一，售後無憂！</span></strong></p>
                        <p><span style="color: #800000; font-size: 14pt;"><strong><span style="background-color: #ccffff;">2️⃣本店支持開發票及信用卡支付，若需要使用信用卡付款請聯絡客服！</span></strong></span></p>
                        <p><span style="color: #800000; font-size: 14pt;"><strong><span style="background-color: #ccffff;">3️⃣支持大量採購，支持全網比價，可帶圖帶產品詢價，歡迎與您長期合作！</span></strong></span></p>"""
        if html_data:
            try:
                soup = BeautifulSoup(html_data, 'lxml')
                body_content = soup.find('body')
                body_html = body_content.decode_contents()
                if account == 'huangjinlang':
                    html_new = html_add + '<br>' + body_html
                else:
                    html_new = body_html
                return html_new
            except Exception as e:
                logging.warning(f'{self.store}-获取详情信息失败, 错误信息: {e}')
        return None

    # 获取分页的商品ID
    def get_pagination_product_id(self, page):
        url = f'https://mybid.ruten.com.tw/master/my.php?p={page}&l_type=sel_selling&p_size=30&o_sort=asc&o_column=post_time'
        response = self.request_function(url, headers=self.headers)
        if response:
            try:
                tree = html.fromstring(response.text)
                id_list = tree.xpath('//tr[@class="row-odd" or @class="row-even"]/@data-gno')
                new_list = []
                for i in id_list:
                    product_data = {
                        'product_id': i,
                        'title': tree.xpath(f'//tr[@data-gno="{i}"]/td[3]/a/text()')[0],
                        'min_price': tree.xpath(f'//tr[@data-gno="{i}"]/td[4]/div/@data-price-min')[0],
                        'max_price': tree.xpath(f'//tr[@data-gno="{i}"]/td[4]/div/@data-price-max')[0],
                        'stock': tree.xpath(f'//tr[@data-gno="{i}"]/td[5]/text()')[0].replace('(', '').strip(),
                        'sales': tree.xpath(f'//tr[@data-gno="{i}"]/td[6]/a/text()')[0],
                        'click': tree.xpath(f'//tr[@data-gno="{i}"]/td[7]/text()')[0],
                        'cart': tree.xpath(f'//tr[@data-gno="{i}"]/td[8]/text()')[0],
                        'upduct_time': tree.xpath(f'//tr[@data-gno="{i}"]/td[10]/text()')[0].strip(),
                    }
                    new_list.append(product_data)
                return new_list
            except Exception as e:
                logging.warning(f'{self.store}-获取第{page}页商品信息失败, 错误信息：{e}')
        return None

    # 处理上货数据
    def process_upload_data(self, product_id):
        try:
            # 获取商品数据包
            product_data = json.loads(self.get_product_package(product_id))
            if not product_data:
                return {'code': 1}  # 如果没有数据包，直接返回 None

            # 获取商品描述
            description = self.get_description(product_id, product_data['item']['descriptionUrl'])
            if not description:
                return {'code': 1}  # 如果没有描述，直接返回 None

            # 判断主图是否异常
            main_images = product_data['item']['images']
            if main_images is None:
                return {'code': 3}

            # 构建上传数据
            upload_data = {
                'name': product_data['item']['name'],
                'mode': product_data['item']['mode'],
                'main_images': [i['original'] for i in main_images],
                'category_id': product_data['item']['class'],
                'direct_price': product_data['item']['directPrice'],
                'remain_num': product_data['item']['remainNum'],
                'spec_info': product_data['item']['specInfo'],
                'description': description,
            }
            return {'code': 0, 'data': upload_data}  # 返回上传数据

        except Exception as e:
            logging.error(f'{self.store}-{product_id}-处理上货数据包失败, 错误信息：{e}')
            return {'code': 1}  # 如果出现异常，返回 None

    # 处理类目编号
    def process_category_id(self, category_id):
        # 判断类目是否为最底层:
        timestamp = int(time.time() * 1000)
        get_category_url = f'https://mybid.ruten.com.tw/upload/ajax_category.php?g_class={category_id}&_={timestamp}'
        category_response = self.request_function(get_category_url, headers=self.headers).json()
        if category_response['is_valid'] is False:
            return '00090014'

        # 判断类目是否为管制类目:
        regulations_url = f'https://rapi.ruten.com.tw/api/seller/v1/common/cate/{category_id}/regulations'
        regulations_response = self.request_function(regulations_url, headers=self.headers).json()
        if regulations_response['data']['bsmi_status'] == 1 or regulations_response['data']['ncc_status'] == 1:
            return '00090014'

        return category_id

    # 处理标题
    def process_title(self, title):
        # title_prefix = ['【現貨免運】', '【公司貨】', '【嚴選好物】', '【可開發票】', '【好物優選】', '【口碑推薦】', '【銷售冠軍】', '【五星好評】', '【人氣爆款】', '【可刷卡】']
        if '【' and '】' in title:
            return title
        if len(title) <= 54:
            selected_prefix = random.choice(title_prefix)
            result = selected_prefix + title
            return result
        return title

    # 处理后台分类
    def process_user_class(self, product_id):
        url = 'https://mybid.ruten.com.tw/master/action_sellnow_modify.php?datatype=0'
        data = {
            "_l_type": "sel_selling",
            "has_search": "0",
            "p": "1",
            "p_size": "30",
            "o_column": "post_time",
            "o_sort": "desc",
            "s_type": "g_name",
            "s_content": "",
            "doaction": "ALot_Down",
            "seven_way": "seven_both",
            "mbox_0": product_id
        }
        response = self.request_function(url, 'post', headers=self.headers, data=data)
        if response:
            try:
                tree = html.fromstring(response.text)
                # 获取表单数据
                data = {
                    'g_single_no': '',
                    'g_single_class': '',
                    'time_key': '',
                    'g_no_0': product_id,
                    f'hash_{product_id}': tree.xpath('//input[@id="g_hash0"]/@value')[0],
                    f'g_mode_{product_id}': tree.xpath('//input[@id="g_mode0"]/@value')[0],
                    f'g_sold_num_{product_id}': tree.xpath('//input[@id="g_sold_num0"]/@value')[0],
                    f'g_ori_price{product_id}': tree.xpath('//input[@id="g_ori_price0"]/@value')[0],
                    f'g_class_{product_id}': tree.xpath('//input[@id="g_class0"]/@value')[0],
                    f'g_name_{product_id}': tree.xpath('//input[@id="g_name0"]/@value')[0],
                    f'user_class_select_{product_id}': tree.xpath('//option[@selected]/@value')[0],
                    f'g_num_{product_id}': tree.xpath('//input[@id="g_num0"]/@value')[0],
                    f'g_direct_price2_{product_id}': tree.xpath('//input[@id="g_direct_priceB0"]/@value')[0]
                }
                return data
            except Exception as e:
                logging.warning(f'{self.store}-{product_id}-获取后台自定义分类失败, 错误信息: {e}')
        return None

    # 构造multipart/form-data格式
    def structure_multipart(self, json_data):
        boundary = 'WebKitFormBoundary' + ''.join(random.choices(string.ascii_letters + string.digits, k=16))
        form_data = ""
        for key, value in json_data.items():
            form_data += f"------{boundary}\n"
            form_data += f"Content-Disposition: form-data; name=\"{key}\"\n\n"
            form_data += f"{value}\n"

        # 结尾添加 boundary
        form_data += f"------{boundary}--\n"

        return boundary, form_data

    # 处理 item_detail
    def process_item_detail(self, spec_info):
        num = 0
        item_detail_dict = {'new_spec_name': ''}
        # 处理 item_detail
        show_num = 0
        for key, value in spec_info.items():
            item_detail_dict[f'item_detail_price_{num}'] = value['spec_price']
            item_detail_dict[f'item_detail_count_{num}'] = value['spec_num']
            item_detail_dict[f'item_detail_note_{num}'] = ''
            num += 1
            show_num += value['spec_num']
        return item_detail_dict, show_num

    # 获取商品下架状态
    def product_items_v2(self, product_id):
        url = f'https://rapi.ruten.com.tw/api/items/v2/list?gno={product_id}&level=simple'
        headers = {
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36',
        }
        result = self.request_function(url, headers=headers).json()
        return result['data'][0]['available']

    # 下架产品总流程
    def remove_products(self, remove_list):
        remove_list_data = self.batch_remove_products(remove_list)
        if remove_list_data['code'] == 0:
            modify_product_status(self.store, remove_list)
        elif remove_list_data['code'] == 1:
            for i in remove_list:
                product_status = self.product_items_v2(i)
                if product_status:
                    self.single_remove_products(i)
                    time.sleep(2)
                else:
                    logging.info(f'{self.store}-{i}-商品已下架修改数据库状态')
                    modify_product_status(self.store, [i])

    # 单个下架产品
    def single_remove_products(self, product_id):
        url = 'https://mybid.ruten.com.tw/master/action_sellnow.php'
        data = {
            'type': 'down',
            'gno_list': product_id
        }
        try:
            response = self.request_function(url, 'post', headers=self.headers, data=data, proxies=self.proxies).json()
            if response['status'] == 'success' or response['message'] == '系統處理中':
                logging.info(f'{self.store}-{product_id}-下架成功')
                modify_product_status(self.store, [product_id])
            else:
                logging.warning(f'{self.store}-{product_id}-单个下架失败')
        except Exception as e:
            logging.warning(f'{self.store}-{product_id}-单个下架失败({e})')

    # 批量下架产品
    def batch_remove_products(self, remove_list):
        url = 'https://mybid.ruten.com.tw/master/action_sellnow.php'
        gno_list = ','.join(i for i in remove_list)
        data = {
            'type': 'down',
            'gno_list': gno_list
        }
        try:
            response = self.request_function(url, 'post', headers=self.headers, data=data, proxies=self.proxies).json()
            if response['status'] == 'success':
                logging.info(f'{self.store}-{gno_list}-下架成功')
                return {'code': 0}
            elif response['message'] == '系統處理中':
                logging.warning(f'{self.store}-{gno_list}-下架异常，进行单个下架处理')
                return {'code': 1}
            else:
                logging.warning(f'{self.store}-{gno_list}-批量下架失败')
                return {'code': 2}
        except Exception as e:
            logging.warning(f'{self.store}-{gno_list}-批量下架严重异常({e})')
            return {'code': 3}

    # 修改标题重新上架(大量修改入口)
    def modify_title_to_upload(self, g_no, title):
        data = self.process_user_class(g_no)
        data[f'g_name_{g_no}'] = title
        url1 = 'https://mybid.ruten.com.tw/master/action_sellnow_modify_deal.php'
        response1 = self.request_function(url1, 'post', headers=self.headers, data=data)
        time.sleep(2)
        if 'filter_msg' in response1.url:
            logging.warning(f"{self.store}-{g_no}-无法通过修改标题的方式上架")
            return {'code': 4}
        elif response1.status_code == 200:
            pattern = r"time_key=(\d+)&hash2=([a-fA-F0-9]+)"
            match = re.search(pattern, response1.text)
            if match:
                time_key = match.group(1)
                hash2 = match.group(2)
                url2 = f'https://mybid.ruten.com.tw/master/action_sellnow_modify_update.php?time_key={time_key}&hash2={hash2}'
                response2 = self.request_function(url2, headers=self.headers)
                if '1件商品修改成功！' in response2.text:
                    logging.info(f"{self.store}-{g_no}-标题更新成功")
                    return {'code': 0}
            logging.warning(f"{self.store}-{g_no}-无法通过修改标题的方式上架")
            return {'code': 4}

    # 上传产品总流程
    def upload_products(self, product_id):
        # 判断上品的状态（前置条件）
        product_status = self.product_items_v2(product_id)
        if not product_status:
            logging.warning(f'{self.store}-{product_id}-此商品已下架无需重新采集上架')
            return {'code': 1, 'status': False, 'product_id': product_id}

        # 获取处理好的商品数据
        product__data = self.process_upload_data(product_id)
        if product__data['code'] == 1:
            logging.warning(f'{self.store}-{product_id}-处理商品上货数据包失败')
            return {'code': 1, 'status': False, 'product_id': product_id}
        elif product__data['code'] == 3:
            logging.warning(f'{self.store}-{product_id}-主图异常进行下架处理')
            return {'code': 3, 'status': False, 'product_id': product_id}
        upload_data = product__data['data']

        # 处理sku参数和 spec_info 的值(单规格或双规格)
        if upload_data['spec_info']:
            item_detail_dict, show_num = self.process_item_detail(upload_data['spec_info']['specs'])
            spec_info = json.dumps(upload_data['spec_info'], ensure_ascii=False)
        else:
            # 无规格 item_detail 参数
            item_detail_dict = {
                'new_spec_name': '',
                'item_detail_price_0': upload_data['direct_price'],
                'item_detail_count_0': upload_data['remain_num'],
                'item_detail_note_0': '',
            }
            spec_info = ''
            show_num = upload_data['remain_num']

        # 获取上传所需ck值
        while True:
            url_initial = 'https://mybidu.ruten.com.tw/upload/item_initial.php'
            response_initial = self.request_function(url_initial, headers=self.headers, proxies=self.proxies)
            if 'ck=' not in response_initial.url:
                logging.warning(f'{self.store}-{product_id}-获取上传ck值失败')
                store_status = self.check_store_status(self.store)
                if store_status is False:
                    return {'code': 1, 'status': False, 'product_id': product_id}
            else:
                break
        ck = response_initial.url.split('ck=')[1]
        logging.info(f'{self.store}-{product_id}-获取上传ck值成功')

        # 开始处理图片上传并组装格式
        main_images = []
        for i in upload_data['main_images']:
            result_dict = self.upload_main_images(i, ck)
            if result_dict['code'] == 0:
                result = result_dict['data']
                if result['complete'] and result['content']['file_name'] != '':
                    image = {"img_name": result['content']['file_name'], "storage": result['content']['storage']}
                    main_images.append(image)
                else:
                    logging.warning(f'{self.store}-{product_id}-上传主图异常')
                    record_main_image_error(self.store, product_id)
                    return {'code': 1, 'status': False, 'product_id': product_id}
            elif result_dict['code'] == 1:
                logging.warning(f'{self.store}-{product_id}-上传主图异常')
                record_main_image_error(self.store, product_id)
                return {'code': 1, 'status': False, 'product_id': product_id}
            elif result_dict['code'] == 3:
                logging.warning(f'{self.store}-{product_id}-主图404异常')
                record_main_image_error(self.store, product_id)
                return {'code': 3, 'status': False, 'product_id': product_id}
        logging.info(f'{self.store}-{product_id}-主图上传成功')

        # 获取大量修改的表单数据
        modify_data = self.process_user_class(product_id)

        # 处理后台自定义分类链接
        user_class_select = modify_data[f'user_class_select_{product_id}']
        if not user_class_select:
            logging.warning(f'{self.store}-{product_id}-获取后台自定义分类编号失败')
            return {'code': 1, 'status': False, 'product_id': product_id}
        logging.info(f'{self.store}-{product_id}-获取后台自定义分类编号成功')

        # 类目id
        category_id = upload_data['category_id']
        shop_id = self.process_category_id(category_id)

        # 商品标题
        title = self.process_title(upload_data['name'])

        # 处理最终的上架数据包
        data_dict = {
            'shop_id': shop_id,  # 类目id
            'process_img': json.dumps(main_images),  # 主图数据包
            'g_name': title,  # 标题
            'user_class_select': user_class_select,  # 后台自自定义分类编码
            'g_mode': 'B',  # mode
            'g_direct_price': upload_data['direct_price'],
            'spec_info': spec_info,  # sku数据包
            'show_num': show_num,  # 总库存数量
            'is_goods_sale': '0',  # 銷售時間設定 0: 立即销售  1: 指定销售时间
            'sale_start_time': '',  # 銷售時間設定-开始时间(如果 is_goods_sale=1,此参数必填)
            'sale_end_time': '',  # 銷售時間設定-结束时间，不填则表示无限
            'g_condition': 'B',  # 物品新旧 B: 全新
            'stock_status': '1',  # 备货状态 3: 24h内出货  1: 3天内出货  4: 7天内出货  0: 21天内出货  6: 较长备货  2: 预售商品
            'customized_ship_date': '',  # 较长备货的天数 22-90天
            'pre_order_ship_date': self.current_month,  # 预计出货时间
            'text2': upload_data['description'],  # 详情
            'g_flag': '6_1',  # 特别醒目标签
            'g_location': '台北市',  # 物品所在地
            'g_buyer_limit_value': '',  # 买家下标限制-评价总分
            'g_buyer_limit_nega': '',  # 买家下标限制-差劲评分
            'g_buyer_limit_abandon': '',  # 买家下标限制-近半年弃单次数
            'g_ship': 'A',  # 运费规定 A: 买家自付  B: 免运费
            'g_pay_way': self.g_pay_way,  # 付款方式
            'g_deliver_way': self.g_deliver_way,  # 运输方式
            'g_accept_shiprule': '1'  # 合并运费规则
        }

        # 将 item_detail 合并在上货数据包中
        data_dict.update(item_detail_dict)

        # 设定两个标记参照
        modify_title_mark = False  # 修改标题重新上架标记
        preview_success_mark = False  # 进入标题预览页面成功标记

        for retry in range(2):
            # 将json转成 multipart/form-data 格式
            boundary, multipart_data = self.structure_multipart(data_dict)

            # 第一次请求进入预览页面
            url_action = f'https://mybidu.ruten.com.tw/upload/item_action.php?ck={ck}'

            headers = dict(self.headers, **{'Content-Type': f'multipart/form-data; boundary=----{boundary}'})
            response_action = self.request_function(url_action, 'post', headers=headers, data=multipart_data, proxies=self.proxies)

            # 判断第一步上架请求的状态
            response_action_url = response_action.url
            if 'filter_msg' in response_action_url:
                logging.warning(f'{self.store}-{product_id}-此商品无法上架露天(尝试修改标题的方式上架)')
                data_dict['g_name'] = f'huangjinlang_{product_id}'
                modify_title_mark = True
                continue
            elif 'item_preview' in response_action_url:
                logging.info(f'{self.store}-{product_id}-初始上架请求成功')
                preview_success_mark = True
                break
            else:
                logging.info(f'{self.store}-{product_id}-上架未知错误')
                return {'code': 1, 'status': False, 'product_id': product_id}

        if preview_success_mark is False:
            return {'code': 1, 'status': False, 'product_id': product_id}

        # 完成最终的上架请求
        url_finalize = f"https://mybidu.ruten.com.tw/upload/item_finalize.php?ck={ck}"
        response_finalize = self.request_function(url_finalize, headers=self.headers, proxies=self.proxies)

        # 判断上架状态
        response_finalize_url = response_finalize.url
        if 'g_no' in response_finalize_url:
            # 提取商品id
            parsed_url = urlparse(response_finalize_url)
            query_params = parse_qs(parsed_url.query)
            g_no = query_params.get('g_no', [None])[0]
            # 记录数据库
            if modify_title_mark:
                filter_data = self.modify_title_to_upload(g_no, title)
                if filter_data['code'] != 0:
                    unable_to_list_id_record(self.store, product_id)
                    record_product_id_listing_status(self.store, g_no, g_no)
                    return {'code': 4, 'status': False, 'product_id': product_id, 'after_listing_id': g_no}
            logging.info(
                f"{self.store}-{product_id}-{ {'after_listing_id': g_no, 'status': True, 'data': '上架成功'} }")
            with self.lock:
                # 成功计数
                self.upload_count += 1
                self.initial_count += 1
                logging.info(f'{self.store}-当日商品已上传成功{self.upload_count}-本轮商品已成功上传{self.initial_count}')
            record_product_id_listing_status(self.store, product_id, g_no)
            return {'code': 0, 'status': True, 'product_id': product_id}
        logging.warning(f'{self.store}-{product_id}-上传商品失败')
        return {'code': 1, 'status': False, 'product_id': product_id}

# 创建店铺处理函数
def process_store(row):
    # 解析数据
    store = row[0]  # 店铺名
    number_of_spaces_in_title = int(row[1])  # 需重新上架 标题空格数
    maximum_bids = int(row[2])  # 需重新上架 最大出价数
    maximum_views = int(row[3])  # 需重新上架 最大点阅数
    maximum_traces = int(row[4])  # 需重新上架 最大追踪数
    min_price = int(row[5])  # 需重新上架 最小价格
    max_price = int(row[6])  # 需重新上架 最大价格
    time_interval_for_loading = row[7]  # 禁止上货时间区间（整点）
    quantity_limit_per_round = int(row[8])  # 每一轮数据处理量

    # 获取当前上货数量
    upload_count = get_the_daily_listing_quantity(store)
    logging.info(f'{store}-当日商品已上传{upload_count}')

    # 创建 Ruten 实例
    ruten_instance = Ruten(store, upload_count)

    # 开始检查是否有需要下架的商品id
    remove_list = get_id_to_be_removed(store)
    if remove_list:
        remove_list_new = split_list(remove_list)
        for sublist in remove_list_new:
            ruten_instance.remove_products(sublist)
        logging.info(f'{store}-需要下架id处理完成')
    logging.info(f'{store}-无需处理下架id')

    # 获取无法上架的ID置于列表
    unable_to_list = get_the_id_that_cannot_be_listed(store)

    # 启动参数
    page_num = 200  # 初始页数
    while True:
        # 判断当前时间是否符合启动条件
        while True:
            current_hour = datetime.now().hour
            start_hour, end_hour = map(int, time_interval_for_loading.split('-'))
            if start_hour <= current_hour < end_hour:
                logging.info(f'{store}-当前时间不符合启动条件, 休眠300s')
                time.sleep(300)
            else:
                break

        remove_list = []  # 下架列表
        logging.info(f'{store}-当前页数第{page_num}页')
        product_id_lsit = ruten_instance.get_pagination_product_id(page_num)  # 获取分页链接的商品数据
        with concurrent.futures.ThreadPoolExecutor(max_workers=store_workers) as executor:
            futures = []
            for product_data in product_id_lsit:
                product_id = str(product_data['product_id'])
                # 如果商品id在不可上架的id列表中，跳过
                if product_id in unable_to_list:
                    continue

                # 判断此轮的上架成功个数
                if ruten_instance.initial_count >= quantity_limit_per_round:
                    ruten_instance.close()
                    return

                # 处理标题空格数
                title = product_data['title']
                while '  ' in title:
                    title = title.replace('  ', ' ')

                # 判断标题空格数
                if title.count(' ') <= number_of_spaces_in_title and int(product_data['sales']) <= maximum_bids:
                    # 判断商品价格最小值、最大值、出价数、点阅数、追踪数
                    if (int(product_data['min_price']) < min_price and int(product_data['max_price']) > 1000) or (
                            min_price <= int(product_data['min_price']) <= max_price):
                        if int(product_data['click']) <= maximum_views and int(product_data['cart']) <= maximum_traces:
                            # 满足条件，提交任务到线程池
                            futures.append(executor.submit(ruten_instance.upload_products, product_id))
                        else:
                            logging.info(f"{store}-{product_id}-不做循环上下架处理(点阅数/追踪数)")
                    else:
                        logging.info(f"{store}-{product_id}-进行下架处理(价格)")
                        remove_list.append(product_id)
                else:
                    logging.info(f"{store}-{product_id}-不做循环上下架处理(标题空格数/销量)")

            # 等待所有提交到线程池的任务完成
            for future in concurrent.futures.as_completed(futures):
                try:
                    upload_data = future.result()
                    if upload_data['code'] == 1:
                        continue
                    elif upload_data['code'] == 0:
                        remove_list.append(upload_data['product_id'])
                    elif upload_data['code'] == 4:
                        remove_list.append(upload_data['after_listing_id'])
                    elif upload_data['code'] == 3:
                        remove_list.append(upload_data['product_id'])
                except Exception:
                    logging.exception(f'{store}-上货发生错误: {e}')
                    record_upload_error(store, upload_data['product_id'])

            if remove_list:
                ruten_instance.remove_products(remove_list)

            # 设置页数
            page_num = 200 if page_num == 1 else page_num - 1


# 设置日志配置
logging_config.setup_logger()


if __name__ == '__main__':
    account = input('请输入你的账号: ')
    if account == 'yey':
        mysql_pool = MySqlPool(host='db-7ff794f7008e4a0595ac3ab2f02bca6c.mysql.rds.aliyuncs.com', password='Luteen123@', user='administrator', database='luteen')
        proxies = {
            'http': 'http://brd-customer-hl_54bd3cd4-zone-datacenter_proxy1:otublxun7iir@brd.superproxy.io:22225',
            'https': 'https://brd-customer-hl_54bd3cd4-zone-datacenter_proxy1:otublxun7iir@brd.superproxy.io:22225',
        }
    elif account == 'gaoqiu':
        mysql_pool = MySqlPool(host='db-7ff794f7008e4a0595ac3ab2f02bca6c.mysql.rds.aliyuncs.com', password='Luteen123@', user='administrator', database='luteen')
        proxies = {
            'http': 'http://brd-customer-hl_9380d5d1-zone-datacenter_proxy1:m1rt0f8g88fl@brd.superproxy.io:33335',
            'https': 'https://brd-customer-hl_9380d5d1-zone-datacenter_proxy1:m1rt0f8g88fl@brd.superproxy.io:33335',
        }
    elif account == 'huangjinlang':
        mysql_pool = MySqlPool(host='rm-gw80g135076f1osh41o.mysql.germany.rds.aliyuncs.com', password='Qiang123@', user='huangjinlang', database='ruten_upload')
        proxies = {
            'http': 'http://brd-customer-hl_8240a7b6-zone-ruten_remove:g4w5c685daes@brd.superproxy.io:33335',
            'https': 'https://brd-customer-hl_8240a7b6-zone-ruten_remove:g4w5c685daes@brd.superproxy.io:33335',
        }
    else:
        # 异常退出，状态码为 1
        sys.exit(1)

    if getattr(sys, 'frozen', False):
        # 打包后，使用临时解压目录
        base_path = sys._MEIPASS
    else:
        # 开发时，使用脚本所在目录
        base_path = r'D:\露天精细化运营工具\ruten循环上下架'

    # 构建 Excel 文件的完整路径
    excel_path = os.path.join(base_path, '店铺配置表.xlsx')

    # 读取店铺配置表
    df = pd.read_excel(excel_path, header=0, sheet_name='基本配置')
    rows_list = df.values.tolist()

    # 读取标题前缀词
    df1 = pd.read_excel(excel_path, sheet_name='标题随机文字')
    title_prefix = df1.iloc[:, 0].tolist()

    # 读取线程数
    df2 = pd.read_excel(excel_path, sheet_name='线程数')
    store_workers = df2.iloc[:, 0].tolist()[0]

    # 最大线程数
    max_workers = len(rows_list)
    logging.info(f'当前执行线程{max_workers}')

    # 创建主线程池
    main_pool = ThreadPoolExecutor(max_workers=max_workers)

    # 外层循环，不断重复执行任务
    while True:
        tasks = []
        for row in rows_list:
            # 提交任务到线程池
            task = main_pool.submit(process_store, row)
            tasks.append(task)  # 将任务添加到列表

        # 等待所有任务完成
        wait(tasks, return_when=ALL_COMPLETED)
        logging.info("所有任务执行完成，开始下一轮任务执行")