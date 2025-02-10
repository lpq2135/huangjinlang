import json
import re
import requests
import time
import hashlib
import hmac
import urllib.parse
import random
import xmltodict
import math
import itertools
import math
import concurrent.futures

from datetime import datetime
from logging_config import logging


class Helper:
    def generate_random_number(self, length):
        """
        :param length: 生成的长度
        :return: 返回生成后的字符串
        """
        if length > 0:
            first_digit = str(random.randint(1, 9))  # a random digit between 1 and 9
            other_digits = ''.join(str(random.randint(0, 9)) for _ in range(length - 1))  # the rest of the digits
            random_number = first_digit + other_digits
            return random_number
        else:
            return "Length should be greater than 0"

    def perform_request(self, url, method='GET', headers=None, files=None, data=None):
        try:
            if method.upper() == 'GET':
                response = requests.get(url, timeout=30)
            elif method.upper() == 'POST':
                response = requests.post(url, headers=headers, files=files, data=data, timeout=30)
            else:
                raise ValueError('Invalid method: {}'.format(method))

            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as http_err:
            logging.warning('HTTP error occurred: {}'.format(http_err))
        except Exception as err:
            logging.warning('Other error occurred: {}'.format(err))


class DarazProduct(Helper):
    """
    daraz上货处理的相关代码
    """
    def __init__(self, app_key=None, app_secret=None, access_token=None, upload_site=None, attrs=None):
        regions = {
            'mm': 'https://api.shop.com.mm/rest',  # 缅甸
            'bd': 'https://api.daraz.com.bd/rest',  # 孟加拉国
            'pk': 'https://api.daraz.pk/rest',  # 巴基斯坦
            'lk': 'https://api.daraz.lk/rest',  # 斯里兰卡
            'np': 'https://api.daraz.com.np/rest',  # 尼泊尔
        }
        self.timestamp = int(time.time() * 1000)
        self.app_key = app_key
        self.app_secret = app_secret
        self.upload_site = upload_site
        self.site_url = regions[self.upload_site]
        self.access_token = access_token
        self.attrs = attrs
        self.product_id = self.attrs.get('product_id') if self.attrs else None
        self.category_attributes = self.get_category_attributes() if self.attrs else None

    def sign(self, parameters, api_path):
        """
        生成签名
        :param api_path:
        :param parameters: 字典格式，排序后组装新的字符串
        :return: 返回签名
        """
        sort_dict = sorted(parameters)
        parameters_str = "%s%s" % (api_path, str().join('%s%s' % (key, parameters[key]) for key in sort_dict))
        h = hmac.new(self.app_secret.encode(encoding="utf-8"), parameters_str.encode(encoding="utf-8"),
                     digestmod=hashlib.sha256)
        return h.hexdigest().upper()

    def build_url(self, parameters, api_path):
        """
        构建请求链接
        :param api_path:
        :param parameters: 字典格式，排序后组装新的字符串
        :return: 返回组装好的链接
        """
        query_string = '&'.join(
            f"{urllib.parse.quote(k, safe='')}={urllib.parse.quote(str(v), safe='')}" for k, v in parameters.items())
        query_string = query_string.replace('%20', '+')
        url = f"{self.site_url}{api_path}?{query_string}"
        return f"{url}&sign={self.sign(parameters, api_path)}"

    def generate_access_token(self, code):
        parameters = {
            'app_key': self.app_key,
            'app_secret': self.app_secret,
            'sign_method': 'sha256',
            'timestamp': self.timestamp,
            'code': code
        }
        url = self.build_url(parameters, '/auth/token/create')
        response = self.perform_request(url, 'post')
        return response

    def upload_image(self, file_path, photo_name):
        """
        上传本地图片
        """
        parameters = {
            'access_token': self.access_token,
            'app_key': self.app_key,
            'sign_method': 'sha256',
            'timestamp': self.timestamp
        }
        url = self.build_url(parameters, '/image/upload')
        with open(file_path, 'rb') as f:
            files = {'image': (photo_name, f)}
            try:
                response = self.perform_request(url, 'post', files=files)
                image_url = response['data']['image']['url']
                return image_url
            except Exception as e:
                logging.warning(f"daraz本地图片上传失败: {e}")

    def migrate_images(self, images):
        """
        一次性上传多张网络图片
        """
        retry = 0
        while True:
            photo_data = {"Request": {"Images": {"Url": images}}}
            xml_photo_data = xmltodict.unparse(photo_data)
            parameters = {
                'payload': xml_photo_data,
                'access_token': self.access_token,
                'app_key': self.app_key,
                'sign_method': 'sha256',
                'timestamp': self.timestamp
            }
            url = self.build_url(parameters, '/images/migrate')
            try:
                response = self.perform_request(url, 'post')
                batch_id = response['batch_id']
                result = self.image_response_get(batch_id)
                if result['status_code'] == 0:
                    logging.info(f"{self.product_id}-{self.upload_site}-图片上传daraz服务器成功")
                    return result['data']
                elif result['status_code'] == 1:
                    retry += 1
                    time.sleep(2)
                    logging.warning(f"{self.product_id}-{self.upload_site}-daraz网络图片重新获取, 重试第{retry}次")
                elif result['status_code'] == 2:
                    return None
            except Exception:
                retry += 1
                logging.warning(f"{self.product_id}-{self.upload_site}-daraz网络图片重新获取, 重试第{retry}次")

    def migrate_image(self, images):
        """
        上传单张网络图片
        """
        photo_data = {"Request": {"Image": {"Url": images}}}
        xml_photo_data = xmltodict.unparse(photo_data)
        parameters = {
            'payload': xml_photo_data,
            'access_token': self.access_token,
            'app_key': self.app_key,
            'sign_method': 'sha256',
            'timestamp': self.timestamp
        }
        url = self.build_url(parameters, '/image/migrate')
        try:
            response = self.perform_request(url, 'post')
            return response['data']['url']
        except Exception as e:
            logging.warning(f"{self.product_id}-daraz网络图片上传失败（单张）: {e}")

    def image_response_get(self, batch_id):
        """
        针对MigrateImages API的返回信息
        """
        for _ in range(3):
            parameters = {
                'batch_id': batch_id,
                'access_token': self.access_token,
                'app_key': self.app_key,
                'sign_method': 'sha256',
                'timestamp': self.timestamp
            }
            url = self.build_url(parameters, '/image/response/get')
            try:
                time.sleep(3)
                response = self.perform_request(url, 'get')
                if response['code'] == '0':
                    images = [i['url'] for i in response['data']['images']]
                    return {'status_code': 0, 'data': images}
                elif response['code'] == '1000':
                    return {'status_code': 1, 'data': None}
                elif response['code'] == '301':
                    return {'status_code': 2, 'data': None}
                else:
                    logging.warning(f"{self.product_id}-{self.upload_site}-daraz网络图片获取异常（多张）,重试第{_ + 1}次")
                    time.sleep(3)
            except Exception:
                logging.warning(f"{self.product_id}-{self.upload_site}-daraz网络图片获取异常（多张）,重试第{_ + 1}次")
                time.sleep(3)
        return {'status_code': 1, 'data': None}

    def get_category_attributes(self):
        """
        获取类别属性
        :return:
        """
        parameters = {
            'access_token': self.access_token,
            'app_key': self.app_key,
            'sign_method': 'sha256',
            'timestamp': self.timestamp,
            'primary_category_id': self.attrs.get('primary_category'),
            'language_code': 'en_US'
        }
        url = self.build_url(parameters, '/category/attributes/get')
        time.sleep(2)
        for _ in range(5):
            try:
                result = self.perform_request(url, 'get')
                if result['code'] == '0':
                    is_mandatory_attributes = {
                        'data': [x for x in result['data'] if x['attribute_type'] == 'normal' and x['is_mandatory'] == 1
                                 and x['name'] != 'name' and x['name'] != 'name_en' and x['name'] != 'short_description'
                                 and x['name'] != 'short_description_en' and x['name'] != 'description_en'
                                 and x['name'] != 'brand']
                    }
                    is_mandatory_sku = [x for x in result['data'] if x['attribute_type'] == 'sku' and x['is_sale_prop'] == 1
                                        and x['name'] != 'SellerSku' and x['name'] != 'price' and x['name'] != 'package_weight'
                                        and x['name'] != 'package_length' and x['name'] != 'package_width'
                                        and x['name'] != 'package_height' and x['name'] != '__images__'
                                        and x['name'] != 'quantity' and x['name'] != 'special_price'
                                        and x['name'] != 'special_from_date' and x['name'] != 'special_to_date'
                                        and x['name'] != 'seller_promotion' and x['name'] != 'package_content']
                    return is_mandatory_attributes, is_mandatory_sku
                elif result['code'] == '4228':
                    return {'status': False, 'data': '此类目在该站点不合法'}
                elif result['code'] == '4227':
                    return {'status': False, 'data': '此类目在该站点不存在'}
                elif result['code'] == 'IllegalAccessToken':
                    return {'status': False, 'data': 'access_token异常'}
            except Exception as e:
                logging.warning(f'{self.product_id}-获取类目属性失败，重试第{_ + 1}次，错误信息：{e}')
                time.sleep(2)
        return None

    def check_sku(self, specifications):
        """
        遍历检查sku长度进行进一步处理
        计算单规格和双规格中字符串长度>20的数据个数占总长度的百分比
        :return:包含百分比的字典
        """
        total_len_over_20_sku1, total_len_over_20_sku2 = 0, 0
        unique_sku1, unique_sku2 = set(), set()
        result = dict()
        for i in self.attrs.get('skumodel')['sku_data']['sku_parameter']:
            i['name'] = ((re.sub(r'\s{2,}', ' ', re.sub(r'\(.*?\)', '', i['name']))).replace('~', '-')).replace(' kg', 'kg')
            if specifications == 1:
                unique_sku1.add(i['name'])
                total_len_over_20_sku1 += len(i['name']) > 20

            elif specifications == 2:
                sku1, sku2 = map(str.strip, i['name'].split('||'))
                unique_sku1.add(sku1)
                unique_sku2.add(sku2)
                total_len_over_20_sku1 += len(sku1) > 20
                total_len_over_20_sku2 += len(sku2) > 20

        if specifications == 1:
            result['sku1_percentage'] = total_len_over_20_sku1 / len(unique_sku1) if unique_sku1 else 0
        elif specifications == 2:
            result['sku1_percentage'] = total_len_over_20_sku1 / len(unique_sku1) if unique_sku1 else 0
            result['sku2_percentage'] = total_len_over_20_sku2 / len(unique_sku2) if unique_sku2 else 0
        return result

    def assembly_attributes(self, sku_transformation_list):
        # 获取标题 列表处理函数
        def split_into_tens(number):
            base = math.floor(number / 10)
            larger_number = math.ceil(number / 10)
            larger_number_count = number % 10
            result = [larger_number] * larger_number_count + [base] * (10 - larger_number_count)
            return result

        def split_list_into_tens(lst):
            divisions = split_into_tens(len(lst))
            it = iter(lst)
            output = [list(itertools.islice(it, i)) for i in divisions]
            return output

        dict_attributes = self.category_attributes[0]
        # 获取标题
        title = (self.attrs.get('title').replace(',', '')).replace('"', '')
        # 获取白底图
        promotion_whitebkg_image = self.attrs.get('promotion_whitebkg_image')
        if promotion_whitebkg_image:
            photo_name = promotion_whitebkg_image['photo_name']
            photo_xpath = r'D:/Daraz运营工具/Daraz采集组装工具/附件库/图片下载/' + photo_name
        # 获取详情文字
        details_text_description = self.attrs.get('details_text_description') if self.attrs.get('details_text_description') else []
        # 处理详情图片成html格式
        detailed_picture_html = "".join(f'<img src="{url}" alt="Image">' for url in self.attrs.get('detailed_picture'))

        # 处理最终的html格式
        if sku_transformation_list:
            if len(sku_transformation_list) <= 10:
                sku_text_description_html = "<ul>" + "".join(f'<li>{item}</li>' for item in sku_transformation_list) + "</ul>"
            else:
                sku_output = split_list_into_tens(sku_transformation_list)
                sku_text_description_html = '<ul>' + ''.join(f'<li>{"  ◕  ".join(map(str, i))}</li>' for i in sku_output) + '</ul>'
            # 处理详情文字html格式
            details_text_description_html = (
                    '<article class="lzd-article" style="white-space:break-spaces"><p style="line-height:1.7;text-align:left;text-indent:0;margin-left:0;margin-top:0;margin-bottom:0"><span style="font-weight:bold;background-color:rgb(153, 204, 255);font-size:18pt">Product Introduction:</span></p>' + "".join(
                f'<p style="font-size:12pt">● {item}</p>' for item in details_text_description) + "</ul>")
            html_all = details_text_description_html + '<br/>' + detailed_picture_html
            # 组装上货属性值
            product_Attributes = {
                'name': title,
                'name_en': title,
                'short_description': sku_text_description_html,
                'short_description_en': sku_text_description_html,
                'description': html_all,
                'description_en': html_all,
                'brand': 'No Brand',
                'promotion_whitebkg_image': self.upload_image(photo_xpath, photo_name) if promotion_whitebkg_image else None
            }
        else:
            if len(details_text_description) <= 10:
                details_text_description_html = "<ul>" + "".join(f'<li>{item}</li>' for item in details_text_description) + "</ul>"
            else:
                details_text_output = split_list_into_tens(details_text_description)
                details_text_description_html = '<ul>' + ''.join(f'<li>{"  ◕  ".join(map(str, i))}</li>' for i in details_text_output) + '</ul>'
            # 组装上货属性值
            product_Attributes = {
                'name': title,
                'name_en': title,
                'short_description': details_text_description_html,
                'short_description_en': details_text_description_html,
                'description': detailed_picture_html,
                'description_en': detailed_picture_html,
                'brand': 'No Brand',
                'promotion_whitebkg_image': self.upload_image(photo_xpath, photo_name) if promotion_whitebkg_image else None
            }
        for x in dict_attributes['data']:
            if x['name'] == 'warranty_type':
                product_Attributes[x['name']] = 'No Warranty'
            elif 'options' in x:
                if any('Not Specified' in option.values() for option in x['options']):
                    product_Attributes[x['name']] = 'Not Specified'
                elif any('Standard' in option.values() for option in x['options']):
                    product_Attributes[x['name']] = 'Standard'
                elif any('-' in option.values() for option in x['options']):
                    product_Attributes[x['name']] = '-'
                else:
                    product_Attributes[x['name']] = x['options'][0]['name']
            else:
                product_Attributes[x['name']] = 'See description'

        return product_Attributes

    def assembly_skus(self):
        """
        声明自定义变体，组装sku数据
        :return: 返回组装好的sku包
        """
        def formatted_time():
            current_time = datetime.now()
            formatted_time = current_time.strftime("%Y-%m-%d")
            return formatted_time

        def add_quantity():
            return random.randint(500, 999)

        def add_images():
            return None if i['imageUrl'] is None else {'Image': i['imageUrl']}

        def process_sku(specifications, i, sku1_property=None, sku1_property_value=None, sku2_property=None,
                        sku2_property_value=None):
            sale_prop = {sku1_property: sku1_property_value} if specifications == 1 else \
                {sku1_property: sku1_property_value, sku2_property: sku2_property_value}
            skus = {
                'SellerSku': self.generate_random_number(8),
                'quantity': add_quantity(),
                'price': i['price'],
                'special_price': int(i['price'] * 0.97),
                'special_from_date': formatted_time(),
                'special_to_date': '2029-12-31',
                'package_length': self.attrs.get('length'),
                'package_height': self.attrs.get('height'),
                'package_weight': self.attrs.get('weight'),
                'package_width': self.attrs.get('width'),
                'package_content': self.product_id,
                'Images': add_images(),
                'saleProp': sale_prop
            }
            return skus

        def process_variation(specifications, sku1_property=None, sku2_property=None):
            is_mandatory_sku = self.category_attributes[1]
            name_list = [item['name'] for item in is_mandatory_sku]
            hasImage = True if sku_data['sku_parameter'][0]['imageUrl'] is not None else False
            properties = [prop for prop in [sku1_property, sku2_property] if prop is not None]
            customize = not all(any(prop in name for name in name_list) for prop in properties)
            if customize:
                sku1_property = sku1_property.title()
                sku2_property = sku2_property.title() if sku2_property else None
            else:
                sku1_property = next(x for x in name_list if sku1_property in x)
                sku2_property = next(x for x in (item['name'] for item in is_mandatory_sku) if sku2_property in x) if sku2_property else None
            if specifications == 2:
                if sku1_property == sku2_property:
                    customize = True
                    sku1_property = 'Variants_1'
                    sku2_property = 'Variants_2'
            variation1 = {
                "name": sku1_property,
                "hasImage": hasImage,
                "customize": customize,
                "options": {"option": []}
            }
            if specifications == 1:
                variation = {'variation1': variation1}
                return variation, hasImage, sku1_property
            elif specifications == 2:
                variation2 = {
                    "name": sku2_property,
                    "hasImage": False,
                    "customize": customize,
                    "options": {"option": []}
                }
                variation = {'variation1': variation1, 'variation2': variation2}
                return variation, hasImage, sku1_property, sku2_property

        def process_tips(specifications, hasImage, price, sku1_property, sku1_property_value, sku2_property=None,
                         sku2_property_value=None):
            skus_under_description = {
                'SellerSku': self.generate_random_number(8),
                "quantity": 0,
                "package_length": 10,
                "package_height": 10,
                "package_weight": 0.1,
                "package_width": 10,
                "price": price,
                'special_from_date': formatted_time(),
                'special_to_date': '2029-12-31',
                "Images": {"Image": 'https://static-01.daraz.pk/p/3c32f9a77a8232967e996a93524d459a.jpg' if self.upload_site == 'pk' else 'https://static-01.daraz.com.bd/p/3c32f9a77a8232967e996a93524d459a.jpg'} if hasImage else None,
                "package_content": self.product_id
            }
            if specifications == 1:
                skus_under_description.update({'saleProp': {sku1_property: sku1_property_value}})
            elif specifications == 2:
                skus_under_description.update(
                    {'saleProp': {sku1_property: sku1_property_value, sku2_property: sku2_property_value}})
            return skus_under_description

        sku_data = self.attrs.get('skumodel')['sku_data']
        product_Skus = {'Sku': []}
        specifications = self.attrs.get('specifications')
        sku_transformation_list = []
        sku1_transformation_list = []
        sku2_transformation_list = []
        sku_deduplication = set()
        # 无规格
        if specifications == 0:
            skus = {
                'SellerSku': self.generate_random_number(8),
                'quantity': random.randint(500, 999),
                'price': sku_data['price'],
                'special_price': int(sku_data['price'] * 0.97),
                'special_from_date': formatted_time(),
                'special_to_date': '2029-12-31',
                'package_length': self.attrs.get('length'),
                'package_height': self.attrs.get('height'),
                'package_weight': self.attrs.get('weight'),
                'package_width': self.attrs.get('width'),
                'package_content': self.product_id,
            }
            product_Skus['Sku'].append(skus)
            variation = {}
        # 单规格
        elif specifications == 1:
            count = 1
            sku_percentage = self.check_sku(specifications)
            sku1_property = sku_data['sku_property_name']['sku1_property_name']
            variation, hasImage, sku1_property = process_variation(specifications, sku1_property)
            for i in sku_data['sku_parameter']:
                if i['name'] in sku_deduplication:
                    continue
                sku_deduplication.add(i['name'])
                if hasImage and i['imageUrl'] is None:
                    continue
                if len(i['name']) > 20 and sku_percentage['sku1_percentage'] <= 0.2:
                    continue
                sku1_property_value = i['name'] if sku_percentage[
                                                       'sku1_percentage'] <= 0.2 else sku1_property.title() + '_' + str(count)
                skus = process_sku(specifications, i, sku1_property, sku1_property_value)
                product_Skus['Sku'].insert(0, skus)
                if sku1_property_value not in variation['variation1']['options']['option']:
                    variation['variation1']['options']['option'].append(sku1_property_value)
                if sku_percentage['sku1_percentage'] > 0.2:
                    sku1_transformation_list.append(sku1_property_value + ': ' + i['name'])
                    count += 1
            if sku_percentage['sku1_percentage'] > 0.2:
                skus_under_description = process_tips(specifications, hasImage, i['price'], sku1_property, 'Skus in details')
                product_Skus['Sku'].append(skus_under_description)
                variation['variation1']['options']['option'].append('Skus in details')
            sku_transformation_list = sku1_transformation_list
            return product_Skus, variation, sku_transformation_list

        # 双规格
        elif specifications == 2:
            unique_sku1, unique_sku2 = {}, {}
            count1 = 1
            count2 = 1
            sku_percentage = self.check_sku(specifications)
            sku1_property = sku_data['sku_property_name']['sku1_property_name']
            sku2_property = sku_data['sku_property_name']['sku2_property_name']
            variation, hasImage, sku1_property, sku2_property = process_variation(specifications, sku1_property,
                                                                                  sku2_property)
            for i in sku_data['sku_parameter']:
                if i['name'] in sku_deduplication:
                    continue
                sku_deduplication.add(i['name'])
                if hasImage and i['imageUrl'] is None:
                    continue
                sku1_value, sku2_value = i['name'].split("||")
                if len(sku1_value) > 20 and sku_percentage['sku1_percentage'] <= 0.2:
                    continue
                if sku1_value not in unique_sku1:
                    unique_sku1[sku1_value] = count1
                    count1 += 1
                sku1_property_value = sku1_value if sku_percentage[
                                                        'sku1_percentage'] <= 0.2 else sku1_property.title() + '_' + str(
                    unique_sku1[sku1_value])
                if len(sku2_value) > 20 and sku_percentage['sku2_percentage'] <= 0.2:
                    continue
                if sku2_value not in unique_sku2:
                    unique_sku2[sku2_value] = count2
                    count2 += 1
                sku2_property_value = sku2_value if sku_percentage[
                                                        'sku2_percentage'] <= 0.2 else sku2_property.title() + '_' + str(
                    unique_sku2[sku2_value])

                skus = process_sku(specifications, i, sku1_property, sku1_property_value, sku2_property,
                                   sku2_property_value)
                if sku1_property_value not in variation['variation1']['options']['option']:
                    variation['variation1']['options']['option'].append(sku1_property_value)
                if sku2_property_value not in variation['variation2']['options']['option']:
                    variation['variation2']['options']['option'].append(sku2_property_value)
                if sku_percentage['sku1_percentage'] > 0.2:
                    if sku1_property_value + ': ' + sku1_value not in sku1_transformation_list:
                        sku1_transformation_list.append(sku1_property_value + ': ' + sku1_value)
                if sku_percentage['sku2_percentage'] > 0.2:
                    if sku2_property_value + ': ' + sku2_value not in sku2_transformation_list:
                        sku2_transformation_list.append(sku2_property_value + ': ' + sku2_value)
                product_Skus['Sku'].insert(0, skus)
            if sku_percentage['sku1_percentage'] > 0.2:
                skus_under_description = process_tips(specifications, hasImage, i['price'], sku1_property, 'Skus in details',
                                                      sku2_property, variation['variation2']['options']['option'][0])
                product_Skus['Sku'].append(skus_under_description)
                variation['variation1']['options']['option'].append('Skus in details')
            else:
                if sku_percentage['sku2_percentage'] > 0.2:
                    skus_under_description = process_tips(specifications, hasImage, i['price'], sku1_property,
                                                          variation['variation1']['options']['option'][0],
                                                          sku2_property, 'Skus in details')
                    product_Skus['Sku'].append(skus_under_description)
                    variation['variation2']['options']['option'].append('Skus in details')
            sku_transformation_list = sku1_transformation_list + sku2_transformation_list
        return product_Skus, variation, sku_transformation_list

    def get_category_tree(self):
        """
        获取类目树
        :return:系统中所有产品类别的列表
        """
        parameters = {
            'access_token': self.access_token,
            'app_key': self.app_key,
            'sign_method': 'sha256',
            'timestamp': self.timestamp
        }
        url = self.build_url(parameters, '/category/tree/get')
        return self.perform_request(url, 'post')

    def create_product(self):
        """
        创建产品
        """
        if 'status' not in self.category_attributes:
            product_Skus, variation, sku_transformation_list = self.assembly_skus()
            images = self.migrate_images(self.attrs.get('main_images'))
            if images:
                json_product_data = {
                    "Request": {
                        "Product": {
                            "PrimaryCategory": self.attrs.get('primary_category'),
                            "Images": {"Image": images},
                            "Attributes": self.assembly_attributes(sku_transformation_list),
                            "Skus": product_Skus,
                        }
                    }
                }
                if variation:
                    json_product_data["Request"]["Product"]["variation"] = variation
                xml_product_data = xmltodict.unparse(json_product_data)
                parameters = {
                    'payload': xml_product_data,
                    'app_key': self.app_key,
                    'sign_method': 'sha256',
                    'access_token': self.access_token,
                    'timestamp': self.timestamp,
                }
                sign = self.sign(parameters, '/product/create')
                url = self.site_url + '/product/create'
                parameters['sign'] = sign
                time.sleep(3)
                for _ in range(6):
                    result = self.perform_request(url, 'post', data=parameters)
                    if result['code'] == '0':
                        return {'upload_site': self.upload_site, 'upload_code': 0, 'product_id': self.product_id, 'data': '商品上传成功', 'item_id': result['data']['item_id']}
                    elif result['code'] == 'ApiCallLimit':
                        time.sleep(3)
                    elif result['code'] == '500':
                        return {'upload_site': self.upload_site, 'upload_code': -1, 'product_id': self.product_id, 'data': '商品上传出现状态码500错误'}
                    elif result['code'] == 'IllegalAccessToken':
                        return {'upload_site': self.upload_site, 'upload_code': -2, 'product_id': self.product_id, 'data': 'accesstoken错误'}
                    elif result['code'] == '4221':
                        return {'upload_site': self.upload_site, 'upload_code': -3, 'product_id': self.product_id, 'data': '平台限制产品上传(可能违规)'}
                    elif result['code'] == '5':
                        return {'upload_site': self.upload_site, 'upload_code': -4, 'product_id': self.product_id, 'data': '数据包错误(异常请求)'}
                    elif result['code'] == '209':
                        return {'upload_site': self.upload_site, 'upload_code': -9, 'product_id': self.product_id, 'data': '规格的长度超过50'}
                    else:
                        return {'upload_site': self.upload_site, 'upload_code': -5, 'product_id': self.product_id, 'data': '上传未知异常'}
            else:
                return {'upload_site': self.upload_site, 'upload_code': -6, 'product_id': self.product_id,
                        'data': '商品主图出现304异常'}
        return {'upload_site': self.upload_site, 'upload_code': -7, 'product_id': self.product_id, 'data': self.category_attributes['data']}

    def get_product_list(self):
        """
        获取产品的详细信息
        :return: 产品信息
        """
        parameters = {
            'access_token': self.access_token,
            'app_key': self.app_key,
            'sign_method': 'sha256',
            'timestamp': self.timestamp,
            'filter': 'live',
            'create_after': '2025-01-20T00:00:00+0800'
        }
        url = self.build_url(parameters, '/products/get')
        return self.perform_request(url, 'get')

    def product_remove(self, sku_id_list):
        """
        获取产品的详细信息
        :return: 产品信息
        """
        parameters = {
            'access_token': self.access_token,
            'app_key': self.app_key,
            'sign_method': 'sha256',
            'timestamp': self.timestamp,
            'sku_id_list': json.dumps(sku_id_list)
        }
        url = self.build_url(parameters, '/product/remove')
        return self.perform_request(url, 'post')


def calculate_price_percentage(sku_parameter, price_max):
    """
    计算超出价格上限得百分比
    """
    price_exceeds_percentage = len(list(filter(lambda x: x['price'] > price_max, sku_parameter))) / len(sku_parameter)
    return price_exceeds_percentage


def processing_price(upload_site, data, weight):
    if 'sku_parameter' in data['sku_data']:
        sku_parameter = data['sku_data']['sku_parameter']
        for i in sku_parameter:
            i['price'] = calculate_local_price(upload_site, i['price'], weight)
        if upload_site == 'pk':
            pk_price_exceeds_percentage = calculate_price_percentage(sku_parameter, 4600)
            if pk_price_exceeds_percentage <= 0.2:
                data['sku_data']['sku_parameter'] = [item for item in sku_parameter if item['price'] <= 4600]
                if data['sku_data']['sku_parameter']:
                    return True
                else:
                    return False
            return False
        return True
    else:
        pk_price_0 = calculate_local_price(upload_site, data['sku_data']['price'], weight)
        data['sku_data']['price'] = pk_price_0
        if upload_site == 'pk':
            if pk_price_0 <= 4600:
                return True
            else:
                return False
        return True


def calculate_local_price(upload_site, original_price, weight):
    usd_to_cny = 7.14  # 美元-人民币汇率
    label_fee = 2.5  # 贴单
    additional_fee_by_1688 = 5  # 1688产生的额外费用
    if upload_site == 'pk':
        acceptance_rate = 0.7  # 签收率
        dommission_rate = 0.0978  # 产品佣金（类目）
        us_to_local = 278.8  # 巴基斯坦卢比-美金 汇率
        order_handling_fee = 0.07  # usd
        final_freight_vat = 0.1  # usd
        payment_fee = 0.08  # 回款手续费
        first_leg_cross_border_freight = 65 / usd_to_cny * weight if weight <= 0.15 else 80 / usd_to_cny * weight  # 头程跨境运费
    elif upload_site == 'bd':
        acceptance_rate = 0.7  # 签收率
        dommission_rate = 0.089  # 产品佣金（类目）
        us_to_local = 119.15  # 孟加拉塔卡-美金 汇率
        order_handling_fee = 0.05  # usd
        final_freight_vat = 0.12  # usd
        payment_fee = 0.085  # 回款手续费
        first_leg_cross_border_freight = 90 / usd_to_cny * weight if weight <= 0.15 else 95 / usd_to_cny * weight  # 头程跨境运费
    price = float(original_price)
    # 物流操作费
    logistics_operation_fee = 2 / usd_to_cny if weight <= 0.15 else 3.5 / usd_to_cny
    # 头程运费总计
    total_first_leg_freight = first_leg_cross_border_freight + logistics_operation_fee
    # 根据采购价计算利润
    profit = 10 if price <= 10 else price
    # 采购价 + 利润
    fod = (profit + price + label_fee + additional_fee_by_1688) / usd_to_cny
    # 美金售价
    price_in_us_dollars = (total_first_leg_freight + fod + order_handling_fee + final_freight_vat) / (
                1 - payment_fee - dommission_rate)
    # 当地售价
    price_in_pk_dollars = price_in_us_dollars * us_to_local
    # 最终售价
    final_price_in_pk_dollars = price_in_pk_dollars / acceptance_rate

    return int(final_price_in_pk_dollars)


app_key = '502742'
app_secret = '0XGyiUMf0obAP9FueDD16fid4M5xgmaV'
access_token = '50000700427xJGacrTiQ7JFvzoxbBahXhkxASTe1bf75f6bchDyeOtzeOqh0Wh'


def process_product(e):
    """ 处理每个 DarazProduct 任务 """
    down_id = DarazProduct(app_key, app_secret, e[0], e[1])

    while True:
        result = down_id.get_product_list()

        if 'total_products' in result['data']:
            for i in result['data']['products']:
                sku_id_list = ['SkuId_' + (j['ShopSku'].replace('PK-', '')).replace('BD-', '') for j in i['skus']]

                # 分批处理，每批 20 个 SKU
                num_chunks = math.ceil(len(sku_id_list) / 20)
                list_chunks = [sku_id_list[i * 20:(i + 1) * 20] for i in range(num_chunks)]

                for list_data in list_chunks:
                    res = down_id.product_remove(list_data)
                    if res['code'] == '0':
                        print(e[2] + json.dumps(list_data, ensure_ascii=False) + " 下架成功")

        else:
            print(f'{e[2]}-{e[1]} 产品下架完成')
            break


if __name__ == '__main__':
    my_dict = {'6005286464204': [['50000401d07tf5Xddpi1a589df7sWTFolMJZDVUAEwEQsDSoWwrMvyAvawF8Sm', 'pk', 'Kotoko2810@163.com'], ['50000201b06rQKpeek17dbb6d6fv9KUxcHiJn0gSVoi0CuucMPzSqpvVh5a0Sj', 'bd', 'Kotoko2810@163.com']], '6005281104176': [['50000601818vTAqbtoEeegQ7NVxgni15ce4f38So2hsUGh5noThMr4RrJqD6Mf', 'pk', 'enjoyed6462@163.com'], ['50000400c31sxAAp3RTcg1itCLyZTqdYgis6rutDFgS11d5b26dgzHQst6pTes', 'bd', 'enjoyed6462@163.com']], '6005286432192': [['50000200a12MUJ7j9qzsrhYz13206279HwEIUgyOGAhFx5PWThFDyJ1kKHOCUC', 'pk', 'hope20242024@163.com'], ['50000401501ap1f27c6bc8ueHreRvgXgDU4oV0hmfuJymtVBjYCPPdLQlfzJnz', 'bd', 'hope20242024@163.com']], '6005280944183': [['50000300b24fhZiBn4vUfB0GUihqfwoefjDS1b3dde946KRWkIiOpaHTScVzhs', 'pk', 'weimei202403@163.com'], ['50000800c04sxAAp144fee24Vnq9BZJwkhwEuvfbcaT3KTXeniMlWfTuASZhes', 'bd', 'weimei202403@163.com']], '6005286336691': [['50000100100b1d16fa16m1wUs9exxlrhnnpxmrDBygUgLwAWolXDFR9Pu8p7AN', 'pk', 'voli_987@163.com'], ['50000501917eYIatojbFaRfmrtFoi1bae3105vKYexV9H1ExTgSvxuPoChVwSK', 'bd', 'voli_987@163.com']], '6005300496577': [['50000700735bRILfvgMAR2OQCD1myhkpAuSg6gEQCnUTGhd11dc3316uQsD0PD', 'pk', 'oywy71@sina.com'], ['50000601122xdIaa3nYFmSAsTldcCShs0T1808021bioIJLYIQyGcwHvkCu8lt', 'bd', 'oywy71@sina.com']], '6005300688794': [['50000400533Ue2brwdr9KAR1tpae6iUjHyDSwi8dav4rw1d2f4a36ufIBEsNUu', 'pk', 'ran1313155@yeah.net'], ['50000300231xPOTpBetygSiiktYQu9YcHxgHtZyxfbj11126c4dcx3sWRsJ8Ak', 'bd', 'ran1313155@yeah.net']], '6005286576113': [['50000301d31tf5XdCphLz0jKfykZkRyGExkpPayO1rL1318226btWVeo78PRQm', 'pk', 'User7824905@163.com'], ['50000301823vTAqbtRhAGhU6l0WCljMoVlS1db49511vFD3BstFNv1qtviRYhf', 'bd', 'User7824905@163.com']], '6005286256781': [['50000101c18biHdYbgUePryGgDJmZl17b0e972xzoEYCoPAOP1QNOzwjOoVLBx', 'pk', 'Jo0ety@163.com'], ['50000101a12jg2sqiYGjx9Nz19c8d8e50dggJn1jzzCFWATvgtuVslmvMkC99e', 'bd', 'Jo0ety@163.com']], '6005285968842': [['50000200c05sxAApw155f1922pRi83j0FjTgTtgachQiqU0hFdxL0iUSklYKMs', 'pk', 'zry29076922@163.com'], ['50000701b05rQKpeb1f440459jcP3px0EkeNG0iuVjD3CorcJxvpPn4WtoWZSj', 'bd', 'zry29076922@163.com']], '6005300336719': [['50000901a13jg2sqkYjEsAmVt1e1c62bblhmLHVDRTHHyFwScxQzqpOze7dDoe', 'pk', 'qkqkqi@sina.com'], ['50000200c05sxAApZ1b93e661qxZa4FwdlqBxPf7Bgu9mt0CfGxHvGUT5wGQfs', 'bd', 'qkqkqi@sina.com']], '6005279952549': [['50000900c33sxAApvrve81iWEpx9UTDYEfReryufhhMhX15bf0670mUzMdN6fs', 'pk', 'duoduooo888@163.com'], ['50000200c28sxAApwntcaZkVhJPgVSj8hbsALUUe1f39a2e3KiLm2ITXZC58gs', 'bd', 'duoduooo888@163.com']], '6005293664349': [['50000900d418YcoxqpABcF1eKwCTQj8dfv6l0YlhkMkzexUkH6HlL19820da0e', 'pk', 'bei913017738@126.com'], ['50000700800c1303d5f7gnesipApaNwgbdjYGHRgupcejht9qtUkgeSjpsHx0g', 'bd', 'bei913017738@126.com']], '6005300544507': [['50000700c29sxAApztybDyIzfJSDuOcYbbqAmRxcK1047becamOozHQUydxGLs', 'pk', 'zrq64979@yeah.net'], ['50000101919eYIatPcAEaterSVchmMk122e0e18XHtule2DsPdNsVRoRxiQLSK', 'bd', 'zrq64979@yeah.net']], '6005286528107': [['500007016100WMdjwizxfd1a1b3fa0ibs3oy1hlFQnVgwWGHX9sQBRpwR3tVU8', 'pk', 'z0987z@yeah.net'], ['50000800220xPOTpgCwvGvklIQWPpEhd1bb5401fIUDIS9wveZiFTAKwLSwOCk', 'bd', 'z0987z@yeah.net']], '6005281056175': [['50000501009pmFqbcZiwf1f955e15ptdyOe9bbyhsuXDkmRgvfzuAFyDKdCUNz', 'pk', 'meiwomaoyi@163.com'], ['50000400322amvobFUMfVDmmQWrpfZZiwF1ec10f35JqERSiWFbQdswUv8AxYz', 'bd', 'meiwomaoyi@163.com']], '6005301136525': [['50000501b21rQKpeekAs8lzteHFLLXkss1f92dd5fECwipvEQTXqLqVapaDcRj', 'pk', 'pu0298579887852@yeah.net'], ['50000200603pQ3q1dba8b6dMgS9lIwwpRAb3FThHrbxwf6FdQekvxFflh8P3hw', 'bd', 'pu0298579887852@yeah.net']], '6005300896679': [['50000900a38MUJ7jFRyPQiZYG1FqSdvTjdgAQBpv1clGJo0lvM1f889ac2TqoC', 'pk', 'wenmo3221963@163.com'], ['50000301011pmFqb9ylTciu18cdbb48DvsGaBhv3Nz0codthYiqzlf2A1alYgz', 'bd', 'wenmo3221963@163.com']], '6005303392719': [['50000901908eYIatPh7e1f084575DT4sTtDigNp4jySoEb9SSePxYPmpVemyRK', 'pk', 'kola1ew11@163.com'], ['50000701c39biHdYhCpClT0HHhPg4hy1ACYkvvjuP2yOq14emPG1d15c08dmVx', 'bd', 'kola1ew11@163.com']], '6005285968917': [['50000701b11rQKpeYdCu9lt1c430b13yliDvoVfxwAi1DtuFxx3ROqvaWqmE9j', 'pk', 'Osong321@163.com'], ['50000100523Ue2brveTDMksWqrgdYmuHMPD15c3f8a5WoC7ddtdtTXija66xUu', 'bd', 'Osong321@163.com']], '6005286272758': [['50000800a24MUJ7jlvwQpcb2j2GnseSTiADg1806d204sgnwufkIvpyh6Ng9VC', 'pk', 'T9T8T7_t5@163.com'], ['50000100d188YcoxmUZBzoUiHSEysg1876d240eCgu6n0xeljyLVkrtmbdR7ee', 'bd', 'T9T8T7_t5@163.com']], '6005286896056': [['50000601706hk5irbz1cb8bdcaSkffBTCrWwCKGyKXkqVBg5muudNr2quAqHcs', 'pk', 'Echo_0987@163.com'], ['50000501539ap8ueiqBtTd6eCPettxDmHKLYkSUol1mTTFKSvKt1ac26733rlz', 'bd', 'Echo_0987@163.com']], '6005286016919': [['50000901c27biHdYhbS3KUYcgiMmyhxTEkwmsvf1a9a3c63uR4toRw04hkIkXx', 'pk', 'JJ18150311072@163.com'], ['50000301b05rQKpeY189dd4a4jEU6nUYckDtHzFyvmf4CQoawRWPNpX3dAmSSj', 'bd', 'JJ18150311072@163.com']], '6005286800026': [['50000600928rB6r8ilQYmqDB7iXiMufxOleiaydL1c800db7RtdIhSGy0Byo90', 'pk', 'well666666888@126.com'], ['50000101331rQ1zh0hqydUxfYicr9Nx1fKgvJykysDF1bafcf4fYjQrcgq3gcq', 'bd', 'well666666888@126.com']], '6005281216167': [['50000700406xJGacvN1e8fe89fIt8lknxpQ9bbFtGHpg0ukWgDx3oTze6jJXTh', 'pk', 'bjyx10058050315@163.com'], ['50000400f14BeOnrga4F1lIyby1d03f4e0tEBdcx7LyWCFmJLyIvsEcwQNNQBs', 'bd', 'bjyx10058050315@163.com']], '6005281088196': [['50000601e31qTzccr7KT2fmgSmxewTAe3FOxgPvyqot1c92a34dx3Dpb2Hp6FK', 'pk', 'luckymini0317@163.com'], ['50000300525Ue2brLDS7ilvWMxEdZj2GhQfuS1464320cD7diu8NyuGovhoiVu', 'bd', 'luckymini0317@163.com']], '6005309232398': [['50000801c22biHdYBis5kR0ljjKoYEt1FD1720453bXlttcJRvyNRwyjYxrVEx', 'pk', 'kehuaishunbu902950@126.com'], ['50000501232og2Z0lxhIxe0uheheS9o0yDljRKYhy1mD166a82ddYmTrylbZfp', 'bd', 'kehuaishunbu902950@126.com']], '6005281264193': [['50000301104xdIaa1ef422fedn1Eip9uukfFdtdPuyDmgNowdtSkkanvb5cpUt', 'pk', 'HTianbooks@163.com'], ['50000701713hk5ir9ywfdciq81f5d25b6LRyggeSHxfTvlExBPuAJQvqQDARxs', 'bd', 'HTianbooks@163.com']], '6005286832015': [['50000500729bRILfwljFNXMuBfcI0gmSZxQHZdcw3120813a0nUVggmx0gbXQD', 'pk', 'Remedy_8@163.com'], ['50000700909rB6r8jnpZv15d2dcd9riZ1GXeLtBrSDfGEQ9K0uCHewm4VOCCW0', 'bd', 'Remedy_8@163.com']], '6005286160793': [['50000300501Ue14e9a12f2brvGV9qHNypRge3l2CoRfrpFbfDvCmTwhh0TlNBu', 'pk', 'tbzt38@sina.com'], ['50000900138bm1wUSDDSKIUgoBoYusgg2JxkJxiSuD7cav3Mry110ebf00zFUN', 'bd', 'tbzt38@sina.com']], '6005294256470': [['50000001b33rQKpe9iBQ5t0xlmkLkxDT0Ee2jPqiOq0wl1bb5a7eePaXCQIkrj', 'pk', 'yum52094@126.com'], ['50000800b15fhZiBsZmrCh0gvFJ1d5d90acrEyQjafiwgpyuDkGMpWmU6Jt0ys', 'bd', 'yum52094@126.com']], '6005294336387': [['50000700412xJGacruitljHr1bfffcd0vtRcf5GXdqpdTREdECtBluxFrmn3Sh', 'pk', 'frfpxd@sina.com'], ['50000200531Ue2brudrCqIu2vuABcjUDqrCVtHAEdw815eb385aOrzkGJ5NzTu', 'bd', 'frfpxd@sina.com']], '6005293664347': [['50000700122bm1wUSfDQTDSEIoNzoSfh3m1d2854000eIx9zRfficRBNSY1UAN', 'pk', 'bdu7gz25@21cn.com'], ['50000901831vTAqbVwC6gcrgkyzCGGwg3HrXDdbESve17b07a28LOzUuDv62hf', 'bd', 'bdu7gz25@21cn.com']], '6005286448008': [['50000801236og2Z0K1ELpBwSE6kju4pW0llFKlVjrsFjyloO136c9dbc9C3fMp', 'pk', 'rosskill1ll@163.com'], ['50000001214og2Z0h2ijrizoib1bfb6305cAwAksxgfFRjxfzvEi1lsvREw3fp', 'bd', 'rosskill1ll@163.com']], '6005300336722': [['50000200634pQ3qMesDnHwYOpZC6oyiiUa0ODAcCvinwtF18c2e3aalkET4ZOw', 'pk', 'rzbrrd@sina.com'], ['50000901427bPRgvCpqiVSjWgipiLT1FFjRivfS1ca36296sBEYHwwBuN35Rez', 'bd', 'rzbrrd@sina.com']], '6005300816746': [['50000601c06biHdYdD1801a4fePgrW0HKhNkylwyECXFSxCSu4pLm2wCAewHCx', 'pk', 'xianwei223476@yeah.net'], ['50000000e00j1f9d27460GwoubfdkXHMwAzQjbdCt8KxuclkRpzHzzmiIQhrTN', 'bd', 'xianwei223476@yeah.net']], '6005286544045': [['50000501a30jg2sqi6hDSCpVTGHdLLZEySlG4mRTfL13dca6bbpvRmtv0AHhpe', 'pk', 'p76652459@163.com'], ['50000201337rQ1zhyeKPbvqeYFcTiqrTcKhwHXdRWCCZGoxBD1d3c1f34NjOdq', 'bd', 'p76652459@163.com']], '6005280944191': [['50000101027pmFqb84g1gjyDvsDBhCP5myzlFku151c5cb6LzEtVHf1FPTsPLz', 'pk', '19926476274@163.com'], ['500001000021QO19d5b145ZxTwicuPirFlCsXQUAhcmUClPctohYiivAX7LjXh', 'bd', '19926476274@163.com']], '6005281280195': [['50000501014pmFqbeaiTjnthVs197f5b34l9bDw3rSwEoEvn4jyvli0nREFY5z', 'pk', 'ftnd44@sina.com'], ['50000200616pQ3qMEq7lEq2nTeb61f1cc5e0oteqxdxSg7DBy3ntycjjXnkXfw', 'bd', 'ftnd44@sina.com']], '6005281232185': [['50000501400b1cecf8bePRgvcLwBuoeYgdp3KS2GkjOo1dSwAcb8vxiQvcT8fz', 'pk', 'Eve1289745@163.com'], ['50000401317rQ1zhTcMPeuReddfr91434a2ccKzuDmmyjzDyWGexBuueD6IEeq', 'bd', 'Eve1289745@163.com']], '6005286688134': [['50000400805cgnesB181f2632jkQ1pUfa4FYGlvaRve8FisiOttDkfLnwDZqhg', 'pk', 'Htlaty724@163.com'], ['50000302029YS3q5KW0gGHLpXIVvkGzjvTCSq0vNO14445173WwgxBtfZozJlu', 'bd', 'Htlaty724@163.com']], '6005294224534': [['50000401815vTAqbzSkccfPBtzu14c187c1ffhQJyhR1ICY9tQBQT1tOmtv1gf', 'pk', 'vvzrpx@sina.com'], ['50000201707hk5irEuP17e95a4fGcgbP7PxUjhkwkweTXFHXBRRgMuvwVsEtws', 'bd', 'vvzrpx@sina.com']], '6005286336683': [['50000301f09eN4brdsWxG17dd3264IfMgweyWEk3DpqCOSVtqM317pGJifkEXy', 'pk', 'vzrb83@sina.com'], ['50000600806cgneshn148db17dApWmsZB5hTHKScwxcWgfwflzUGFeRlJc970g', 'bd', 'vzrb83@sina.com']], '6005301264375': [['50000501e37qTzccyhtwzljltj4HwyHdbFwRjOT4yNMazixd2191765bb7ekFK', 'pk', 'quanwen2472996@163.com'], ['50000200609pQ3qMkrkLo1a026508sxRvihaHylJwgVrjaecwCqutgFkomGuiw', 'bd', 'quanwen2472996@163.com']], '6005301104583': [['50000301a19jg2sqcXkdrBMrVCGGxKw12378d23grTHgbARwEysYQuvZN2Jzpe', 'pk', 'qiaolu7199065095@yeah.net'], ['500009016090WMdjqdWul169596f3cbEwBru1FgjNjaivxDeZFxtBuwYtyw5m8', 'bd', 'qiaolu7199065095@yeah.net']], '6005301056671': [['50000100536Ue2brvfrBLAoxqUAA7IVjLQgtuCcdDqdl0Yfm14fd1dbaz41FBu', 'pk', 'yaozhen48669027@163.com'], ['50000301c02biH1d381544dYhDsetsXEjgSgVfSXFE39woBNqVqqO2V6RDHlWx', 'bd', 'yaozhen48669027@163.com']], '6005301184459': [['50000901d17tf5Xdis9MvYigFOH3I1cd8f72fwyDfbHwuevTywqq1Y8vD9qKSm', 'pk', 'qingding37657659@163.com'], ['50000000d138YcoxMtDhyFzfH18c0806cyDusjAFbt7MwVhiEvpwitvn8JjCde', 'bd', 'qingding37657659@163.com']], '6005286464024': [['50000400220xPOTpdBrygzEp9w3mwZc3161a7cd6KTeMS9UwGWFgvdtT6YPdtk', 'pk', 'yifugongsi123@163.com'], ['50000600e23j0GwoSDZ4gXCmqcutG9hguCn16b8c2b2WzemeNh2iQTCcNXBVQN', 'bd', 'yifugongsi123@163.com']], '6005301024584': [['50000400d128YcoxvycDaGYH142a048cMSDUQFZhcwhPWYcliMj4eU1oIlyVNe', 'pk', 'qiaoshaogoudao782@126.com'], ['50000600200x181af786POTpdaTyFQ8j9OyuQDeyn2ehueVOlWFiq5nyka5m9k', 'bd', 'qiaoshaogoudao782@126.com']], '6005294464384': [['50000401d04tf5Xd10d534d2FsdKTzDGfQgwHvsEEwlsSAuuYrnsa0BR0pSjRm', 'pk', 'ffbjhl@sina.com'], ['50000600701bR1ccb6406ILfRiIFnXPuicYlWFquexqi8Cbw4qwVjjhthFwklD', 'bd', 'ffbjhl@sina.com']], '6005280928151': [['50000100916rB6r8qjuYnvggYKXl17b058b5mqhVxi6EcU5qUygHgKpXSlGoA0', 'pk', 'empty_2324@163.com'], ['50000501e37qTzccp5Mr2EifRnZks0DfWmPxfLoYtLP4zAobL1b29ef85qevYK', 'bd', 'empty_2324@163.com']], '6005301184542': [['50000200338amvobjwTGvBkjrZqUDh4lVlmphWQieFFyemVUHp16d60c91ZeFz', 'pk', 'wushoudou@yeah.net'], ['50000400712bRILfsDoGR3mw10381cdcf8ah2jqvCzwjafav8nrXejmLqpHKkD', 'bd', 'wushoudou@yeah.net']], '6005301152509': [['50000900b12fhZiBo0qPAgaF1727a617tiiycWvEdFguhOUVGKdKHxEvjuzDjs', 'pk', 'qunmeiju1@126.com'], ['50000301714hk5irhurdWhBv8m14f56a01z2GJfLh1iwzBfYiwwcRxZyeaaDfs', 'bd', 'qunmeiju1@126.com']], '6005294304376': [['50000601f00e1bd2a637N4briquvgfeMJYgxzAcWBvOgOxvPOMwa8QhPrdpDoy', 'pk', 'dbpl42@sina.com'], ['50000300233xPOTpgBtuEVCjEpVqr9bdK1iqrgvoF8fdu11898aedfOvd75j9k', 'bd', 'dbpl42@sina.com']], '6005354704412': [['50000201710hk5irdVwcAC1d21b1fbhSdtWwdjIvk2my09GwksxfwoaR03BXxs', 'pk', 'yuuiaw@sina.com'], ['50000900b20fhZiBoWpwhh4nuchqcyPg18bdabc8fkeU4sy0HiiyH2Duk0aZ1s', 'bd', 'yuuiaw@sina.com']], '6005286336693': [['50000300630pQ3qMHy6ojS3vRA93f2EhpBxPC6CAU81132bfdeOvvgGege04Pw', 'pk', 'alexandr0318@163.com'], ['50000000803cgne19b73974sFpCQ2NSgAcIzcMQbVvhZfDt5kVyDojxoF4TOzg', 'bd', 'alexandr0318@163.com']], '6005286464129': [['50000900628pQ3qMgTjLCqzmx9aZiyFLSaTpjefD16c4fb68Q8mrwGGkupIkSw', 'pk', 'Cax_ew@163.com'], ['50000000521Ue2bryIv8JIwwRsCabo1im1edab81ey9vScZDCy9oxyiKtmnGFu', 'bd', 'Cax_ew@163.com']], '6005285936897': [['50000701317rQ1zhWgnsgTPiYcjrh1a79f4dfmtzfGkuiwhUumFWHprczWTZJq', 'pk', 'Ri984025622@163.com'], ['50000000108bm1wUpbAT15d976d0NhV6plS1PqfBcfxDLxh0pjaehp4rzA53TN', 'bd', 'Ri984025622@163.com']], '6005294576231': [['50000100f13BeOnrcBaJWDhxh17cf6c46spiZEEtgpxVCKEvpvdtxkiaIOEKss', 'pk', 'muli898895@163.com'], ['50000800d118YcoxutefYg117e3bbe6kHycrqfcGeSBkxyjoFylVgrXm8iVRfe', 'bd', 'muli898895@163.com']], '6005309248519': [['50000902013YS3q5szxFnlvp21cc3272elxwDgbEoOhNxaSPn204TeHbzTgxmu', 'pk', 'liehan0663@126.com'], ['50000301b41rQKpecdawglV1inGMlZlxuEfWFuQiSQwxPtxXzVrzS1d234175j', 'bd', 'liehan0663@126.com']], '6005286256783': [['50000301734hk5irbxoHWhbxgou1fGDuLVeyuDH0DrxaQp1e838ab9Yxb0LRLs', 'pk', 'ugiumq@sina.com'], ['50000801025pmFqbBck2jotZySFbift9pzXjj192874bcGxm3Fq1lEYjVWF4ez', 'bd', 'ugiumq@sina.com']], '6005300336721': [['50000100a34MUJ7j9o1rtebyGThKqCTuhBchs4MwYfIjxm11348889VlSB0BDC', 'pk', 'lxhvht@sina.com'], ['50000400c32sxAApYmwDC4IuDKRhwPl7ghT3tvyHKHtl1e915b29ajV0PjLufs', 'bd', 'lxhvht@sina.com']], '6005286640049': [['50000901927eYIatueAGcRfmR0lliyj3HUy9cy9149b666atwauwWrnN3jG2AK', 'pk', 'w35626099@126.com'], ['50000500541Ue2brveR8qCSwNRhB7H0GhPctqCdbbyhKsUDK93y8T1beb4b14u', 'bd', 'w35626099@126.com']], '6005281216182': [['50000200d168YcoxsuCdZmUgMyht1075e103qfeigyfpVWhIhRJ3htvDC4piee', 'pk', 'goodgoodstudy968@163.com'], ['50000001d23tf5Xdip9qryHkhKp3IS1EH1m14d0511dvofOuXpnp34gsXxZdjm', 'bd', 'goodgoodstudy968@163.com']], '6005300640029': [['50000900517Ue2brvjSjhAQzqUh821da834e8g1lMwcySGbjfriPuzDownQAAu', 'pk', 'pbzlbf@sina.com'], ['50000200b34fhZiBq2tv9Y6IxfJPhwoCBDbw5NyzcgkvJZ1ee3d4aamuytTj1s', 'bd', 'pbzlbf@sina.com']], '6005301056649': [['50000900c26sxAApaOwaAcivEjPczRfbkFT8pu1fd52788yDiExnYiqV0S7NMs', 'pk', 'tuhua09@yeah.net'], ['50000700515Ue2brMmvgilt3qrh1b058778abHvGmshSPHYhgSCLVvihMW4FEu', 'bd', 'tuhua09@yeah.net']], '6005309248518': [['50000800d258YcoxoS99bo1HpvgTSjcBjReNR180e0983xDjjvH0fyVlxnqnLe', 'pk', 'bzryintianyi63@163.com'], ['50000900e19j0GwoxffcHxdoQerwldd16814bc4EpAsTTdmkRkahzyDDO0kbPN', 'bd', 'bzryintianyi63@163.com']], '6005286128815': [['50000501b08rQKpediDt18f0478e7PSWflhwjxFu1kd3AQOePqYSmv23qH7s7j', 'pk', 'oq101010@163.com'], ['50000200c09sxAAp1uyD8111dc84ddFVCpt9tSlbCFQ5qUuiofyKyiTt2efEfs', 'bd', 'oq101010@163.com']], '6005286816089': [['50000901339rQ1zhUGIpeVteAjCqfLRWHHhupwkSwAFbjSOawLV12935c6b3bq', 'pk', 'MAIL_SY555@163.com'], ['500005000381QOZx4PditwlS9L9vWRSiBZkXeiygVqiYeCxdZJ13488d16lrVh', 'bd', 'MAIL_SY555@163.com']], '6005281216134': [['50000400240xPOTpfgUveUCIlwwttBazmvFqvdVudWdiqAoyeqoh1e5ffcb1qk', 'pk', 'joymm1991@163.com'], ['50000100304amvob10585493esShQkJnoVtscC2mXhnShwvG8idq6pVzkUuQWz', 'bd', 'joymm1991@163.com']], '6005280432939': [['50000900906rB6r8MC1a27f1b9PwNSfZ3mxeLpbwRcfdCs4lVxdGkRI1MXWh90', 'pk', 'samsame114@163.com'], ['50000201c25biHdYkfpetxVcHFMl3dysleylx14e429dcOeJRXstNwZhuIMIWx', 'bd', 'samsame114@163.com']], '6005308960722': [['50000201325rQ1zhVHjqAUOHaehSiKvTiKmuj13ef54f3xFuUnfyjosj148vsq', 'pk', 'lastacy@126.com'], ['50000200131bm1wURBbTvET8pDpXPReC3FvfkRCrQkB1e459dd1Bjvdk2OxoXN', 'bd', 'lastacy@126.com']], '6005316544117': [['50000700e21j0Gwoybc7lzlhvCyslbgcP1041f4785sUYCFmRn0FxWCDBEWLrN', 'pk', 'xvlhrj@sina.com'], ['500006000341QOZx5w9DRydUipCN1usCCyJucmqgRrhAgB170da435v6BKMlYh', 'bd', 'xvlhrj@sina.com']], '6005293952174': [['50000401522ap8uelpBySfbeEs6rV1kKhR1e89e320iaiz0jd39Rojwte1f6Sz', 'pk', 'bbzflz@sina.com'], ['50000101a23jg2sqFbGDu7pwzellvl2iRTk16d817ebGz9otAvOvsOQvVQS28e', 'bd', 'bbzflz@sina.com']], '6005301056640': [['50000001f32eN4brdOSYlFiOpafT0jeyFqQhuo1SlpZV1a661ef04OiJiMdiAy', 'pk', 'tanfang19134296@yeah.net'], ['50000600911rB6r8h9n4mwh1b654426Dbm2dJSCTScaFCyALz2fFjOK3KfuBW0', 'bd', 'tanfang19134296@yeah.net']], '6005276864407': [['500007016140WMdjud0REZjiTd16d4a0a0Or0djHPIwGrWmHxBsOhJox6MYBU8', 'pk', 'aliceii1lo@163.com'], ['50000901126xdIaaaj0cMtazvCeijSBMyXDIfQ1477a81aJxlsSmeZCrEp4Dlt', 'bd', 'aliceii1lo@163.com']], '6005300192718': [['50000800525Ue2brQmzkpnp0Oy9aYnximubVo15167fd0lADCw7pxtfIDFowAu', 'pk', 'zlxd72@sina.com'], ['50000600e37j0GwoSEgaKxCJvgUTh9gcRdLwzcjeRHyErwACh14eae88cWZrUN', 'bd', 'zlxd72@sina.com']], '6005286736097': [['50000701200o171bd1a3g2Z0ntiIwBwPDAGjx6mU2HkfLlaFw0lCxkTp5k98ip', 'pk', 'tammy0010@163.com'], ['50000800d0081c18f540YcoxMtZf0g2iipDuqGdehR5qSVDhlujydSyAtOC6he', 'bd', 'tammy0010@163.com']], '6005281232184': [['50000401e06qTzccQd1f8bc5f2nTwDglPI4Fz0HcYjurfvR1uMuX19xDeuh3GK', 'pk', 'Ruby1890_ruby@163.com'], ['50000601c22biHdYbFuiNRYffDLgydtuDF1b56dd093nSQFwT3pqoZx47grVYx', 'bd', 'Ruby1890_ruby@163.com']], '6005280432921': [['50000100f17BeOnrdC2nTfoya0ojZ179deedcfhtgtvYFGkShYit0jfYU5NUqs', 'pk', 'babycong1112@163.com'], ['50000702000Y1fac502bS3q5L0UlkmRjwGwymEWiSpFuw3Tln0zisENcV4nplu', 'bd', 'babycong1112@163.com']], '6005281104203': [['50000301e28qTzccR5LS0dKmyh0fqTmG0GRRBNvx1c3e45f5PPQ2VfvjeUenZK', 'pk', 'engineer987987@163.com'], ['50000401337rQ1zhYkkPhvxeeigy7N02gllSiWkx0BlxCxQeO12b1df5dDdlcq', 'bd', 'engineer987987@163.com']], '6005309376334': [['50000402012YS3q5osVEgjwk1589e563alxXkFw9tPjPPxtmRVVfoiLDsSANSu', 'pk', 'LYNN681@yeah.net'], ['50000601e41qTzccyipx1DFktlykvSIfxCqrhJswSLMW46QBrOMmZ1dc465e7K', 'bd', 'LYNN681@yeah.net']], '6005281120159': [['50000901812vTAqbzPFBhfs814d55f7flRvcjFRI4Fq1jgXEQSCOOVxr2EDsNf', 'pk', 'DrunkQQ@163.com'], ['50000802036YS3q5qWTFKGLIamqyDg5EQSAxuwvqPxXfQEHf12c9f1824NpFju', 'bd', 'DrunkQQ@163.com']], '6005308928803': [['500003016250WMdjvcWphXjfrBpvtdHguHVGS192d344aUkf4lPqcPqYnvewJ8', 'pk', 'nvxjvl@sina.com'], ['50000900e03j0Gw17517955otEe0KteKwAVviYDat4ly2lFHvjxHvvHD7Lk9TN', 'bd', 'nvxjvl@sina.com']], '6005286400133': [['50000300710bRILftkmHSx1312a7d4MTiZzJtjIrbUxkAdEudoSyiIFPSiLikD', 'pk', 'Uchiha2421811@163.com'], ['50000301715hk5iraTvcbjFw3Ls1e8cd2abuCkHwlwGQwBg1nuqbyvYTTJDqws', 'bd', 'Uchiha2421811@163.com']], '6005300160815': [['500005016170WMdjQasxcaFip7k0V13632becCljxmvDUWlhxHOsbuqX4dAIC8', 'pk', 'xhhfdv@sina.com'], ['50000300101bm113131721wUpgeyPjx6I9paNxdfyGyhpq9swGdfiwColcDkWN', 'bd', 'xhhfdv@sina.com']], '6005309056525': [['50000500706bRILfsD11e21f98koNztQBDZIwjnyfTOk9eiT3ovYeGfvqw0UOD', 'pk', 'ci69147715@126.com'], ['50000201215og2Z0H1jprBrSHah14b882cfbu4puwCGGOpZeqyjiWHRPE54wfp', 'bd', 'ci69147715@126.com']], '6005300672848': [['50000800212xPOTpfdSThRDq1734b2e9FR2nvhc0lxhpwB0sCAiCQisxo68ftk', 'pk', 'shihe3041@yeah.net'], ['50000901b26rQKpeYfaT6NzwEiGLlzlRvHc5Fv1eb19b6dPcLuwurPa1MrS4Sj', 'bd', 'shihe3041@yeah.net']], '6005300944663': [['50000300909rB6r8qAqVR1c993328Ucd3KyfMwErOgdEeuhoWwiigLKzHned90', 'pk', 'tangdu46753@yeah.net'], ['50000100541Ue2brSmt7MIs4vwif1fxEKyBTTkaeEw4oyWeH9leVW134d6787u', 'bd', 'tangdu46753@yeah.net']], '6005294528286': [['50000600324amvobERvGwFhAuvtPAf1jwhoR1f00f33ahzoF7DiS7ryWpefSFz', 'pk', 'yebi993931061@126.com'], ['50000701e20qTzccx9OwTjFgKn1kwzAk1348e3123CoxbwsXroOxaAwGOtEcbK', 'bd', 'yebi993931061@126.com']], '6005300128876': [['50000601933eYIatqEZCdt4qyXDhdNnVltTAkaBurAvp114e3af17PttD2weAK', 'pk', 'pingzhi3741@126.com'], ['50000601903eYIa1f172c4ftOFdGerCLWvfgGLh1IxWoCzHPtCPo1qOOaMBgRK', 'bd', 'pingzhi3741@126.com']]}
    all_tasks = []

    # 线程池最大并发数（可以根据 CPU 适当调整）
    max_threads = 10

    with concurrent.futures.ThreadPoolExecutor(max_threads) as executor:
        for d in my_dict.values():
            for e in d:
                all_tasks.append(executor.submit(process_product, e))

        # 等待所有任务完成
        concurrent.futures.wait(all_tasks)

    print("所有任务执行完毕！")


