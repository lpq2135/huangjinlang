import requests
import random
import string
import logging
import time
import os
import io

from opencc import OpenCC
from PIL import Image, ImageEnhance
from requests.exceptions import ReadTimeout, RequestException


class BaseCrawler:
    """所有爬虫类的基类，包含共用方法"""
    def request_function(self, url, method='GET', headers=None, data=None, params=None, proxies=None, files=None, timeout=30, max_retries=6):
        """通用的请求方法"""
        # 进行最多max_retries次重试
        for attempt in range(max_retries):
            try:
                response = requests.request(
                    url=url,
                    method=method.upper(),
                    headers=headers,
                    data=data,
                    params=params,
                    proxies=proxies,
                    files=files,
                    timeout=timeout
                )

                # 对于404或400状态码，直接返回响应对象
                if response.status_code in (404, 400):
                    return response

                # 检查HTTP状态码，如果不是2xx会抛出HTTPError异常
                response.raise_for_status()
                return response

            except ReadTimeout as e:
                # 单独处理超时错误
                logging.warning(f"请求超时 ({method}-{url}): {e}. 重试中... ({attempt + 1}/{max_retries})")
                time.sleep(2 ** attempt)  # 指数退避策略

            except RequestException as e:
                if hasattr(e, 'response') and e.response is not None:
                    if e.response.status_code in (404, 400):
                        return e.response
                logging.warning(f"请求错误 ({method}-{url}): {e}. 重试中... ({attempt + 1}/{max_retries})")
                time.sleep(2 ** attempt)

            except Exception as e:
                # 处理其他未知异常
                logging.warning(f"未知错误 ({method}-{url}): {e}. 重试中... ({attempt + 1}/{max_retries})")
                time.sleep(2 ** attempt)

        logging.error(f"请求失败，已重试{max_retries}次: {url}")
        return None

    def generate_random_string(self, length=10):
        """生成随机字符串"""
        chars = string.ascii_letters + string.digits
        return ''.join(random.choice(chars) for _ in range(length))

    def generate_random_number(self, length=8):
        """生成指定位数的随机数字，第一位不为0"""
        first_digit = random.choice("123456789")  # 第一位1-9
        other_digits = ''.join(random.choices("0123456789", k=length - 1))  # 其余位0-9
        return first_digit + other_digits

    def generate_spec_info_by_ruten(self, data_json):
        """组装成 ruten 上货数据包"""
        # 提取基础数据
        sku_parameters = data_json['data']['skumodel']['sku_data']['sku_parameter']
        # 获取规格数
        specifications = data_json['data']['specifications']

        # 计算最低价格
        price_list = [int(float(i['price'])) for i in sku_parameters]
        min_price = min(price_list) if price_list else 0

        # 初始化数据结构
        structure = {}
        specs = {}
        d_new = {}  # 临时ID映射

        # 单规格处理
        if specifications == 1:
            for item in sku_parameters:
                temp_id = 'temp_' + self.generate_random_number()
                structure[temp_id] = []

                specs[temp_id] = {
                    'spec_id': temp_id,
                    'parent_id': 0,
                    'spec_name': item['name'][:20],
                    'spec_num': item['stock'],
                    'spec_price': item['price'],
                    'spec_status': 'Y',
                    'childs': [],
                    'spec_ext': {'goods_no': None}
                }
        # 双规格处理
        elif specifications == 2:
            d1, d2 = [], []  # 规格1和规格2的值列表

            # 收集所有规格值并去重
            for item in sku_parameters:
                sku1_value, sku2_value = item['name'].split('||')
                if sku1_value not in d1:
                    d1.append(sku1_value)
                if sku2_value not in d2:
                    d2.append(sku2_value)

            # 为每个规格值生成临时ID并构建结构
            for spec1 in d1[:30]:
                temp1 = 'temp_' + self.generate_random_number()
                d_new[temp1] = spec1
                structure[temp1] = {}

                for spec2 in d2[:15]:
                    temp2 = 'temp_' + self.generate_random_number()
                    d_new[temp2] = spec2
                    structure[temp1][temp2] = []

            # 构建规格详情
            for parent_id, children in structure.items():
                specs[parent_id] = {
                    'spec_id': parent_id,
                    'parent_id': '0',
                    'spec_name': d_new[parent_id][:20],
                    'spec_num': '0',
                    'spec_status': 'Y',
                    'childs': children,
                    'spec_ext': {'goods_no': ''}
                }

            for parent_id, children in structure.items():
                for child_id in children.keys():
                    combined_name = f"{d_new[parent_id]}||{d_new[child_id]}"
                    sku_item = next((i for i in sku_parameters if i['name'] == combined_name), None)

                    specs[child_id] = {
                        'spec_id': child_id,
                        'parent_id': parent_id,
                        'spec_name': d_new[child_id][:20],
                        'spec_num': sku_item['stock'] if sku_item else 499,
                        'spec_price': sku_item['price'] if sku_item else min_price,
                        'spec_status': 'Y' if sku_item else 'N',
                        'childs': [],
                        'spec_ext': {'goods_no': ''}
                    }

        spec_info = {
            'level': specifications,
            'structure': structure,
            'specs': specs,
        }
        g_direct_price = min_price
        return spec_info, g_direct_price

    def split_list(self, input_list):
        """将输入列表分成多个子列表，每个子列表最多包含 chunk_size 个元素"""
        return [input_list[i:i + 30] for i in range(0, len(input_list), 30)]

    def zh_to_tw(self, data):
        """翻译成繁体"""
        converter = OpenCC('s2tw')
        # 提取重复路径
        sku_data = data['data']['skumodel']['sku_data']
        # 转换标题
        data['data']['title'] = converter.convert(data['data']['title'])
        # 转换规格参数
        if data['data']['specifications'] != 0:
            # 属性名转换
            sku_data['sku_property_name'] = {k: converter.convert(v) for k, v in sku_data['sku_property_name'].items()}
            # 参数列表转换
            for param in sku_data['sku_parameter']:
                param['name'] = converter.convert(param['name'])
        # 转换详情描述
        if isinstance(data['data']['details_text_description'], list):
            data['data']['details_text_description'] = [converter.convert(i) for i in data['data']['details_text_description']]
        else:
            data['data']['details_text_description'] = converter.convert(data['data']['details_text_description'])
        return data

    def construction_details_html(self, detail_text, detail_img):
        # 表情符号
        emoticons = ['💯', '🔊', '📢', '🔔', '⚙️', '🔗', '🏷️', '⏳', '📌', '🌀', '💝', '✅']
        # 拼装图片
        if detail_img:
            html_img = "".join(f'<img alt="" src="{url}" width="800">' for url in detail_img[2:-1])
        # 拼装文字
        if detail_img:
            emo = random.choice(emoticons)
            html_text = "".join(
                f'<p style="color: rgba(0, 0, 0, 0.8); font-family: helvetica, arial, lihei pro, microsoft jhenghei; background-color: #ffffff; margin-bottom: 8px; font-size: 14pt"><strong>{emo}{text}</strong></p>'
                for text in detail_text
            )
        # 合并文字和图片html
        html = html_text + html_img
        return html

    def add_image_watermark(
            self,
            original_image,
            watermark_image_path,
            opacity=1,
            image_scale=0.2,
            margin=3
    ):
        """
        给图片添加水印（右上角，可调整边距）
        参数:
            original_image: PIL.Image对象（原始图片）
            watermark_image_path: 图片水印路径
            opacity: 水印透明度(0.0-1.0)
            image_scale: 图片水印缩放比例(0.0-1.0)
            margin: 水印与边界的距离(像素)
        返回:
            带水印的PIL.Image对象
        """
        try:
            # 检查水印文件是否存在
            if not os.path.exists(watermark_image_path):
                logging.warning(f"水印文件不存在: {watermark_image_path}")
                return original_image

            # 打开水印图片并确保RGBA模式
            watermark = Image.open(watermark_image_path).convert("RGBA")

            # 调整水印大小（保持宽高比）
            base_width = int(original_image.width * image_scale)
            wm_ratio = watermark.height / watermark.width
            new_height = int(base_width * wm_ratio)
            watermark = watermark.resize((base_width, new_height), Image.Resampling.LANCZOS)

            # 调整透明度
            if opacity < 1.0:
                alpha = watermark.split()[3]
                alpha = ImageEnhance.Brightness(alpha).enhance(opacity)
                watermark.putalpha(alpha)

            # 计算位置（右上角）
            x = original_image.width - watermark.width - margin
            y = margin

            # 确保位置有效
            x = max(0, x)
            y = max(0, y)

            # 创建副本并添加水印
            watermarked = original_image.copy().convert("RGBA")
            watermarked.paste(watermark, (x, y), watermark)

            # # 新增保存逻辑
            # output_path = r'C:\Users\Administrator\Desktop\水印图片测试\watermarked_output.jpg'
            # watermarked.convert("RGB").save(output_path, quality=100)

            return watermarked.convert("RGB")

        except Exception as e:
            logging.error(f"添加水印失败: {str(e)}", exc_info=True)
            return original_image


if __name__ == '__main__':
    # data = {'platform': '1688', 'code': 0, 'message': '请求成功', 'data': {'product_id': '895157423598', 'specifications': 2, 'unit_weight': 0.02, 'start_amount': 1, 'title': '一加13钢化膜边胶无尘仓Reno13pro秒贴盒曲面findX8pro手机膜适用', 'main_images': ['https://cbu01.alicdn.com/img/ibank/O1CN013qBbQ91fjHw997Gce_!!2218330604042-0-cib.jpg', 'https://cbu01.alicdn.com/img/ibank/O1CN01s2NUiz1fjHw8BAYYi_!!2218330604042-0-cib.jpg', 'https://cbu01.alicdn.com/img/ibank/O1CN01g64Fsg1fjHw816Xwd_!!2218330604042-0-cib.jpg', 'https://cbu01.alicdn.com/img/ibank/O1CN01c1SyEx1fjHw7B9Uvb_!!2218330604042-0-cib.jpg', 'https://cbu01.alicdn.com/img/ibank/O1CN01yBD54N1fjHw9gGFny_!!2218330604042-0-cib.jpg'], 'skumodel': {'sku_data': {'sku_property_name': {'sku1_property_name': '颜色', 'sku2_property_name': '尺寸'}, 'sku_parameter': [{'remote_id': '895157423598_yLYeKrJ6Ro', 'name': '四边胶款无尘仓秒贴盒-高清||1+13（超声波解锁）', 'imageUrl': None, 'price': '4.50', 'stock': 949}, {'remote_id': '895157423598_mtISahSUoi', 'name': '四边胶款无尘仓秒贴盒-高清||Reno13pro', 'imageUrl': None, 'price': '4.50', 'stock': 986}, {'remote_id': '895157423598_zQUyr5KALo', 'name': '四边胶款无尘仓秒贴盒-高清||findX8pro', 'imageUrl': None, 'price': '4.50', 'stock': 987}, {'remote_id': '895157423598_jBifSo2utD', 'name': '四边胶款无尘仓秒贴盒-高清||Reno3pro/Reno4pro/Reno5pro/Reno6pro', 'imageUrl': None, 'price': '4.50', 'stock': 953}, {'remote_id': '895157423598_vR99bftp5D', 'name': '四边胶款无尘仓秒贴盒-高清||findX6pro/findX7ultra', 'imageUrl': None, 'price': '4.50', 'stock': 905}, {'remote_id': '895157423598_lIjLhLlSGB', 'name': '四边胶款无尘仓秒贴盒-高清||真我10pro+/真我13pro+', 'imageUrl': None, 'price': '4.50', 'stock': 903}, {'remote_id': '895157423598_IAJvDCOvUa', 'name': '四边胶款无尘仓秒贴盒-高清||findX3/1+ACE2/1+11/1+11R/findX5pro/1+9pro/1+10pro/', 'imageUrl': None, 'price': '4.50', 'stock': 909}]}}, 'video': 'https://cloud.video.taobao.com/play/u/2218330604042/p/2/e/6/t/1/510298916352.mp4', 'details_text_description': ['品牌:其他', '材质:钢化玻璃', '贴膜类型:前膜', '贴膜特点:高清,防爆,防尘,防指纹,防摔,全屏,秒贴盒', '颜色:四边胶款无尘仓秒贴盒-高清', '尺寸:1+13（超声波解锁）,Reno13pro,findX8pro,Reno3pro/Reno4pro/Reno5pro/Reno6pro,findX6pro/findX7ultra,真我10pro+/真我13pro+,findX3/1+ACE2/1+11/1+11R/findX5pro/1+9pro/1+10pro/', '适用机型:OPPO'], 'detailed_picture': ['https://cbu01.alicdn.com/img/ibank/O1CN013qBbQ91fjHw997Gce_!!2218330604042-0-cib.jpg', 'https://cbu01.alicdn.com/img/ibank/O1CN01s2NUiz1fjHw8BAYYi_!!2218330604042-0-cib.jpg', 'https://cbu01.alicdn.com/img/ibank/O1CN01g64Fsg1fjHw816Xwd_!!2218330604042-0-cib.jpg', 'https://cbu01.alicdn.com/img/ibank/O1CN01c1SyEx1fjHw7B9Uvb_!!2218330604042-0-cib.jpg', 'https://cbu01.alicdn.com/img/ibank/O1CN01ImKSBg1fjHw8d6UsT_!!2218330604042-0-cib.jpg']}}
    base = BaseCrawler()
    detail_text = ['【現貨免運】', '【公司貨】', '【嚴選好物】', '【可開發票】', '【好物優選】', '【口碑推薦】', '【銷售冠軍】', '【五星好評】', '【人氣爆款】', '【可刷卡】']
    detail_img = [
      'https://cbu01.alicdn.com/img/ibank/O1CN01ylfX6W2G5ZDeDbCiB_!!2196368964-0-cib.jpg',
      'https://cbu01.alicdn.com/img/ibank/O1CN013Np2c12G5ZDQPX7LD_!!2196368964-0-cib.jpg',
      'https://cbu01.alicdn.com/img/ibank/O1CN01rQPqrW2G5ZDV2Y5m9_!!2196368964-0-cib.jpg',
      'https://cbu01.alicdn.com/img/ibank/O1CN01TNW7I92G5ZDZuCDMm_!!2196368964-0-cib.jpg',
      'https://cbu01.alicdn.com/img/ibank/O1CN016C8vM52G5ZDYlK362_!!2196368964-0-cib.jpg',
      'https://cbu01.alicdn.com/img/ibank/O1CN01jeCge02G5ZDVXe9La_!!2196368964-0-cib.jpg',
      'https://cbu01.alicdn.com/img/ibank/O1CN011EDHTc2G5ZDUR5zsV_!!2196368964-0-cib.jpg',
      'https://cbu01.alicdn.com/img/ibank/O1CN01skcmPn2G5ZDYjO2vE_!!2196368964-0-cib.jpg'
    ]
    image_result = base.request_function(detail_img[0])
    original_img = Image.open(io.BytesIO(image_result.content))
    watermark_image_path = r'C:\Users\Administrator\Desktop\水印图片测试\店铺水印\LOGO\dyqt41.png'
    res = base.add_image_watermark(original_img, watermark_image_path)
