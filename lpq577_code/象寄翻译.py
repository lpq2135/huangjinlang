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
            cursor.execute("SELECT user_key, img_trans_key FROM xiangji_key WHERE account = %s AND status = '0' LIMIT 100 ", (self.account,))
            rows = cursor.fetchall()
            if rows is None:
                logging.warning('数据库无象寄翻译密匙')
                self.is_available = False
                return None
            else:
                logging.info(f'象寄密匙列表获取成功')
                self.is_available = True
                return rows
        except Exception as e:
            logging.warning("象寄数据库获取数据异常: ", str(e))
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

    def change_and_get_xiangji_key(self, api_key):
        """
        更新象寄密匙数据库状态
        """
        cnx, cursor = self.mysql_pool.get_conn()
        try:
            cursor.execute("UPDATE xiangji_key SET status = '1' WHERE user_key = %s", (api_key,))
            cnx.commit()
        except Exception as e:
            logging.warning(f'象寄数据库更改{user_key}异常: {e}')
        finally:
            self.mysql_pool.close_mysql(cnx, cursor)

    def xiangji_image_translate(self, images, max_count):
        with self.lock:
            while True:
                if self.api_list:
                    api_data = random.choice(self.api_list)
                    api_key = api_data[0]
                    img_trans_key = api_data[1]
                    break
                else:
                    self.get_xiangji_key()
                    if not self.is_available:
                        return None
        url = 'https://api.tosoiot.com'
        for idx, i in enumerate(images[:max_count]):
            success = False
            while True:
                for retry_attempts in range(5):
                    current_time = str(int(time.time()))
                    try:
                        sign_string = md5((current_time + "_" + api_key + "_" + img_trans_key).encode('utf-8')).hexdigest()
                        parameters = {
                            'Action': 'GetImageTranslate',
                            'SourceLanguage': 'CHS',
                            'TargetLanguage': 'ENG',
                            'Url': quote(i, safe=':/'),
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
                        elif response['Code'] == 112 or response['Code'] == 118:
                            logging.warning(f'象寄密匙额度用完, api_key: {api_key}')
                            self.api_list.remove(api_data)
                            self.change_and_get_xiangji_key(api_key)
                            with self.lock:
                                while True:
                                    if self.api_list:
                                        api_data = random.choice(self.api_list)
                                        api_key = api_data[0]
                                        img_trans_key = api_data[1]
                                        break
                                    else:
                                        self.get_xiangji_key()
                                        if not self.is_available:
                                            return None
                        else:
                            logging.warning(f'象寄翻译请求失败, 重试第{retry_attempts + 1}, api_key: {api_key}次')
                            time.sleep(3)

                    except Exception:
                        logging.warning(f'象寄翻译请求失败, 重试第{retry_attempts + 1}次, api_key: {api_key}')
                        time.sleep(3)

                if success:
                    break

                logging.info(f"象寄翻译重新5次失败，正在尝试更新密钥, api_key: {api_key}")
                with self.lock:
                    while True:
                        if self.api_list:
                            api_data = random.choice(self.api_list)
                            api_key = api_data[0]
                            img_trans_key = api_data[1]
                            break
                        else:
                            self.get_xiangji_key()
                            if not self.is_available:
                                return None

        return images  # 返回翻译后的图片列表


if __name__ == '__main__':
    mysql_pool = MySqlPool(host='47.122.62.157', password='Qiang123@', user='daraz', database='daraz')
    images = ['https://cbu01.alicdn.com/img/ibank/O1CN01CDeHBa23WVdjJaL1F_!!2218387277263-0-cib.jpg','https://cbu01.alicdn.com/img/ibank/O1CN01hr3pME23WVdlp1ev6_!!2218387277263-0-cib.jpg']
    res = XiangJi(account='yilin', mysql_pool=mysql_pool)
    res1 = res.xiangji_image_translate(images, 1)
    print(res1)