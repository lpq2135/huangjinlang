import requests
import re
import hashlib
import logging
from copy import deepcopy
from concurrent.futures import ThreadPoolExecutor, as_completed
import concurrent.futures


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
                result = [i['text'] for i in response.json()["translations"]]
                return result
            except Exception as e:
                logging.warning(f"deepl翻译请求失败，尝试第{attempt}次. Error: {e}")
            attempt += 1
        raise Exception("deepl翻译请求失败")

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

    def split_list(self, input_list):
        # 将列表按照指定大小切分
        return [input_list[i:i + 50] for i in range(0, len(input_list), 50)]

    def process_skumodel(self):
        # 获取skumodel键下需要翻译的文本
        text = []
        for value in self.data['skumodel']['sku_data']['sku_property_name'].values():
            text.append(value)
        for i in self.data['skumodel']['sku_data']['sku_parameter']:
            text.append(i['name'])

        # 判断列表长度进行拆分
        sub_lists = self.split_list(text)
        text_lists = []
        for sub_list in sub_lists:
            text_lists.extend(self.translate_text_with_deepl(sub_list))

        # 开始依序替换原始数据
        keys = list(self.data['skumodel']['sku_data']['sku_property_name'].keys())
        for i, key in enumerate(keys):
            self.data['skumodel']['sku_data']['sku_property_name'][key] = text_lists[i]
        for i in range(len(tetx['data']['skumodel']['sku_data']['sku_parameter'])):
            self.data['skumodel']['sku_data']['sku_parameter'][i]['name'] = text_lists[i + len(keys)]

    def process_title(self):
        self.data['title'] = self.translate_text_with_deepl(self.data['title']) if self.is_chinese(self.data['title']) \
            else self.data['title']

    def process_details_text_description(self):
        # 获取skumodel键下需要翻译的文本
        text = self.data['details_text_description']

        # 判断列表长度进行拆分
        sub_lists = self.split_list(text)

        # 替换原始数据
        text_lists = []
        for sub_list in sub_lists:
            text_lists.extend(self.translate_text_with_deepl(sub_list))
        self.data['details_text_description'] = text_lists

    def process_all(self):
        self.process_title()
        self.process_skumodel()
        self.process_details_text_description()
        return self.data

tetx = {
  'status': True,
  'data': {
    'product_id': '771673382691',
    'specifications': 1,
    'start_amount': 1,
    'title': '学生迷你小型自动折叠洗衣机清洗内衣裤洗袜子机洗脱两用洗衣神器',
    'main_images': [
      {
        'size220x220ImageURI': 'https://cbu01.alicdn.com/img/ibank/O1CN017fRHBj2Nf1ETR8GbT_!!2217544969989-0-cib.220x220.jpg',
        'imageURI': 'img/ibank/O1CN017fRHBj2Nf1ETR8GbT_!!2217544969989-0-cib.jpg',
        'searchImageURI': 'https://cbu01.alicdn.com/img/ibank/O1CN017fRHBj2Nf1ETR8GbT_!!2217544969989-0-cib.search.jpg',
        'summImageURI': 'https://cbu01.alicdn.com/img/ibank/O1CN017fRHBj2Nf1ETR8GbT_!!2217544969989-0-cib.summ.jpg',
        'size310x310ImageURI': 'https://cbu01.alicdn.com/img/ibank/O1CN017fRHBj2Nf1ETR8GbT_!!2217544969989-0-cib.310x310.jpg',
        'fullPathImageURI': 'https://cbu01.alicdn.com/img/ibank/O1CN017fRHBj2Nf1ETR8GbT_!!2217544969989-0-cib.jpg'
      },
      {
        'size220x220ImageURI': 'https://cbu01.alicdn.com/img/ibank/O1CN0141JK3u2Nf1EWJh9E7_!!2217544969989-0-cib.220x220.jpg',
        'imageURI': 'img/ibank/O1CN0141JK3u2Nf1EWJh9E7_!!2217544969989-0-cib.jpg',
        'searchImageURI': 'https://cbu01.alicdn.com/img/ibank/O1CN0141JK3u2Nf1EWJh9E7_!!2217544969989-0-cib.search.jpg',
        'summImageURI': 'https://cbu01.alicdn.com/img/ibank/O1CN0141JK3u2Nf1EWJh9E7_!!2217544969989-0-cib.summ.jpg',
        'size310x310ImageURI': 'https://cbu01.alicdn.com/img/ibank/O1CN0141JK3u2Nf1EWJh9E7_!!2217544969989-0-cib.310x310.jpg',
        'fullPathImageURI': 'https://cbu01.alicdn.com/img/ibank/O1CN0141JK3u2Nf1EWJh9E7_!!2217544969989-0-cib.jpg'
      },
      {
        'size220x220ImageURI': 'https://cbu01.alicdn.com/img/ibank/O1CN01Ww4ILA2Nf1ERDaZcc_!!2217544969989-0-cib.220x220.jpg',
        'imageURI': 'img/ibank/O1CN01Ww4ILA2Nf1ERDaZcc_!!2217544969989-0-cib.jpg',
        'searchImageURI': 'https://cbu01.alicdn.com/img/ibank/O1CN01Ww4ILA2Nf1ERDaZcc_!!2217544969989-0-cib.search.jpg',
        'summImageURI': 'https://cbu01.alicdn.com/img/ibank/O1CN01Ww4ILA2Nf1ERDaZcc_!!2217544969989-0-cib.summ.jpg',
        'size310x310ImageURI': 'https://cbu01.alicdn.com/img/ibank/O1CN01Ww4ILA2Nf1ERDaZcc_!!2217544969989-0-cib.310x310.jpg',
        'fullPathImageURI': 'https://cbu01.alicdn.com/img/ibank/O1CN01Ww4ILA2Nf1ERDaZcc_!!2217544969989-0-cib.jpg'
      },
      {
        'size220x220ImageURI': 'https://cbu01.alicdn.com/img/ibank/O1CN01Io2kQm2Nf1EOzqrRL_!!2217544969989-0-cib.220x220.jpg',
        'imageURI': 'img/ibank/O1CN01Io2kQm2Nf1EOzqrRL_!!2217544969989-0-cib.jpg',
        'searchImageURI': 'https://cbu01.alicdn.com/img/ibank/O1CN01Io2kQm2Nf1EOzqrRL_!!2217544969989-0-cib.search.jpg',
        'summImageURI': 'https://cbu01.alicdn.com/img/ibank/O1CN01Io2kQm2Nf1EOzqrRL_!!2217544969989-0-cib.summ.jpg',
        'size310x310ImageURI': 'https://cbu01.alicdn.com/img/ibank/O1CN01Io2kQm2Nf1EOzqrRL_!!2217544969989-0-cib.310x310.jpg',
        'fullPathImageURI': 'https://cbu01.alicdn.com/img/ibank/O1CN01Io2kQm2Nf1EOzqrRL_!!2217544969989-0-cib.jpg'
      },
      {
        'size220x220ImageURI': 'https://cbu01.alicdn.com/img/ibank/O1CN01bBkeoO2Nf1EREt3t1_!!2217544969989-0-cib.220x220.jpg',
        'imageURI': 'img/ibank/O1CN01bBkeoO2Nf1EREt3t1_!!2217544969989-0-cib.jpg',
        'searchImageURI': 'https://cbu01.alicdn.com/img/ibank/O1CN01bBkeoO2Nf1EREt3t1_!!2217544969989-0-cib.search.jpg',
        'summImageURI': 'https://cbu01.alicdn.com/img/ibank/O1CN01bBkeoO2Nf1EREt3t1_!!2217544969989-0-cib.summ.jpg',
        'size310x310ImageURI': 'https://cbu01.alicdn.com/img/ibank/O1CN01bBkeoO2Nf1EREt3t1_!!2217544969989-0-cib.310x310.jpg',
        'fullPathImageURI': 'https://cbu01.alicdn.com/img/ibank/O1CN01bBkeoO2Nf1EREt3t1_!!2217544969989-0-cib.jpg'
      },
      {
        'size220x220ImageURI': 'https://cbu01.alicdn.com/img/ibank/O1CN01TYftHq2Nf1EO0k88I_!!2217544969989-0-cib.220x220.jpg',
        'imageURI': 'img/ibank/O1CN01TYftHq2Nf1EO0k88I_!!2217544969989-0-cib.jpg',
        'searchImageURI': 'https://cbu01.alicdn.com/img/ibank/O1CN01TYftHq2Nf1EO0k88I_!!2217544969989-0-cib.search.jpg',
        'summImageURI': 'https://cbu01.alicdn.com/img/ibank/O1CN01TYftHq2Nf1EO0k88I_!!2217544969989-0-cib.summ.jpg',
        'size310x310ImageURI': 'https://cbu01.alicdn.com/img/ibank/O1CN01TYftHq2Nf1EO0k88I_!!2217544969989-0-cib.310x310.jpg',
        'fullPathImageURI': 'https://cbu01.alicdn.com/img/ibank/O1CN01TYftHq2Nf1EO0k88I_!!2217544969989-0-cib.jpg'
      },
      {
        'size220x220ImageURI': 'https://cbu01.alicdn.com/img/ibank/O1CN01fU0cza2Nf1EVfQszI_!!2217544969989-0-cib.220x220.jpg',
        'imageURI': 'img/ibank/O1CN01fU0cza2Nf1EVfQszI_!!2217544969989-0-cib.jpg',
        'searchImageURI': 'https://cbu01.alicdn.com/img/ibank/O1CN01fU0cza2Nf1EVfQszI_!!2217544969989-0-cib.search.jpg',
        'summImageURI': 'https://cbu01.alicdn.com/img/ibank/O1CN01fU0cza2Nf1EVfQszI_!!2217544969989-0-cib.summ.jpg',
        'size310x310ImageURI': 'https://cbu01.alicdn.com/img/ibank/O1CN01fU0cza2Nf1EVfQszI_!!2217544969989-0-cib.310x310.jpg',
        'fullPathImageURI': 'https://cbu01.alicdn.com/img/ibank/O1CN01fU0cza2Nf1EVfQszI_!!2217544969989-0-cib.jpg'
      },
      {
        'size220x220ImageURI': 'https://cbu01.alicdn.com/img/ibank/O1CN01Hlvzmy2Nf1EP0OMUt_!!2217544969989-0-cib.220x220.jpg',
        'imageURI': 'img/ibank/O1CN01Hlvzmy2Nf1EP0OMUt_!!2217544969989-0-cib.jpg',
        'searchImageURI': 'https://cbu01.alicdn.com/img/ibank/O1CN01Hlvzmy2Nf1EP0OMUt_!!2217544969989-0-cib.search.jpg',
        'summImageURI': 'https://cbu01.alicdn.com/img/ibank/O1CN01Hlvzmy2Nf1EP0OMUt_!!2217544969989-0-cib.summ.jpg',
        'size310x310ImageURI': 'https://cbu01.alicdn.com/img/ibank/O1CN01Hlvzmy2Nf1EP0OMUt_!!2217544969989-0-cib.310x310.jpg',
        'fullPathImageURI': 'https://cbu01.alicdn.com/img/ibank/O1CN01Hlvzmy2Nf1EP0OMUt_!!2217544969989-0-cib.jpg'
      },
      {
        'size220x220ImageURI': 'https://cbu01.alicdn.com/img/ibank/O1CN01rvWXHv2Nf1ESynYYx_!!2217544969989-0-cib.220x220.jpg',
        'imageURI': 'img/ibank/O1CN01rvWXHv2Nf1ESynYYx_!!2217544969989-0-cib.jpg',
        'searchImageURI': 'https://cbu01.alicdn.com/img/ibank/O1CN01rvWXHv2Nf1ESynYYx_!!2217544969989-0-cib.search.jpg',
        'summImageURI': 'https://cbu01.alicdn.com/img/ibank/O1CN01rvWXHv2Nf1ESynYYx_!!2217544969989-0-cib.summ.jpg',
        'size310x310ImageURI': 'https://cbu01.alicdn.com/img/ibank/O1CN01rvWXHv2Nf1ESynYYx_!!2217544969989-0-cib.310x310.jpg',
        'fullPathImageURI': 'https://cbu01.alicdn.com/img/ibank/O1CN01rvWXHv2Nf1ESynYYx_!!2217544969989-0-cib.jpg'
      },
      {
        'size220x220ImageURI': 'https://cbu01.alicdn.com/img/ibank/O1CN01n3Omrd2Nf1ERzJOam_!!2217544969989-0-cib.220x220.jpg',
        'imageURI': 'img/ibank/O1CN01n3Omrd2Nf1ERzJOam_!!2217544969989-0-cib.jpg',
        'searchImageURI': 'https://cbu01.alicdn.com/img/ibank/O1CN01n3Omrd2Nf1ERzJOam_!!2217544969989-0-cib.search.jpg',
        'summImageURI': 'https://cbu01.alicdn.com/img/ibank/O1CN01n3Omrd2Nf1ERzJOam_!!2217544969989-0-cib.summ.jpg',
        'size310x310ImageURI': 'https://cbu01.alicdn.com/img/ibank/O1CN01n3Omrd2Nf1ERzJOam_!!2217544969989-0-cib.310x310.jpg',
        'fullPathImageURI': 'https://cbu01.alicdn.com/img/ibank/O1CN01n3Omrd2Nf1ERzJOam_!!2217544969989-0-cib.jpg'
      },
      {
        'size220x220ImageURI': 'https://cbu01.alicdn.com/img/ibank/O1CN01OKVxoS2Nf1EUvZKvO_!!2217544969989-0-cib.220x220.jpg',
        'imageURI': 'img/ibank/O1CN01OKVxoS2Nf1EUvZKvO_!!2217544969989-0-cib.jpg',
        'searchImageURI': 'https://cbu01.alicdn.com/img/ibank/O1CN01OKVxoS2Nf1EUvZKvO_!!2217544969989-0-cib.search.jpg',
        'summImageURI': 'https://cbu01.alicdn.com/img/ibank/O1CN01OKVxoS2Nf1EUvZKvO_!!2217544969989-0-cib.summ.jpg',
        'size310x310ImageURI': 'https://cbu01.alicdn.com/img/ibank/O1CN01OKVxoS2Nf1EUvZKvO_!!2217544969989-0-cib.310x310.jpg',
        'fullPathImageURI': 'https://cbu01.alicdn.com/img/ibank/O1CN01OKVxoS2Nf1EUvZKvO_!!2217544969989-0-cib.jpg'
      },
      {
        'size220x220ImageURI': 'https://cbu01.alicdn.com/img/ibank/O1CN01wi7fOX2Nf1EPQrnqH_!!2217544969989-0-cib.220x220.jpg',
        'imageURI': 'img/ibank/O1CN01wi7fOX2Nf1EPQrnqH_!!2217544969989-0-cib.jpg',
        'searchImageURI': 'https://cbu01.alicdn.com/img/ibank/O1CN01wi7fOX2Nf1EPQrnqH_!!2217544969989-0-cib.search.jpg',
        'summImageURI': 'https://cbu01.alicdn.com/img/ibank/O1CN01wi7fOX2Nf1EPQrnqH_!!2217544969989-0-cib.summ.jpg',
        'size310x310ImageURI': 'https://cbu01.alicdn.com/img/ibank/O1CN01wi7fOX2Nf1EPQrnqH_!!2217544969989-0-cib.310x310.jpg',
        'fullPathImageURI': 'https://cbu01.alicdn.com/img/ibank/O1CN01wi7fOX2Nf1EPQrnqH_!!2217544969989-0-cib.jpg'
      },
      {
        'size220x220ImageURI': 'https://cbu01.alicdn.com/img/ibank/O1CN01ZjXkzW2Nf1EO0gEfm_!!2217544969989-0-cib.220x220.jpg',
        'imageURI': 'img/ibank/O1CN01ZjXkzW2Nf1EO0gEfm_!!2217544969989-0-cib.jpg',
        'searchImageURI': 'https://cbu01.alicdn.com/img/ibank/O1CN01ZjXkzW2Nf1EO0gEfm_!!2217544969989-0-cib.search.jpg',
        'summImageURI': 'https://cbu01.alicdn.com/img/ibank/O1CN01ZjXkzW2Nf1EO0gEfm_!!2217544969989-0-cib.summ.jpg',
        'size310x310ImageURI': 'https://cbu01.alicdn.com/img/ibank/O1CN01ZjXkzW2Nf1EO0gEfm_!!2217544969989-0-cib.310x310.jpg',
        'fullPathImageURI': 'https://cbu01.alicdn.com/img/ibank/O1CN01ZjXkzW2Nf1EO0gEfm_!!2217544969989-0-cib.jpg'
      },
      {
        'size220x220ImageURI': 'https://cbu01.alicdn.com/img/ibank/O1CN01BWJm8M2Nf1ERFWOun_!!2217544969989-0-cib.220x220.jpg',
        'imageURI': 'img/ibank/O1CN01BWJm8M2Nf1ERFWOun_!!2217544969989-0-cib.jpg',
        'searchImageURI': 'https://cbu01.alicdn.com/img/ibank/O1CN01BWJm8M2Nf1ERFWOun_!!2217544969989-0-cib.search.jpg',
        'summImageURI': 'https://cbu01.alicdn.com/img/ibank/O1CN01BWJm8M2Nf1ERFWOun_!!2217544969989-0-cib.summ.jpg',
        'size310x310ImageURI': 'https://cbu01.alicdn.com/img/ibank/O1CN01BWJm8M2Nf1ERFWOun_!!2217544969989-0-cib.310x310.jpg',
        'fullPathImageURI': 'https://cbu01.alicdn.com/img/ibank/O1CN01BWJm8M2Nf1ERFWOun_!!2217544969989-0-cib.jpg'
      },
      {
        'size220x220ImageURI': 'https://cbu01.alicdn.com/img/ibank/O1CN01CbevmK2Nf1EO0k8CU_!!2217544969989-0-cib.220x220.jpg',
        'imageURI': 'img/ibank/O1CN01CbevmK2Nf1EO0k8CU_!!2217544969989-0-cib.jpg',
        'searchImageURI': 'https://cbu01.alicdn.com/img/ibank/O1CN01CbevmK2Nf1EO0k8CU_!!2217544969989-0-cib.search.jpg',
        'summImageURI': 'https://cbu01.alicdn.com/img/ibank/O1CN01CbevmK2Nf1EO0k8CU_!!2217544969989-0-cib.summ.jpg',
        'size310x310ImageURI': 'https://cbu01.alicdn.com/img/ibank/O1CN01CbevmK2Nf1EO0k8CU_!!2217544969989-0-cib.310x310.jpg',
        'fullPathImageURI': 'https://cbu01.alicdn.com/img/ibank/O1CN01CbevmK2Nf1EO0k8CU_!!2217544969989-0-cib.jpg'
      },
      {
        'size220x220ImageURI': 'https://cbu01.alicdn.com/img/ibank/O1CN01RVJiL82Nf1EP0CgMC_!!2217544969989-0-cib.220x220.jpg',
        'imageURI': 'img/ibank/O1CN01RVJiL82Nf1EP0CgMC_!!2217544969989-0-cib.jpg',
        'searchImageURI': 'https://cbu01.alicdn.com/img/ibank/O1CN01RVJiL82Nf1EP0CgMC_!!2217544969989-0-cib.search.jpg',
        'summImageURI': 'https://cbu01.alicdn.com/img/ibank/O1CN01RVJiL82Nf1EP0CgMC_!!2217544969989-0-cib.summ.jpg',
        'size310x310ImageURI': 'https://cbu01.alicdn.com/img/ibank/O1CN01RVJiL82Nf1EP0CgMC_!!2217544969989-0-cib.310x310.jpg',
        'fullPathImageURI': 'https://cbu01.alicdn.com/img/ibank/O1CN01RVJiL82Nf1EP0CgMC_!!2217544969989-0-cib.jpg'
      },
      {
        'size220x220ImageURI': 'https://cbu01.alicdn.com/img/ibank/O1CN01hGlRcs2Nf1ETeclQ5_!!2217544969989-0-cib.220x220.jpg',
        'imageURI': 'img/ibank/O1CN01hGlRcs2Nf1ETeclQ5_!!2217544969989-0-cib.jpg',
        'searchImageURI': 'https://cbu01.alicdn.com/img/ibank/O1CN01hGlRcs2Nf1ETeclQ5_!!2217544969989-0-cib.search.jpg',
        'summImageURI': 'https://cbu01.alicdn.com/img/ibank/O1CN01hGlRcs2Nf1ETeclQ5_!!2217544969989-0-cib.summ.jpg',
        'size310x310ImageURI': 'https://cbu01.alicdn.com/img/ibank/O1CN01hGlRcs2Nf1ETeclQ5_!!2217544969989-0-cib.310x310.jpg',
        'fullPathImageURI': 'https://cbu01.alicdn.com/img/ibank/O1CN01hGlRcs2Nf1ETeclQ5_!!2217544969989-0-cib.jpg'
      },
      {
        'size220x220ImageURI': 'https://cbu01.alicdn.com/img/ibank/O1CN01nyvxO02Nf1EP0GuOu_!!2217544969989-0-cib.220x220.jpg',
        'imageURI': 'img/ibank/O1CN01nyvxO02Nf1EP0GuOu_!!2217544969989-0-cib.jpg',
        'searchImageURI': 'https://cbu01.alicdn.com/img/ibank/O1CN01nyvxO02Nf1EP0GuOu_!!2217544969989-0-cib.search.jpg',
        'summImageURI': 'https://cbu01.alicdn.com/img/ibank/O1CN01nyvxO02Nf1EP0GuOu_!!2217544969989-0-cib.summ.jpg',
        'size310x310ImageURI': 'https://cbu01.alicdn.com/img/ibank/O1CN01nyvxO02Nf1EP0GuOu_!!2217544969989-0-cib.310x310.jpg',
        'fullPathImageURI': 'https://cbu01.alicdn.com/img/ibank/O1CN01nyvxO02Nf1EP0GuOu_!!2217544969989-0-cib.jpg'
      },
      {
        'size220x220ImageURI': 'https://cbu01.alicdn.com/img/ibank/O1CN01WBtyx82Nf1EVfLRh9_!!2217544969989-0-cib.220x220.jpg',
        'imageURI': 'img/ibank/O1CN01WBtyx82Nf1EVfLRh9_!!2217544969989-0-cib.jpg',
        'searchImageURI': 'https://cbu01.alicdn.com/img/ibank/O1CN01WBtyx82Nf1EVfLRh9_!!2217544969989-0-cib.search.jpg',
        'summImageURI': 'https://cbu01.alicdn.com/img/ibank/O1CN01WBtyx82Nf1EVfLRh9_!!2217544969989-0-cib.summ.jpg',
        'size310x310ImageURI': 'https://cbu01.alicdn.com/img/ibank/O1CN01WBtyx82Nf1EVfLRh9_!!2217544969989-0-cib.310x310.jpg',
        'fullPathImageURI': 'https://cbu01.alicdn.com/img/ibank/O1CN01WBtyx82Nf1EVfLRh9_!!2217544969989-0-cib.jpg'
      }
    ],
    'skumodel': {
      'sku_data': {
        'sku_property_name': {
          'sku1_property_name': '颜色'
        },
        'sku_parameter': [
          {
            'remote_id': '771673382691_pLem9M2IHD',
            'name': '4L【 洗衣机+沥水篮+排水+蓝光+定时+直流电源】蓝色',
            'imageUrl': 'https://cbu01.alicdn.com/img/ibank/O1CN01RVJiL82Nf1EP0CgMC_!!2217544969989-0-cib.jpg',
            'price': '39.90',
            'stock': 4736
          },
          {
            'remote_id': '771673382691_fZosay5khC',
            'name': '4L【 洗衣机+沥水篮+排水+蓝光+定时+直流电源】绿色',
            'imageUrl': 'https://cbu01.alicdn.com/img/ibank/O1CN01hGlRcs2Nf1ETeclQ5_!!2217544969989-0-cib.jpg',
            'price': '39.90',
            'stock': 4867
          },
          {
            'remote_id': '771673382691_Y4HtLvCGYW',
            'name': '4L【 洗衣机+沥水篮+排水+蓝光+定时+直流电源】粉色',
            'imageUrl': 'https://cbu01.alicdn.com/img/ibank/O1CN01nyvxO02Nf1EP0GuOu_!!2217544969989-0-cib.jpg',
            'price': '39.90',
            'stock': 4938
          },
          {
            'remote_id': '771673382691_wxa4UqK3Xf',
            'name': '【专用款】洗衣机洗涤专用粘毛器',
            'imageUrl': 'https://cbu01.alicdn.com/img/ibank/O1CN01CbevmK2Nf1EO0k8CU_!!2217544969989-0-cib.jpg',
            'price': '8.18',
            'stock': 4665
          },
          {
            'remote_id': '771673382691_ITQNNOMH2w',
            'name': '单独沥水篮【无机器+洗衣机配件】',
            'imageUrl': 'https://cbu01.alicdn.com/img/ibank/O1CN01fU0cza2Nf1EVfQszI_!!2217544969989-0-cib.jpg',
            'price': '11.90',
            'stock': 4991
          }
        ]
      }
    },
    'video': 'https://cloud.video.taobao.com/play/u/2217544969989/p/2/e/6/t/1/452076326629.mp4',
    'details_text_description': [
      '洗涤容量:2kg以下',
      '电源方式:插电式',
      '能效等级:1级',
      '高度:70.1-75cm',
      '电机类型:定频',
      '宽度:29*29cm',
      '深度:50.1cm以下;',
      '材质:塑料,树脂',
      '功能:可旋转',
      '产品规格:29*29',
      '颜色:4L【 洗衣机+沥水篮+排水+蓝光+定时+直流电源】蓝色,4L【 洗衣机+沥水篮+排水+蓝光+定时+直流电源】绿色,4L【 洗衣机+沥水篮+排水+蓝光+定时+直流电源】粉色,8.5L【 洗衣机+沥水篮+排水+蓝光+定时+直流电源】蓝色,8.5L【 洗衣机+沥水篮+排水+蓝光+定时+直流电源】绿色,8.5L【 洗衣机+沥水篮+排水+蓝光+定时+直流电源】粉色,8.5L【 洗衣机+沥水篮+排水+蓝光+定时+USB电源】蓝色,8.5L【 洗衣机+沥水篮+排水+蓝光+定时+USB电源】绿色,8.5L【 洗衣机+沥水篮+排水+蓝光+定时+USB电源】粉色,8.5L【 洗衣机+沥水篮+排水+蓝光+定时+双供电（直流电源+USB）】蓝色,8.5L【 洗衣机+沥水篮+排水+蓝光+定时+双供电（直流电源+USB）】绿色,8.5L【 洗衣机+沥水篮+排水+蓝光+定时+双供电（直流电源+USB）】粉色,【专用款】洗衣机洗涤专用粘毛器,单独沥水篮【无机器+洗衣机配件】',
      '重量:2kg',
      '品牌:悠汇',
      '3C证书编号:2019010713148672',
      '产品类别:家用清洁',
      '物流服务:物流点自提',
      '型号:008',
      '包装清单:单个包装',
      '成色:全新'
    ],
    'detailed_picture': [
      'https://cbu01.alicdn.com/img/ibank/O1CN01pzyCV52Nf1EVfjofk_!!2217544969989-0-cib.jpg',
      'https://cbu01.alicdn.com/img/ibank/O1CN01YLYTIg2Nf1ESzHpbp_!!2217544969989-0-cib.jpg',
      'https://cbu01.alicdn.com/img/ibank/O1CN01liNji12Nf1EO12vWL_!!2217544969989-0-cib.jpg',
      'https://cbu01.alicdn.com/img/ibank/O1CN019hQ9HQ2Nf1EP0k7BM_!!2217544969989-0-cib.jpg',
      'https://cbu01.alicdn.com/img/ibank/O1CN019FSEjO2Nf1EPRMLd7_!!2217544969989-0-cib.jpg',
      'https://cbu01.alicdn.com/img/ibank/O1CN01ZHnDjN2Nf1ES4GKHA_!!2217544969989-0-cib.jpg',
      'https://cbu01.alicdn.com/img/ibank/O1CN01ZooyXH2Nf1EVflMLL_!!2217544969989-0-cib.jpg',
      'https://cbu01.alicdn.com/img/ibank/O1CN01M54Zj02Nf1ES4EBEz_!!2217544969989-0-cib.jpg',
      'https://cbu01.alicdn.com/img/ibank/O1CN01iwHuO22Nf1ERFnaeY_!!2217544969989-0-cib.jpg',
      'https://cbu01.alicdn.com/img/ibank/O1CN01bonTh02Nf1EO117J3_!!2217544969989-0-cib.jpg',
      'https://cbu01.alicdn.com/img/ibank/O1CN016vyKAx2Nf1ETS3fPq_!!2217544969989-0-cib.jpg',
      'https://cbu01.alicdn.com/img/ibank/O1CN01CsHTex2Nf1ETS5sbY_!!2217544969989-0-cib.jpg',
      'https://cbu01.alicdn.com/img/ibank/O1CN01UwSBdR2Nf1EUXdnQA_!!2217544969989-0-cib.jpg',
      'https://cbu01.alicdn.com/img/ibank/O1CN01fdIDWN2Nf1EWKbTJc_!!2217544969989-0-cib.jpg',
      'https://cbu01.alicdn.com/img/ibank/O1CN01mAhrAO2Nf1EWKcwpE_!!2217544969989-0-cib.jpg',
      'https://cbu01.alicdn.com/img/ibank/O1CN01Nze8lu2Nf1EWKcwpP_!!2217544969989-0-cib.jpg',
      'https://cbu01.alicdn.com/img/ibank/O1CN01Ojb2Sn2Nf1EUvv5Yl_!!2217544969989-0-cib.jpg',
      'https://cbu01.alicdn.com/img/ibank/O1CN01REaXLg2Nf1ETS6cM8_!!2217544969989-0-cib.jpg',
      'https://cbu01.alicdn.com/img/ibank/O1CN01JXzDXF2Nf1EREYj1h_!!2217544969989-0-cib.jpg'
    ]
  }
}
deepl_api = 'eaffb79e-edf7-447a-a76e-3e6ae3883e21'
translator_deepl = Translator(tetx['data'], deepl_api)
res = translator_deepl.process_title()
print(tetx)



