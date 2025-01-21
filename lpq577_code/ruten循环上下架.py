import requests
import base64
import logging
import re
import time


def request_function(url, method='GET', headers=None, data=None, proxies=None, retries=5, timeout=30):
    """
    发送HTTP请求，支持GET和POST方法，支持重试机制。

    :param url: 请求的URL
    :param method: 请求的方法，'GET' 或 'POST' (默认为 'GET')
    :param headers: 请求的头信息（可选）
    :param data: POST请求时提交的数据（可选）
    :param params: GET请求时的查询参数（可选）
    :param retries: 请求失败后的重试次数（默认为3次）
    :param timeout: 请求的超时时间，格式为 (连接超时, 读取超时)（默认为(30, 120)）
    :return: 返回响应对象，如果请求失败，则返回None
    """
    for attempt in range(retries):
        try:
            if method.upper() == 'POST':
                response = requests.post(url, headers=headers, data=data, timeout=timeout, proxies=proxies)
            else:
                response = requests.get(url, headers=headers, timeout=timeout, proxies=proxies)

            # 检查响应状态码
            response.raise_for_status()  # 如果响应状态码不是 2xx，将抛出异常
            return response

        except requests.exceptions.RequestException as e:
            logging.warning(f"请求错误 ({method}-{url}): {e}. 重试中... ({attempt + 1}/{retries})")
            time.sleep(2)

    logging.error(f"请求失败 ({method}-{url})，超过最大重试次数")
    return None


def get_product_package(product_id):
    headers = {'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36'}
    url = f'https://www.ruten.com.tw/item/show?{product_id}'
    response = request_function(url, method='GET', headers=headers)
    match = re.search(r'(?<=RT\.context\ =\ ).*(?=;)', response.text)
    if match:
        return match.group(0)
    else:
        print("No match found")
        return match


def get_cookie_by_api(store):
    """
    通过本地接口获取cookie
    """
    local_url = 'http://127.0.0.1:8802/get_user_by_name'
    data = {'store': store}

    response = request_function(local_url, method='POST', data=data)

    if response is None:
        logging.error(f"无法获取 {store} 的cookie，请求失败")
        return None

    try:
        return response.json()['cookie']
    except ValueError as e:
        logging.error(f"解析响应失败: {e}")
        return None


if __name__ == '__main__':
    result = get_product_package('22442980171235')
    print(result)
