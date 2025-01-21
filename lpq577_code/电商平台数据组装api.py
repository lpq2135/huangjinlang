import json
import time

import requests
import re
import random
import string

from PIL import Image
from bs4 import BeautifulSoup
from io import BytesIO
from logging_config import logging


class Alibaba:
    def __init__(self, product_id=None, source=None):
        self.product_id = product_id
        self.source = source if source else self.link_request()

    def request_function(self, url, headers=None, stream=None):
        for attempt in range(10):
            try:
                response = requests.get(url=url, headers=headers, stream=stream, timeout=(30, 120))

                # 如果状态码是 404，直接返回
                if response.status_code == 404:
                    return response

                # 检查其他状态码的合法性
                response.raise_for_status()
                return response

            except requests.exceptions.RequestException as e:
                logging.warning(f"HTTP请求异常 (尝试 {attempt + 1}/8): {e}")
                time.sleep(2)

        logging.error(f"请求失败，已尝试8次: {url}")
        return None

    def link_request(self):
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36'}
        try:
            request_url = f'https://m.1688.com/offer/{self.product_id}.htm'
            response = self.request_function(request_url, headers).text
            if '下架商品页面' in response or '无法查看或已下架' in response:
                return False
            sku_source = re.findall(r'(?<=window\.__INIT_DATA=).*', response)[0]
            return json.loads(sku_source)
        except Exception as e:
            logging.warning(f"1688链接请求错误: {str(e)}")
            return None

    def generate_random_string(self, length):
        letters = string.ascii_letters + string.digits
        return ''.join(random.choice(letters) for _ in range(length))

    def first_non_empty_item_in_data(self, name=None):
        for key in self.source['data']:
            if 'data' in self.source['data'][key]:
                data = self.source['data'][key]['data']
                if name in (data if isinstance(data, dict) else data[0]):
                    return data

    def get_title(self):
        title_word_replacement = ['厂家', '供应', '销售', '规格', '齐全', '现货', '发货', '促销', '生产', '东莞',
                                  '武汉', '地区', '成都', '跨境', '批发', '直发', '量大从优']
        title = self.source['globalData']['tempModel']['offerTitle']
        for word in title_word_replacement:
            title = title.replace(word, '')
        return title

    def get_main_images(self):
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
        }
        images_data = [i['fullPathImageURI'] if 'fullPathImageURI' in i else i['imgUrl'] for i in self.source['globalData']['images']]
        main_images = []
        for i in images_data[:8]:
            response = self.request_function(i, headers, True)
            if response.status_code == 404:
                return []
            elif response.status_code == 200:
                img = Image.open(BytesIO(response.content))
                if img.size[0] >= 200 and img.size[1] >= 200:
                    main_images.append(i.split('?')[0])
                    continue
                return []
        return main_images if len(main_images) >= 3 else []

    def get_unit_weight(self):
        try:
            # 尝试获取 unit_weight
            unit_weight = self.source['globalData']['skuModel']['extraInfo']['freightInfo']['unitWeight']

            # 如果 unit_weight 为 0，从 skuWeight 中提取第一个值
            if unit_weight == 0:
                unit_weight = next(
                    iter(self.source['globalData']['skuModel']['extraInfo']['freightInfo']['skuWeight'].values()), None
                )

            # 如果 unit_weight 小于等于 0.01，返回 None
            if unit_weight is not None and unit_weight <= 0.01:
                return None

            # 返回有效的 unit_weight
            return unit_weight
        except Exception:
            # 发生异常时返回 None
            return None

    def get_current_price(self):
        data = self.first_non_empty_item_in_data('priceModel')
        if data and 'priceModel' in data:
            return data['priceModel']['currentPrices'][0]['price']

    def get_detail_images(self):
        data = self.first_non_empty_item_in_data('detailUrl')
        image_sources = []
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'
        }
        if data and 'detailUrl' in data:
            soup = BeautifulSoup(self.request_function(url=data['detailUrl']).text, 'html.parser')
            for img in soup.find_all('img'):
                if 'src' in img.attrs:
                    src = img['src'].replace("\\\"", "").strip('/').split('?')[0]
                    if 'data:image' in src or 'chrome-extension' in src or 'file' in src or src == '' or 'cbu1' in src or not any(ext in src for ext in ['.jpg', '.jpeg', '.png']):
                        continue
                    response = self.request_function(src, headers, True)
                    img = Image.open(BytesIO(response.content))
                    if img.size[0] >= 700 and img.size[1] >= 600:
                        if img.size[1] / img.size[0] <= 3:
                            image_sources.append(src)
            return image_sources

    def get_product_attribute(self):
        # web端
        # data = self.first_non_empty_item_in_data('values')
        # app端
        data = self.first_non_empty_item_in_data('propsList')
        if data is not None:
            Filter_words = ['专利', '跨境', '货号', '下游', '订制', '地区', '授权', '进口', 'LOGO', '上市', '是否', '加工',
                            '货源',
                            '产地', '形象', '代理', '售后']
            attribute_list = [(f"{x['name']}:{x['value']}") for x in data['propsList'] if
                              all(word not in x['name'] for word in Filter_words) and x['value'] != '/']
            return attribute_list
        return None

    def get_video(self):
        data = self.first_non_empty_item_in_data('videoUrl')
        if data:
            return data['videoUrl']

    def get_start_amount(self):
        data = self.source['globalData']['orderParamModel']['orderParam']['beginNum']
        return data

    def build_product_package(self):
        if self.source:
            if self.get_start_amount() <= 5:
                main_images = self.get_main_images()
                if len(main_images) != 0:
                    skuProps = self.source['globalData']['skuModel'].get('skuProps', [])
                    if not skuProps:
                        specifications = 0
                        stock = random.randint(900, 1000)
                        price = \
                        self.source['globalData']['orderParamModel']['orderParam']['skuParam']['skuRangePrices'][0][
                            'price']
                        if float(price) <= 40:
                            sku_assembly = {
                                'sku_data': {'price': price, 'stock': stock},
                            }
                        else:
                            return {'status': False, 'specifications': specifications, 'data': '商品价格不符合'}
                    elif len(skuProps) == 1:
                        specifications = 1
                        sku1_property_name = self.source['globalData']['skuModel']['skuProps'][0]['prop'].replace(
                            '产品', '')
                        sku_assembly = {
                            'sku_data': {
                                'sku_property_name': {'sku1_property_name': sku1_property_name},
                                'sku_parameter': []
                            }
                        }
                        sku_props = self.source['globalData']['skuModel']['skuProps']
                        sku_maps = self.source['globalData']['skuModel']['skuInfoMap']
                        for i in sku_props[0]['value']:
                            sku_value = i['name']
                            imageUrl = i.get('imageUrl', None)
                            if sku_value in sku_maps:
                                price = sku_maps[sku_value].get('discountPrice') or sku_maps[sku_value].get(
                                    'price') or self.get_current_price()
                                if float(price) <= 40:
                                    if imageUrl:
                                        skus = {
                                            'remote_id': self.product_id + '_' + self.generate_random_string(10),
                                            'name': sku_value,
                                            'imageUrl': imageUrl,
                                            'price': price,
                                            'stock': random.randint(900, 1000)
                                        }
                                        sku_assembly['sku_data']['sku_parameter'].append(skus)
                                    else:
                                        return {'status': False, 'specifications': specifications,
                                                'data': 'sku图片缺失'}
                                else:
                                    continue

                    elif len(skuProps) == 2:
                        specifications = 2
                        sku1_property_name = self.source['globalData']['skuModel']['skuProps'][0]['prop'].replace(
                            '产品', '')
                        sku2_property_name = self.source['globalData']['skuModel']['skuProps'][1]['prop'].replace(
                            '产品', '')
                        sku_props = self.source['globalData']['skuModel']['skuProps']
                        sku_maps = self.source['globalData']['skuModel']['skuInfoMap']
                        sku_assembly = {
                            'sku_data': {
                                'sku_property_name': {
                                    'sku1_property_name': sku1_property_name,
                                    'sku2_property_name': sku2_property_name
                                },
                                'sku_parameter': []
                            }
                        }
                        for i in sku_props[0]['value']:
                            imageUrl = i.get('imageUrl', None)
                            for j in sku_props[1]['value']:
                                sku_value = i['name'] + '&gt;' + j['name']
                                if sku_value in sku_maps:
                                    price = sku_maps[sku_value].get('discountPrice') or sku_maps[sku_value].get(
                                        'price') or self.get_current_price()
                                    if float(price) <= 40:
                                        if imageUrl:
                                            skus = {
                                                'remote_id': self.product_id + '_' + self.generate_random_string(10),
                                                'name': i['name'] + '||' + j['name'],
                                                'imageUrl': i.get('imageUrl', None),
                                                'price': price,
                                                'stock': random.randint(900, 1000)
                                            }
                                            sku_assembly['sku_data']['sku_parameter'].append(skus)
                                        else:
                                            return {'status': False, 'specifications': specifications,
                                                    'data': 'sku图片缺失'}
                                    else:
                                        continue
                    else:
                        return {'status': False, 'specifications': None, 'data': '商品规格超出'}
                    if specifications == 0 or sku_assembly['sku_data']['sku_parameter']:
                        product_package = {
                            'product_id': self.product_id,
                            'specifications': specifications,
                            'unit_weight': self.get_unit_weight(),
                            'start_amount': self.get_start_amount(),
                            'title': self.get_title(),
                            'main_images': main_images,
                            'skumodel': sku_assembly,
                            'video': self.get_video(),
                            'details_text_description': self.get_product_attribute(),
                            'detailed_picture': self.get_detail_images(),
                        }
                        return {'status': True, 'data': product_package}
                    else:
                        return {'status': False, 'specifications': specifications, 'data': '商品价格处理后未满足要求'}
                else:
                    return {'status': False, 'specifications': None, 'data': '商品主图异常'}
            return {'status': False, 'specifications': None, 'data': '商品起批数不符合要求'}
        else:
            return {'status': False, 'specifications': None, 'data': '商品已离线'}


if __name__ == '__main__':
    res = Alibaba('863212756596')
    try:
        res1 = res.build_product_package()
        print(res1)
    except Exception as e:
        print(e)