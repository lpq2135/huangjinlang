import requests
import time
import threading
import signal
import random
import mysql.connector
import logging

from hashlib import md5
from urllib.parse import quote
from concurrent.futures import ThreadPoolExecutor, as_completed
from 电商平台爬虫api.basic_assistanc import BaseCrawler

class XiangJi(BaseCrawler):
    def __init__(self, account=None):
        self.account = account
        self.lock = threading.Lock()
        self.is_available = False  # 获取密匙状态
        self.api_list = None

    def get_connection(self):
        """创建新的数据库连接"""
        try:
            connection = mysql.connector.connect(
                host='47.122.62.157',
                user='xiangji',
                password='Qiang123..',
                database='xiangji',
                port=3306,
            )
            cursor = connection.cursor()
            return connection, cursor
        except Exception as e:
            logging.error(f"创建数据库连接失败: {str(e)}")
            raise

    def close_connection(self, connection, cursor):
        """关闭数据库连接"""
        try:
            if cursor:
                cursor.close()
            if connection:
                connection.close()
        except Exception as e:
            logging.error(f"关闭数据库连接时出错: {str(e)}")

    def get_xiangji_key(self):
        """
        连接象寄数据库获取翻译密匙
        """
        try:
            connection, cursor = self.get_connection()
            cursor.execute("SELECT user_key, img_trans_key FROM xiangji_key WHERE account = %s AND status = '0' LIMIT 10", (self.account,))
            rows = cursor.fetchall()
            if not rows:
                logging.warning('数据库无象寄翻译密匙')
                self.is_available = False
                self.api_list = []
                return None
            logging.info('象寄密匙列表获取成功')
            self.is_available = True
            return rows
        except Exception as e:
            logging.error(f"象寄数据库获取数据异常: {str(e)}")
            self.is_available = False
            self.api_list = []
            return None
        finally:
            self.close_connection(connection, cursor)

    def get_xiangji_key_count(self):
        """
        获取指定accunt的象寄密匙数量
        """
        try:
            connection, cursor = self.get_connection()
            cursor.execute("SELECT COUNT(*) FROM xiangji_key WHERE account = %s AND status = '0'", (self.account,))
            row_count = cursor.fetchone()[0]
            if row_count is None:
                logging.warning('数据库无象寄翻译密匙')
                return 0
            else:
                return row_count
        except Exception as e:
            logging.warning("象寄数据库获取数据异常: ", str(e))
        finally:
            self.close_connection(connection, cursor)

    def change_and_get_xiangji_key(self, user_key):
        """
        更新象寄密匙数据库状态
        """
        try:
            connection, cursor = self.get_connection()
            cursor.execute("UPDATE xiangji_key SET status = '1' WHERE user_key = %s", (user_key,))
            cnx.commit()
        except Exception as e:
            logging.warning(f'象寄数据库更改{user_key}异常: {e}')
        finally:
            self.close_connection(connection, cursor)

    def image_translation_record(self, product_id, image_link):
        """
        如果 product_id 存在则更新，否则插入新的记录
        """
        try:
            connection, cursor = self.get_connection()
            cursor.execute("INSERT INTO image_translation_record (product_id, image_link) VALUES (%s, %s) ON DUPLICATE KEY UPDATE image_link = VALUES(image_link)", (product_id, image_link))
            cnx.commit()
        except Exception as e:
            # 异常处理
            cnx.rollback()
        finally:
            self.close_connection(connection, cursor)

    def get_image_link(self, product_id):
        """
        查询 product_id 是否存在：
        - 如果存在，返回 image_link
        - 如果不存在，返回 None
        """
        try:
            connection, cursor = self.get_connection()
            # 查询 image_link 的 SQL 语句
            cursor.execute("SELECT image_link FROM image_translation_record WHERE product_id = %s", (product_id,))
            result = cursor.fetchone()
            # 如果记录存在，返回 image_link；否则返回 None
            return result[0] if result else None
        except Exception:
            return None
        finally:
            self.close_connection(connection, cursor)

    def get_api_key_from_api_list(self):
        """加锁获取api_key和img_trans_key"""
        with self.lock:
            while True:
                if self.api_list:
                    api_data = random.choice(self.api_list)
                    api_key = api_data[0]
                    img_trans_key = api_data[1]
                    return api_key, img_trans_key
                else:
                    self.api_list = self.get_xiangji_key()
                    if not self.is_available:
                        return None, None

    def translate_single_image(self, image):
        """翻译单张图片"""
        api_key, img_trans_key = self.get_api_key_from_api_list()
        if api_key is None:
           return {'status_code': 1, 'api_key': api_key, 'img_trans_key': img_trans_key, 'data': '象寄密匙已用完'}
        url = 'https://api.tosoiot.com'
        while True:
            retry_attempts = 0
            while retry_attempts < 5:
                current_time = str(int(time.time()))
                try:
                    sign_string = md5(
                        (current_time + "_" + api_key + "_" + img_trans_key).encode('utf-8')).hexdigest()
                    parameters = {
                        'Action': 'GetImageTranslate',
                        'SourceLanguage': 'CHS',
                        'TargetLanguage': 'CHT',
                        'Url': quote(image.split('?')[0], safe=':/'),
                        'ImgTransKey': img_trans_key,
                        'Sign': sign_string,
                        'NeedWatermark': 0,
                        'Qos': 'BestQuality',
                        'CommitTime': current_time
                    }
                    response = self.request_function(url, 'get', params=parameters).json()
                    if response['Code'] == 200:
                        # 如果翻译成功，更新图像URL
                        translated_image_url = response['Data']['Url']
                        return {'status_code': 0, 'data': translated_image_url}
                    elif response['Code'] == 118:
                        logging.warning(f'象寄密匙额度用完, api_key: {api_key}')
                        if api_data in self.api_list:
                            self.api_list.remove(api_data)
                            self.change_and_get_xiangji_key(api_key)

                        api_key, img_trans_key = self.get_api_key_from_api_list()
                        if api_key is None:
                            return {'status_code': 1, 'api_key': api_key, 'img_trans_key': img_trans_key,
                                    'data': '象寄密匙已用完'}
                        # 获取新的密匙之后重置 retry_attempts
                        retry_attempts = 0
                        time.sleep(2)
                    else:
                        logging.warning(
                            f'象寄翻译请求失败, 重试第{retry_attempts + 1}, api_key: {api_key}')
                        retry_attempts += 1
                        time.sleep(3)

                except Exception as e:
                    logging.warning(
                        f'象寄翻译请求失败, 重试第{retry_attempts + 1}次, api_key: {api_key}, 错误: {str(e)}')
                    retry_attempts += 1
                    time.sleep(3)

            logging.info(f"象寄翻译重新5次失败，正在尝试更新密钥, api_key: {api_key}")
            api_key, img_trans_key = self.get_api_key_from_api_list()
            if api_key is None:
                return {'status_code': 1, 'api_key': api_key, 'img_trans_key': img_trans_key, 'data': '象寄密匙已用完'}

    def xiangji_image_translate_threaded(self, images, max_count):
        with ThreadPoolExecutor(max_workers=4) as executor:
            # 初始化空字典
            future_to_index = {}
            for idx, img_url in enumerate(images[:max_count]):
                future = executor.submit(self.translate_single_image, img_url)
                future_to_index[future] = idx

            for future in as_completed(future_to_index):
                idx = future_to_index[future]
                try:
                    result = future.result()
                    if result['status_code'] == 0:
                        images[idx] = result['data']
                    if result['status_code'] == 1:
                        return {'code': 1, 'data': '象寄密匙不足'}
                except Exception as e:
                    logging.error(f"图片翻译线程异常: {str(e)}")

        return {'code': 0, 'data': images}


if __name__ == '__main__':
    proxies = {
        'http': 'http://brd-customer-hl_8240a7b6-zone-ruten_remove:g4w5c685daes@brd.superproxy.io:33335',
        'https': 'https://brd-customer-hl_8240a7b6-zone-ruten_remove:g4w5c685daes@brd.superproxy.io:33335',
    }
    images = [
      'https://cbu01.alicdn.com/img/ibank/O1CN013Np2c12G5ZDQPX7LD_!!2196368964-0-cib.jpg',
      'https://cbu01.alicdn.com/img/ibank/O1CN01rQPqrW2G5ZDV2Y5m9_!!2196368964-0-cib.jpg',
      'https://cbu01.alicdn.com/img/ibank/O1CN01TNW7I92G5ZDZuCDMm_!!2196368964-0-cib.jpg',
      'https://cbu01.alicdn.com/img/ibank/O1CN016C8vM52G5ZDYlK362_!!2196368964-0-cib.jpg',
      'https://cbu01.alicdn.com/img/ibank/O1CN01jeCge02G5ZDVXe9La_!!2196368964-0-cib.jpg',
      'https://cbu01.alicdn.com/img/ibank/O1CN011EDHTc2G5ZDUR5zsV_!!2196368964-0-cib.jpg',
      'https://cbu01.alicdn.com/img/ibank/O1CN01skcmPn2G5ZDYjO2vE_!!2196368964-0-cib.jpg'
    ]
    res = XiangJi(account='huangjinlang')
    res1 = res.xiangji_image_translate_threaded(images, 10)
    # res1 = res.get_image_link(1000974660)
    print(res1)