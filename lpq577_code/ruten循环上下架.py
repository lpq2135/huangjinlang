import requests
import base64
import logging
import re
import time
import io


def request_function(url, method='GET', headers=None, data=None, proxies=None, files=None, timeout=30):
    # 创建通用请求函数
    for attempt in range(5):
        try:
            if method.upper() == 'POST':
                response = requests.post(url, headers=headers, data=data, files=files, timeout=timeout, proxies=proxies)
            else:
                response = requests.get(url, headers=headers, files=files, timeout=timeout, proxies=proxies)
            # 检查响应状态码
            response.raise_for_status()  # 如果响应状态码不是 2xx，将抛出异常
            return response
        except requests.exceptions.RequestException as e:
            logging.warning(f"请求错误 ({method}-{url}): {e}. 重试中... ({attempt + 1}/5)")
            time.sleep(2)


class Ruten:
    def __init__(self, store):
        self.store = store
        self.proxies = {
            'http': 'http://brd-customer-hl_8240a7b6-zone-ruten_remove:g4w5c685daes@brd.superproxy.io:33335',
            'https': 'https://brd-customer-hl_8240a7b6-zone-ruten_remove:g4w5c685daes@brd.superproxy.io:33335',
        }
        self.headers = {
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
            'cookie': self.get_cookie_by_api()}
        self.ck = self.get_upload_ck_value()

    def get_product_package(self, product_id):
        # 获取商品数据包
        url = f'https://www.ruten.com.tw/item/show?{product_id}'
        response = request_function(url, headers=self.headers, proxies=self.proxies)
        match = re.search(r'(?<=RT\.context\ =\ ).*(?=;)', response.text)
        if match:
            return match.group(0)
        else:
            print("No match found")
            return match

    def get_cookie_by_api(self):
        # 通过本地接口获取cookie
        local_url = 'http://127.0.0.1:8802/get_user_by_name'
        data = {'store': self.store}
        response = request_function(local_url, method='POST', data=data)
        if response is None:
            logging.error(f"无法获取{self.store}的cookie")
            return None
        try:
            return response.json()['cookie']
        except ValueError as e:
            logging.error(f"解析{self.store}参数数据失败: {e}")
            return None

    def get_upload_ck_value(self):
        # 获取上传所需ck值
        url = 'https://mybidu.ruten.com.tw/upload/item_initial.php'
        response = request_function(url, headers=self.headers)
        return response.url.split('ck=')[1]

    def upload_main_images(self):
        # 上传主图
        url = f'https://upload.ruten.com.tw/item/image.php?ck={self.ck}'
        image_path = 'https://a.rimg.com.tw/c1/7f7/4f0/dfhgfghngf/6/3a/22422669590074_161.jpg'
        image_result = request_function(image_path, headers=self.headers)
        files = {'image': (image_path.split('/')[-1], io.BytesIO(image_result.content), 'image/jpeg')}
        response = request_function(url, method='POST', headers=self.headers, files=files)
        return response.text

    def get_pagination_product_id(self, page):
        url = f'https://mybid.ruten.com.tw/master/my.php?p={page}&l_type=sel_selling&p_size=30&o_sort=asc&o_column=post_time'
        response = request_function(url, headers=self.headers)
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

    def process_category_id(self):
        # 处理类目编号
        pass

    def process_img(self):
        # 处理主图
        pass

    def process_title(self):
        # 处理标题
        pass

    def process_user_class(self):
        # 处理后台分类
        pass

    def process_sku(self):
        # 处理sku规格
        pass

    def process_details(self):
        # 处理详情
        pass


if __name__ == '__main__':
    reten = Ruten('urxfntnl')
    result = reten.upload_main_images()
    print(result)
