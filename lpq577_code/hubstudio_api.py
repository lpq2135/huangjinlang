import time
import sys
import json
import mysql.connector
import requests
import logging
import logging_config

from daraz_api import DarazMessages
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


class Hubstudio:
    def __init__(self):
        self.interface = 'http://127.0.0.1:6873'
        self.app_id = '202403061214910375162671104'
        self.app_secret = 'MIIEvQIBADANBgkqhkiG9w0BAQEFAASCBKcwggSjAgEAAoIBAQCmLtJdkRWLXT2Jn/i7Y4LydWBtGhFHRAxvpFvkrshq/fPmjytYxse8Z4d1meqLeKfIpActZcE00tyNNO7hKQKWu+ZzsFt2u24zFrBeI7gll/k9MPRjGrJzJKGFDLz1TfvzxVpyOkab/5NJwU9ojYYXu8fvkHJGC6i6epni3O9ZrFAOT78upRJ5jhOIEDpsSNabeIwGYmMoyBBttyR5wCRPeQ3bZn2Domk7eQBsArrl4vFPg7fbeRWDkSRxhQqsbP3Fpc9vMdLPJ1AtnjQkB24wqrDEFHWvyZe7c3q80w56WgAB26+0LO4phswnlm+/6m3ZDQZDicpBCYTxPe/4Q2BpAgMBAAECggEAKUvtXu8U6YMMLc0hJIAAJHxir/oQXSNd68huRY/hoiTlnV/qp68OJ5WapfDPxkT/fO62EeP9dUEJKdYDntRwHkEnbYxfzkuZgPyca2h49G6lsz0dHhueSNrLgKK/uj3c5KEgbs5oiY+jbGqrbxHsRq2Va8T7gMiY725UG3pHyIKQNm5BISVu/YogigRg8urGmnqj3SQ5MM0NoY9MCyWQEWd2+XFLmQlzP7Fw9fPU6VXklR/ZProciMenotbZvALK0ObJ3blxhDH15PJExBHJxlReMdk2sjRFRYMKazcAF9vjrex3uPQoVRQ/YQ7TPuAfaEdmg9xMDKXUtj+H57hdeQKBgQDp9m7NZp/zpA55Fv0A/NBxzLOpK0tMvMLoWBImGVE3hYUBOmgdV34K56vqlRqN6Yl4+ilTTPfO0smiTr58j/8NrSxw8n2W4gapRwbLZpbvBFDh4ehcqGiGsbgVM+zdhDbUptgtwA7qoQHjtYEd+7mzUlvPdYOAgV1mA42/DOL5ewKBgQC11gI2e53gMbBMsXIe4aBL038ms9qoj7LQRLlfKt56v3XZ36U7gqyt6RbsSbTK2WjADx0dPwIe8FgV2v6xx5nwKc18OC4RhaRIGc0sN2kMZB6iLNjPUNWtsnyNlTNZ4VtrVbrUFC+ZUO12trWV9c88G4HbHJNSEKCPyjDdVmMuawKBgCCjz6t6MMB118sO6PcVTiNCMqJcNuIax3pQpx+HkqwTRY35TwMg7KWq0nIkoRLBTPuCsvc7GqtQ/u5U3ABWund2/Gc5fUnqeJFvJkSEKHRp/rq0oI0ktYhtDMhweRAiXN/n8urXC32yPqg87yl2r96Tk9lqhJEN+zC7ODA6JQQ3AoGAUWqhUwPGjLuy1KQfFPSxcUIhjJK7NP4icl5TIelv9EYF3qfks+CusK/NM79M1AbEgDpELvQnXvL+fcqwf6l/o6kT+Kqu9emAxUfINiQZRRMPJE4wRaNMCZoBauODOptM86JPJOZk6aDyslTcuWh2gdNPMWx6CiSnv7ooZvJnNkECgYEAnK91IFRVIscf2gIz0BXpjxWMCTRpZELQ0w7uxcNGRaIKgWxUu06kvgyJlK0KbI6eHirtacmvrg3tID5O1zJwd8vFlmgjL+gvD0sbimr+IL8mXctq5ksL5DK3/KWNFs6D2DfzCxmPYAE0LPLcvRA/IkZ6bk1PsYcOR5M2z0JDeo8='
        self.group_code = '11659518'
        self.login = self.account_login()

    def account_login(self):
        url = self.interface + '/login'
        data = {
            'appId': self.app_id,
            'appSecret': self.app_secret,
            'groupCode': self.group_code
        }
        response = requests.post(url, json=data)
        return response

    def get_env_list(self):
        url = self.interface + '/api/v1/env/list'
        data = {
            'size': '200'
        }
        response = requests.post(url, json=data).json()
        if response['code'] == 0:
            env_list = {env['containerName']: env['containerCode'] for env in response['data']['list']}
            return env_list

    def start_browser(self, container_code):
        url = self.interface + '/api/v1/browser/start'
        data = {
            'containerCode': container_code,
            'args': ['--start-maximized', '--disable-notifications'],
            'skipSystemResourceCheck': True
        }
        response = requests.post(url, json=data)
        return response.text

    def get_browser_status(self, container_code):
        url = self.interface + '/api/v1/browser/all-browser-status'
        data = {
            'containerCodes': [container_code],
        }
        response = requests.post(url, json=data)
        return response.text

    def get_driver_by_path(self, webdriver_path, port):
        options = webdriver.ChromeOptions()
        options.add_experimental_option("debuggerAddress", '127.0.0.1:' + str(port))
        return webdriver.Chrome(service=Service(webdriver_path), options=options)

    def store_login(self, driver, store_data):
        driver.get("https://sellercenter.daraz.pk/apps/im/chat")
        try:
            # 检测是否存在 //div[@class="next-tabs-tab-inner"]
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, '//div[@class="next-tabs-tab-inner"]')))
            logging.info(f"{store_data[0]}-已登录，无需进行登录操作操作")
            return  # 如果检测到该元素，直接结束函数
        except Exception:
            # 如果未检测到该元素，继续执行登录逻辑
            logging.info(f"{store_data[0]}-未登录，开始登录流程")

        try:
            # 等待页面加载完成，并检查是否存在 //button[@type="submit"]
            submit_button = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "//button[@type='submit']"))
            )
            if submit_button:
                # 输入账号
                account_input = driver.find_element(By.XPATH, "//input[@id='account']")
                while True:
                    driver.execute_script("arguments[0].value = ''", account_input)
                    account_input.send_keys(store_data[2])
                    value = account_input.get_attribute('value')
                    if value == store_data[2]:
                        break

                # 输入密码
                password_input = driver.find_element(By.XPATH, "//input[@id='password']")
                while True:
                    driver.execute_script("arguments[0].value = ''", password_input)
                    password_input.send_keys("Daraz@123")
                    value = password_input.get_attribute('value')
                    if value == 'Daraz@123':
                        break

                # 点击提交按钮
                submit_button.click()

        except Exception as e:
            logging.error(f"{store_data[0]}-登录失败: {e}")

def get_access_token_by_im(account):
    """
    获取daraz店铺消息的店铺token
    """
    mysql_config = dict(host='47.122.62.157', password='Qiang123@', user='daraz', database='daraz')
    cnx = mysql.connector.connect(**mysql_config)
    cursor = cnx.cursor()
    try:
        cursor.execute("SELECT store_name, access_token, email FROM daraz_store_internal_parameters WHERE account = %s AND application_category = 'im'", (account,))
        row = cursor.fetchall()
        return row
    finally:
        cursor.close()
        cnx.close()


# 设置日志配置
logging_config.setup_logger()


if __name__ == '__main__':
    account = input('请输入你的daraz主账号: ')
    access_token_list = get_access_token_by_im(account)
    hubstudio_instance = Hubstudio()  # 创建 Hubstudio 实例
    env_dict = hubstudio_instance.get_env_list()  # 获取环境列表
    while True:
        for i in access_token_list:
            daraz_messages = DarazMessages('pk', i[1])
            messages_count = daraz_messages.get_session_list()
            if messages_count > 0:
                browser_status = json.loads(hubstudio_instance.get_browser_status(env_dict[i[0]]))
                if browser_status['data']['containers'][0]['status'] != 0:
                    logging.info(f'{i[0]}-开始启动hub浏览器进行回复')
                    open_res = json.loads(hubstudio_instance.start_browser(env_dict[i[0]]))
                    webdriver_path = open_res['data']['webdriver']  # 获取webdriver路径
                    debugging_port = open_res['data']['debuggingPort']  # 获取调试端口
                    driver = hubstudio_instance.get_driver_by_path(webdriver_path, debugging_port)
                    hubstudio_instance.store_login(driver, i)  # 填写打开环境返回的webdriver和debuggingPort参数
                else:
                    logging.info(f'{i[0]}-窗口已经打开无需重复打开')
            else:
                logging.info(f'{i[0]}-无待处理的消息')
        logging.info('此轮客服消息更新完成，等待 7200s 继续下一轮更新')
        time.sleep(7200)





