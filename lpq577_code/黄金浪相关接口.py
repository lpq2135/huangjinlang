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
from 电商平台数据组装api import Alibaba
from openai import OpenAI


app = Flask(__name__)

def user_authentication(account, password):
    """
    验证账号密码是否正确
    """
    mysql_config = dict(host='47.122.62.157', password='Qiang123..', user='ruten_str', database='ruten_str')
    cnx = mysql.connector.connect(**mysql_config)
    cursor = cnx.cursor()
    try:
        cursor.execute("SELECT * FROM user_information WHERE account = %s", (account,))
        row = cursor.fetchone()
        if row is None:
            return False
        elif row[1] != password:
            return False
        else:
            return True
    finally:
        cursor.close()
        cnx.close()

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


app.run(host='0.0.0.0', port=8803, debug=False)