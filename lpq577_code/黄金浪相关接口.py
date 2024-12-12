import requests
import mysql.connector
import base64
import gzip
import daraz_api
import json

from flask import Flask, request
from logging_config import logging
from 电商平台数据组装api import Alibaba


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
            response = requests.post(deepl_url, data=data).json()
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
    product = daraz_api.DarazProduct('502742', '0XGyiUMf0obAP9FueDD16fid4M5xgmaV', upload_site=upload_site)
    store_information = product.generate_access_token(code)
    return store_information

@app.route('/format_alibaba_for_daraz', methods=['post'])
def format_alibaba_v2():
    product_id = request.values.get('product_id')
    source = json.loads(gzip.decompress(base64.b64decode(request.values.get('source').strip().replace(' ', '+'))).decode(
        'utf-8'))
    alibaba_instance = Alibaba(product_id, source)
    if alibaba_instance.source:
        product_package_data = alibaba_instance.build_product_package()
        if product_package_data['status']:
            json_data = json.dumps(product_package_data['data'], ensure_ascii=False)
            return json_data
    return product_package_data


app.run(host='0.0.0.0', port=8803, debug=False)