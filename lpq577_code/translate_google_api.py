import requests
import re
import logging


def translated_content(text, target_language):
    """谷歌翻译api破解版"""
    headers = {
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
        "accept-language": "en,zh-CN;q=0.9,zh;q=0.8",
        "content-type": "application/x-www-form-urlencoded;charset=UTF-8",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.66 Safari/537.36",
    }
    # 请求url
    url = "https://translate.google.com/_/TranslateWebserverUi/data/batchexecute?rpcids=MkEWBc&f.sid=-2609060161424095358&bl=boq_translate-webserver_20201203.07_p0&hl=zh-CN&soc-app=1&soc-platform=1&soc-device=1&_reqid=359373&rt=c"
    # 数据参数
    from_data = {
        "f.req": r"""[[["MkEWBc","[[\"{}\",\"auto\",\"{}\",true],[null]]",null,"generic"]]]""".format(
            text, target_language
        )
    }
    try:
        response = requests.post(url, headers=headers, data=from_data, timeout=30)
        if response.status_code == 200:
            # 正则匹配结果
            result = re.findall(r'(?<=\[\[\\").*?(?=\\")', response.text)
            return result[0]
    except Exception as e:
        logging.warning(e)
        return False


# 翻译各个国家语言
if __name__ == "__main__":
    result = translated_content(
        "床上用品纯棉a类全棉色织水洗布料纯棉面料条格日式无印面料批发", "ur"
    )
    print(result)
