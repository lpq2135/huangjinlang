import requests
import base64
import gzip
import json
import 图鉴打码
import re
import math
import logging
from logging_config import setup_logger

from opencc import OpenCC
from urllib.parse import quote_plus
from flask import Flask, request
from 电商平台爬虫api.api_1688 import Alibaba
from ruten循环上下架 import RutenUpload
from 电商平台爬虫api.api_ruten import Ruten
from 电商平台爬虫api.api_taobao import TaoBao
from 象寄翻译 import XiangJi
from 电商平台爬虫api.api_pinduoduo import PinDuoDuo
from 电商平台爬虫api.basic_assistanc import BaseCrawler

# 在创建Flask应用前设置日志
setup_logger()

# 然后创建Flask应用
app = Flask(__name__)

@app.route('/deepl/translate', methods=['post'])
def translate_text_with_deepl():
    """deepl翻译接口"""
    auth_key = request.values.get('auth_key')
    text = request.values.get('text')
    source_lang = request.values.get('source_lang')
    target_lang = request.values.get('target_lang')
    deepl_url = "https://api.deepl.com/v2/translate"
    data = {
        'auth_key': auth_key,
        'text': text,
        'source_lang': source_lang,
        'target_lang': target_lang
    }
    for _ in range(5):
        try:
            response = requests.post(deepl_url, data=data)
            if 'text' in response["translations"][0]:
                result = response["translations"][0]["text"]
                return result
        except Exception as e:
            logging.warning(f"deepl翻译请求失败，尝试第{_ + 1}次. Error: {e}")
    raise Exception("deepl翻译请求失败")

@app.route('/auth_token_create_by_daraz', methods=['post'])
def auth_token_create_by_daraz():
    """获取daraz店铺的token"""
    code = request.values.get('code')
    upload_site = request.values.get('upload_site')
    product = daraz_api.DarazProduct(upload_site=upload_site)
    store_information = product.generate_access_token(code)
    return store_information


@app.route('/format_alibaba', methods=['post'])
def format_alibaba():
    """获取1688商品重量"""
    product_id = request.values.get('product_id')
    alibaba_instance = Alibaba(product_id)
    weight = alibaba_instance.get_unit_weight()
    return str(weight)

@app.route('/handling_verification_codes', methods=['post'])
def handling_verification_codes():
    """利用图鉴代码处理验证码"""
    img_path = request.values.get('img_path')
    uname = request.values.get('uname')
    pwd = request.values.get('pwd')
    typeid = request.values.get('typeid')
    result = 图鉴打码.base64_api(uname=uname, pwd=pwd, img=img_path, typeid=typeid)
    return result

@app.route('/get_sku_price_by_ruten', methods=['post'])
def get_sku_price_by_ruten():
    """获取露天商品包的sku价格"""
    product_id = request.values.get('product_id')
    ruten_instance = Ruten(product_id)
    product_data = ruten_instance.get_product_package(product_id)
    if product_data['item']['soldNum'] == 0:
        return '0'

    if not product_data['item']['isActive']:
        return '-2'
    sku_price = {}
    num = 0

    if not product_data['item']['specInfo']:
        if 280 <= int(product_data['item']['directPrice']) <= 330:
            sku_price[f'{num}_spec_id'] = ''
            sku_price[f'{num}_spec_price'] = product_data['item']['directPrice']
            return sku_price
        return '-1'

    specifications = product_data['item']['specInfo']['level']
    for key, value in product_data['item']['specInfo']['specs'].items():
        if specifications == 2:
            if value['parent_id'] == '0' or value['spec_status'] == 'N':
                continue
        if 280 <= value['spec_price'] <= 330:
            sku_price[f'{num}_spec_id'] = value['spec_id']
            sku_price[f'{num}_spec_price'] = value['spec_price']
            num += 1
    if len(sku_price) == 0:
        return '-1'
    return sku_price

@app.route('/get_min_price_by_ruten', methods=['post'])
def get_min_price_by_ruten():
    """
    产品对比竞品，计算出价格差距百分比
    0: 成功获取价格差值百分比
    -1: 商品销量为0
    -2: 商品已下架
    -3: 商品已是最低价格
    -4: 标题一致但是sku参数不一致
    -5: 找不到相关产品
    """

    # 获取需要过滤的sellerid
    with open(r'D:\露天精细化运营工具\其他辅助工具\露天全网比价程序\计算折扣百分比\附件库\seller_id.txt', 'r', encoding='utf-8') as f:
        seller_id_total = [line.strip() for line in f]

    # 创建翻译实例
    converter = OpenCC('s2tw')

    product_id = request.values.get('product_id')
    lower_limit_percentage = int(request.values.get('lower_limit_percentage'))
    fixed_value = int(request.values.get('fixed_value'))

    # 创建 ruten_instance 实例
    ruten_instance = Ruten(product_id)
    product_data = ruten_instance.get_product_package(product_id)

    if product_data['item']['soldNum'] == 0:
        return {'code': -1, 'data': '商品销量为0'}

    if not product_data['item']['isActive']:
        return {'code': -2, 'data': '商品已下架'}

    # 获取规格数
    if not product_data['item']['specInfo']:
        specifications = 0
    else:
        specifications = product_data['item']['specInfo']['level']

    # 获取标题并进行编码
    title = product_data['item']['name']
    title = (re.sub(r"【.*?】", "", title).strip().replace('台灣現貨', '')).replace('台灣出貨', '')

    # 处理title末尾的数字和字母
    pattern = r'[a-zA-Z0-9]+$'
    title1 = re.sub(pattern, '', title[:30]).strip()

    # 将标题进行url编码
    keywords = quote_plus(title1)

    # 获取最大价格和最小价格
    min_price = product_data['item']['priceRange']['min']

    # 查找跟卖的链接ruten_instance
    ids_data = ruten_instance.get_ids_by_reception(keywords)

    # 先过滤掉不符合条件的字典
    filtered_data = [item for item in ids_data if title in item['ProdName']]

    if len(filtered_data) == 0:
        return {'code': -5, 'data': '找不到相关产品'}

    # 按 PriceRange[0] 降序排列
    sorted_data = sorted(filtered_data, key=lambda x: int(x['PriceRange'][0]))

    # 开始遍历处理数据
    for i in sorted_data:
        seller_id = i['SellerId']

        # 判断是否为团队内的店铺
        if seller_id in seller_id_total:
            return {'code': -3, 'data': '商品已是最低价格'}

        # sku不为0的情况处理
        if specifications != 0:
            # 对比两个商品是否完全一致
            contrast_data = ruten_instance.get_product_package(i['ProdId'])
            if not contrast_data['item']['specInfo']:
                continue
            if converter.convert(next(iter(product_data['item']['specMap']['spec']))) != converter.convert(next(iter(contrast_data['item']['specMap']['spec']))):
                continue

        # 计算价格最小值的差值百分比
        contrast_price = i['PriceRange'][0]
        result = 100 - math.floor(int(contrast_price) / int(min_price) * 100)

        if result == 0:
            return {'code': -3, 'data': '商品已是最低价格'}

        if result >= 85:
            continue

        # 如果折扣幅度超过 lower_limit_percentage，则定折扣幅度为 fixed_value
        if result > lower_limit_percentage:
            result = fixed_value
        else:
            result += 1
        return {'code': 0, 'data': result}
    return {'code': -5, 'data': '找不到相关产品'}

@app.route('/upload_to_ruten', methods=['post'])
def upload_to_ruten():
    """多平台露天上架集成接口"""
    platform = request.values.get('platform')
    store = request.values.get('store')
    sub_account = request.values.get('sub_account')
    # 根据平台获取不同的参数
    if platform == '1688' or platform == 'ruten':
        product_id = request.values.get('product_id')

    elif platform == 'taobao':
        source_base64 = request.values.get('source_base64')
        source_base64 = source_base64.replace(' ', '+')
        # Base64解码
        decoded_data = base64.b64decode(source_base64)
        # Gzip解压缩
        decompressed_data = gzip.decompress(decoded_data)
        # 解码为UTF-8字符串
        source = decompressed_data.decode('utf-8')

        # 获取详情图片
        detail_img = request.values.get('detail_img')
        detail_img_list = detail_img.split(',')
        detail_img_list_new = ['https:' + img if 'https:' not in img else img for img in detail_img_list]

    elif platform == 'pinduoduo':
        source_base64 = request.values.get('source_base64')
        source_base64 = source_base64.replace(' ', '+')
        # Base64解码
        decoded_data = base64.b64decode(source_base64)
        # Gzip解压缩
        decompressed_data = gzip.decompress(decoded_data)
        # 解码为UTF-8字符串
        source = decompressed_data.decode('utf-8')

    category_id = request.values.get('category_id')
    background_classification = request.values.get('background_classification')
    price_multi = request.values.get('price_multi')
    price_add = request.values.get('price_add')
    is_trans_img = int(request.values.get('is_trans_img'))
    is_add_main_logo = int(request.values.get('is_add_main_logo'))
    img_save_path = request.values.get('img_save_path')
    is_save_img = int(request.values.get('is_save_img'))

    # 判断 is_trans_img 对应的参数
    if is_trans_img == 0:
        max_count = 0
    else:
        xiangji = XiangJi(sub_account)
        if is_trans_img == 1:
            max_count = 1
        elif is_trans_img == 2:
            max_count = 10

    # 创建 RutenUpload 的实例
    ruten_uplaod_instance = RutenUpload(store, is_add_main_logo=is_add_main_logo, img_save_path=img_save_path, is_save_img=is_save_img)

    # 创建各个平台的实例并组装差别参数
    if platform == '1688':
        # 创建 Alibaba 的实例
        alibaba_instance = Alibaba(product_id)
        product_data = alibaba_instance.build_product_package()

    elif platform == 'ruten':
        # 创建 ruten 实例，获取商品数据包
        ruten_instance = Ruten(product_id)
        product_data = ruten_instance.build_product_package()

        if category_id == '':
            category_id = ruten_instance.product_data['item']['class']

    elif platform == 'taobao':
        # 创建 taobao 的实例
        taobao_instance = TaoBao(json.loads(source))
        product_data = taobao_instance.build_product_package()

    elif platform == 'pinduoduo':
        pinduoduo_instance = PinDuoDuo(json.loads(source))
        product_data = pinduoduo_instance.build_product_package()

    if product_data['code'] != 0:
        return {'code': -5, 'store': store, 'data': product_data['message']}

    product_id = product_data['data']['product_id']
    logging.info(f'{product_id}-商品数据包成功解析')

    # 获取违禁品词列表
    forbidden_items = ruten_uplaod_instance.load_forbidden_items()
    for i in forbidden_items:
        if i in product_data['data']['title'].lower():
            logging.warning(f'{product_id}-{category_id}-标题包含违禁词-{i}')
            return {'code': -5, 'store': store, 'product_id': product_id, 'data': f'标题包含违禁词-{i}'}

    # 判断类目是否可用
    category_id_status = ruten_uplaod_instance.check_category_id(category_id)
    if not category_id_status:
        logging.error(f'{product_id}-{category_id}-类目id验证不可用')
        return {'code': -2, 'store': store, 'product_id': product_id, 'data': f'{category_id}-类目id不合法(请更换)'}

    logging.info(f'{product_id}-{category_id}-类目id验证可用')
    # 进行价格转换
    product_data = ruten_uplaod_instance.price_conversion(product_data, price_multi, price_add)

    # 语言简体换成繁体
    product_data = ruten_uplaod_instance.zh_to_tw(product_data)

    # 组装最终的html格式
    if platform == '1688' or platform == 'pinduoduo':
        detail_html = ruten_uplaod_instance.construction_details_html(product_data['data']['details_text_description'], product_data['data']['detailed_picture'])
    elif platform == 'ruten':
        detail_html = product_data['data']['details_text_description']

    elif platform == 'taobao':
        detail_html = ruten_uplaod_instance.construction_details_html(product_data['data']['details_text_description'], detail_img_list_new)

    # 获取sku组装的数据
    sku_data = ruten_uplaod_instance.structure_sku_data(product_data)

    # 获取标题
    title = product_data['data']['title']

    # 主图+轮播图
    main_images = product_data['data']['main_images']

    # 保存首张原图
    ruten_uplaod_instance.save_top_image(img_save_path, product_id, main_images[0])

    # 使用象寄翻译主图+轮播图
    if max_count != 0:
        logging.info(f'{product_id}-开始进行象寄图片翻译')
        main_images_data = xiangji.translate_images(main_images, max_count)
        if main_images_data['status_code'] == 0:
            main_images_tw = main_images_data['data']
        elif main_images_data['status_code'] == 1:
            return {'code': -4, 'store': store, 'product_id': product_id, 'data': '象寄翻译密匙不足'}
    else:
        main_images_tw = main_images

    # 获取自定义后台分类id
    if background_classification == '':
        user_class_select = 0
    else:
        user_class_select = ruten_uplaod_instance.get_class(background_classification)

    # 组装最终的上货表
    upload_product_package = {
        'specifications': sku_data['specifications'],
        'spec_info': sku_data['spec_info'],
        'item_detail_dict': sku_data['item_detail_dict'],
        'g_direct_price': sku_data['g_direct_price'],
        'show_num': sku_data['show_num'],
        'title': title,
        'main_images': main_images_tw,
        'user_class_select': user_class_select,
        'category_id': category_id,
        'detail_html': detail_html
    }

    upload_products = ruten_uplaod_instance.upload_products(product_id, upload_product_package)
    if upload_products['code'] == 0 or upload_products['code'] == 4:
        logging.info(f'{store}-{product_id}-上架露天成功')
        return {'code': 0, 'store': store, 'product_id': product_id, 'after_listing_id': upload_products['after_listing_id'], 'data': '上架成功'}
    return {'code': -1, 'store': store, 'product_id': product_id, 'data': '上架失败'}


app.run(host='0.0.0.0', port=8803, debug=False)