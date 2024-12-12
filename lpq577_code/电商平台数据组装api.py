import json
import PIL
import requests
import re
import random
import string

from PIL import Image
from bs4 import BeautifulSoup
from io import BytesIO
from logging_config import logging
from fake_useragent import UserAgent

class Alibaba:
    def __init__(self, product_id=None, source=None):
        self.product_id = product_id
        self.ua = UserAgent().chrome
        self.source = source if source else self.link_request()

    def link_request(self):
        for _ in range(4):
            try:
                request_url = f'https://m.1688.com/offer/{self.product_id}.htm'
                response = requests.get(url=request_url, headers={'User-Agent': self.ua}).text
                if '下架商品页面' in response:
                    return False
                sku_source = re.findall(r'(?<=window\.__INIT_DATA=).*', response)[0]
                return json.loads(sku_source)
            except Exception as e:
                logging.warning(f"1688链接请求错误: {str(e)}")

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
                                  '武汉', '地区', '成都', '跨境', '批发', '直发']
        title = self.source['globalData']['tempModel']['offerTitle']
        for word in title_word_replacement:
            title = title.replace(word, '')
        return title

    def get_main_images(self):
        return self.source['globalData']['images']

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
            soup = BeautifulSoup(requests.get(url=data['detailUrl']).text, 'html.parser')
            for img in soup.find_all('img'):
                if 'src' in img.attrs:
                    src = img['src'].replace("\\\"", "")
                    response = requests.get(src, headers=headers)
                    try:
                        img = Image.open(BytesIO(response.content))
                        if img.size[0] >= 700 and img.size[1] >= 600:
                            if img.size[1]/img.size[0] <= 3:
                                image_sources.append(src)
                    except PIL.UnidentifiedImageError:
                        logging.warning(f"The URL {src} does not seem to be a valid image.")
            return image_sources

    def get_product_attribute(self):
        data = self.first_non_empty_item_in_data('values')
        Filter_words = ['专利', '跨境', '货号', '下游', '订制', '地区', '授权', '进口', 'LOGO', '上市', '是否', '加工', '货源',
                        '产地', '形象', '代理', '售后']
        attribute_list = [(f"{x['name']}:{x['value']}") for x in data if
                          all(word not in x['name'] for word in Filter_words) and x['value'] != '/']
        return attribute_list

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
                skuProps = self.source['globalData']['skuModel'].get('skuProps', [])
                if not skuProps:
                    specifications = 0
                    stock = self.source['globalData']['orderParamModel']['orderParam'].get('canBookedAmount', None)
                    price = self.source['globalData']['orderParamModel']['orderParam']['skuParam']['skuRangePrices'][0]['price']
                    if float(price) <= 40:
                        sku_assembly = {
                            'sku_data': {'price': price, 'stock': stock},
                        }
                    else:
                        return {'status': False, 'specifications': specifications, 'data': '商品价格不符合'}
                elif len(skuProps) == 1:
                    specifications = 1
                    sku1_property_name = self.source['globalData']['skuModel']['skuProps'][0]['prop'].replace('产品', '')
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
                            price = sku_maps[sku_value].get('discountPrice') or sku_maps[sku_value].get('price') or self.get_current_price()
                            if float(price) <= 40:
                                if imageUrl:
                                    skus = {
                                        'remote_id': self.product_id + '_' + self.generate_random_string(10),
                                        'name': sku_value,
                                        'imageUrl': imageUrl,
                                        'price': price,
                                        'stock': sku_maps[sku_value]['canBookCount']
                                    }
                                    sku_assembly['sku_data']['sku_parameter'].append(skus)
                                else:
                                    return {'status': False, 'specifications': specifications, 'data': 'sku图片缺失'}
                            else:
                                continue

                elif len(skuProps) == 2:
                    specifications = 2
                    sku1_property_name = self.source['globalData']['skuModel']['skuProps'][0]['prop'].replace('产品', '')
                    sku2_property_name = self.source['globalData']['skuModel']['skuProps'][1]['prop'].replace('产品', '')
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
                                price = sku_maps[sku_value].get('discountPrice') or sku_maps[sku_value].get('price') or self.get_current_price()
                                if float(price) <= 40:
                                    if imageUrl:
                                        skus = {
                                            'remote_id': self.product_id + '_' + self.generate_random_string(10),
                                            'name': i['name'] + '||' + j['name'],
                                            'imageUrl': i.get('imageUrl', None),
                                            'price': price,
                                            'stock': sku_maps[sku_value]['canBookCount']
                                        }
                                        sku_assembly['sku_data']['sku_parameter'].append(skus)
                                    else:
                                        return {'status': False, 'specifications': specifications, 'data': 'sku图片缺失'}
                                else:
                                    continue
                else:
                    return {'status': False, 'specifications': '-1', 'data': '商品规格超出'}
                if specifications == 0 or sku_assembly['sku_data']['sku_parameter']:
                    product_package = {
                        'product_id': self.product_id,
                        'specifications': specifications,
                        'start_amount': self.get_start_amount(),
                        'title': self.get_title(),
                        'main_images': self.get_main_images(),
                        'skumodel': sku_assembly,
                        'video': self.get_video(),
                        'details_text_description': self.get_product_attribute(),
                        'detailed_picture': self.get_detail_images(),
                    }
                    return {'status': True, 'data': product_package}
                else:
                    return {'status': False, 'specifications': '-1', 'data': '商品价格处理后未满足要求'}
            return {'status': False, 'specifications': None, 'data': '商品起批数不符合要求'}
        else:
            return {'status': False, 'specifications': None, 'data': '商品已离线'}

res = Alibaba('638797126308')
res1 = res.build_product_package()
print(res1)