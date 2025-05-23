import requests
from lxml import html
import random
import logging
import string
import logging_config
from urllib.parse import urlencode
import concurrent.futures
import time


def request_function(
    url, method="GET", headers=None, data=None, proxies=None, files=None, timeout=30
):
    for attempt in range(8):
        try:
            # 使用实例的 session 发起请求
            response = requests.request(
                url=url,
                method=method.upper(),
                headers=headers,
                data=data,
                proxies=proxies,
                files=files,
                timeout=timeout,
            )
            response.raise_for_status()
            return response
        except requests.exceptions.RequestException as e:
            if response.status_code == 404:
                return response
            logging.warning(
                f"请求错误 ({method}-{url}): {e}. 重试中... ({attempt + 1}/8)"
            )
            time.sleep(2)
    logging.error(f"请求失败，已重试 8 次: {url}")
    return None


def product_items_v2(product_id):
    url = f"https://rapi.ruten.com.tw/api/items/v2/list?gno={product_id}&level=simple"
    headers = {
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36",
    }
    result = request_function(url, headers=headers, proxies=proxies).json()
    return result["data"][0]["images"]["url"][0]


def check_img(url):
    headers = {
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36",
    }
    result = request_function(url, headers=headers, proxies=proxies)
    return result


def main(i):
    img = product_items_v2(i)
    img_status = check_img(img)
    if img_status.status_code == 200:
        logging.info(f"{i}-图片正常")
        return True
    else:
        logging.warning(f"zwojteke-{i}-图片异常")
        return False


proxies = {
    "http": "http://brd-customer-hl_8240a7b6-zone-ruten_remove:g4w5c685daes@brd.superproxy.io:33335",
    "https": "https://brd-customer-hl_8240a7b6-zone-ruten_remove:g4w5c685daes@brd.superproxy.io:33335",
}


# 设置日志配置
logging_config.setup_logger()

if __name__ == "__main__":
    headers = {
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
        "cookie": get_cookie_by_api("zwojteke"),
    }
    page = 400
    while True:
        logging.info(f"zwojteke-当前页数{page}")
        new_id_list = []
        id_list = get_pagination_product_id(page)
        # 使用 ThreadPoolExecutor 开启多线程
        with concurrent.futures.ThreadPoolExecutor(max_workers=15) as executor:
            # 提交任务到线程池
            future_to_id = {executor.submit(process_product, i): i for i in id_list}

            # 获取任务结果
            for future in concurrent.futures.as_completed(future_to_id):
                i = future_to_id[future]
                try:
                    result = future.result()
                    if result is not None:
                        new_id_list.append(result)
                except Exception as e:
                    logging.error(f"zwojteke-{i}-处理失败: {e}")

        result = large_quantities_of_shelves(page, new_id_list)
        page = 400 if page == 1 else page - 1
