import logging
import time
import concurrent.futures

from daraz_api import DarazProduct
from lpq577_code.logging_config import setup_logger


def process_product_remove(daraz_product, sku_list, item_id):
    """多线程任务函数：执行下架操作并处理响应"""
    try:
        response = daraz_product.product_remove(sku_list)
        remove_data = response.json()
        if remove_data['code'] == '0' or remove_data['code'] == '503':
            logging.info(f'{item_id}-产品下架删除成功')
            return
    except Exception as e:
        logging.error(f'{item_id}-处理过程中发生异常: {str(e)}')


if __name__ == '__main__':
    # 初始化日志
    setup_logger()

    daraz_product = DarazProduct('50000801f28eN4brfssXcigNk4HwvEDbESQgMRyu1c9f22e6mp0agxeKqAQFpy', 'pk')

    while True:  # 主循环保持长期运行
        # 获取产品列表（带重试机制）
        while True:
            product_data = daraz_product.get_product_list()
            if product_data['code'] == '0':
                break
            logging.warning("获取产品列表失败，3秒后重试...")
            time.sleep(3)

        # 创建线程池
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = []

            # 遍历所有产品
            for product in product_data['data']['products']:
                item_id = str(product['item_id'])

                # 生成SKU列表
                sku_id_list = [
                    f"SkuId_{item_id}_{sku['ShopSku'].split('-')[1]}"
                    for sku in product['skus']
                ]

                # 拆分SKU列表（假设split_list返回分块后的二维列表）
                sku_chunks = daraz_product.split_list(sku_id_list)

                # 为每个SKU块提交任务到线程池
                for chunk in sku_chunks:
                    future = executor.submit(
                        process_product_remove,
                        daraz_product,
                        chunk,
                        item_id
                    )
                    futures.append(future)