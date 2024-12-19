import requests
import time
import threading

from hashlib import md5
from urllib.parse import quote
from logging_config import logging
from 数据库连接 import MySqlPool


class XiangJi:
    def __init__(self, account=None, mysql_pool=None):
        self.commitTime = str(int(time.time()))
        self.account = account
        self.mysql_pool = mysql_pool
        self.lock = threading.Lock()
        self.api_key = None  # 当前密钥
        self.img_trans_key = None  # 当前翻译密钥
        self.is_key_valid = True  # 密钥是否有效

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
                return None
            else:
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

    def change_xiangji_key_status(self, user_key):
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

    def get_shared_xiangji_key(self):
        """
        获取共享的API密钥
        """
        with self.lock:
            if self.api_key is None:
                key_data = self.get_xiangji_key()
                if key_data:
                    self.api_key = key_data[0]
                    self.img_trans_key = key_data[1]
                else:
                    logging.error('数据库无可用象寄API密钥')
                    self.is_key_valid = False  # 没有密钥
            return self.api_key, self.img_trans_key

    def update_shared_xiangji_key(self):
        """
        当当前密钥的额度用完时，更新密钥
        """
        with self.lock:
            self.change_xiangji_key_status(self.api_key)  # 更新密钥状态
            key_data = self.get_xiangji_key()  # 获取新的密钥
            if key_data:
                self.api_key = key_data[0]
                self.img_trans_key = key_data[1]
                self.is_key_valid = True  # 密钥有效
            else:
                self.is_key_valid = False  # 没有密钥
            logging.info(f'象寄密钥已更新：{self.api_key}')

    def xiangji_image_translate(self, images, max_count):
        api_key, img_trans_key = self.get_shared_xiangji_key()  # 获取共享密钥
        if not self.is_key_valid:
            return None    # 如果没有密钥，返回空

        url = 'https://api.tosoiot.com'
        for idx, i in enumerate(images[:max_count]):
            success = False  # 标记当前图片是否翻译成功
            retry_attempts = 0  # 累计重试次数
            while retry_attempts < 3:  # 最多重试 3 次
                try:
                    sign_string = md5((self.commitTime + "_" + api_key + "_" + img_trans_key).encode('utf-8')).hexdigest()
                    parameters = {
                        'Action': 'GetImageTranslate',
                        'SourceLanguage': 'CHS',
                        'TargetLanguage': 'ENG',
                        'Url': quote(i, safe=':/'),
                        'ImgTransKey': img_trans_key,
                        'Sign': sign_string,
                        'NeedWatermark': 0,
                        'Qos': 'BestQuality',
                        'CommitTime': self.commitTime
                    }
                    response = requests.get(url=url, params=parameters).json()

                    if response['Code'] == 104 or response['Code'] == 118:  # 密钥额度用完
                        logging.info("密钥额度用完，正在尝试更新密钥")
                        self.update_shared_xiangji_key()  # 更新密钥
                        if not self.is_key_valid:
                            logging.error("象寄密钥更新失败，无法继续翻译")
                            return None  # 直接结束程序
                        retry_attempts = 0
                        continue  # 跳出重试循环，重新尝试
                    elif response['Code'] == 200:
                        # 如果翻译成功，更新图像URL
                        translated_image_url = response['Data']['Url']
                        images[idx] = translated_image_url  # 替换原始图片 URL
                        success = True  # 标记翻译成功
                        break  # 跳出重试循环

                except Exception as e:
                    logging.warning(f'象寄翻译请求失败: {e}')

                retry_attempts += 1
                time.sleep(2)

            if not success:
                # 如果3次重试都失败，更新密钥
                logging.warning(f"象寄翻译失败，尝试更新密钥")
                return None  # 如果三次重试都失败，直接结束程序

        return images  # 返回翻译后的图片列表


# mysql_pool = MySqlPool(host='47.122.62.157', password='Qiang123@', user='daraz', database='daraz')
# images = ['https://cbu01.alicdn.com/img/ibank/O1CN01CDeHBa23WVdjJaL1F_!!2218387277263-0-cib.jpg','https://cbu01.alicdn.com/img/ibank/O1CN01hr3pME23WVdlp1ev6_!!2218387277263-0-cib.jpg']
# res = XiangJi(account='shaojie', mysql_pool=mysql_pool)
# res1 = res.xiangji_image_translate(images, 1)
# print(res1)