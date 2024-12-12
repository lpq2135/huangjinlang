import json
import math
import requests
import mysql.connector
import logging
import datetime
import time
import pandas as pd
from lxml import html
import re
import os
import sys
import threading


# 设置了日志的基本配置
log_dir = "log_files"
os.makedirs(log_dir, exist_ok=True)
log_format = '%(asctime)s - %(levelname)s - %(message)s'
level = logging.INFO

# 文件日志
logging.basicConfig(filename=os.path.join(log_dir, "mylog.log"), format=log_format, level=level)

# 控制台日志
console = logging.StreamHandler()
console.setLevel(level)
console.setFormatter(logging.Formatter(log_format))
logging.getLogger('').addHandler(console)

def connect_mysql():
    """
    连接数据库
    """
    mysql_config = dict(host='47.122.62.157', password='Qiang123..', user='ruten_str', database='ruten_str')
    cnx = mysql.connector.connect(**mysql_config)
    cursor = cnx.cursor()
    return cnx, cursor

def close_mysql(cnx, cursor):
    """
    关闭数据库
    """
    cursor.close()
    cnx.close()

def user_authentication():
    """
    验证账号密码是否正确
    """
    cnx, cursor = connect_mysql()
    try:
        cursor.execute("SELECT * FROM user_information WHERE account = %s", (account,))
        row = cursor.fetchone()
        if row is None:
            logging.warning('该账号不存在')
            return False
        elif row[1] != password:
            logging.warning("密码错误")
            return False
        else:
            logging.info("账号验证正确，符合启动条件")
            return True
    finally:
        close_mysql(cnx, cursor)

def get_shop_by_mysql():
    """
    获取满足条件的店铺
    """
    cnx, cursor = connect_mysql()
    shops = []
    try:
        cursor.execute("SELECT store FROM exp_automatically_down WHERE account = %s AND operation_time != %s",
                       (account, current_date,))
        result = cursor.fetchall()
        if result:
            shops = [res[0] for res in result[:thread_count]]
    finally:
        close_mysql(cnx, cursor)
    return shops

def writing_to_database(store):
    cnx, cursor = connect_mysql()
    try:
        cursor.execute("UPDATE exp_automatically_down SET operation_time = %s WHERE account = %s AND store = %s;",
                       (current_date, account, store))
    finally:
        cnx.commit()
        close_mysql(cnx, cursor)

def get_cookie_by_api(store):
    """
    通过本地接口获取cookie
    """
    local_url = 'http://127.0.0.1:8802/get_user_by_name'
    data = {'store': store}
    try:
        response = requests.post(url=local_url, data=data)
        return response.json()['cookie']
    except requests.exceptions.RequestException as e:
        logging.warning(f'请求cookie错误：{e}')

def get_products(store, cookie, page):
    """
    进入商品页获取商品的相关信息
    """
    url = f'https://mybid.ruten.com.tw/master/my.php?p={page}&l_type=sel_selling&p_size=30&o_sort=asc&o_column=post_time'
    header = {
        'cookie': cookie,
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 '
                      'Safari/537.36'
    }
    max_retries = 5
    for _ in range(max_retries):
        try:
            response = requests.get(url=url, headers=header, proxies=proxies, timeout=15).text
            tree = html.fromstring(response)
            product_num = re.findall(r'"real_total":(.*?)}', response)[0]
            if product_num is not None:
                id_list = tree.xpath('//tr[@class="row-odd" or @class="row-even"]/@data-gno')
                new_list = []
                for i in id_list:
                    product_data = {
                        'product_id': i,
                        'title': tree.xpath(f'//tr[@data-gno="{i}"]/td[3]/a/text()')[0],
                        'price': tree.xpath(f'//tr[@data-gno="{i}"]/td[4]/div/@data-price-min')[0],
                        'stock': tree.xpath(f'//tr[@data-gno="{i}"]/td[5]/text()')[0].replace('(', '').strip(),
                        'sales': tree.xpath(f'//tr[@data-gno="{i}"]/td[6]/a/text()')[0],
                        'click': tree.xpath(f'//tr[@data-gno="{i}"]/td[7]/text()')[0],
                        'cart': tree.xpath(f'//tr[@data-gno="{i}"]/td[8]/text()')[0],
                        'upduct_time': tree.xpath(f'//tr[@data-gno="{i}"]/td[10]/text()')[0].strip(),
                    }
                    new_list.append(product_data)
                return product_num, new_list
        except requests.exceptions.RequestException as e:
            logging.warning(f'{store}请求商品管理页面异常：{e}')
        logging.warning(f'[{store}]商品页面请求失败，重试第{_ + 1}次并暂停5s')
        time.sleep(5)

def get_the_number_of_online_products(store, cookie):
    url = 'https://mybid.ruten.com.tw/master/my.php?l_type=sel_selling'
    header = {
        'cookie': cookie,
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 '
                      'Safari/537.36'
    }
    max_retries = 5
    for _ in range(max_retries):
        try:
            response = requests.get(url=url, headers=header, proxies=proxies, timeout=15).text
            tree = html.fromstring(response)
            product_num = re.findall(r'"real_total":(.*?)}', response)[0]
            if product_num is not None:
                total_num = tree.xpath('//div[@class="rt-text-activated"]/text()')[0].split('/')[1].replace(',', '')
                return product_num, total_num
        except requests.exceptions.RequestException as e:
            logging.warning(f'{store}请求商品管理页面异常：{e}')
        logging.warning(f'[{store}]商品页面请求失败，重试第{_ + 1}次并暂停5s')
        time.sleep(5)

def remove_products(store, cookie, gno_list):
    """
    下架产品
    """
    url = 'https://mybid.ruten.com.tw/master/action_sellnow.php'
    header = {
        'cookie': cookie,
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 '
                      'Safari/537.36',
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    data = {
        'type': 'down',
        'gno_list': gno_list
    }
    max_retries = 5
    for _ in range(max_retries):
        try:
            response = requests.post(url=url, headers=header, data=data, proxies=proxies, timeout=15)
            response.raise_for_status()
            if response.json()['status'] == 'success' or response.json()['status'] == 'fail':
                logging.info(f'{store} 商品下架成功：{gno_list}')
                return True
            else:
                logging.info(f'{store} 商品下架失败：{gno_list}')
        except requests.exceptions.HTTPError as err:
            logging.error(f'HTTP 请求错误：{err}')
        except Exception as e:
            logging.error(f'未预期的错误：{e}')
        logging.warning(f'{store} 商品下架请求失败，重试第{_ + 1}次并暂停5s')
        time.sleep(5)

def process_store(store):
    cookie = get_cookie_by_api(store)
    product_num1, total_num1 = get_the_number_of_online_products(store, cookie)
    if int(product_num1) <= int(total_num1) * float(delisting_percentage):
        logging.warning(f'{store} 当前产品数:{product_num1}，无需执行下架任务')
        writing_to_database(store)
    elif int(product_num1) > int(total_num1) * float(delisting_percentage):
        page = 400 if math.ceil(int(product_num1) / 30) >= 400 else math.ceil(int(product_num1) / 30)
        while True:
            product_num2, new_list2 = get_products(store, cookie, page)
            if int(product_num2) >= int(total_num1) * float(delisting_percentage):
                gno_list1 = ",".join([item['product_id'] for item in list(
                    filter(lambda x: int(x['price']) < int(price) and int(x['sales']) < int(bid) or int(x['price']) >= int(
                        price) and int(x['sales']) < int(bid) and int(x['click']) < int(click) and int(x['cart']) < int(
                        cart), new_list2))])
                number_of_ids = 0 if gno_list1 == '' else len(gno_list1.split(','))
                if gno_list1:
                    logging.info(f'{store} 当前产品数:{product_num2}，当前页数：{page}，符合条件的商品数：{number_of_ids}')
                    if remove_products(store, cookie, gno_list1):
                        if page > 1:
                            page -= 1
                        elif page == 1:
                            page = 400 if math.ceil(int(product_num2) / 30) >= 400 else math.ceil(int(product_num2) / 30)
                    else:
                        time.sleep(10)
                else:
                    logging.info(f'{store} 当前产品数:{product_num2}，当前页数：{page}，符合条件的商品数：{number_of_ids}')
                    if page > 1:
                        page -= 1
                    elif page == 1:
                        page = 400 if math.ceil(int(product_num2) / 30) >= 400 else math.ceil(
                            int(product_num2) / 30)
            else:
                logging.warning(f'{store} 当前产品数:{product_num2}，下架任务执行成功')
                writing_to_database(store)
                break


account = input('请输入你的账号：')
password = input('请输入你的密码：')
thread_count = int(input('请输入线程数（最小为1，最大为5）：'))
while thread_count < 1 or thread_count > 5:
    print("线程数太高，请重新输入!!!")
    thread_count = int(input('请输入线程数：'))
logging.info(f'当前线程数：{thread_count}')
# exe_path = os.path.dirname(sys.executable)
if user_authentication():
    first_row = pd.read_excel(r'C:\Users\Administrator\Desktop\扩充包自动下架\参数配置表.xlsx').iloc
    sort_by = first_row[0, 0]
    price = first_row[0, 1]
    bid = first_row[0, 2]
    click = first_row[0, 3]
    cart = first_row[0, 4]
    delisting_percentage = first_row[0, 5]
    proxies = json.loads(first_row[0, 6])
    current_date = datetime.date.today().strftime("%Y-%m-%d")
    while True:
        stores = get_shop_by_mysql()
        if not stores:
            logging.warning('当前无可执行店铺，休眠12h')
            time.sleep(12 * 60 * 60)
        else:
            threads = [threading.Thread(target=process_store, args=(store,)) for store in stores]
            for thread in threads:
                thread.start()
            for thread in threads:
                thread.join()
else:
    time.sleep(5)
    sys.exit()

