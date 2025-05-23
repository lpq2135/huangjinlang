import copy
import logging
import sys
import time
from lpq577_code.daraz相关 import daraz_api
import datetime

from collections import defaultdict
from itertools import cycle
from threading import Event
from concurrent.futures import ThreadPoolExecutor, TimeoutError


# 获取店铺的 access_token 和其他相关信息
def get_access_token():
    """获取店铺的 access_token 和其他相关信息"""
    cnx, cursor = mysql_pool.get_conn()
    try:
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


# 获取待处理的商品数据
def get_product_data():
    """获取待处理的商品数据"""
    cnx, cursor = mysql_pool.get_conn()
    try:
        table_name = f"product_id_deduplication_by_{account}"
        query = (
            f"SELECT * FROM {table_name} WHERE status = '0' ORDER BY RAND() LIMIT 500"
        )
        cursor.execute(query)
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


# 记录商品上传状态
def record_product_status(upload_info):
    """记录商品上传状态"""
    # 从数据库连接池中获取连接和游标对象
    cnx, cursor = mysql_pool.get_conn()

    try:
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
        item_id = upload_info.get("item_id", None)  # 如果 item_id 不存在，使用 None

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
        # 关闭数据库连接和游标
        mysql_pool.close_mysql(cnx, cursor)


# 记录1688异常产品
def record_1688_error(product_id, mark):
    cnx, cursor = mysql_pool.get_conn()
    try:
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
    获取指定accunt的象寄密匙数量
    """
    cnx, cursor = mysql_pool.get_conn()
    try:
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


def get_deepl_api():
    """
    获取指定accunt的deepl密匙
    """
    cnx, cursor = mysql_pool.get_conn()
    try:
        cursor.execute(
            "SELECT deepl_api FROM deepl_api WHERE account = %s AND status = '0'",
            (account,),
        )
        row = cursor.fetchone()[0]
        if row is None:
            logging.warning("数据库无象寄翻译密匙")
            return
        else:
            return row
    except Exception as e:
        logging.warning("象寄数据库获取数据异常: ", str(e))
    finally:
        mysql_pool.close_mysql(cnx, cursor)


# 处理数据库中获取的多行数据，返回以 user_id 为键的字典
def access_token_deal_with(rows):
    my_dict = defaultdict(list)
    for row in rows:
        if row[1] == "bd":
            continue
        my_dict[row[2]].append([row[0], row[1], row[3]])
    return dict(my_dict)


# 处理每个商品的具体任务
def process_product(value, product_data, stop_event):
    if stop_event.is_set():
        logging.info("检测到停止事件，终止任务执行")
        return

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

    # 如果数据包构建失败，更新商品状态并返回
    if not product_package["status"]:
        logging.warning(f'{product_id}-{product_package["data"]}')
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
    daraz_price = daraz_api.DarazPrice()
    if len(value) == 1 and value[0][1] == "pk":
        skumodel_temporary = copy.deepcopy(product_package["data"]["skumodel"])
        pk_processing_price = daraz_price.processing_price(
            "pk", skumodel_temporary, weight
        )
        # 判断数据包价格是否符合要求
        if pk_processing_price is False:
            logging.warning(f"{product_id}-{value[0][1]}-数据包价格不符合要求")
            update_product_status(product_id)
            return

    logging.info(f"{product_id}-开始文字翻译数据包")

    # 使用 Translator 类进行文字翻译
    text_translator = Translator(product_package["data"], deepl_api)
    data_packet_translate = text_translator.process_all()

    if data_packet_translate:
        # 主图
        main_images = data_packet_translate["main_images"]

        # 判断是否需要进行主图翻译
        if is_img_translate == "0":
            logging.info(f"{product_id}-主图不进行象寄api翻译")
        else:
            logging.info(f"{product_id}-主图开始进行象寄api翻译")
            image_frist = img_translate.get_image_link(product_id)
            if image_frist:
                main_images[0] = image_frist
            else:
                images_data = img_translate.xiangji_image_translate(
                    main_images, 1, product_id
                )

            # 如果象寄翻译返回为空，停止后续线程任务
            if images_data["status_code"] == 1:
                logging.warning(f"{product_id}-象寄翻译返回为空, 停止继续启动新的线程")
                stop_event.set()  # 设置停止事件，通知其他线程停止
                return
            elif images_data["status_code"] == 2:
                logging.warning(f"{product_id}-主图出现304异常，跳过")
                update_product_status(product_id)
                return
            else:
                main_images = images_data["images"]

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

# 设置日志配置
logging_config.setup_logger()

# 主程序
if __name__ == "__main__":
    account = input("请输入你的account: ")
    is_img_translate = input("请输入主图翻译选项(0:不开启主图翻译; 1:开启主图翻译): ")
    # 获取对应account的deepl_api
    deepl_api = get_deepl_api()
    if not deepl_api:
        logging.error("数据库可用对应accoun的deepl_api")
        time.sleep(5)
        sys.exit()
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

    max_workers = min(20, len(access_token_data))  # 最大线程数
    logging.info(f"当前工作线程数量：{max_workers}")

    if is_img_translate == 1:
        # 创建 XiangJi 实例
        img_translate = XiangJi(account, mysql_pool)
        xiangji_count = img_translate.get_xiangji_key_count()
        if xiangji_count > 0:
            logging.info(f"当前象寄密匙数量: {xiangji_count}")
        else:
            logging.info(f"当前象寄密匙数量: {xiangji_count}, 终止启动")
            time.sleep(5)
            sys.exit()

    access_token_cycle = cycle(
        access_token_data.values()
    )  # 创建access_token的无限迭代器
    stop_event = Event()  # 假设的停止事件
    main_pool = ThreadPoolExecutor(max_workers=max_workers)  # 主线程池

    while True:
        tasks = []  # 存储任务的列表
        product_data_list = get_product_data()
        if not product_data_list:
            break  # 如果没有数据了，就结束循环

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
                task.result(timeout=150)  # 每个任务最多等待 150 秒
            except TimeoutError:
                logging.error(f"任务超时，跳过该任务: {task}")
            except Exception as e:
                logging.error(f"任务发生异常: {e}")

        # 如果检测到停止事件被设置，终止整个循环
        if stop_event.is_set():
            logging.info("检测到停止事件，终止任务执行")
            break
