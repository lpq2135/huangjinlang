import requests
import random
import string
import logging
import time
from requests.exceptions import ReadTimeout, RequestException


class BaseCrawler:
    """所有爬虫类的基类，包含共用方法"""
    def request_function(self, url, method='GET', headers=None, data=None, proxies=None, files=None, timeout=30, max_retries=5):
        """通用的请求方法"""
        # 进行最多max_retries次重试
        for attempt in range(max_retries):
            try:
                response = requests.request(
                    url=url,
                    method=method.upper(),
                    headers=headers,
                    data=data,
                    proxies=proxies,
                    files=files,
                    timeout=timeout
                )

                # 对于404或400状态码，直接返回响应对象
                if response.status_code in (404, 400):
                    return response

                # 检查HTTP状态码，如果不是2xx会抛出HTTPError异常
                response.raise_for_status()
                return response

            except ReadTimeout as e:
                # 单独处理超时错误
                logging.warning(f"请求超时 ({method}-{url}): {e}. 重试中... ({attempt + 1}/{max_retries})")
                time.sleep(2 ** attempt)  # 指数退避策略

            except RequestException as e:
                if hasattr(e, 'response') and e.response is not None:
                    if e.response.status_code in (404, 400):
                        return e.response
                logging.warning(f"请求错误 ({method}-{url}): {e}. 重试中... ({attempt + 1}/{max_retries})")
                time.sleep(2 ** attempt)

            except Exception as e:
                # 处理其他未知异常
                logging.error(f"未知错误 ({method}-{url}): {e}")
                return None

        logging.error(f"请求失败，已重试{max_retries}次: {url}")
        return None

    def generate_random_string(self, length=10):
        """生成随机字符串"""
        chars = string.ascii_letters + string.digits
        return ''.join(random.choice(chars) for _ in range(length))

    def generate_random_number(self, length=8):
        """生成指定位数的随机数字，第一位不为0"""
        first_digit = random.choice("123456789")  # 第一位1-9
        other_digits = ''.join(random.choices("0123456789", k=length - 1))  # 其余位0-9
        return first_digit + other_digits

    def generate_spec_info_by_ruten(self, data_json):
        """组装成 ruten 上货数据包"""
        # 提取基础数据
        sku_parameters = data_json['data']['skumodel']['sku_data']['sku_parameter']
        # 获取规格数
        specifications = data_json['data']['specifications']

        # 计算最低价格
        price_list = [int(i['price']) for i in sku_parameters]
        min_price = min(price_list) if price_list else 0

        # 初始化数据结构
        structure = {}
        specs = {}
        d_new = {}  # 临时ID映射

        # 单规格处理
        if specifications == 1:
            for item in sku_parameters:
                temp_id = 'temp_' + self.generate_random_number()
                structure[temp_id] = []

                specs[temp_id] = {
                    'spec_id': temp_id,
                    'parent_id': 0,
                    'spec_name': item['name'],
                    'spec_num': item['stock'],
                    'spec_price': item['price'],
                    'spec_status': 'Y',
                    'childs': [],
                    'spec_ext': {'goods_no': None}
                }
        # 双规格处理
        elif specifications == 2:
            d1, d2 = [], []  # 规格1和规格2的值列表

            # 收集所有规格值并去重
            for item in sku_parameters:
                sku1_value, sku2_value = item['name'].split('||')
                if sku1_value not in d1:
                    d1.append(sku1_value)
                if sku2_value not in d2:
                    d2.append(sku2_value)

            # 为每个规格值生成临时ID并构建结构
            for spec1 in d1:
                temp1 = 'temp_' + self.generate_random_number()
                d_new[temp1] = spec1
                structure[temp1] = {}

                for spec2 in d2:
                    temp2 = 'temp_' + self.generate_random_number()
                    d_new[temp2] = spec2
                    structure[temp1][temp2] = []

            # 构建规格详情
            for parent_id, children in structure.items():
                specs[parent_id] = {
                    'spec_id': parent_id,
                    'parent_id': '0',
                    'spec_name': d_new[parent_id],
                    'spec_num': '0',
                    'spec_status': 'Y',
                    'childs': children,
                    'spec_ext': {'goods_no': ''}
                }

            for parent_id, children in structure.items():
                for child_id in children.keys():
                    combined_name = f"{d_new[parent_id]}||{d_new[child_id]}"
                    sku_item = next((i for i in sku_parameters if i['name'] == combined_name), None)

                    specs[child_id] = {
                        'spec_id': child_id,
                        'parent_id': parent_id,
                        'spec_name': d_new[child_id],
                        'spec_num': sku_item['stock'] if sku_item else 499,
                        'spec_price': sku_item['price'] if sku_item else min_price,
                        'spec_status': 'Y' if sku_item else 'N',
                        'childs': [],
                        'spec_ext': {'goods_no': ''}
                    }

        spec_info = {
            'level': specifications,
            'structure': structure,
            'specs': specs,
        }
        g_direct_price = min_price
        return spec_info, g_direct_price

    def split_list(self, input_list):
        """将输入列表分成多个子列表，每个子列表最多包含 chunk_size 个元素"""
        return [input_list[i:i + 30] for i in range(0, len(input_list), 30)]