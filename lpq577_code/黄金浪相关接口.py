import requests
import mysql.connector
import base64
import gzip
import daraz_api
import json
import 图鉴打码
import concurrent.futures
import time
import 露天店铺快速上架

from flask import Flask, request
from logging_config import logging
from openai import OpenAI
from 电商平台爬虫api.api_1688 import Alibaba
from 电商平台爬虫api.basic_assistanc import BaseCrawler
from ruten循环上下架 import RutenUpload
from 电商平台爬虫api.api_ruten import Ruten
from 电商平台爬虫api.api_taobao import TaoBao
from 象寄翻译 import XiangJi

app = Flask(__name__)

@app.route('/deepl/translate', methods=['post'])
def translate_text_with_deepl():
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

@app.route('/auth/token/create', methods=['post'])
def auth_token_create():
    code = request.values.get('code')
    upload_site = request.values.get('upload_site')
    product = daraz_api.DarazProduct(upload_site=upload_site)
    store_information = product.generate_access_token(code)
    return store_information

@app.route('/format_alibaba', methods=['post'])
def format_alibaba():
    product_id = request.values.get('product_id')
    alibaba_instance = Alibaba(product_id)
    weight = alibaba_instance.get_unit_weight()
    return str(weight)

@app.route('/handling_verification_codes', methods=['post'])
def handling_verification_codes():
    img_path = request.values.get('img_path')
    uname = request.values.get('uname')
    pwd = request.values.get('pwd')
    typeid = request.values.get('typeid')
    result = 图鉴打码.base64_api(uname=uname, pwd=pwd, img=img_path, typeid=typeid)
    return result

@app.route('/get_product_by_jumia', methods=['post'])
def get_product_by_jumia():
    url = request.values.get('url').strip()
    proxy = request.values.get('proxy').strip()
    proxies = {
        'http': f'http://{proxy}',
        'https': f'https://{proxy}',
    }
    headers = {'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36'}
    result = requests.get(url, headers, proxies=proxies)
    return {'code': result.status_code, 'data': result.text}

@app.route('/deepseek_chat', methods=['post'])
def deepseek_chat():
    api_key = request.values.get('api_key').strip()
    model = request.values.get('model').strip()
    content = request.values.get('content').strip()
    client = OpenAI(api_key=api_key, base_url="https://api.deepseek.com")
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": "You are a helpful assistant"},
                {"role": "user", "content": content},
        ],
        stream=False
    )
    return (response.choices[0].message.content)

@app.route('/check_img', methods=['post'])
def check_img():
    ids = request.values.get('ids').strip()
    id_list = ids.split(',')  # 将字符串拆分为列表
    with concurrent.futures.ThreadPoolExecutor(max_workers=30) as executor:
        # 提交任务到线程池
        future_to_id = {executor.submit(露天店铺快速上架.main, gn_o): gn_o for gn_o in id_list}

        gn_o_list = []
        # 获取任务结果
        count = 0
        for future in concurrent.futures.as_completed(future_to_id):
            gn_o = future_to_id[future]
            res = {
                'count': count,
                'gn_o': gn_o,
                'status': future.result()
            }
            gn_o_list.append(res)
            count += 1
        return gn_o_list

@app.route('/upload_to_ruten', methods=['post'])
def upload_to_ruten():
    """1688数据上架露天"""
    platform = request.values.get('platform')
    store = request.values.get('store')
    account = request.values.get('account')
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
        pass

    category_id = request.values.get('category_id')
    background_classification = request.values.get('background_classification')
    price_multi = request.values.get('price_multi')
    price_add = request.values.get('price_add')
    is_trans_img = int(request.values.get('is_trans_img'))
    is_add_main_logo = int(request.values.get('is_add_main_logo'))
    img_save_path = request.values.get('img_save_path')
    # 判断 is_trans_img 对应的参数
    if is_trans_img == 0:
        max_count = 0
    else:
        xiangji = XiangJi(account)
        if is_trans_img == 1:
            max_count = 1
        elif is_trans_img == 2:
            max_count = 10

    # 创建 RutenUpload 的实例
    ruten_uplaod_instance = RutenUpload(store, is_add_main_logo=is_add_main_logo)

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
        product_id = product_data['data']['product_id']

    # 进行价格转换
    product_data = ruten_uplaod_instance.price_conversion(product_data, price_multi, price_add)

    # 语言简体换成繁体
    product_data = ruten_uplaod_instance.zh_to_tw(product_data)

    # 组装最终的html格式
    if platform == '1688':
        detail_html = ruten_uplaod_instance.construction_details_html(product_data['data']['details_text_description'], product_data['data']['detailed_picture'])
    elif platform == 'ruten':
        detail_html = product_data['data']['details_text_description']

    elif platform == 'taobao':
        detail_html = ruten_uplaod_instance.construction_details_html(product_data['data']['details_text_description'], detail_img_list_new)

    # 获取sku组装的数据
    sku_data = ruten_uplaod_instance.structure_sku_data(product_data)

    # 获取标题
    title = product_data['data']['title']

    # 使用象寄翻译主图+轮播图
    main_images = product_data['data']['main_images']
    if max_count != 0:
        main_images_data = xiangji.xiangji_image_translate_threaded(main_images, max_count)
        if main_images_data['code'] == 0:
            main_images_tw = main_images_data['data']
        elif main_images_data['code'] == 1:
            return {'code': 7, 'store': store, 'product_id': product_id, 'data': '象寄翻译密匙不足'}
    else:
        main_images_tw = main_images

    # 获取自定义后台分类id
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
    if upload_products['code'] == 0:
        logging.info(f'{store}-{product_id}-上架露天成功')
        return {'code': 0, 'store': store, 'product_id': product_id, 'after_listing_id': upload_products['after_listing_id'], 'data': '上架成功'}
    return {'code': -1, 'store': store, 'product_id': product_id, 'data': '上架失败'}


app.run(host='0.0.0.0', port=8803, debug=False)