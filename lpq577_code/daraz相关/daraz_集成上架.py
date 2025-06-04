import copy
import logging
import sys
import time
from lpq577_code.数据库连接 import MySqlPool
from lpq577_code.daraz相关 import daraz_api
from lpq577_code.电商平台爬虫api.api_1688 import Alibaba
from lpq577_code.文本翻译.文字翻译 import Translator
from collections import defaultdict
from itertools import cycle
from threading import Event
from concurrent.futures import ThreadPoolExecutor, TimeoutError

def get_access_token():
    """
    获取店铺的access_token和相关店铺信息。

    从数据库查询指定账号的access_token、国家、用户ID和邮箱等信息，
    并通过access_token_deal_with函数处理后返回。

    Returns:
        dict or None: 返回处理后的access_token字典，结构为：
            {
                'access_token': str,
                'country': str,
                'user_id': str,
                'email': str
            }
            如果查询无结果或出错则返回None
    """
    try:
        cnx, cursor = mysql_pool.get_conn()
        cursor.execute(
            "SELECT access_token, country, user_id, email FROM daraz_store_internal_parameters WHERE status = 0 AND application_category = 'erp' AND account = %s",
            (account,),
        )
        rows = cursor.fetchall()
        if rows:
            access_token_dict = access_token_deal_with(rows)
            return access_token_dict
        return None
    except Exception as e:
        logging.warning("获取店铺access_token异常: %s", str(e))
    finally:
        mysql_pool.close_mysql(cnx, cursor)

def get_product_data(sort_order='ASC'):
    """
    获取待处理的商品数据（按product_id排序）

    从指定账号的product_id去重表中查询状态为'0'的商品数据，
    并按product_id升序或降序返回限定数量的记录。

    Args:
        sort_order (str): 排序方式，可选值：
            - 'ASC'  : 按product_id升序排列（默认）
            - 'DESC' : 按product_id降序排列

    Returns:
        Optional[list]: 返回查询结果列表，每行是一个商品记录字典；
                       如果查询无结果或出错则返回None
    """
    try:
        cnx, cursor = mysql_pool.get_conn()
        table_name = f"product_id_deduplication_by_{account}"
        query = (
            f"SELECT * FROM {table_name} WHERE status = '0' ORDER BY product_id {sort_order} LIMIT 500"
        )
        cursor.execute(query)
        rows = cursor.fetchall()
        return rows if rows else None
    except Exception as e:
        logging.warning(f"获取商品数据异常(account={account}): {str(e)}")
        return None
    finally:
        mysql_pool.close_mysql(cnx, cursor)

def update_product_status(product_id):
    """
    更新指定商品在去重表中的状态

    Args:
        product_id (str): 要更新的商品ID
    """
    try:
        cnx, cursor = mysql_pool.get_conn()
        table_name = f"product_id_deduplication_by_{account}"  # 构建完整的表名
        query = f"UPDATE {table_name} SET status = '1' WHERE product_id = %s"
        cursor.execute(query, (product_id,))
        cnx.commit()
    except Exception as e:
        logging.warning(
            "更新商品状态异常, product_id: %s, error: %s", product_id, str(e)
        )
        cnx.rollback()
    finally:
        mysql_pool.close_mysql(cnx, cursor)

def record_product_status(upload_info):
    """
    记录商品上传状态

    Args:
        upload_info(dict):
            - platform (str): 平台名称， 默认1688
            - email (str): 店铺邮箱
            - product_id (str): 商品id
            - upload_site (str): 上传站点
            - product_id (str): 商品id
            - upload_code (str): 上传状态码
            - data (str): 上架状态说明
    """
    try:
        cnx, cursor = mysql_pool.get_conn()

        # 提取字典中的字段，使用get方法来避免键不存在时抛出异常
        platform = upload_info.get("platform")
        email = upload_info.get("email")
        product_id = upload_info.get("product_id")
        upload_site = upload_info.get("upload_site")
        upload_code = upload_info.get("upload_code")
        data = (
            upload_info.get("data")
            if "message" not in upload_info.get("data")[0]
            else "上架包数据异常"
        )

        # 如果 item_id 不存在，使用 None
        item_id = upload_info.get("item_id", None)

        # 获取当前时间，格式化为字符串（YYYY-MM-DD HH:MM:SS）
        current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # 检查指定上传站点和商品ID是否已经存在
        cursor.execute(
            "SELECT * FROM record_product_status_by_daraz WHERE product_id = %s AND upload_site = %s",
            (product_id, upload_site),
        )
        existing_product = cursor.fetchone()  # 查询是否存在该商品记录

        if not existing_product:
            # 如果记录不存在，则插入新记录
            cursor.execute(
                """
                INSERT INTO record_product_status_by_daraz (platform, email, product_id, upload_site, upload_code, data, item_id, account, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    platform,
                    email,
                    product_id,
                    upload_site,
                    upload_code,
                    data,
                    item_id,
                    account,
                    current_time,
                ),
            )

        # 提交事务
        cnx.commit()

    except Exception as e:
        # 如果发生异常，记录错误日志并回滚事务
        logging.warning(
            "记录商品上传信息异常, product_id: %s, error: %s", product_id, str(e)
        )
        cnx.rollback()  # 回滚事务，避免无效或部分更新的数据

    finally:
        mysql_pool.close_mysql(cnx, cursor)

def record_1688_error(product_id, mark):
    """
    记录1688的异常产品，方便排查代码

    Args:
        product_id: 商品id
        mark: 商品标记
    """
    try:
        cnx, cursor = mysql_pool.get_conn()
        cursor.execute(
            "INSERT INTO 1688_error (product_id, mark) VALUES (%s, %s)",
            (product_id, mark),
        )
        cnx.commit()
    except Exception as e:
        logging.warning(
            "记录1688异常ID错误, product_id: %s, error: %s", product_id, str(e)
        )
        cnx.rollback()
    finally:
        mysql_pool.close_mysql(cnx, cursor)

def get_available_id_count():
    """
    获取指定accunt的商品id数量

    Returns:
        独赢account数据库的商品数量
    """
    try:
        cnx, cursor = mysql_pool.get_conn()
        table_name = f"product_id_deduplication_by_{account}"
        query = f"SELECT COUNT(*) FROM {table_name} WHERE status = '0'"
        cursor.execute(query)
        row_count = cursor.fetchone()[0]
        if row_count is None:
            logging.warning("数据库无象寄翻译密匙")
            return
        else:
            return row_count
    except Exception as e:
        logging.warning("象寄数据库获取数据异常: ", str(e))
    finally:
        mysql_pool.close_mysql(cnx, cursor)

def access_token_deal_with(rows):
    """
    处理数据库中获取的多行数据，返回以user_id为键的字典

    Args:
        rows (list): 数据库查询的原始结果集，每行包含：
            - row[0]: access_token
            - row[1]: country (国家代码)
            - row[2]: user_id
            - row[3]: email

    Returns:
        dict: 结构为 {user_id: [[access_token, country, email], ...]} 的字典
    """
    my_dict = defaultdict(list)
    for row in rows:
        if row[1] == "bd":
            continue
        my_dict[row[2]].append([row[0], row[1], row[3]])
    return dict(my_dict)

# 处理每个商品的具体任务
def process_product(value, product_data, stop_event):
    # 检测停止信号，终止任务执行
    if stop_event.is_set():
        logging.info("检测到停止事件，终止任务执行")
        return

    # 获取product_id
    product_id = product_data[2]
    # 使用 Alibaba 类来处理商品数据
    logging.info(f"{product_id}-获取成功-开始请求数据包")
    try:
        product_object = Alibaba(product_id)
        product_package = product_object.build_product_package()
    except Exception as e:
        logging.warning(f"1688商品ID异常: {product_id}-{e}")
        record_1688_error(product_id, "0")
        return

    # 记录异常的1688商品id
    if product_package["code"] != 0:
        logging.warning(f'{product_id}-{product_package["data"]}')
        update_product_status(product_id)
        return

    # 判断sku是否有规格图
    if not product_package["data"]["other_parameters"]["sku_has_image"]:
        logging.warning(f'{product_id}-"sku主图缺失"')
        update_product_status(product_id)
        return

    # 获取商品重量，并准备上货数据包
    unit_weight = product_package["data"]["unit_weight"]
    mysql_weight = float(product_data[7])
    if unit_weight is None:
        weight = mysql_weight
    else:
        weight = min(float(unit_weight), mysql_weight)

    # 创建daraz价格类的实例
    # daraz_price = daraz_api.DarazPrice()
    # if len(value) == 1 and value[0][1] == "pk":
    #     skumodel_temporary = copy.deepcopy(product_package["data"]["skumodel"])
    #     pk_processing_price = daraz_price.processing_price(
    #         "pk", skumodel_temporary, weight
    #     )
    #     # 判断数据包价格是否符合要求
    #     if pk_processing_price is False:
    #         logging.warning(f"{product_id}-{value[0][1]}-数据包价格不符合要求")
    #         update_product_status(product_id)
    #         return
    #
    # logging.info(f"{product_id}-开始文字翻译数据包")

    # 使用 Translator 类进行文字翻译
    text_translator = Translator(product_package["data"])
    data_packet_translate = text_translator.process_all()

    if data_packet_translate:
        # 主图
        main_images = data_packet_translate["main_images"]

        attrs = {
            "primary_category": product_data[3],
            "length": product_data[4],
            "width": product_data[5],
            "height": product_data[6],
            "weight": weight,
            "product_id": product_id,
            "specifications": data_packet_translate["specifications"],
            "start_amount": data_packet_translate["start_amount"],
            "title": data_packet_translate["title"],
            "main_images": main_images,
            "skumodel": data_packet_translate["skumodel"],
            "video": data_packet_translate["video"],
            "details_text_description": data_packet_translate[
                "details_text_description"
            ],
            "detailed_picture": data_packet_translate["detailed_picture"][2:],
            "promotion_whitebkg_image": None,
        }

        upload_results_list = []

        # 循环遍历要上传的站点数据
        for i in value:
            logging.info(f"{product_id}-{i[1]}-开始进行上货处理")
            upload_site = i[1].lower()
            skumodel_new = copy.deepcopy(data_packet_translate["skumodel"])

            # 处理价格
            if daraz_price.processing_price(upload_site, skumodel_new, weight):
                attrs["skumodel"] = skumodel_new  # 更新数据包中的价格信息

                # 创建上货请求并上传商品
                try:
                    daraz_product = daraz_api.DarazProduct(i[0], i[1], attrs)
                    upload_results = daraz_product.create_product()
                except Exception as e:
                    logging.warning(f"{product_id}-{i[1]}上传异常-{e}")
                    record_1688_error(product_id, "1")
                    return
                # 收集上传结果
                new_dict = {"platform": product_data[0], "email": i[2]}
                new_dict.update(upload_results)
                record_product_status(new_dict)
                upload_results_list.append(new_dict)
            else:
                logging.warning(f"{product_id}-{i[1]}-数据包价格不符合要求")
                new_dict = {
                    "platform": product_data[0],
                    "email": i[2],
                    "upload_site": i[1],
                    "upload_code": -8,
                    "product_id": product_id,
                    "data": "数据包价格不符合要求",
                }
                upload_results_list.append(new_dict)
                record_product_status(new_dict)
        # 更新商品状态
        update_product_status(product_id)
        logging.info(upload_results_list)  # 输出上传结果
    else:
        logging.info(f"{product_id}-文字翻译异常")  # 如果文字翻译异常，记录日志


# 配置数据库连接和其他配置信息
mysql_pool = MySqlPool(
    host="47.122.62.157", password="Qiang123@", user="daraz", database="daraz"
)
app_key = "502742"
app_secret = "0XGyiUMf0obAP9FueDD16fid4M5xgmaV"


# 主程序
if __name__ == "__main__":
    account = input("请输入你的account: ")

    # 获取对应account的数据库id数量
    available_id_count = get_available_id_count()
    if not available_id_count:
        logging.error("数据库可用商品ID数量不足")
        time.sleep(5)
        sys.exit()
    logging.info(f"当前可用商品ID数量: {available_id_count}")

    # 获取 access_token 数据
    access_token_data = get_access_token()
    if not access_token_data:
        logging.error("没有找到有效的access token")
        time.sleep(5)
        sys.exit()

    # 最大线程数
    # max_workers = min(20, len(access_token_data))  # 最大线程数
    max_workers = 1
    logging.info(f"当前工作线程数量：{max_workers}")

    # 创建access_token的无限迭代器
    access_token_cycle = cycle(access_token_data.values())  # 创建access_token的无限迭代器

    # 假设的停止事件
    stop_event = Event()

    # 创建主线程池
    main_pool = ThreadPoolExecutor(max_workers=max_workers)  # 主线程池

    while True:
        tasks = []  # 存储任务的列表
        product_data_list = get_product_data()

        # 如果没有数据了，就结束循环
        if not product_data_list:
            break

        # 每次循环时逐个提交任务
        for product_data in product_data_list:
            access_token = next(access_token_cycle)  # 获取下一个 access_token
            task = main_pool.submit(
                process_product, access_token, product_data, stop_event
            )
            tasks.append(task)  # 将任务添加到列表

        # 逐个等待任务，并设置超时
        for task in tasks:
            try:
                task.result()
            except TimeoutError:
                logging.error(f"任务超时，跳过该任务: {task}")
            except Exception as e:
                logging.error(f"任务发生异常: {e}")

        # 如果检测到停止事件被设置，终止整个循环
        if stop_event.is_set():
            logging.info("检测到停止事件，终止任务执行")
            break
