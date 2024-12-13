import concurrent.futures
import copy
import itertools
import json
import logging
import sys
import threading
import time
import daraz_api
import logging_config

from 数据库连接 import MySqlPool
from 文字翻译 import Translator
from 电商平台数据组装api import Alibaba
from 象寄翻译 import XiangJi


def get_access_token():
    cnx, cursor = mysql_pool.get_conn()
    try:
        cursor.execute(
            "SELECT access_token, country, user_id, email FROM daraz_store_internal_parameters WHERE status = 0")
        rows = cursor.fetchall()
        access_token_dict = access_token_deal_with(rows)
        return access_token_dict
    finally:
        mysql_pool.close_mysql(cnx, cursor)


def get_product_data():
    cnx, cursor = mysql_pool.get_conn()
    try:
        cnx.start_transaction()
        select_query = "SELECT * FROM product_id_deduplication WHERE status = 0 AND account = %s ORDER BY RAND() LIMIT 10"
        cursor.execute(select_query, (account,))
        records = cursor.fetchall()
        if records:
            product_ids = [record[2] for record in records]
            formatted_ids = ','.join(['%s'] * len(product_ids))
            update_query = "UPDATE product_id_deduplication SET status = 1 WHERE product_id IN (%s) AND account = %%s" % formatted_ids
            cursor.execute(update_query, tuple(product_ids + [account]))
            cnx.commit()
        else:
            logging.warning("数据库获取上货数据异常")
    except Exception as e:
        cnx.rollback()
        print("Transaction failed: ", str(e))
    finally:
        mysql_pool.close_mysql(cnx, cursor)
    return records


def access_token_deal_with(rows):
    my_dict = {}
    for row in rows:
        if row[2] not in my_dict:
            my_dict[row[2]] = [[row[0], row[1], row[3]]]
        else:
            my_dict[row[2]].append([row[0], row[1], row[3]])
    return my_dict


def process_product(value, product_data):
    product_id = product_data[2]
    logging.info(f'[{product_id}-获取成功]')
    product_object = Alibaba(product_id)
    product_package = product_object.build_product_package()
    if not product_package['status']:
        logging.warning(f'[{product_id}-{product_package["data"]}]')
        return
    logging.info(f'[{product_id}-开始翻译数据包]')
    text_translator = Translator(product_package['data'])
    data_packet_translate = text_translator.process_all()
    if data_packet_translate:
        # 主图处理
        main_images = [x['fullPathImageURI'] for x in data_packet_translate['main_images']]
        if len(main_images) > 8:
            main_images = main_images[:8]
        # 进行是否翻译主图的判断
        if is_img_translate == '0':
            logging.info(f'[{product_id}-主图不进行象寄api翻译]')
        else:
            logging.info(f'[{product_id}-主图开始进行象寄api翻译]')
            img_translate = XiangJi(account, mysql_pool)
            main_images = img_translate.xiangji_image_translate(main_images, 1)
        weight = float(product_data[7])
        # 组装上货数据包
        attrs = {
            'primary_category': product_data[3],
            'length': product_data[4],
            'width': product_data[5],
            'height': product_data[6],
            'weight': weight,
            'product_id': product_id,
            'specifications': data_packet_translate['specifications'],
            'start_amount': data_packet_translate['start_amount'],
            'title': data_packet_translate['title'],
            'main_images': main_images,
            'skumodel': data_packet_translate['skumodel'],
            'video': data_packet_translate['video'],
            'details_text_description': data_packet_translate['details_text_description'],
            'detailed_picture': data_packet_translate['detailed_picture'][2:],
            'promotion_whitebkg_image': None
        }
        upload_results_list = []
        for i in value:
            upload_site = i[1].lower()
            skumodel_new = copy.deepcopy(data_packet_translate['skumodel'])
            if daraz_api.processing_price(upload_site, skumodel_new, weight):
                # 替换数据包翻译后的数据包
                attrs['skumodel'] = skumodel_new
                # 上货请求处理
                daraz_product = daraz_api.DarazProduct(app_key, app_secret, i[0], i[1], attrs)
                upload_results = daraz_product.create_product()
                new_dict = {'email': i[2]}
                new_dict.update(upload_results)
                upload_results_list.append(new_dict)
            else:
                product_id = data_packet_translate['product_id']
                upload_results_list.append({'email': i[2], 'upload_code': -3, 'product_id': product_id,
                                            'data': '数据包价格不符合要求'})
        logging.info(upload_results_list)
    else:
        logging.info('文字翻译异常')


# 相关配置信息
mysql_pool = MySqlPool(host='47.122.62.157', password='Qiang123@', user='daraz', database='daraz')
app_key = '502742'
app_secret = '0XGyiUMf0obAP9FueDD16fid4M5xgmaV'
# 创建日志实例
logging_config.setup_logger()

if __name__ == '__main__':
    account = input('请输入你的account:')
    is_img_translate = input('请输入主图翻译选项(0:不开启主图翻译; 1:开启主图翻译):')
    access_token_data = get_access_token()
    product_data_list = []
    max_workers = min(5, len(access_token_data))
    logging.info(f'当前工作线程数量：{max_workers}')
    # 创建一个锁对象
    lock = threading.Lock()
    futures = set()
    cyclic_values = itertools.cycle(access_token_data.values())
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        for _ in range(max_workers):
            with lock:
                if not product_data_list:
                    product_new_data = get_product_data()
                    if product_new_data:
                        product_data_list.extend(product_new_data)
                    else:
                        logging.error('数据库无商品id')
                        time.sleep(5)
                        sys.exit(1)
                product_data = product_data_list.pop(0)
            value = next(cyclic_values)
            future = executor.submit(process_product, value, product_data)
            futures.add(future)
        while futures or max_workers == 1:
            done, futures = concurrent.futures.wait(futures, return_when=concurrent.futures.FIRST_COMPLETED)
            with lock:
                if product_data_list:
                    value = next(cyclic_values)
                    product_data = product_data_list.pop(0)
                    future = executor.submit(process_product, value, product_data)
                    futures.add(future)
                else:
                    product_new_data = get_product_data()
                    if product_new_data:
                        product_data_list.extend(product_new_data)
                    else:
                        logging.error('数据库无商品数据')
                        time.sleep(5)
                        sys.exit(1)
                        #路人话