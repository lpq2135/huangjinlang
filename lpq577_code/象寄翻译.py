import requests
import time
import threading
import signal

from hashlib import md5
from urllib.parse import quote
from logging_config import logging
from 数据库连接 import MySqlPool


class XiangJi:
    def __init__(self, account=None, mysql_pool=None):
        self.commitTime = str(int(time.time()))
        self.account = account
        self.mysql_pool = mysql_pool
        self.lock = threading.Lock()  # 用于保护访问密钥的锁
        self.api_key = None  # 当前密钥
        self.img_trans_key = None  # 当前翻译密钥
        self.is_available = False  # 获取密匙状态

    def get_xiangji_key(self):
        """
        连接象寄数据库获取翻译密匙
        """
        cnx, cursor = self.mysql_pool.get_conn()
        try:
            cursor.execute("SELECT user_key, img_trans_key FROM xiangji_key WHERE account = %s AND status = '0'", (self.account,))
            rows = cursor.fetchone()
            if rows is None:
                logging.warning('数据库无象寄翻译密匙')
                self.is_available = False
            else:
                self.api_key = rows[0]
                self.img_trans_key = rows[1]
                self.is_available = True
                logging.info(f'象寄密匙获取成功, api_key: {self.api_key}, img_trans_key: {self.img_trans_key}')
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

    def change_and_get_xiangji_key(self):
        """
        更新象寄密匙数据库状态
        """
        cnx, cursor = self.mysql_pool.get_conn()
        try:
            cursor.execute("UPDATE xiangji_key SET status = '1' WHERE user_key = %s", (self.api_key,))
            cnx.commit()
            self.get_xiangji_key()
        except Exception as e:
            logging.warning(f'象寄数据库更改{user_key}异常: {e}')
        finally:
            self.mysql_pool.close_mysql(cnx, cursor)

    def xiangji_image_translate(self, images, max_count):
        if self.api_key is None:
            self.get_xiangji_key()
        if not self.is_available:
            return None
        url = 'https://api.tosoiot.com'
        for idx, i in enumerate(images[:max_count]):
            success = False
            while True:
                for retry_attempts in range(5):
                    try:
                        sign_string = md5((self.commitTime + "_" + self.api_key + "_" + self.img_trans_key).encode('utf-8')).hexdigest()
                        parameters = {
                            'Action': 'GetImageTranslate',
                            'SourceLanguage': 'CHS',
                            'TargetLanguage': 'ENG',
                            'Url': quote(i, safe=':/'),
                            'ImgTransKey': self.img_trans_key,
                            'Sign': sign_string,
                            'NeedWatermark': 0,
                            'Qos': 'BestQuality',
                            'CommitTime': self.commitTime
                        }
                        response = requests.get(url=url, params=parameters, timeout=30).json()
                        if response['Code'] == 200:
                            # 如果翻译成功，更新图像URL
                            translated_image_url = response['Data']['Url']
                            images[idx] = translated_image_url  # 替换原始图片 URL
                            success = True
                            break  # 跳出重试循环
                        else:
                            logging.warning(f'象寄翻译请求失败, 重试第{retry_attempts}次')
                            retry_attempts += 1
                            time.sleep(3)

                    except Exception:
                        logging.warning(f'象寄翻译请求失败, 重试第{retry_attempts}次')
                        retry_attempts += 1
                        time.sleep(3)

                if success:
                    break

                logging.info("象寄翻译异常，正在尝试更新密钥")
                self.change_and_get_xiangji_key()
                self.commitTime = str(int(time.time()))
                if not self.is_available:
                    return None

        return images  # 返回翻译后的图片列表


# mysql_pool = MySqlPool(host='47.122.62.157', password='Qiang123@', user='daraz', database='daraz')
# images = ['https://cbu01.alicdn.com/img/ibank/O1CN01CDeHBa23WVdjJaL1F_!!2218387277263-0-cib.jpg','https://cbu01.alicdn.com/img/ibank/O1CN01hr3pME23WVdlp1ev6_!!2218387277263-0-cib.jpg']
# res = XiangJi(account='yilin', mysql_pool=mysql_pool)
# res1 = res.xiangji_image_translate(images, 1)
# print(res1)