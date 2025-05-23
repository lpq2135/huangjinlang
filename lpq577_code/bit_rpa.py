import requests
import json
import random
import time
import sys
from faker import Faker
import logging_config
import logging

from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

class Bit:
    def __init__(self):
        self.local_url = 'http://127.0.0.1:54345'
        self.headers = {'Content-Type': 'application/json'}
        self.fake = Faker('en_US')

    # 获取分组
    def get_group_list(self):
        xpath_url = '/group/list'
        data = {
          "page": 0,
          "pageSize": 100,
          "all": True
        }
        res = requests.post(f'{self.local_url}{xpath_url}', data=json.dumps(data), headers=self.headers).json()
        group_dict = {i['groupName']: i['id'] for i in res['data']['list']}
        return group_dict

    # 获取分组详情
    def get_browser_list(self, group_id):
        xpath_url = '/browser/list'
        data = {
            'page': 0,
            'pageSize': 100,
            'groupId': group_id
        }
        res = requests.post(f'{self.local_url}{xpath_url}', data=json.dumps(data), headers=self.headers).json()
        return res

    # 打开浏览器鎵撳紑娴忚鍣?
    def open_browser(self, browser_id):
        xpath_url = '/browser/open'
        data = {
            'id': f'{browser_id}',
        }
        res = requests.post(f'{self.local_url}{xpath_url}', data=json.dumps(data), headers=self.headers).json()
        # 获取连接浏览器的参数
        driverPath = res['data']['driver']
        debuggerAddress = res['data']['http']
        return driverPath, debuggerAddress

    # 关闭浏览器
    def close_browser(self, browser_id):
        xpath_url = '/browser/close'
        data = {'id': f'{browser_id}'}
        res = requests.post(f'{self.local_url}{xpath_url}', data=json.dumps(data), headers=self.headers).json()
        return res

    # 删除浏览器
    def delete_browser(self, browser_id):
        xpath_url = '/browser/delete'
        data = {'id': f'{browser_id}'}
        res = requests.post(f'{self.local_url}{xpath_url}', data=json.dumps(data), headers=self.headers).json()
        return res

    # 获取浏览器窗口详情
    def get_browser_detail(self, browser_id):
        xpath_url = '/browser/detail'
        data = {'id': f'{browser_id}'}
        res = requests.post(f'{self.local_url}{xpath_url}', data=json.dumps(data), headers=self.headers).json()
        port = res['data'].get('port', None)
        proxy_data = {
            'proxyMethod': res['data']['proxyMethod'],
            'proxyType': res['data']['proxyType'],
            'proxyUserName': res['data']['proxyUserName'],
            'proxyPassword': res['data']['proxyPassword'],
            'ipCheckService': res['data']['ipCheckService'],
            'host': res['data']['host'],
            'port': port
        }
        return proxy_data

    # 代理检测接口
    def check_agent(self, proxy_data):
        xpath_url = '/checkagent'
        data = {
            'host': proxy_data['host'],
            'port': proxy_data['port'],
            'proxyType': proxy_data['proxyType'],
            'proxyUserName': proxy_data['proxyUserName'],
            'proxyPassword': proxy_data['proxyPassword'],
            'ipCheckService': proxy_data['ipCheckService'],
            'checkExists': 0
        }
        res = requests.post(f'{self.local_url}{xpath_url}', data=json.dumps(data), headers=self.headers).json()
        return res

    # 代理检测接口
    def get_browser_pids(self, ids):
        xpath_url = '/browser/pids'
        data = {'ids': [ids]}
        res = requests.post(f'{self.local_url}{xpath_url}', data=json.dumps(data), headers=self.headers).json()
        return res

    def link_selenium(self, browser_id, card_data):
        username = self.fake.name()
        cardnumber = card_data.split('|')[0]
        expiration = card_data.split('|')[2]
        cvv = card_data.split('|')[1]

        # 检查代理
        proxy_data = self.get_browser_detail(browser_id)
        if proxy_data['host'] != '':
            proxy_status = self.check_agent(proxy_data)
            if proxy_status['data']['success']:
                pass
            else:
                self.delete_browser(browser_id)

        # 获取 selenium 连接参数
        driverPath, debuggerAddress = self.open_browser(browser_id)
        # selenium 连接代码
        chrome_options = webdriver.ChromeOptions()
        chrome_options.add_experimental_option("debuggerAddress", debuggerAddress)

        chrome_service = Service(driverPath)
        driver = webdriver.Chrome(service=chrome_service, options=chrome_options)

        # 获取所有标签页的句柄
        window_handles = driver.window_handles

        # 遍历每个标签页
        for handle in window_handles:
            driver.switch_to.window(handle)
            current_url = driver.current_url

            if "console.bitbrowser.net" not in current_url:
                driver.close()

        # 在新标签页中打开指定网址
        driver.get('https://business.facebook.com/billing_hub/payment_settings')

        # 等待页面加载完成
        WebDriverWait(driver, 10).until(lambda d: d.execute_script("return document.readyState") == "complete")

        # 等待特定元素出现并可以点击
        try:
            text_mapping = ['Add payment method', 'Aggiungi metodo di pagamento', 'Agregar método de pago', 'Ajouter un moyen de paiement']
            found_text = None
            for text in text_mapping:
                try:
                    add_payment_method = WebDriverWait(driver, 2).until(
                        EC.element_to_be_clickable((By.XPATH, f"//div[text()='{text}']"))
                    )
                    found_text = text
                    break
                except:
                    continue

            # 如果找到 text_mapping 中的文本，点击对应的按钮
            if found_text:
                add_payment_method.click()
            else:
                # 检查是否存在 'Blodeface, votre compte a été bloqué'
                try:
                    blocked_text = WebDriverWait(driver, 2).until(
                        EC.presence_of_element_located(
                            (By.XPATH, "//span[contains(text(), 'votre compte a été bloqué')]"))
                    )
                    logging.error(f'{browser_id}-账号已被封')
                    self.close_browser(browser_id)
                    self.delete_browser(browser_id)
                except:
                    try:
                        login_text = WebDriverWait(driver, 2).until(
                            EC.presence_of_element_located(
                                (By.XPATH, "//span[text()='Log into business tools from Meta']"))
                        )
                        logging.error(f'{browser_id}-账号未登录')
                        self.close_browser(browser_id)
                        self.delete_browser(browser_id)
                    except:
                        pass

            # 等待并点击 'Next' 或 'Avanti'
            WebDriverWait(driver, 10).until(lambda d: d.execute_script("return document.readyState") == "complete")
            avanti_button = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, "//div[@aria-label='Enregistrer']/div/div/div/span/span")))
            avanti_button.click()

            # 等待 'Save' 或 'Salva'
            WebDriverWait(driver, 10).until(lambda d: d.execute_script("return document.readyState") == "complete")
            salva_button = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, "//div[@aria-label='Enregistrer']/div/div/div/span/span")))

            # 输入姓名
            username_input = driver.find_element(By.XPATH, "//input[@name='firstName']")
            username_input.send_keys(username)

            # 输入卡号
            cardnumber_input = driver.find_element(By.XPATH, "//input[@name='cardNumber']")
            cardnumber_input.send_keys(cardnumber)

            # 输入截至日期
            expiration_input_input = driver.find_element(By.XPATH, "//input[@name='expiration']")
            expiration_input_input.send_keys(expiration)

            # 输入卡号
            cvv_input = driver.find_element(By.XPATH, "//input[@name='securityCode']")
            cvv_input.send_keys(cvv)

            try:
                check_box = driver.find_element(By.XPATH, "//span[text()='Accetto che Meta possa effettuare addebiti su questa carta in modo ricorrente.']")
                check_box.click()
            except:
                pass

            # 点击 'Salva'
            salva_button.click()

            # 等待并判断绑卡是否成功
            try:
                WebDriverWait(driver, 15).until(
                    EC.element_to_be_clickable(
                        (By.XPATH, "//span[text()='Carta di fatturazione non utilizzabile' or text()='Si è verificato un errore' or text()='Something went wrong' or text()='Si è verificato un errore' or text()='Carta di fatturazione non utilizzabile']"))
                )
                logging.warning(f'{browser_id}-绑卡失败')
                write_to_txt(file_path_2, f'{card_data} 拒绝')
                self.close_browser(browser_id)

            except:
                pass

        except Exception as e:
            logging.warning(f'操作过程中出错: {e}')

# 随机获取 txt 文档的一行数据
def get_and_delete_first_line(file_path):
    try:
        # 读取文件中的所有行
        with open(file_path, 'r', encoding='utf-8') as file:
            lines = file.readlines()

        # 检查文件是否为空
        if not lines:
            logging.error('无可测试的卡数据')
            return None

        # 获取第一行并删除
        first_line = lines.pop(0)  # 删除并获取第一行

        # 将剩余的行写回文件
        with open(file_path, 'w', encoding='utf-8') as file:
            file.writelines(lines)

        return first_line.strip()

    except FileNotFoundError:
        logging.error(f"文件 {file_path} 未找到")
    except Exception as e:
        logging.error(f"操作过程中出错: {e}")

# 往txt 写入数据
def write_to_txt(file_path, data):
    with open(file_path, 'a', encoding='utf-8') as file:
        file.write(data + "\n")


# 设置日志配置
logging_config.setup_logger()


if __name__ == '__main__':
    file_path_1 = r'C:\Users\Administrator\Desktop\facebook\测卡.txt'
    file_path_2 = r'C:\Users\Administrator\Desktop\facebook\测试结果.txt'
    card_data = get_and_delete_first_line(file_path_1)
    if card_data is None:
        time.sleep(2)
        sys.exit()

    # group_name = input('请输入分组名称: ')
    group_name = '意大利'
    bit_instance = Bit()  # 创建实例
    group_dict = bit_instance.get_group_list()  # 获取分组列表并组装成字典
    group_id = group_dict[group_name]  # 获取 group_id
    browser_data = bit_instance.get_browser_list(group_id)  # 获取分组下的 browser_id 列表
    browser_id_list = [i['id'] for i in browser_data['data']['list']]

    for browser_id in browser_id_list:
        bit_instance.link_selenium(browser_id, card_data)


