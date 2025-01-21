import requests
import re
import hashlib
import logging
from copy import deepcopy
from concurrent.futures import ThreadPoolExecutor, wait, ALL_COMPLETED

class Translator:
    def __init__(self, data=None, deepl_api=None):
        self.data = data
        self.deepl_api = deepl_api

    def translate_text_with_sougou(self, text, translate_to='en'):
        headers = {
            "User-Agent": 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36'}
        sougou_url1 = f"https://fanyi.sogou.com/text?keyword={text}&transfrom=zh-CHS&transto=en&model=general&exchange=true"
        sougou_url2 = 'https://fanyi.sogou.com/api/transpc/text/result'
        for attempt in range(5):
            try:
                response1 = requests.get(sougou_url1, headers=headers)
                uuid = re.findall(r'<meta name="reqinfo" content="uuid:(.*?),', response1.content.decode())[0]
                cookies = response1.cookies
                if cookies:
                    cookie_str = '; '.join([f'{name}={value}' for name, value in cookies.items()])
                    headers['Cookie'] = cookie_str
                t = f"zh-CHSen{text}109984457"
                tt = hashlib.md5(t.encode()).hexdigest()
                data = {
                    "from": "zh-CHS",
                    "to": translate_to,
                    "text": text,
                    "client": "web",
                    "fr": "browser_pc",
                    "needQc": 1,
                    "s": tt,
                    "uuid": uuid,
                    "exchange": True
                }
                response = requests.post(url=sougou_url2, headers=headers, data=data).json()
                if response['data']['translate']['errorCode'] == '0':
                    result = response['data']['translate']['dit'].split(" or ")[0].strip()
                    if self.is_chinese(result) is False:
                        return (self.remove_last_dot(result)).title()
            except Exception as e:
                logging.warning(f"搜狗翻译请求失败，尝试第{attempt + 1}次. Error: {e}")
        raise Exception("搜狗翻译请求失败")

    def translate_text_with_deepl(self, text):
        # 对 text 进行格式化处理
        for i in range(len(text)):
            value = self.replace_brackets(text[i])
            value = self.format_text(value)
            text[i] = value

        auth_key = self.deepl_api
        deepl_url = "https://api.deepl.com/v2/translate"
        data = {
            'auth_key': auth_key,
            'text': text,
            'source_lang': 'ZH',
            'target_lang': 'EN'
        }
        attempt = 1
        while attempt <= 10:
            try:
                response = requests.post(deepl_url, data=data, timeout=30)
                if response.status_code != 200:
                    logging.warning(f"deepl翻译请求网络异常: {response.status_code}，第{attempt}次重试")
                    continue
                result = [self.format_brackets(self.remove_last_dot(i['text'])).title() for i in response.json()["translations"]]
                return result
            except Exception as e:
                logging.warning(f"deepl翻译请求失败，尝试第{attempt}次. Error: {e}")
            attempt += 1
        raise Exception("deepl翻译请求失败")

    def remove_last_dot(self, str):
        """
        去掉字符串末尾的点号，并去除尾部空格。
        :param str: 输入字符串
        :return: 处理后的字符串
        """
        return str.rstrip('.').strip()

    def is_chinese(self, check_str):
        """
        检查字符串是否包含中文字符。
        :param check_str: 输入字符串
        :return: 如果包含中文字符返回True，否则返回False
        """
        return bool(re.search(r'[\u4e00-\u9fff]', check_str))

    def split_list(self, input_list):
        # 将列表按照指定大小切分
        return [input_list[i:i + 50] for i in range(0, len(input_list), 50)]

    def format_title(self, title):
        lowercase_words = [
            # 连接词和冠词
            "and", "or", "but", "for", "nor", "so", "the", "a", "an", "in", "on", "at",
            "by", "with", "from", "of", "to",

            # 介词
            "as", "about", "over", "under", "between", "among", "through", "into",
            "during", "before", "after", "out", "without", "against", "across",

            # 副词和其他常用词
            "to", "up", "down", "off", "over", "around", "out", "under", "inside", "outside",
            "again", "only", "just", "more", "less", "than",

            # 品牌名的常见词汇
            "store", "brand", "company", "shop",

            # 常见动词和形容词（标题中间或结尾时）
            "be", "have", "do", "is", "are", "was", "were", "will", "can", "make", "use",
            "give", "take", "help", "get", "keep", "allow", "support", "easy", "fast",
            "low", "high"
        ]
        # 遍历要替换成小写的指定词
        for word in lowercase_words:
            # 使用正则替换，忽略大小写，并将匹配到的词替换成小写
            title = re.sub(r'\b' + re.escape(word) + r'\b', word.lower(), title, flags=re.IGNORECASE)
        return title

    def format_text(self, text):
        return re.sub(r'[^\w\s.,!?:;\'"[\]+\-|]', '', text)

    def replace_brackets(self, text):
        # 替换【为[，】为]
        text = re.sub(r'【', '[', text)
        text = re.sub(r'】', ']', text)
        return text

    def replace_sku_value(self, text):
        # 格式化详情文字
        text = re.sub(r'\(.*?\)', '', text)
        text = text.replace('"', '')
        text = text.replace(',', '+')
        text = text.replace('and', '+')
        return text

    def format_brackets(self, text):
        # 1. 如果 [ 前没有字符（即它是开头或前面有空格），不加空格；否则加一个空格
        text = re.sub(r'(?<=\S)\[', ' [', text)

        # 2. 确保 `[` 后面没有空格
        text = re.sub(r'\[\s+', '[', text)

        # 3. 确保 `]` 前面没有空格
        text = re.sub(r'\s*\]', ']', text)

        # 4. 确保 `]` 后面只有一个空格
        text = re.sub(r'\](?!\s)', '] ', text)  # 如果 ] 后面没有空格，添加一个空格

        # 5. 确保 `,` 后面只有一个空格
        text = re.sub(r'\s*,\s*', ', ', text)

        # 6. 确保 `-` 前后面都没有空格
        text = re.sub(r'\s*-\s*', '-', text)

        # 6. 格式化处理
        text = ((text.replace(':', ': ')).replace(":  ", ": ")).strip()

        return text

    def process_skumodel(self):
        if self.data['specifications'] != 0:
            sku_data = self.data['skumodel']['sku_data']
            # 获取skumodel键下需要翻译的文本
            text = set()
            for value in sku_data['sku_property_name'].values():
                text.add(value)
            if self.data['specifications'] == 1:
                for i in sku_data['sku_parameter']:
                    text.add(i['name'])
            elif self.data['specifications'] == 2:
                for i in sku_data['sku_parameter']:
                    sku1_value, sku2_value = i['name'].split('||')
                    text.add(sku1_value)
                    text.add(sku2_value)

            # 将集合转换成列表
            text_list = list(text)

            # 判断列表长度进行拆分
            sub_lists = self.split_list(list(text_list))
            text_lists = []
            for sub_list in sub_lists:
                text_lists.extend(self.translate_text_with_deepl(sub_list))

            count = 1
            for key in sku_data['sku_property_name'].keys():
               value = text_lists[text_list.index(sku_data['sku_property_name'][key])]
               if 'colour' in value.lower() or 'color' in value.lower():
                   sku_data['sku_property_name'][key] = 'color'
               elif 'size' in value:
                   sku_data['sku_property_name'][key] = 'size'
               else:
                   value = re.sub(r'[\(\)]', '', re.sub(r' +', '_', value))
                   if len(value) > 15:
                       sku_data['sku_property_name'][key] = f'Variants_{count}'
                   else:
                       sku_data['sku_property_name'][key] = value
               count += 1

            if self.data['specifications'] == 1:
                for i in sku_data['sku_parameter']:
                    value = text_lists[text_list.index(i['name'])]
                    i['name'] = self.replace_sku_value(value)

            elif self.data['specifications'] == 2:
                for i in sku_data['sku_parameter']:
                    value_1, value_2 = i['name'].split('||')
                    sku1_value = text_lists[text_list.index(value_1)]
                    sku2_value = text_lists[text_list.index(value_2)]
                    i['name'] = self.replace_sku_value(sku1_value) + '||' + self.replace_sku_value(sku2_value)

    def process_title(self):
        title = self.translate_text_with_deepl([self.data['title']])
        title = self.format_title(title[0]).replace(',', '')
        self.data['title'] = title

    def process_details_text_description(self):
        # 获取skumodel键下需要翻译的文本
        text = self.data['details_text_description']

        # 判断列表长度进行拆分
        sub_lists = self.split_list(text)

        # 替换原始数据
        text_lists = []
        new_text_lists = []
        for sub_list in sub_lists:
            text_lists.extend(self.translate_text_with_deepl(sub_list))
        for i in range(len(text_lists)):
            if self.is_chinese(text_lists[i]) or (text_lists[i]).count(',') >= 4:
                continue
            new_text_lists.append(text_lists[i])
        self.data['details_text_description'] = new_text_lists

    def process_all(self):
        # 使用 ThreadPoolExecutor 并行执行这些任务
        with ThreadPoolExecutor(max_workers=3) as executor:
            # 提交任务并返回 future 对象
            future_title = executor.submit(self.process_title)
            future_skumodel = executor.submit(self.process_skumodel)
            future_description = executor.submit(self.process_details_text_description)

            # 等待所有任务完成
            wait([future_title, future_skumodel, future_description], return_when=ALL_COMPLETED)

        # 在所有任务完成后返回处理的数据
        return self.data  # 返回处理后的所有结果


if __name__ == '__main__':
    tetx = {'status': True, 'data': {'product_id': '734990688469', 'specifications': 2, 'start_amount': 1, 'title': '美甲贴一件代发成品的甲片小红书假指甲美甲片美甲穿戴甲穿戴美甲', 'main_images': [{'size220x220ImageURI': 'https://cbu01.alicdn.com/img/ibank/O1CN01OAQC9A1bRBef3wzwA_!!2216396973461-0-cib.220x220.jpg', 'imageURI': 'img/ibank/O1CN01OAQC9A1bRBef3wzwA_!!2216396973461-0-cib.jpg', 'searchImageURI': 'https://cbu01.alicdn.com/img/ibank/O1CN01OAQC9A1bRBef3wzwA_!!2216396973461-0-cib.search.jpg', 'summImageURI': 'https://cbu01.alicdn.com/img/ibank/O1CN01OAQC9A1bRBef3wzwA_!!2216396973461-0-cib.summ.jpg', 'size310x310ImageURI': 'https://cbu01.alicdn.com/img/ibank/O1CN01OAQC9A1bRBef3wzwA_!!2216396973461-0-cib.310x310.jpg', 'fullPathImageURI': 'https://cbu01.alicdn.com/img/ibank/O1CN01OAQC9A1bRBef3wzwA_!!2216396973461-0-cib.jpg'}, {'size220x220ImageURI': 'https://cbu01.alicdn.com/img/ibank/O1CN01xVCQ5t1bRBeUg3pg6_!!2216396973461-0-cib.220x220.jpg', 'imageURI': 'img/ibank/O1CN01xVCQ5t1bRBeUg3pg6_!!2216396973461-0-cib.jpg', 'searchImageURI': 'https://cbu01.alicdn.com/img/ibank/O1CN01xVCQ5t1bRBeUg3pg6_!!2216396973461-0-cib.search.jpg', 'summImageURI': 'https://cbu01.alicdn.com/img/ibank/O1CN01xVCQ5t1bRBeUg3pg6_!!2216396973461-0-cib.summ.jpg', 'size310x310ImageURI': 'https://cbu01.alicdn.com/img/ibank/O1CN01xVCQ5t1bRBeUg3pg6_!!2216396973461-0-cib.310x310.jpg', 'fullPathImageURI': 'https://cbu01.alicdn.com/img/ibank/O1CN01xVCQ5t1bRBeUg3pg6_!!2216396973461-0-cib.jpg'}, {'size220x220ImageURI': 'https://cbu01.alicdn.com/img/ibank/O1CN01OQaWFT1bRBeg7LiTR_!!2216396973461-0-cib.220x220.jpg', 'imageURI': 'img/ibank/O1CN01OQaWFT1bRBeg7LiTR_!!2216396973461-0-cib.jpg', 'searchImageURI': 'https://cbu01.alicdn.com/img/ibank/O1CN01OQaWFT1bRBeg7LiTR_!!2216396973461-0-cib.search.jpg', 'summImageURI': 'https://cbu01.alicdn.com/img/ibank/O1CN01OQaWFT1bRBeg7LiTR_!!2216396973461-0-cib.summ.jpg', 'size310x310ImageURI': 'https://cbu01.alicdn.com/img/ibank/O1CN01OQaWFT1bRBeg7LiTR_!!2216396973461-0-cib.310x310.jpg', 'fullPathImageURI': 'https://cbu01.alicdn.com/img/ibank/O1CN01OQaWFT1bRBeg7LiTR_!!2216396973461-0-cib.jpg'}, {'size220x220ImageURI': 'https://cbu01.alicdn.com/img/ibank/O1CN01FV4cgw1bRBecsje6C_!!2216396973461-0-cib.220x220.jpg', 'imageURI': 'img/ibank/O1CN01FV4cgw1bRBecsje6C_!!2216396973461-0-cib.jpg', 'searchImageURI': 'https://cbu01.alicdn.com/img/ibank/O1CN01FV4cgw1bRBecsje6C_!!2216396973461-0-cib.search.jpg', 'summImageURI': 'https://cbu01.alicdn.com/img/ibank/O1CN01FV4cgw1bRBecsje6C_!!2216396973461-0-cib.summ.jpg', 'size310x310ImageURI': 'https://cbu01.alicdn.com/img/ibank/O1CN01FV4cgw1bRBecsje6C_!!2216396973461-0-cib.310x310.jpg', 'fullPathImageURI': 'https://cbu01.alicdn.com/img/ibank/O1CN01FV4cgw1bRBecsje6C_!!2216396973461-0-cib.jpg'}, {'size220x220ImageURI': 'https://cbu01.alicdn.com/img/ibank/O1CN01y80zeJ1bRBemTPawb_!!2216396973461-0-cib.220x220.jpg', 'imageURI': 'img/ibank/O1CN01y80zeJ1bRBemTPawb_!!2216396973461-0-cib.jpg', 'searchImageURI': 'https://cbu01.alicdn.com/img/ibank/O1CN01y80zeJ1bRBemTPawb_!!2216396973461-0-cib.search.jpg', 'summImageURI': 'https://cbu01.alicdn.com/img/ibank/O1CN01y80zeJ1bRBemTPawb_!!2216396973461-0-cib.summ.jpg', 'size310x310ImageURI': 'https://cbu01.alicdn.com/img/ibank/O1CN01y80zeJ1bRBemTPawb_!!2216396973461-0-cib.310x310.jpg', 'fullPathImageURI': 'https://cbu01.alicdn.com/img/ibank/O1CN01y80zeJ1bRBemTPawb_!!2216396973461-0-cib.jpg'}, {'size220x220ImageURI': 'https://cbu01.alicdn.com/img/ibank/O1CN01ZdWuzE1bRBeYxzycQ_!!2216396973461-0-cib.220x220.jpg', 'imageURI': 'img/ibank/O1CN01ZdWuzE1bRBeYxzycQ_!!2216396973461-0-cib.jpg', 'searchImageURI': 'https://cbu01.alicdn.com/img/ibank/O1CN01ZdWuzE1bRBeYxzycQ_!!2216396973461-0-cib.search.jpg', 'summImageURI': 'https://cbu01.alicdn.com/img/ibank/O1CN01ZdWuzE1bRBeYxzycQ_!!2216396973461-0-cib.summ.jpg', 'size310x310ImageURI': 'https://cbu01.alicdn.com/img/ibank/O1CN01ZdWuzE1bRBeYxzycQ_!!2216396973461-0-cib.310x310.jpg', 'fullPathImageURI': 'https://cbu01.alicdn.com/img/ibank/O1CN01ZdWuzE1bRBeYxzycQ_!!2216396973461-0-cib.jpg'}, {'size220x220ImageURI': 'https://cbu01.alicdn.com/img/ibank/O1CN01GuoCMU1bRBeT8LQRc_!!2216396973461-0-cib.220x220.jpg', 'imageURI': 'img/ibank/O1CN01GuoCMU1bRBeT8LQRc_!!2216396973461-0-cib.jpg', 'searchImageURI': 'https://cbu01.alicdn.com/img/ibank/O1CN01GuoCMU1bRBeT8LQRc_!!2216396973461-0-cib.search.jpg', 'summImageURI': 'https://cbu01.alicdn.com/img/ibank/O1CN01GuoCMU1bRBeT8LQRc_!!2216396973461-0-cib.summ.jpg', 'size310x310ImageURI': 'https://cbu01.alicdn.com/img/ibank/O1CN01GuoCMU1bRBeT8LQRc_!!2216396973461-0-cib.310x310.jpg', 'fullPathImageURI': 'https://cbu01.alicdn.com/img/ibank/O1CN01GuoCMU1bRBeT8LQRc_!!2216396973461-0-cib.jpg'}, {'size220x220ImageURI': 'https://cbu01.alicdn.com/img/ibank/O1CN01LoCWU21bRBeYy0Nb3_!!2216396973461-0-cib.220x220.jpg', 'imageURI': 'img/ibank/O1CN01LoCWU21bRBeYy0Nb3_!!2216396973461-0-cib.jpg', 'searchImageURI': 'https://cbu01.alicdn.com/img/ibank/O1CN01LoCWU21bRBeYy0Nb3_!!2216396973461-0-cib.search.jpg', 'summImageURI': 'https://cbu01.alicdn.com/img/ibank/O1CN01LoCWU21bRBeYy0Nb3_!!2216396973461-0-cib.summ.jpg', 'size310x310ImageURI': 'https://cbu01.alicdn.com/img/ibank/O1CN01LoCWU21bRBeYy0Nb3_!!2216396973461-0-cib.310x310.jpg', 'fullPathImageURI': 'https://cbu01.alicdn.com/img/ibank/O1CN01LoCWU21bRBeYy0Nb3_!!2216396973461-0-cib.jpg'}, {'size220x220ImageURI': 'https://cbu01.alicdn.com/img/ibank/O1CN01Jq6HuS1bRBehThh9V_!!2216396973461-0-cib.220x220.jpg', 'imageURI': 'img/ibank/O1CN01Jq6HuS1bRBehThh9V_!!2216396973461-0-cib.jpg', 'searchImageURI': 'https://cbu01.alicdn.com/img/ibank/O1CN01Jq6HuS1bRBehThh9V_!!2216396973461-0-cib.search.jpg', 'summImageURI': 'https://cbu01.alicdn.com/img/ibank/O1CN01Jq6HuS1bRBehThh9V_!!2216396973461-0-cib.summ.jpg', 'size310x310ImageURI': 'https://cbu01.alicdn.com/img/ibank/O1CN01Jq6HuS1bRBehThh9V_!!2216396973461-0-cib.310x310.jpg', 'fullPathImageURI': 'https://cbu01.alicdn.com/img/ibank/O1CN01Jq6HuS1bRBehThh9V_!!2216396973461-0-cib.jpg'}, {'size220x220ImageURI': 'https://cbu01.alicdn.com/img/ibank/O1CN01Qa5DyD1bRBegZGFCU_!!2216396973461-0-cib.220x220.jpg', 'imageURI': 'img/ibank/O1CN01Qa5DyD1bRBegZGFCU_!!2216396973461-0-cib.jpg', 'searchImageURI': 'https://cbu01.alicdn.com/img/ibank/O1CN01Qa5DyD1bRBegZGFCU_!!2216396973461-0-cib.search.jpg', 'summImageURI': 'https://cbu01.alicdn.com/img/ibank/O1CN01Qa5DyD1bRBegZGFCU_!!2216396973461-0-cib.summ.jpg', 'size310x310ImageURI': 'https://cbu01.alicdn.com/img/ibank/O1CN01Qa5DyD1bRBegZGFCU_!!2216396973461-0-cib.310x310.jpg', 'fullPathImageURI': 'https://cbu01.alicdn.com/img/ibank/O1CN01Qa5DyD1bRBegZGFCU_!!2216396973461-0-cib.jpg'}, {'size220x220ImageURI': 'https://cbu01.alicdn.com/img/ibank/O1CN01dUzuNc1bRBeZaYZM2_!!2216396973461-0-cib.220x220.jpg', 'imageURI': 'img/ibank/O1CN01dUzuNc1bRBeZaYZM2_!!2216396973461-0-cib.jpg', 'searchImageURI': 'https://cbu01.alicdn.com/img/ibank/O1CN01dUzuNc1bRBeZaYZM2_!!2216396973461-0-cib.search.jpg', 'summImageURI': 'https://cbu01.alicdn.com/img/ibank/O1CN01dUzuNc1bRBeZaYZM2_!!2216396973461-0-cib.summ.jpg', 'size310x310ImageURI': 'https://cbu01.alicdn.com/img/ibank/O1CN01dUzuNc1bRBeZaYZM2_!!2216396973461-0-cib.310x310.jpg', 'fullPathImageURI': 'https://cbu01.alicdn.com/img/ibank/O1CN01dUzuNc1bRBeZaYZM2_!!2216396973461-0-cib.jpg'}, {'size220x220ImageURI': 'https://cbu01.alicdn.com/img/ibank/O1CN01XkTknF1bRBeiJxfSz_!!2216396973461-0-cib.220x220.jpg', 'imageURI': 'img/ibank/O1CN01XkTknF1bRBeiJxfSz_!!2216396973461-0-cib.jpg', 'searchImageURI': 'https://cbu01.alicdn.com/img/ibank/O1CN01XkTknF1bRBeiJxfSz_!!2216396973461-0-cib.search.jpg', 'summImageURI': 'https://cbu01.alicdn.com/img/ibank/O1CN01XkTknF1bRBeiJxfSz_!!2216396973461-0-cib.summ.jpg', 'size310x310ImageURI': 'https://cbu01.alicdn.com/img/ibank/O1CN01XkTknF1bRBeiJxfSz_!!2216396973461-0-cib.310x310.jpg', 'fullPathImageURI': 'https://cbu01.alicdn.com/img/ibank/O1CN01XkTknF1bRBeiJxfSz_!!2216396973461-0-cib.jpg'}, {'size220x220ImageURI': 'https://cbu01.alicdn.com/img/ibank/O1CN01pWsGIy1bRBeco4tep_!!2216396973461-0-cib.220x220.jpg', 'imageURI': 'img/ibank/O1CN01pWsGIy1bRBeco4tep_!!2216396973461-0-cib.jpg', 'searchImageURI': 'https://cbu01.alicdn.com/img/ibank/O1CN01pWsGIy1bRBeco4tep_!!2216396973461-0-cib.search.jpg', 'summImageURI': 'https://cbu01.alicdn.com/img/ibank/O1CN01pWsGIy1bRBeco4tep_!!2216396973461-0-cib.summ.jpg', 'size310x310ImageURI': 'https://cbu01.alicdn.com/img/ibank/O1CN01pWsGIy1bRBeco4tep_!!2216396973461-0-cib.310x310.jpg', 'fullPathImageURI': 'https://cbu01.alicdn.com/img/ibank/O1CN01pWsGIy1bRBeco4tep_!!2216396973461-0-cib.jpg'}, {'size220x220ImageURI': 'https://cbu01.alicdn.com/img/ibank/O1CN01YEYIGb1bRBi1PfLAn_!!2216396973461-0-cib.220x220.jpg', 'imageURI': 'img/ibank/O1CN01YEYIGb1bRBi1PfLAn_!!2216396973461-0-cib.jpg', 'searchImageURI': 'https://cbu01.alicdn.com/img/ibank/O1CN01YEYIGb1bRBi1PfLAn_!!2216396973461-0-cib.search.jpg', 'summImageURI': 'https://cbu01.alicdn.com/img/ibank/O1CN01YEYIGb1bRBi1PfLAn_!!2216396973461-0-cib.summ.jpg', 'size310x310ImageURI': 'https://cbu01.alicdn.com/img/ibank/O1CN01YEYIGb1bRBi1PfLAn_!!2216396973461-0-cib.310x310.jpg', 'fullPathImageURI': 'https://cbu01.alicdn.com/img/ibank/O1CN01YEYIGb1bRBi1PfLAn_!!2216396973461-0-cib.jpg'}, {'size220x220ImageURI': 'https://cbu01.alicdn.com/img/ibank/O1CN01uXGDmv1bRBee1fxVm_!!2216396973461-0-cib.220x220.jpg', 'imageURI': 'img/ibank/O1CN01uXGDmv1bRBee1fxVm_!!2216396973461-0-cib.jpg', 'searchImageURI': 'https://cbu01.alicdn.com/img/ibank/O1CN01uXGDmv1bRBee1fxVm_!!2216396973461-0-cib.search.jpg', 'summImageURI': 'https://cbu01.alicdn.com/img/ibank/O1CN01uXGDmv1bRBee1fxVm_!!2216396973461-0-cib.summ.jpg', 'size310x310ImageURI': 'https://cbu01.alicdn.com/img/ibank/O1CN01uXGDmv1bRBee1fxVm_!!2216396973461-0-cib.310x310.jpg', 'fullPathImageURI': 'https://cbu01.alicdn.com/img/ibank/O1CN01uXGDmv1bRBee1fxVm_!!2216396973461-0-cib.jpg'}, {'size220x220ImageURI': 'https://cbu01.alicdn.com/img/ibank/O1CN01x9I7Mk1bRBeegV8Cq_!!2216396973461-0-cib.220x220.jpg', 'imageURI': 'img/ibank/O1CN01x9I7Mk1bRBeegV8Cq_!!2216396973461-0-cib.jpg', 'searchImageURI': 'https://cbu01.alicdn.com/img/ibank/O1CN01x9I7Mk1bRBeegV8Cq_!!2216396973461-0-cib.search.jpg', 'summImageURI': 'https://cbu01.alicdn.com/img/ibank/O1CN01x9I7Mk1bRBeegV8Cq_!!2216396973461-0-cib.summ.jpg', 'size310x310ImageURI': 'https://cbu01.alicdn.com/img/ibank/O1CN01x9I7Mk1bRBeegV8Cq_!!2216396973461-0-cib.310x310.jpg', 'fullPathImageURI': 'https://cbu01.alicdn.com/img/ibank/O1CN01x9I7Mk1bRBeegV8Cq_!!2216396973461-0-cib.jpg'}, {'size220x220ImageURI': 'https://cbu01.alicdn.com/img/ibank/O1CN01Pw3n1w1bRBeZaXYy3_!!2216396973461-0-cib.220x220.jpg', 'imageURI': 'img/ibank/O1CN01Pw3n1w1bRBeZaXYy3_!!2216396973461-0-cib.jpg', 'searchImageURI': 'https://cbu01.alicdn.com/img/ibank/O1CN01Pw3n1w1bRBeZaXYy3_!!2216396973461-0-cib.search.jpg', 'summImageURI': 'https://cbu01.alicdn.com/img/ibank/O1CN01Pw3n1w1bRBeZaXYy3_!!2216396973461-0-cib.summ.jpg', 'size310x310ImageURI': 'https://cbu01.alicdn.com/img/ibank/O1CN01Pw3n1w1bRBeZaXYy3_!!2216396973461-0-cib.310x310.jpg', 'fullPathImageURI': 'https://cbu01.alicdn.com/img/ibank/O1CN01Pw3n1w1bRBeZaXYy3_!!2216396973461-0-cib.jpg'}, {'size220x220ImageURI': 'https://cbu01.alicdn.com/img/ibank/O1CN01sErJE91bRBebkyAh2_!!2216396973461-0-cib.220x220.jpg', 'imageURI': 'img/ibank/O1CN01sErJE91bRBebkyAh2_!!2216396973461-0-cib.jpg', 'searchImageURI': 'https://cbu01.alicdn.com/img/ibank/O1CN01sErJE91bRBebkyAh2_!!2216396973461-0-cib.search.jpg', 'summImageURI': 'https://cbu01.alicdn.com/img/ibank/O1CN01sErJE91bRBebkyAh2_!!2216396973461-0-cib.summ.jpg', 'size310x310ImageURI': 'https://cbu01.alicdn.com/img/ibank/O1CN01sErJE91bRBebkyAh2_!!2216396973461-0-cib.310x310.jpg', 'fullPathImageURI': 'https://cbu01.alicdn.com/img/ibank/O1CN01sErJE91bRBebkyAh2_!!2216396973461-0-cib.jpg'}, {'size220x220ImageURI': 'https://cbu01.alicdn.com/img/ibank/O1CN01z6pXIY1bRBeT8NuK4_!!2216396973461-0-cib.220x220.jpg', 'imageURI': 'img/ibank/O1CN01z6pXIY1bRBeT8NuK4_!!2216396973461-0-cib.jpg', 'searchImageURI': 'https://cbu01.alicdn.com/img/ibank/O1CN01z6pXIY1bRBeT8NuK4_!!2216396973461-0-cib.search.jpg', 'summImageURI': 'https://cbu01.alicdn.com/img/ibank/O1CN01z6pXIY1bRBeT8NuK4_!!2216396973461-0-cib.summ.jpg', 'size310x310ImageURI': 'https://cbu01.alicdn.com/img/ibank/O1CN01z6pXIY1bRBeT8NuK4_!!2216396973461-0-cib.310x310.jpg', 'fullPathImageURI': 'https://cbu01.alicdn.com/img/ibank/O1CN01z6pXIY1bRBeT8NuK4_!!2216396973461-0-cib.jpg'}, {'size220x220ImageURI': 'https://cbu01.alicdn.com/img/ibank/O1CN01nssuzv1bRBeiJyL3v_!!2216396973461-0-cib.220x220.jpg', 'imageURI': 'img/ibank/O1CN01nssuzv1bRBeiJyL3v_!!2216396973461-0-cib.jpg', 'searchImageURI': 'https://cbu01.alicdn.com/img/ibank/O1CN01nssuzv1bRBeiJyL3v_!!2216396973461-0-cib.search.jpg', 'summImageURI': 'https://cbu01.alicdn.com/img/ibank/O1CN01nssuzv1bRBeiJyL3v_!!2216396973461-0-cib.summ.jpg', 'size310x310ImageURI': 'https://cbu01.alicdn.com/img/ibank/O1CN01nssuzv1bRBeiJyL3v_!!2216396973461-0-cib.310x310.jpg', 'fullPathImageURI': 'https://cbu01.alicdn.com/img/ibank/O1CN01nssuzv1bRBeiJyL3v_!!2216396973461-0-cib.jpg'}, {'size220x220ImageURI': 'https://cbu01.alicdn.com/img/ibank/O1CN01pBJL6R1bRBebmN6vC_!!2216396973461-0-cib.220x220.jpg', 'imageURI': 'img/ibank/O1CN01pBJL6R1bRBebmN6vC_!!2216396973461-0-cib.jpg', 'searchImageURI': 'https://cbu01.alicdn.com/img/ibank/O1CN01pBJL6R1bRBebmN6vC_!!2216396973461-0-cib.search.jpg', 'summImageURI': 'https://cbu01.alicdn.com/img/ibank/O1CN01pBJL6R1bRBebmN6vC_!!2216396973461-0-cib.summ.jpg', 'size310x310ImageURI': 'https://cbu01.alicdn.com/img/ibank/O1CN01pBJL6R1bRBebmN6vC_!!2216396973461-0-cib.310x310.jpg', 'fullPathImageURI': 'https://cbu01.alicdn.com/img/ibank/O1CN01pBJL6R1bRBebmN6vC_!!2216396973461-0-cib.jpg'}, {'size220x220ImageURI': 'https://cbu01.alicdn.com/img/ibank/O1CN01LsxUw71bRBef3x8Eu_!!2216396973461-0-cib.220x220.jpg', 'imageURI': 'img/ibank/O1CN01LsxUw71bRBef3x8Eu_!!2216396973461-0-cib.jpg', 'searchImageURI': 'https://cbu01.alicdn.com/img/ibank/O1CN01LsxUw71bRBef3x8Eu_!!2216396973461-0-cib.search.jpg', 'summImageURI': 'https://cbu01.alicdn.com/img/ibank/O1CN01LsxUw71bRBef3x8Eu_!!2216396973461-0-cib.summ.jpg', 'size310x310ImageURI': 'https://cbu01.alicdn.com/img/ibank/O1CN01LsxUw71bRBef3x8Eu_!!2216396973461-0-cib.310x310.jpg', 'fullPathImageURI': 'https://cbu01.alicdn.com/img/ibank/O1CN01LsxUw71bRBef3x8Eu_!!2216396973461-0-cib.jpg'}], 'skumodel': {'sku_data': {'sku_property_name': {'sku1_property_name': '颜色', 'sku2_property_name': '颜色分类'}, 'sku_parameter': [{'remote_id': '734990688469_sexrRGp4rq', 'name': '艳冠群芳【中长】||【胶水款】', 'imageUrl': 'https://cbu01.alicdn.com/img/ibank/O1CN01OAQC9A1bRBef3wzwA_!!2216396973461-0-cib.jpg', 'price': '4.80', 'stock': 9551}, {'remote_id': '734990688469_DdT3wuRGFp', 'name': '艳冠群芳【中长】||五件套【果冻胶+胶水+指甲锉+酒精棉+木棒】', 'imageUrl': 'https://cbu01.alicdn.com/img/ibank/O1CN01OAQC9A1bRBef3wzwA_!!2216396973461-0-cib.jpg', 'price': '5.50', 'stock': 9948}, {'remote_id': '734990688469_urkiIjA35G', 'name': '黑碟银链【中长】||【胶水款】', 'imageUrl': 'https://cbu01.alicdn.com/img/ibank/O1CN01dUzuNc1bRBeZaYZM2_!!2216396973461-0-cib.jpg', 'price': '4.80', 'stock': 9956}, {'remote_id': '734990688469_2psUJdFEE6', 'name': '黑碟银链【中长】||五件套【果冻胶+胶水+指甲锉+酒精棉+木棒】', 'imageUrl': 'https://cbu01.alicdn.com/img/ibank/O1CN01dUzuNc1bRBeZaYZM2_!!2216396973461-0-cib.jpg', 'price': '5.50', 'stock': 9959}, {'remote_id': '734990688469_Ux0bADLW91', 'name': '蓝山茶花【中长】||【胶水款】', 'imageUrl': 'https://cbu01.alicdn.com/img/ibank/O1CN01pBJL6R1bRBebmN6vC_!!2216396973461-0-cib.jpg', 'price': '4.80', 'stock': 9957}, {'remote_id': '734990688469_158XL6EDQB', 'name': '蓝山茶花【中长】||五件套【果冻胶+胶水+指甲锉+酒精棉+木棒】', 'imageUrl': 'https://cbu01.alicdn.com/img/ibank/O1CN01pBJL6R1bRBebmN6vC_!!2216396973461-0-cib.jpg', 'price': '5.50', 'stock': 9959}, {'remote_id': '734990688469_kltlgPL6fz', 'name': '银河蝴蝶【中长】||【胶水款】', 'imageUrl': 'https://cbu01.alicdn.com/img/ibank/O1CN01ZdWuzE1bRBeYxzycQ_!!2216396973461-0-cib.jpg', 'price': '4.80', 'stock': 9960}, {'remote_id': '734990688469_F5m0Uoe4f0', 'name': '银河蝴蝶【中长】||五件套【果冻胶+胶水+指甲锉+酒精棉+木棒】', 'imageUrl': 'https://cbu01.alicdn.com/img/ibank/O1CN01ZdWuzE1bRBeYxzycQ_!!2216396973461-0-cib.jpg', 'price': '5.50', 'stock': 9959}, {'remote_id': '734990688469_RseGu0O7kK', 'name': '魔镜爱心【中长】||【胶水款】', 'imageUrl': 'https://cbu01.alicdn.com/img/ibank/O1CN01OQaWFT1bRBeg7LiTR_!!2216396973461-0-cib.jpg', 'price': '4.80', 'stock': 9958}, {'remote_id': '734990688469_oZspTsydql', 'name': '魔镜爱心【中长】||五件套【果冻胶+胶水+指甲锉+酒精棉+木棒】', 'imageUrl': 'https://cbu01.alicdn.com/img/ibank/O1CN01OQaWFT1bRBeg7LiTR_!!2216396973461-0-cib.jpg', 'price': '5.50', 'stock': 9960}, {'remote_id': '734990688469_QxeO67fTiT', 'name': '花飞碟舞【短款】||【胶水款】', 'imageUrl': 'https://cbu01.alicdn.com/img/ibank/O1CN01Pw3n1w1bRBeZaXYy3_!!2216396973461-0-cib.jpg', 'price': '4.80', 'stock': 9960}, {'remote_id': '734990688469_9fO2ycKTUF', 'name': '花飞碟舞【短款】||五件套【果冻胶+胶水+指甲锉+酒精棉+木棒】', 'imageUrl': 'https://cbu01.alicdn.com/img/ibank/O1CN01Pw3n1w1bRBeZaXYy3_!!2216396973461-0-cib.jpg', 'price': '5.50', 'stock': 9960}, {'remote_id': '734990688469_rPS7x5mhU0', 'name': '粉驹兔子【短款】||【胶水款】', 'imageUrl': 'https://cbu01.alicdn.com/img/ibank/O1CN01LoCWU21bRBeYy0Nb3_!!2216396973461-0-cib.jpg', 'price': '4.80', 'stock': 9958}, {'remote_id': '734990688469_fPUBp76nu4', 'name': '粉驹兔子【短款】||五件套【果冻胶+胶水+指甲锉+酒精棉+木棒】', 'imageUrl': 'https://cbu01.alicdn.com/img/ibank/O1CN01LoCWU21bRBeYy0Nb3_!!2216396973461-0-cib.jpg', 'price': '5.50', 'stock': 9960}, {'remote_id': '734990688469_SUp6APBRio', 'name': '法式蝴蝶【中长】||【胶水款】', 'imageUrl': 'https://cbu01.alicdn.com/img/ibank/O1CN01x9I7Mk1bRBeegV8Cq_!!2216396973461-0-cib.jpg', 'price': '3.90', 'stock': 9959}, {'remote_id': '734990688469_BXGvSRmPZc', 'name': '法式蝴蝶【中长】||五件套【果冻胶+胶水+指甲锉+酒精棉+木棒】', 'imageUrl': 'https://cbu01.alicdn.com/img/ibank/O1CN01x9I7Mk1bRBeegV8Cq_!!2216396973461-0-cib.jpg', 'price': '5.50', 'stock': 9960}, {'remote_id': '734990688469_I1EldLmbqS', 'name': '果冻葡萄【短款】||【胶水款】', 'imageUrl': 'https://cbu01.alicdn.com/img/ibank/O1CN01nssuzv1bRBeiJyL3v_!!2216396973461-0-cib.jpg', 'price': '3.90', 'stock': 9959}, {'remote_id': '734990688469_kdIwu7pMkl', 'name': '果冻葡萄【短款】||五件套【果冻胶+胶水+指甲锉+酒精棉+木棒】', 'imageUrl': 'https://cbu01.alicdn.com/img/ibank/O1CN01nssuzv1bRBeiJyL3v_!!2216396973461-0-cib.jpg', 'price': '5.50', 'stock': 9960}, {'remote_id': '734990688469_GetL9rrmjp', 'name': '蓝色爱心【中长】||【胶水款】', 'imageUrl': 'https://cbu01.alicdn.com/img/ibank/O1CN01Jq6HuS1bRBehThh9V_!!2216396973461-0-cib.jpg', 'price': '3.90', 'stock': 9958}, {'remote_id': '734990688469_zzHFKmYI1V', 'name': '蓝色爱心【中长】||五件套【果冻胶+胶水+指甲锉+酒精棉+木棒】', 'imageUrl': 'https://cbu01.alicdn.com/img/ibank/O1CN01Jq6HuS1bRBehThh9V_!!2216396973461-0-cib.jpg', 'price': '5.50', 'stock': 9859}, {'remote_id': '734990688469_5KpZJOn73b', 'name': '心心蝴蝶【短款】||【胶水款】', 'imageUrl': 'https://cbu01.alicdn.com/img/ibank/O1CN01LsxUw71bRBef3x8Eu_!!2216396973461-0-cib.jpg', 'price': '3.90', 'stock': 9960}, {'remote_id': '734990688469_fc3O4DysTd', 'name': '心心蝴蝶【短款】||五件套【果冻胶+胶水+指甲锉+酒精棉+木棒】', 'imageUrl': 'https://cbu01.alicdn.com/img/ibank/O1CN01LsxUw71bRBef3x8Eu_!!2216396973461-0-cib.jpg', 'price': '5.50', 'stock': 9960}, {'remote_id': '734990688469_RATtTu5BLT', 'name': '紫色云朵【中长】||【胶水款】', 'imageUrl': 'https://cbu01.alicdn.com/img/ibank/O1CN01sErJE91bRBebkyAh2_!!2216396973461-0-cib.jpg', 'price': '3.90', 'stock': 9960}, {'remote_id': '734990688469_szSQIucpJz', 'name': '紫色云朵【中长】||五件套【果冻胶+胶水+指甲锉+酒精棉+木棒】', 'imageUrl': 'https://cbu01.alicdn.com/img/ibank/O1CN01sErJE91bRBebkyAh2_!!2216396973461-0-cib.jpg', 'price': '5.50', 'stock': 9959}, {'remote_id': '734990688469_29kg3G2vyx', 'name': '芭蕾爱心【中长】||【胶水款】', 'imageUrl': 'https://cbu01.alicdn.com/img/ibank/O1CN01uXGDmv1bRBee1fxVm_!!2216396973461-0-cib.jpg', 'price': '3.90', 'stock': 9939}, {'remote_id': '734990688469_sKJgLtbUNU', 'name': '芭蕾爱心【中长】||五件套【果冻胶+胶水+指甲锉+酒精棉+木棒】', 'imageUrl': 'https://cbu01.alicdn.com/img/ibank/O1CN01uXGDmv1bRBee1fxVm_!!2216396973461-0-cib.jpg', 'price': '5.50', 'stock': 9960}, {'remote_id': '734990688469_xMye2LuwgJ', 'name': '月光晕染【短款】||【胶水款】', 'imageUrl': 'https://cbu01.alicdn.com/img/ibank/O1CN01pWsGIy1bRBeco4tep_!!2216396973461-0-cib.jpg', 'price': '3.90', 'stock': 9960}, {'remote_id': '734990688469_gYJVkMsj63', 'name': '月光晕染【短款】||五件套【果冻胶+胶水+指甲锉+酒精棉+木棒】', 'imageUrl': 'https://cbu01.alicdn.com/img/ibank/O1CN01pWsGIy1bRBeco4tep_!!2216396973461-0-cib.jpg', 'price': '5.50', 'stock': 9960}, {'remote_id': '734990688469_VXxPpmvKmm', 'name': '珍珠爱心【中长】||【胶水款】', 'imageUrl': 'https://cbu01.alicdn.com/img/ibank/O1CN01Qa5DyD1bRBegZGFCU_!!2216396973461-0-cib.jpg', 'price': '3.90', 'stock': 9960}, {'remote_id': '734990688469_wfzfNPwcaT', 'name': '珍珠爱心【中长】||五件套【果冻胶+胶水+指甲锉+酒精棉+木棒】', 'imageUrl': 'https://cbu01.alicdn.com/img/ibank/O1CN01Qa5DyD1bRBegZGFCU_!!2216396973461-0-cib.jpg', 'price': '5.50', 'stock': 9960}, {'remote_id': '734990688469_XN86urNyUy', 'name': '酒红银边【短款】||【胶水款】', 'imageUrl': 'https://cbu01.alicdn.com/img/ibank/O1CN01GuoCMU1bRBeT8LQRc_!!2216396973461-0-cib.jpg', 'price': '3.90', 'stock': 9960}, {'remote_id': '734990688469_FBtb7j3eL7', 'name': '酒红银边【短款】||五件套【果冻胶+胶水+指甲锉+酒精棉+木棒】', 'imageUrl': 'https://cbu01.alicdn.com/img/ibank/O1CN01GuoCMU1bRBeT8LQRc_!!2216396973461-0-cib.jpg', 'price': '5.50', 'stock': 9959}, {'remote_id': '734990688469_Roy0yHOyLp', 'name': '长岛冰茶【短款】||【胶水款】', 'imageUrl': 'https://cbu01.alicdn.com/img/ibank/O1CN01z6pXIY1bRBeT8NuK4_!!2216396973461-0-cib.jpg', 'price': '3.90', 'stock': 9960}, {'remote_id': '734990688469_Aiosl7rIS9', 'name': '长岛冰茶【短款】||五件套【果冻胶+胶水+指甲锉+酒精棉+木棒】', 'imageUrl': 'https://cbu01.alicdn.com/img/ibank/O1CN01z6pXIY1bRBeT8NuK4_!!2216396973461-0-cib.jpg', 'price': '4.60', 'stock': 9960}, {'remote_id': '734990688469_AOr0RHcpN7', 'name': '爱心腮红【中长】||【胶水款】', 'imageUrl': 'https://cbu01.alicdn.com/img/ibank/O1CN01XkTknF1bRBeiJxfSz_!!2216396973461-0-cib.jpg', 'price': '3.90', 'stock': 9960}, {'remote_id': '734990688469_kEri5KMByx', 'name': '爱心腮红【中长】||五件套【果冻胶+胶水+指甲锉+酒精棉+木棒】', 'imageUrl': 'https://cbu01.alicdn.com/img/ibank/O1CN01XkTknF1bRBeiJxfSz_!!2216396973461-0-cib.jpg', 'price': '4.60', 'stock': 9960}, {'remote_id': '734990688469_wvhsuOqU2n', 'name': '白边链条【长款】||【胶水款】', 'imageUrl': 'https://cbu01.alicdn.com/img/ibank/O1CN01YEYIGb1bRBi1PfLAn_!!2216396973461-0-cib.jpg', 'price': '5.80', 'stock': 9959}, {'remote_id': '734990688469_rWgoKBz5h8', 'name': '白边链条【长款】||五件套【果冻胶+胶水+指甲锉+酒精棉+木棒】', 'imageUrl': 'https://cbu01.alicdn.com/img/ibank/O1CN01YEYIGb1bRBi1PfLAn_!!2216396973461-0-cib.jpg', 'price': '6.50', 'stock': 10000}]}}, 'video': 'https://cloud.video.taobao.com/play/u/2216396973461/p/2/e/6/t/1/424655918454.mp4', 'details_text_description': ['品牌:null', '颜色:艳冠群芳【中长】,黑碟银链【中长】,蓝山茶花【中长】,银河蝴蝶【中长】,魔镜爱心【中长】,花飞碟舞【短款】,粉驹兔子【短款】,法式蝴蝶【中长】,果冻葡萄【短款】,蓝色爱心【中长】,心心蝴蝶【短款】,紫色云朵【中长】,芭蕾爱心【中长】,月光晕染【短款】,珍珠爱心【中长】,酒红银边【短款】,长岛冰茶【短款】,爱心腮红【中长】,白边链条【长款】', '颜色分类:【胶水款】,五件套【果冻胶+胶水+指甲锉+酒精棉+木棒】', '风格:甜美,辣妹,爆闪,简约,欧美,轻奢风,纯欲', '款式:长款,中款,穿戴式,芭蕾型', '图案:星空,蝴蝶', '品牌类型:国货品牌', '非特化妆品备案证号:无', '特殊用途化妆品:否', '适用人群:女士'], 'detailed_picture': ['https://cbu01.alicdn.com/img/ibank/O1CN01tXwDNU1bRBf25TRHe_!!2216396973461-0-cib.jpg', 'https://cbu01.alicdn.com/img/ibank/O1CN01hgWLXC1bRBf3BWR9k_!!2216396973461-0-cib.jpg', 'https://cbu01.alicdn.com/img/ibank/O1CN01tEJpyZ1bRBezyR5rS_!!2216396973461-0-cib.jpg', 'https://cbu01.alicdn.com/img/ibank/O1CN01jD1Q6R1bRBezyUeHG_!!2216396973461-0-cib.jpg', 'https://cbu01.alicdn.com/img/ibank/O1CN01nJZ7aX1bRBeyBxdBe_!!2216396973461-0-cib.jpg', 'https://cbu01.alicdn.com/img/ibank/O1CN01pQ5bCE1bRBf3BXurd_!!2216396973461-0-cib.jpg', 'https://cbu01.alicdn.com/img/ibank/O1CN01JYaxO21bRBf7hMT1r_!!2216396973461-0-cib.jpg', 'https://cbu01.alicdn.com/img/ibank/O1CN01PtVO1J1bRBf6mKtz7_!!2216396973461-0-cib.jpg', 'https://cbu01.alicdn.com/img/ibank/O1CN016yrgEN1bRBf8UFFlx_!!2216396973461-0-cib.jpg', 'https://cbu01.alicdn.com/img/ibank/O1CN01RVyCQH1bRBf37ncyo_!!2216396973461-0-cib.jpg', 'https://cbu01.alicdn.com/img/ibank/O1CN01w6WuLG1bRBf7hKBhP_!!2216396973461-0-cib.jpg']}}
    deepl_api = 'eaffb79e-edf7-447a-a76e-3e6ae3883e21'
    translator_deepl = Translator(tetx['data'], deepl_api)
    res = translator_deepl.process_all()
    print(tetx)
