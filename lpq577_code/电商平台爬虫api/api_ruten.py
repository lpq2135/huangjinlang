import logging
import re
import json
from lxml import html
from bs4 import BeautifulSoup
from .basic_assistanc import BaseCrawler


class Ruten(BaseCrawler):
    def __init__(self, product_id, proxies=None):
        self.proxies = proxies
        self.product_id = product_id
        self.product_data = self.get_product_package(self.product_id)
        self.headers = {'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36'}

    def get_product_package(self, product_id):
        """获取商品数据包"""
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
        response = self.request_function(url, headers=headers, proxies=self.proxies)
        match = re.search(r'(?<=RT\.context\ =\ ).*(?=;)', response.text)
        if match:
            try:
                return json.loads(match.group(0))
            except Exception as e:
                logging.warning(f'获取商品数据包失败-{self.product_id}, 错误信息: {e}')
        return None

    def get_description(self):
        """获取商品详情"""
        description_url = self.product_data['item']['descriptionUrl']
        # 请求详情专用请求头，需要带 referer
        headers = {
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36',
            'referer': f'https://www.ruten.com.tw/item/show?{self.product_id}'
        }
        # 请求详情链接获取 html 数据
        html_data = self.request_function(description_url, headers=headers, proxies=self.proxies).text
        # 格式化 html 数据
        if html_data:
            try:
                soup = BeautifulSoup(html_data, 'lxml')
                body_content = soup.find('body')
                body_html = body_content.decode_contents()
                return body_html
            except Exception as e:
                logging.warning(f'{self.product_id}-获取详情信息失败, 错误信息: {e}')
        return None

    def get_title(self):
        """获取商品标题"""
        title = self.product_data['item']['name']
        return title

    def get_ids_by_reception(self, keywords):
        """通过前台搜索词v3和v1接口获取商品id和商品信息"""
        v3_url = f'https://rtapi.ruten.com.tw/api/search/v3/index.php/core/prod?q={keywords}&type=direct&sort=rnk%2Fdc&limit=60&offset=1'
        v3_result = self.request_function(v3_url, headers=self.headers).json()
        v3_ids = ','.join(i['Id'] for i in v3_result['Rows'])
        # 获取折扣活动价格
        discountprice_data = self.get_ids_by_discountprice(v3_ids)
        discountprice_result = {i['ProdId']: i['Discount'][0]['Price'] for i in discountprice_data if len(i['Discount']) != 0}
        v3_data = self.get_titles_by_v2(v3_ids)
        # 将价格替换成活动价格
        for i in v3_data:
            if i['ProdId'] in discountprice_result:
                i['PriceRange'] = discountprice_result[i['ProdId']]
        return v3_data

    def get_ids_by_discountprice(self, v3_ids):
        """通过前台搜索词v3和v1接口获取商品id和商品信息"""
        discountprice_url = f'https://rtapi.ruten.com.tw/api/prod/v3/index.php/prod/discountprice?id={v3_ids}'
        discountprice_result = self.request_function(discountprice_url, headers=self.headers).json()
        return discountprice_result

    def get_titles_by_v2(self, ids):
        """通过ids获取商品信息"""
        v2_url = f'https://rtapi.ruten.com.tw/api/prod/v2/index.php/prod?id={ids}'
        v2_result = self.request_function(v2_url, headers=self.headers).json()
        return v2_result

    def get_main_images(self):
        """获取商品主图"""
        main_images_data = self.product_data['item']['images']
        if main_images_data is None:
            return None
        main_images = [i['original'] for i in main_images_data]
        return main_images

    def build_product_package(self):
        """组装数据包"""
        # 商品数据包异常
        if not self.product_data:
            return {'platform': 'ruten', 'code': 4, 'message': '商品数据包异常', 'product_id': self.product_id}

        # 商品主图异常
        main_images = self.get_main_images()
        if main_images is None:
            return {'platform': 'ruten', 'code': 3, 'message': '商品主图异常', 'product_id': self.product_id}

        # 商品详情异常
        description = self.get_description()
        if not description:
            return {'platform': 'ruten', 'code': 6, 'message': '商品详情异常', 'product_id': self.product_id}

        # 若没有 self.product_data['item']['specInfo']是 False，则为单规格
        if not self.product_data['item']['specInfo']:
            specifications = 0
            sku_assembly = {'sku_data': {'price': self.product_data['item']['directPrice'], 'stock': self.product_data['item']['remainNum']}}
        else:
            # 规格数
            specifications = self.product_data['item']['specInfo']['level']
            # specs数据
            specs = self.product_data['item']['specInfo']['specs']
            # structure 数据
            structure = self.product_data['item']['specInfo']['structure']
            # 规格为 1
            if specifications == 1:
                sku1_property_name = '規格'
                sku_assembly = {
                    'sku_data': {
                        'sku_property_name': {'sku1_property_name': sku1_property_name},
                        'sku_parameter': []
                    }
                }
                for v in specs.values():
                    skus = {
                        'remote_id': self.product_id + '_' + self.generate_random_string(10),
                        'name': v['spec_name'],
                        'imageUrl': None,
                        'price': v['spec_price'],
                        'stock': v['spec_num']
                    }
                    sku_assembly['sku_data']['sku_parameter'].append(skus)
            # 规格为 2
            if specifications == 2:
                sku1_property_name = '規格'
                sku2_property_name = '項目'
                sku_assembly = {
                    'sku_data': {
                        'sku_property_name': {
                            'sku1_property_name': sku1_property_name,
                            'sku2_property_name': sku2_property_name
                        },
                        'sku_parameter': []
                    }
                }
                for k, v in structure.items():
                    for x in v.keys():
                        if specs[x]['spec_status'] == 'N':
                            continue
                        sku1_valus = specs[k]['spec_name']
                        sku2_valus = specs[x]['spec_name']
                        name = sku1_valus + '||' + sku2_valus
                        skus = {
                            'remote_id': self.product_id + '_' + self.generate_random_string(10),
                            'name': name,
                            'imageUrl': None,
                            'price': specs[x]['spec_price'],
                            'stock': specs[x]['spec_num']
                        }
                        sku_assembly['sku_data']['sku_parameter'].append(skus)

        product_package = {
            'product_id': self.product_id,
            'specifications': specifications,
            'unit_weight': None,
            'start_amount': None,
            'title': self.get_title(),
            'main_images': main_images,
            'skumodel': sku_assembly,
            'video': None,
            'details_text_description': description,
            'detailed_picture': None,
        }
        return {'platform': 'ruten', 'code': 0, 'message': '请求成功', 'data': product_package}


if __name__ == '__main__':
    res = Ruten('22315417806403')
    product_data = res.build_product_package()
    print(product_data)