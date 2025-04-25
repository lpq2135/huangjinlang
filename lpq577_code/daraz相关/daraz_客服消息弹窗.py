import time
import mysql.connector
import logging
import logging_config

from bit_rpa import Bit
from lpq577_code.daraz相关.daraz_api import DarazMessages
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


class MessageBox(Bit):
    def store_login(self, store_data, ids, driverPath, debuggerAddress):

        # selenium 连接代码
        chrome_options = webdriver.ChromeOptions()
        chrome_options.add_experimental_option("debuggerAddress", debuggerAddress)

        chrome_service = Service(driverPath)
        driver = webdriver.Chrome(service=chrome_service, options=chrome_options)

        # 获取所有窗口句柄
        window_handles = driver.window_handles

        # 遍历每个窗口
        for handle in window_handles:
            driver.switch_to.window(handle)  # 切换到当前窗口
            current_url = driver.current_url  # 获取当前窗口的 URL

            # 如果 URL 不包含 "sjhdf"，关闭该窗口
            if ids not in current_url:
                driver.close()

        driver.get("https://sellercenter.daraz.pk/apps/im/chat")

        try:
            # 检测是否存在 //div[@class="next-tabs-tab-inner"]
            WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.XPATH, '//div[@class="next-tabs-tab-inner"]')))
            logging.info(f"{store_data[0]}-已登录，无需进行登录操作操作")
            return True  # 如果检测到该元素，直接结束函数
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
                time.sleep(1)
                return True

        except Exception as e:
            logging.error(f"{store_data[0]}-登录失败: {e}")
            return False

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
    account = input('请输入你的daraz管理账号: ')
    access_token_list = get_access_token_by_im(account)
    message_box = MessageBox()  # 创建 MessageBox 实例
    group_list = message_box.get_group_list()  # 获取分组列表
    env_dict = message_box.get_browser_list(group_list[account])  # 获取环境列表
    browser_id_dict = {i['name']: i['id'] for i in env_dict['data']['list']}  # 获取店铺名对应的浏览器 id
    while True:
        for i in access_token_list:
            daraz_message = DarazMessages('pk', i[1])
            messages_count = daraz_message.get_session_list()
            browser_id = browser_id_dict[i[0]]
            if messages_count > 0:
                # 获取浏览器的打开状态
                browser_status = message_box.get_browser_pids(browser_id)
                if not browser_status['data']:
                    logging.info(f'{i[0]}-开始启动bit浏览器进行回复')
                    # 启动浏览器
                    driverPath, debuggerAddress = message_box.open_browser(browser_id)
                    for _ in range(5):
                        operate_status = message_box.store_login(i, browser_id, driverPath, debuggerAddress)
                        if operate_status:
                            break
                        logging.warning(f'{i[0]}-登录失败尝试重新登录(当前第{_ + 1}次)')

                else:
                    logging.info(f'{i[0]}-窗口已经打开无需重复打开')
            else:
                logging.info(f'{i[0]}-无待处理的消息')
            time.sleep(5)
        logging.info('此轮客服消息更新完成，等待 7200s 继续下一轮更新')
        time.sleep(7200)
