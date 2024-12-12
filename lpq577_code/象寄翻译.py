import requests
import time

from hashlib import md5
from urllib.parse import quote
from logging_config import logging


class XiangJi:
    def __init__(self, account=None, mysql_pool=None):
        self.commitTime = str(int(time.time()))
        self.account = account
        self.mysql_pool = mysql_pool

    def get_xiangji_key(self):
        """
        连接象寄数据库获取翻译密匙
        """
        cnx, cursor = self.mysql_pool.get_conn()
        try:
            cursor.execute("SELECT user_key, img_trans_key FROM xiangji_key WHERE account = %s AND status = '0'", (self.account,))
            rows = cursor.fetchall()
            if rows is None:
                logging.warning('数据库无象寄翻译密匙')
                return None
            else:
                return rows[0]
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

    def xiangji_image_translate(self, image, max_count):
        data = self.get_xiangji_key()
        user_key = data[0]
        img_trans_key = data[1]
        url = 'https://api.tosoiot.com'

        for idx, i in enumerate(image):
            while True:
                if int(idx) < int(max_count):
                    sign_string = md5((self.commitTime + "_" + user_key + "_" + img_trans_key).encode('utf-8')).hexdigest()
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
                    try:
                        response = requests.get(url=url, params=parameters).json()
                        if response['Code'] == 118:
                            self.change_xiangji_key_status(user_key)
                            data = self.get_xiangji_key()
                            user_key = data[0]
                            img_trans_key = data[1]
                        else:
                            translated_image_url = response['Data']['Url']
                            image[idx] = translated_image_url
                            break
                    except Exception as e:
                        logging.warning(f'象寄翻译请求失败: {e}')
                else:
                    break
        return image
