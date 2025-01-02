import requests
import time
import threading
import signal
import random

from hashlib import md5
from urllib.parse import quote
from logging_config import logging
from 数据库连接 import MySqlPool


class XiangJi:
    def __init__(self, account=None, mysql_pool=None):
        self.account = account
        self.mysql_pool = mysql_pool
        self.lock = threading.Lock()
        self.is_available = False  # 获取密匙状态
        self.api_list = self.get_xiangji_key()

    def get_xiangji_key(self):
        """
        连接象寄数据库获取翻译密匙
        """
        cnx, cursor = self.mysql_pool.get_conn()
        try:
            cursor.execute("SELECT user_key, img_trans_key FROM xiangji_key WHERE account = %s AND status = '0' LIMIT 50", (self.account,))
            rows = cursor.fetchall()
            if len(rows) == 0:
                logging.warning('数据库无象寄翻译密匙')
                self.is_available = False
                self.api_list = []
                return None
            else:
                logging.info(f'象寄密匙列表获取成功')
                self.is_available = True
                return rows
        except Exception as e:
            logging.warning("象寄数据库获取数据异常: ", str(e))
            self.is_available = True
            self.api_list = []
        finally:
            self.mysql_pool.close_mysql(cnx, cursor)

    def get_xiangji_key_count(self):
        """
        获取指定accunt的象寄密匙数量
        """
        cnx, cursor = self.mysql_pool.get_conn()
        try:
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
            self.mysql_pool.close_mysql(cnx, cursor)

    def change_and_get_xiangji_key(self, user_key):
        """
        更新象寄密匙数据库状态
        """
        cnx, cursor = self.mysql_pool.get_conn()
        try:
            cursor.execute("UPDATE xiangji_key SET status = '1' WHERE user_key = %s", (user_key,))
            cnx.commit()
        except Exception as e:
            logging.warning(f'象寄数据库更改{user_key}异常: {e}')
        finally:
            self.mysql_pool.close_mysql(cnx, cursor)

    def image_translation_record(self, product_id, image_link):
        """
        如果 product_id 存在则更新，否则插入新的记录
        """
        cnx, cursor = self.mysql_pool.get_conn()
        try:
            cursor.execute("INSERT INTO image_translation_record (product_id, image_link) VALUES (%s, %s) ON DUPLICATE KEY UPDATE image_link = VALUES(image_link)", (product_id, image_link))
            cnx.commit()
        except Exception as e:
            # 异常处理
            cnx.rollback()
        finally:
            self.mysql_pool.close_mysql(cnx, cursor)

    def get_image_link(self, product_id):
        """
        查询 product_id 是否存在：
        - 如果存在，返回 image_link
        - 如果不存在，返回 None
        """
        cnx, cursor = self.mysql_pool.get_conn()
        try:
            # 查询 image_link 的 SQL 语句
            cursor.execute("SELECT image_link FROM image_translation_record WHERE product_id = %s", (product_id,))
            result = cursor.fetchone()
            # 如果记录存在，返回 image_link；否则返回 None
            return result[0] if result else None
        except Exception as e:
            return None
        finally:
            self.mysql_pool.close_mysql(cnx, cursor)

    def xiangji_image_translate(self, images, max_count, product_id):
        with self.lock:
            while True:
                if self.api_list:
                    api_data = random.choice(self.api_list)
                    api_key = api_data[0]
                    img_trans_key = api_data[1]
                    break
                else:
                    self.api_list = self.get_xiangji_key()
                    if not self.is_available:
                        return None
        url = 'https://api.tosoiot.com'
        for idx, i in enumerate(images[:max_count]):
            success = False
            while True:
                retry_attempts = 0
                while retry_attempts < 5:
                    current_time = str(int(time.time()))
                    try:
                        sign_string = md5((current_time + "_" + api_key + "_" + img_trans_key).encode('utf-8')).hexdigest()
                        parameters = {
                            'Action': 'GetImageTranslate',
                            'SourceLanguage': 'CHS',
                            'TargetLanguage': 'ENG',
                            'Url': quote(i.split('?')[0], safe=':/'),
                            'ImgTransKey': img_trans_key,
                            'Sign': sign_string,
                            'NeedWatermark': 0,
                            'Qos': 'BestQuality',
                            'CommitTime': current_time
                        }
                        response = requests.get(url=url, params=parameters, timeout=30).json()
                        if response['Code'] == 200:
                            # 如果翻译成功，更新图像URL
                            translated_image_url = response['Data']['Url']
                            images[idx] = translated_image_url  # 替换原始图片 URL
                            success = True
                            break  # 跳出重试循环
                        elif response['Code'] == 118:
                            logging.warning(f'象寄密匙额度用完, api_key: {api_key}, product_id: {product_id}')
                            if api_data in self.api_list:
                                self.api_list.remove(api_data)
                                self.change_and_get_xiangji_key(api_key)
                            with self.lock:
                                while True:
                                    if self.api_list:
                                        api_data = random.choice(self.api_list)
                                        api_key = api_data[0]
                                        img_trans_key = api_data[1]
                                        retry_attempts = 0
                                        time.sleep(2)
                                        break
                                    else:
                                        self.api_list = self.get_xiangji_key()
                                        if not self.is_available:
                                            return None
                        else:
                            logging.warning(f'象寄翻译请求失败, 重试第{retry_attempts + 1}, api_key: {api_key}, product_id: {product_id}')
                            retry_attempts += 1
                            time.sleep(3)

                    except Exception as e:
                        logging.warning(f'象寄翻译请求失败, 重试第{retry_attempts + 1}次, api_key: {api_key}, product_id: {product_id}, 错误: {str(e)}')
                        retry_attempts += 1
                        time.sleep(3)

                if success:
                    break

                logging.info(f"象寄翻译重新5次失败，正在尝试更新密钥, api_key: {api_key}, product_id: {product_id}")
                with self.lock:
                    while True:
                        if self.api_list:
                            api_data = random.choice(self.api_list)
                            api_key = api_data[0]
                            img_trans_key = api_data[1]
                            break
                        else:
                            self.api_list = self.get_xiangji_key()
                            if not self.is_available:
                                return None
        self.image_translation_record(product_id, images[0])
        return images  # 返回翻译后的图片列表


if __name__ == '__main__':
    mysql_pool = MySqlPool(host='47.122.62.157', password='Qiang123@', user='daraz', database='daraz')
    images = ['https://cbu01.alicdn.com/img/ibank/O1CN01CDeHBa23WVdjJaL1F_!!2218387277263-0-cib.jpg','https://cbu01.alicdn.com/img/ibank/O1CN01hr3pME23WVdlp1ev6_!!2218387277263-0-cib.jpg']
    res = XiangJi(account='shaojie', mysql_pool=mysql_pool)
    # res1 = res.xiangji_image_translate(images, 1, 1000974660)
    res1 = res.get_image_link(1000974660)
    print(res1)