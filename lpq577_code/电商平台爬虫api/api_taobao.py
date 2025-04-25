import json
import ast
import random
from .basic_assistanc import BaseCrawler

class TaoBao(BaseCrawler):
    """此类用于处理淘宝和天猫的商品数据包"""
    def __init__(self, data):
        self.data = data
        self.product_id = self.get_product_id()
        self.headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36'}

    def get_title(self):
        """获取商品标题"""
        title = self.data['data']['item']['title']
        return title

    def get_product_id(self):
        """获取商品id"""
        product_id = self.data['data']['item']['itemId']
        return product_id

    def get_main_images(self):
        """获取商品主图"""
        main_images = [self.enforce_https(url) for url in self.data['data']['componentsVO']['headImageVO']['images'][:8]]
        return main_images

    def get_videos(self):
        """获取商品视频"""
        if 'videos' in self.data['data']['item']:
            video = self.data['data']['item']['videos'][0]['url']
            return video
        return None

    def get_sku_price(self, specifications, skus=None, vid=None, pid=None):
        """获取sku对应的价格"""
        # 获取价格数据包
        sku_price_data = self.get_price_map()

        # 规格为 0
        if specifications == 0:
            return sku_price_data[0].get('price2', sku_price_data[0]['price1'])

        # 规格为 1 或 2
        for sku in skus:
            # 检查规格匹配条件
            if specifications == 1 and vid not in sku['propPath']:
                continue
            if specifications == 2 and (vid not in sku['propPath'] or pid not in sku['propPath']):
                continue
            # 获取 sku_id
            sku_id = int(sku['skuId'])
            # 判断sku库存
            stock_data = self.get_stock_data(sku_id)
            if not stock_data:
                return None

            # 获取 sku 价格
            if sku_id not in sku_price_data:
                return None
            price_data = sku_price_data[sku_id]

            # 优先返回price2，不存在则返回price1
            return price_data.get('price2', price_data.get('price1'))

    def get_stock_data(self, sku_id):
        """获取sku库存"""
        stock_data = self.data['data']['skuCore']['sku2info'][str(sku_id)]['quantityText']
        return False if '无货' in stock_data else True

    def get_price_map(self):
        """获取sku价格数据包"""
        umpPriceLogVO = self.data['data']['componentsVO']['umpPriceLogVO']['map']
        return ast.literal_eval(umpPriceLogVO)

    def get_product_attribute(self):
        """获取详情文字"""
        Filter_words = ['专利', '跨境', '货号', '下游', '订制', '地区', '授权', '进口', 'LOGO', '上市', '是否', '加工',
                        '货源',
                        '产地', '形象', '代理', '售后']
        res = self.data['data']['componentsVO']['extensionInfoVO']
        # 若详情文字的标题包含过滤词则过滤
        for i in res['infos']:
            if i['title'] == '参数':
                attribute_list = [(f"{x['title']} : {x['text'][0]}") for x in i['items'] if
                                  all(word not in x['title'] for word in Filter_words)]
                return attribute_list

    def build_product_package(self):
        """组装数据包"""
        # props 数据包包含了sku的详细信息
        props = self.data['data']['skuBase'].get('props', [])
        # 规格数
        specifications = len(props)

        if specifications == 0:
            stock = random.randint(900, 1000)
            sku_assembly = {'sku_data': {'price': self.get_sku_price(specifications), 'stock': stock}}
        else:
            skus_data = self.data['data']['skuBase']['skus']
            if specifications == 1:
                sku1_property_name = props[0]['name']
                sku_assembly = {
                    'sku_data': {
                        'sku_property_name': {'sku1_property_name': sku1_property_name},
                        'sku_parameter': []
                    }
                }
                for i in props[0]['values']:
                    price = self.get_sku_price(specifications, skus_data, i['vid'])
                    if price is None:
                        continue
                    skus = {
                        'remote_id': self.product_id + '_' + self.generate_random_string(10),
                        'name': i['name'],
                        'imageUrl': i.get('image', None),
                        'price': price,
                        'stock': random.randint(900, 1000)
                    }
                    sku_assembly['sku_data']['sku_parameter'].append(skus)
            elif specifications == 2:
                sku1_property_name = props[0]['name']
                sku2_property_name = props[1]['name']
                sku_assembly = {
                    'sku_data': {
                        'sku_property_name': {
                            'sku1_property_name': sku1_property_name,
                            'sku2_property_name': sku2_property_name
                        },
                        'sku_parameter': []
                    }
                }
                for i in props[0]['values']:
                    for j in props[1]['values']:
                        price = self.get_sku_price(specifications, skus_data, i['vid'], j['vid'])
                        if price is None:
                            continue
                        skus = {
                            'remote_id': self.product_id + '_' + self.generate_random_string(10),
                            'name': i['name'] + '||' + j['name'],
                            'imageUrl': i.get('image', j.get('image', None)),
                            'price': price,
                            'stock': random.randint(900, 1000)
                        }
                        sku_assembly['sku_data']['sku_parameter'].append(skus)

            else:
                return {'platform': 'taobao', 'code': 5, 'message': 'sku规格数超出', 'product_id': self.product_id}

        product_package = {
            'product_id': self.product_id,
            'specifications': specifications,
            'unit_weight': None,
            'start_amount': None,
            'title': self.get_title(),
            'main_images': self.get_main_images(),
            'skumodel': sku_assembly,
            'video': self.get_videos(),
            'details_text_description': self.get_product_attribute(),
            'detailed_picture': None,
        }
        return {'platform': 'taobao', 'code': 0, 'message': '请求成功', 'data': product_package}


if __name__ == '__main__':
    taobao = TaoBao()
    res = taobao.build_product_package()
    print(res)