import requests
from urllib import parse
import time
import re
import execjs
from pprint import pprint
import base64


# 获取签名
def get_sign(p):
    with open(r'C:\Users\Administrator\PycharmProjects\pythonProject\huangjinlang\lpq577_code\配置文件\1688js算法.js', 'r', encoding='utf-8') as f:
        ctx = execjs.compile(f.read())  # 执行读取的js代码
    return ctx.call('i', p)


if __name__ == '__main__':
    headers = {
        'cookie': 'leftMenuLastMode=EXPEND; cna=/ZgsILa4Ex8CAXUYedIwlBSS; leftMenuModeTip=shown; __cn_logon__=false; cookie2=1330f9bf7b87d465f47014068c518b0e; t=c5e9919f6bc95a5d20cf2bd326f32f19; _tb_token_=e1aad0e9e63bf; xlly_s=1; _m_h5_c=5f9ac72146280a761babff2fabef43a2_1739774402949%3Bab39bedea8d006b2e447c45e92c8fc6e; taklid=0e0e2e5af334477f8d1f3a2232c90b80; _csrf_token=1739783015295; mtop_partitioned_detect=1; _m_h5_tk=056d708190b3cb2fd9af7af7b0df97e9_1739798549005; _m_h5_tk_enc=3c42f5bb05a5530415e7086924d734ae; x5sec=7b22733b32223a2266363264376161653637383233313439222c22617365727665723b33223a22307c434f32707a4c3047454c4c52757338454d4f6239317358382f2f2f2f2f77453d227d; isg=BIiIZwotexhrkZedQpkmMQp0WfaaMew7sdtj2UI55IP2HSmH6kTey6ZWlfVtLaQT; tfstk=gZcEmmvBYBdexqGeqPVPQ6kNDtFLwWxfKbZ7r40uRkqHpvwoQzafqg0kv0lzj0r7VWxdz7oZfvNS-UCrb4m2JztKNcRrbmDCV4c7rboTt8HQVkZza4n25nOXG23Lw-xXcIOaxjnYtyfht_YusyUD5yYb6yOLw7xXfIOjJ2F-D1XU4D0M7za5qzmuElfgol4hEzmujR40lMVuZ0YaIyalxufhtObgzlquZ7moSFzSwUunr1zbKUopmRXBt1w3m2qNZs7Y8J2DMlflrf4E7o0hI_fo_yyEw69ZrqyIEqexO4RP6WgqI54rwEXz4-koO5cHjI2TEfmgSDT5ePkrrjFLdZCx0WoznX2Nrs0LakPaSjY5HlGaA0cUIE14F5cbnWD6BHw7Troo9D7PZm0slXetanSg2vaYszlJoTrzEgS12P2ncbHFqTy3WPrX7Fkk4eHU0j5KITB8ISUaceaCeTe3WPrXRy6ReR4Y7oTQR; _user_vitals_session_data_={"user_line_track":true,"ul_session_id":"71jcw26ib3e","last_page_id":"air.1688.com%2Fuycrjccikq"}',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/95.0.4638.54 Safari/537.36'
    }
    data = {"sceneSearchParamStr":"{\"keyword\":\"手机壳\",\"pageSize\":50,\"pageIndex\":1,\"filter\":[],\"sortModel\":\"\",\"sceneCode\":\"\",\"searchMode\":\"KEYWORD_SEARCH\"}"}
    token = re.findall('_m_h5_tk=(.+?)_', headers['cookie'], re.S)[0]
    appKey = "12574478"
    # 时间戳
    t = int(time.time() * 1000)
    p = (token + '&' + str(t) + '&' + appKey + '&' + str(data))
    sign = get_sign(p)
    url = f'https://h5api.m.1688.com/h5/mtop.cbu.distribute.selection.scenesearch/1.0/?jsv=2.7.0&appKey=12574478&t={str(t)}&sign={sign}&v=1.0&ecode=1&type=originaljson&dataType=jsonp&timeout=20000&api=mtop.cbu.distribute.selection.sceneSearch&preventFallback=true'
    headers = {
        'content-type': 'application/x-www-form-urlencoded',
        'cookie': 'leftMenuLastMode=EXPEND; cna=/ZgsILa4Ex8CAXUYedIwlBSS; leftMenuModeTip=shown; __cn_logon__=false; cookie2=1330f9bf7b87d465f47014068c518b0e; t=c5e9919f6bc95a5d20cf2bd326f32f19; _tb_token_=e1aad0e9e63bf; xlly_s=1; _m_h5_c=5f9ac72146280a761babff2fabef43a2_1739774402949%3Bab39bedea8d006b2e447c45e92c8fc6e; taklid=0e0e2e5af334477f8d1f3a2232c90b80; _csrf_token=1739783015295; mtop_partitioned_detect=1; _m_h5_tk=056d708190b3cb2fd9af7af7b0df97e9_1739798549005; _m_h5_tk_enc=3c42f5bb05a5530415e7086924d734ae; x5sec=7b22733b32223a2266363264376161653637383233313439222c22617365727665723b33223a22307c434f32707a4c3047454c4c52757338454d4f6239317358382f2f2f2f2f77453d227d; isg=BIiIZwotexhrkZedQpkmMQp0WfaaMew7sdtj2UI55IP2HSmH6kTey6ZWlfVtLaQT; tfstk=gZcEmmvBYBdexqGeqPVPQ6kNDtFLwWxfKbZ7r40uRkqHpvwoQzafqg0kv0lzj0r7VWxdz7oZfvNS-UCrb4m2JztKNcRrbmDCV4c7rboTt8HQVkZza4n25nOXG23Lw-xXcIOaxjnYtyfht_YusyUD5yYb6yOLw7xXfIOjJ2F-D1XU4D0M7za5qzmuElfgol4hEzmujR40lMVuZ0YaIyalxufhtObgzlquZ7moSFzSwUunr1zbKUopmRXBt1w3m2qNZs7Y8J2DMlflrf4E7o0hI_fo_yyEw69ZrqyIEqexO4RP6WgqI54rwEXz4-koO5cHjI2TEfmgSDT5ePkrrjFLdZCx0WoznX2Nrs0LakPaSjY5HlGaA0cUIE14F5cbnWD6BHw7Troo9D7PZm0slXetanSg2vaYszlJoTrzEgS12P2ncbHFqTy3WPrX7Fkk4eHU0j5KITB8ISUaceaCeTe3WPrXRy6ReR4Y7oTQR; _user_vitals_session_data_={"user_line_track":true,"ul_session_id":"71jcw26ib3e","last_page_id":"air.1688.com%2Fuycrjccikq"}',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.0.0 Safari/537.36'
    }
    pyload = "data=" + parse.quote(str(data))
    response = requests.request("POST", url, headers=headers, data=pyload).json()
    pprint(response)