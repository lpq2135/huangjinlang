import logging
import time

from daraz_api import DarazProduct
from lpq577_code.logging_config import setup_logger


if __name__ == '__main__':
    # 设置日志
    setup_logger()

    # 读取违禁品数据
    file_path = r'D:\Daraz运营工具\Daraz下架\违禁词.txt'
    with open(file_path, 'r', encoding='utf-8') as file:
        banned_words = [line.strip() for line in file if line.strip()]

    # 违禁词列表转小写
    banned_words_lower = [word.lower() for word in banned_words]

    daraz_product = DarazProduct('50000401a20jg2sqgXDCq9NvYkmIuJve1f79a538vTIiXAspFtOWpsrY8dGioe', 'pk')
    offset = 0
    while True:
        while True:
            logging.info(f'store-当前offset: {offset}')
            product_data = daraz_product.get_product_list(offset)
            if product_data['code'] == '0':
                break
            time.sleep(3)

        for product in product_data['data']['products']:
            # 获取标题并判断是否包含违禁词
            title = product['attributes']['name']
            title_check = daraz_product.find_banned_words_case_insensitive(banned_words_lower, title)
            if not title_check:
                continue

            logging.warning(f'store-{title}-包含违禁品: {title_check}')
            # 获取 item_id
            item_id = str(product['item_id'])

            # 创建 sku_id_list 列表
            sku_id_list = []
            for sku in product['skus']:
                skuid = str(sku['ShopSku'].split('-')[1])
                sku_data = 'SkuId_' + item_id + '_' + skuid
                sku_id_list.append(sku_data)
            # 格式化列表，最大长度50
            sku_id_list_new = daraz_product.split_list(sku_id_list)
            for lst in sku_id_list_new:
                remove_data = daraz_product.product_remove(lst).json()
                if remove_data['code'] == '0':
                    logging.info(f'{item_id}-产品下架删除成功')
                else:
                    logging.warning(f'{item_id}-产品下架异常')
        offset += 20



