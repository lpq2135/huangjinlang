import requests
import re
import hashlib
import logging
from copy import deepcopy
from concurrent.futures import ThreadPoolExecutor, as_completed
import concurrent.futures


class Translator:
    def __init__(self, data=None):
        self.data = data

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
        auth_key = "a6434d71-4d86-4ef8-bdfd-6faebcd0008a"  # Replace with your key
        deepl_url = "https://api.deepl.com/v2/translate"
        data = {
            'auth_key': auth_key,
            'text': text,
            'source_lang': 'ZH',
            'target_lang': 'EN'
        }
        for _ in range(5):
            try:
                response = requests.post(deepl_url, data=data).json()
                if 'text' in response["translations"][0]:
                    result = response["translations"][0]["text"]
                    if self.is_chinese(result) is False:
                        return (self.remove_last_dot(result)).title()
            except Exception as e:
                logging.warning(f"deepl翻译请求失败，尝试第{_ + 1}次. Error: {e}")
        raise Exception("deepl翻译请求失败")

    def get_proxy(self):
        juliang_url = 'https://v2.api.juliangip.com/unlimited/getips?auto_white=1&num=10&pt=1&result_type=json&trade_no=5551379604897883&sign=f1448f67995d2b956efa78fda1d30a8c'
        result = requests.get(juliang_url).json()
        return result['data']['proxy_list']

    def remove_last_dot(self, str):
        if str[-1] == '.':
            return str[:-1]
        else:
            return str

    def is_chinese(self, check_str):
        for ch in check_str:
            if ('\u4e00' <= ch <= '\u9fff') and ch != '，':
                return True
        return False

    def process_sku_property_name(self):
        if 'sku_property_name' in self.data['skumodel']['sku_data']:
            data_mew = self.data['skumodel']['sku_data']['sku_property_name']
            count = 1
            for key, value in data_mew.items():
                if self.is_chinese(value):
                    translated_value = self.translate_text_with_deepl(value).lower()
                    if 'colour' in translated_value or 'color' in translated_value:
                        data_mew[key] = 'color_family'
                    elif 'size' in translated_value:
                        data_mew[key] = 'size'
                    else:
                        translated_value = re.sub(r' +', '_', self.translate_text_with_deepl(value))
                        if len(translated_value) > 15:
                            data_mew[key] = f'variants_{count}'
                        else:
                            data_mew[key] = translated_value
                    count += 1
                else:
                    value1 = re.sub(r' +', '_', value)
                    if len(value1) > 15:
                        data_mew[key] = f'variants_{count}'
                        count += 1
                    else:
                        data_mew[key] = value1

    def process_sku_parameter(self):
        specifications = self.data['specifications']
        if specifications >= 1:
            with ThreadPoolExecutor(max_workers=3) as executor:
                if specifications == 1:
                    new_params = []
                    futures = {}
                    for param in self.data['skumodel']['sku_data']['sku_parameter']:
                        new_param = deepcopy(param)
                        new_params.append(new_param)
                        if self.is_chinese(new_param['name']):
                            future = executor.submit(self.translate_text_with_deepl, new_param['name'])
                            futures[future] = new_param
                    for future in as_completed(futures):
                        new_param = futures[future]
                        new_param['name'] = future.result()
                    self.data['skumodel']['sku_data']['sku_parameter'] = new_params

                elif specifications == 2:
                    new_params = []
                    future_to_param_and_original = dict()
                    translated_values = dict()
                    for param in self.data['skumodel']['sku_data']['sku_parameter']:
                        new_param = deepcopy(param)
                        new_params.append(new_param)
                        sku1_value, sku2_value = new_param['name'].split('||')
                        if self.is_chinese(sku1_value) and sku1_value not in translated_values:
                            future = executor.submit(self.translate_text_with_deepl, sku1_value)
                            future_to_param_and_original[future] = (new_param, sku1_value)
                        if self.is_chinese(sku2_value) and sku2_value not in translated_values:
                            future = executor.submit(self.translate_text_with_deepl, sku2_value)
                            future_to_param_and_original[future] = (new_param, sku2_value)
                    for future in as_completed(future_to_param_and_original.keys()):
                        result = future.result()
                        param, original_value = future_to_param_and_original[future]
                        param['name'] = param['name'].replace(original_value, result)
                        translated_values[original_value] = result
                    for new_param in new_params:
                        sku1_value, sku2_value = new_param['name'].split('||')
                        if sku1_value in translated_values:
                            sku1_value = translated_values[sku1_value]
                        if sku2_value in translated_values:
                            sku2_value = translated_values[sku2_value]
                        new_param['name'] = sku1_value + '||' + sku2_value
                    self.data['skumodel']['sku_data']['sku_parameter'] = new_params

    def process_title(self):
        self.data['title'] = self.translate_text_with_deepl(self.data['title']) if self.is_chinese(self.data['title']) \
            else self.data['title']

    def process_details_text_description(self):
        new = []
        for i in self.data['details_text_description']:
            if self.is_chinese(i):
                new.append(self.remove_last_dot(((self.translate_text_with_deepl(i)).replace(':', ': ').replace(":  ", ": "))))
            else:
                new.append(i)
        self.data['details_text_description'] = new

    def process_all(self):
        try:
            with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
                futures = {executor.submit(self.process_sku_property_name),
                           executor.submit(self.process_sku_parameter),
                           executor.submit(self.process_title),
                           executor.submit(self.process_details_text_description)}
                for future in futures:
                    future.result()
        except Exception as error:
            logging.warning("搜狗翻译多线程错误捕获: ", error)
            return False

        return self.data
