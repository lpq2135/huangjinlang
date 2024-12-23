import os
import sys
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
import datetime

from 数据库连接 import MySqlPool
from 文字翻译 import Translator
from 电商平台数据组装api import Alibaba
from 象寄翻译 import XiangJi


# 获取店铺的 access_token 和其他相关信息
def get_access_token():
    cnx, cursor = mysql_pool.get_conn()
    try:
        cursor.execute(
            "SELECT access_token, country, user_id, email FROM daraz_store_internal_parameters WHERE status = 0 AND account = %s",
            (account,))
        rows = cursor.fetchall()
        if rows:
            access_token_dict = access_token_deal_with(rows)
            return access_token_dict
        return None
    except Exception as e:
        logging.warning("获取店铺access_token异常: %s", str(e))
    finally:
        mysql_pool.close_mysql(cnx, cursor)


# 获取待处理的商品数据
def get_product_data():
    cnx, cursor = mysql_pool.get_conn()
    try:
        cursor.execute(
            "SELECT * FROM product_id_deduplication WHERE status = '0' AND account = %s ORDER BY RAND() LIMIT 50",
            (account,))
        rows = cursor.fetchall()
        return None if not rows else rows
    except Exception as e:
        logging.warning("获取商品数据异常: %s", str(e))
        return None
    finally:
        mysql_pool.close_mysql(cnx, cursor)


# 更新商品状态，标记为已处理
def update_product_status(product_id):
    cnx, cursor = mysql_pool.get_conn()
    try:
        cursor.execute(
            "UPDATE product_id_deduplication SET status = '1' WHERE account = %s AND product_id = %s",
            (account, product_id,)
        )
        cnx.commit()
    except Exception as e:
        print(1)
        a = 1
        logging.warning('更新商品状态异常, product_id: %s, error: %s', product_id, str(e))
        cnx.rollback()
    finally:
        mysql_pool.close_mysql(cnx, cursor)

# 记录商品上传状态
def record_product_status(upload_info):
    # 从数据库连接池中获取连接和游标对象
    cnx, cursor = mysql_pool.get_conn()

    try:
        # 提取字典中的字段，使用get方法来避免键不存在时抛出异常
        platform = upload_info.get('platform')
        email = upload_info.get('email')
        product_id = upload_info.get('product_id')
        upload_site = upload_info.get('upload_site')
        upload_code = upload_info.get('upload_code')
        data = upload_info.get('data')
        item_id = upload_info.get('item_id', None)  # 如果 item_id 不存在，使用 None

        # 获取当前时间，格式化为字符串（YYYY-MM-DD HH:MM:SS）
        current_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        # 检查指定上传站点和商品ID是否已经存在
        cursor.execute(
            "SELECT * FROM record_product_status_by_daraz WHERE product_id = %s AND upload_site = %s",
            (product_id, upload_site)
        )
        existing_product = cursor.fetchone()  # 查询是否存在该商品记录

        if not existing_product:
            # 如果记录不存在，则插入新记录
            cursor.execute(
                """
                INSERT INTO record_product_status_by_daraz (platform, email, product_id, upload_site, upload_code, data, item_id, account, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (platform, email, product_id, upload_site, upload_code, data, item_id, account, current_time)
            )

        # 提交事务
        cnx.commit()

    except Exception as e:
        # 如果发生异常，记录错误日志并回滚事务
        logging.warning('更新商品状态异常, product_id: %s, error: %s', product_id, str(e))
        cnx.rollback()  # 回滚事务，避免无效或部分更新的数据

    finally:
        # 关闭数据库连接和游标
        mysql_pool.close_mysql(cnx, cursor)

def get_available_id_count():
    """
    获取指定accunt的象寄密匙数量
    """
    cnx, cursor = mysql_pool.get_conn()
    try:
        cursor.execute("SELECT COUNT(*) FROM product_id_deduplication WHERE account = %s AND status = '0'", (account,))
        row_count = cursor.fetchone()[0]
        if row_count is None:
            logging.warning('数据库无象寄翻译密匙')
            return
        else:
            return row_count
    except Exception as e:
        logging.warning("象寄数据库获取数据异常: ", str(e))
    finally:
        mysql_pool.close_mysql(cnx, cursor)

def get_deepl_api():
    """
    获取指定accunt的deepl密匙
    """
    cnx, cursor = mysql_pool.get_conn()
    try:
        cursor.execute("SELECT deepl_api FROM deepl_api WHERE account = %s AND status = '0'", (account,))
        row = cursor.fetchone()[0]
        if row is None:
            logging.warning('数据库无象寄翻译密匙')
            return
        else:
            return row
    except Exception as e:
        logging.warning("象寄数据库获取数据异常: ", str(e))
    finally:
        mysql_pool.close_mysql(cnx, cursor)

# 处理数据库中获取的多行数据，返回以 user_id 为键的字典
def access_token_deal_with(rows):
    my_dict = {}
    for row in rows:
        if row[2] not in my_dict:
            my_dict[row[2]] = [[row[0], row[1], row[3]]]
        else:
            my_dict[row[2]].append([row[0], row[1], row[3]])
    return my_dict


# 处理每个商品的具体任务
def process_product(value, product_data, event):
    # 检查是否设置了停止事件
    if event.is_set():
        logging.info("程序终止，请检查相关异常")
        return

    product_id = product_data[2]
    logging.info(f'{product_id}-获取成功')

    # 使用 Alibaba 类来处理商品数据
    product_object = Alibaba(product_id)
    product_package = product_object.build_product_package()

    # 如果数据包构建失败，更新商品状态并返回
    if not product_package['status']:
        logging.warning(f'{product_id}-{product_package["data"]}')
        update_product_status(product_id)
        return

    logging.info(f'{product_id}-开始文字翻译数据包')

    # 使用 Translator 类进行文字翻译
    text_translator = Translator(product_package['data'], deepl_api)
    data_packet_translate = text_translator.process_all()

    if data_packet_translate:
        # 处理主图数据
        main_images = [x['fullPathImageURI'] for x in data_packet_translate['main_images']]

        # 限制主图数量不超过8张
        if len(main_images) > 8:
            main_images = main_images[:8]

        # 判断是否需要进行主图翻译
        if is_img_translate == '0':
            logging.info(f'{product_id}-主图不进行象寄api翻译')
        else:
            logging.info(f'{product_id}-主图开始进行象寄api翻译')
            main_images = img_translate.xiangji_image_translate(main_images, 1)

            # 如果象寄翻译返回为空，停止后续线程任务
            if not main_images:
                logging.warning(f'{product_id}-象寄翻译返回为空, 停止继续启动新的线程')
                event.set()  # 设置停止事件，通知其他线程停止
                return

        # 获取商品重量，并准备上货数据包
        weight = float(product_data[7])
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

        # 循环遍历要上传的站点数据
        for i in value:
            upload_site = i[1].lower()
            skumodel_new = copy.deepcopy(data_packet_translate['skumodel'])

            # 处理价格
            if daraz_api.processing_price(upload_site, skumodel_new, weight):
                attrs['skumodel'] = skumodel_new  # 更新数据包中的价格信息

                # 创建上货请求并上传商品
                daraz_product = daraz_api.DarazProduct(app_key, app_secret, i[0], i[1], attrs)
                upload_results = daraz_product.create_product()

                # 收集上传结果
                new_dict = {'platform': product_data[0], 'email': i[2]}
                new_dict.update(upload_results)
                record_product_status(new_dict)
                upload_results_list.append(new_dict)

                # 更新商品状态
                update_product_status(product_id)
            else:
                # 如果价格不符合要求，更新商品状态并记录错误
                product_id = data_packet_translate['product_id']
                update_product_status(product_id)
                new_dict = {'platform': product_data[0],  'email': i[2], 'upload_site': i[1], 'upload_code': -3, 'product_id': product_id, 'data': '数据包价格不符合要求'}
                upload_results_list.append(new_dict)
                record_product_status(new_dict)

        logging.info(upload_results_list)  # 输出上传结果
    else:
        logging.info(f'{product_id}-文字翻译异常')  # 如果文字翻译异常，记录日志


# 配置数据库连接和其他配置信息
mysql_pool = MySqlPool(host='47.122.62.157', password='Qiang123@', user='daraz', database='daraz')
app_key = '502742'
app_secret = '0XGyiUMf0obAP9FueDD16fid4M5xgmaV'

# 设置日志配置
logging_config.setup_logger()

# 主程序
if __name__ == '__main__':
    account = input('请输入你的account:')
    is_img_translate = input('请输入主图翻译选项(0:不开启主图翻译; 1:开启主图翻译):')
    # 获取对应account的deepl_api
    deepl_api = get_deepl_api()
    if not deepl_api:
        logging.error('数据库可用对应accoun的deepl_api')
        time.sleep(5)
        sys.exit()
    # 获取对应account的数据库id数量
    available_id_count = get_available_id_count()
    if not available_id_count:
        logging.error('数据库可用商品ID数量不足')
        time.sleep(5)
        sys.exit()
    logging.info(f'当前可用商品ID数量: {available_id_count}')

    # 获取 access_token 数据
    access_token_data = get_access_token()
    if not access_token_data:
        logging.error('没有找到有效的access token')
        time.sleep(5)
        sys.exit()

    product_data_list = []
    max_workers = min(10, len(access_token_data))  # 最大线程数
    logging.info(f'当前工作线程数量：{max_workers}')

    # 创建一个锁对象
    lock = threading.Lock()
    futures = set()  # 用于存储线程的 future 对象
    cyclic_values = itertools.cycle(access_token_data.values())  # 循环的账号数据

    # 创建 XiangJi 实例
    img_translate = XiangJi(account, mysql_pool)
    xiangji_count = img_translate.get_xiangji_key_count()

    if xiangji_count > 0:
        logging.info(f'当前象寄密匙数量: {xiangji_count}')
    else:
        logging.info(f'当前象寄密匙数量: {xiangji_count}, 终止启动')
        time.sleep(5)
        sys.exit()

    # 创建一个 threading.Event 实例，用于线程间同步
    stop_event = threading.Event()

    # 启动线程池处理任务
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        # 提交初始的线程任务
        for _ in range(max_workers):
            with lock:
                if not product_data_list:
                    product_new_data = get_product_data()
                    if product_new_data:
                        product_data_list.extend(product_new_data)
                    else:
                        logging.error('数据库无商品id')
                        time.sleep(5)
                        sys.exit()
                product_data = product_data_list.pop(0)

            value = next(cyclic_values)
            future = executor.submit(process_product, value, product_data, stop_event)
            futures.add(future)

        # 等待线程执行完毕
        while futures or max_workers == 1:
            done, futures = concurrent.futures.wait(futures, return_when=concurrent.futures.FIRST_COMPLETED)

            with lock:
                if stop_event.is_set():  # 如果事件已设置，停止所有工作
                    break
                if product_data_list:
                    value = next(cyclic_values)
                    product_data = product_data_list.pop(0)
                    future = executor.submit(process_product, value, product_data, stop_event)
                    futures.add(future)
                else:
                    product_new_data = get_product_data()
                    if product_new_data:
                        product_data_list.extend(product_new_data)
                    else:
                        logging.error('数据库无商品数据')
                        time.sleep(5)
                        sys.exit()
