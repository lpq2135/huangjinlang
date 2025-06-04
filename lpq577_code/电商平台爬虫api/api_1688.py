import json
import logging
import random
import re
from io import BytesIO

from PIL import Image
from bs4 import BeautifulSoup
from lpq577_code.电商平台爬虫api.basic_assistanc import BaseCrawler

# from .basic_assistanc import BaseCrawler

class Alibaba(BaseCrawler):
    """
    此类用于获取1688商品详情返回指定的数据包
    -1: 未知错误
    0: 请求成功
    1: 商品已下架或离线
    2: sku无主图
    3: 主图异常
    4: 商品数据包异常
    5: sku规格数超出
    6: 商品详情异常
    """

    def __init__(self, product_id=None):
        self.product_id = product_id
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
        }
        self.source = None

    def get_data_packet_by_1688(self):
        """获取1688商品数据包"""
        try:
            request_url = f"https://m.1688.com/offer/{self.product_id}.htm"
            response = self.request_function(request_url, headers=self.headers).text
            if "下架商品页面" in response or "无法查看或已下架" in response:
                return None
            sku_source = re.findall(r"(?<=window\.__INIT_DATA=).*", response)[0]
            return json.loads(sku_source)
        except Exception as e:
            logging.warning(f"1688链接请求错误: {str(e)}")
            return None

    def first_non_empty_item_in_data(self, name=None):
        """遍历找到指定的数据"""
        for key in self.source["data"]:
            if "data" in self.source["data"][key]:
                data = self.source["data"][key]["data"]
                if name in (data if isinstance(data, dict) else data[0]):
                    return data

    def get_title(self):
        """获取标题并进行处理"""
        title_word_replacement = [
            "厂家",
            "供应",
            "销售",
            "规格",
            "齐全",
            "现货",
            "发货",
            "促销",
            "生产",
            "东莞",
            "武汉",
            "地区",
            "成都",
            "跨境",
            "批发",
            "直发",
            "量大从优",
        ]
        # title_word_prohibited = ['YSL', 'Yves', 'Saint', 'Laurent', '布裏奧尼', 'Brioni', '克裏斯多福', 'Christopher', 'Kane', '寶曼蘭朵', 'Pomellato', '雅典錶', 'Ulysse', 'Nardin', '芝柏錶', 'Girard', 'Perregaux', '尚維沙', 'JeanRichard', '麒麟珠寶', 'Qeelin', 'PUMA', 'GUCCI', '塞喬羅希', 'Sergio', 'Rossi', '寶詩龍', 'Boucheron', '亞歷山大', '麥昆', 'Alexander', 'McQueen', '寶緹嘉', 'Bottega', 'Veneta', '巴黎世家', 'Balenciaga', '三宅', 'BAOBAO', 'NIKE', 'Adidas', '勞力士', '雙B', 'BB', 'B字母', 'Paris', '真皮', 'G家', 'G字', 'B家', 'B字', 'P家', 'P字', 'R牌', '正品', '大牌', '潮牌', '奢侈', '字母', '牛津樹', 'Branches', 'Scholastic', '學樂', '倖存者', 'Atelier', '細胞素', '精華液', '溶色霜', '內褲超人', 'Phonics', '黑枸杞', '桑葚', '玫瑰花', '茶包', '瑞邁特', '呼吸機', '微風芯', '蜥蜴', '另類寵物', '鬃獅', '瑞士勞', '勞力', '浪琴', '保暖', '加絨', 'houmai', '潤眼膜', '眼袋', '美瞳片', '隱形眼鏡', '煙嘴', '淨菸器', '保健貼', '戒煙神器', '普洱茶', '七子餅', '向物', '早c晚a', '電子煙', '香煙', '香菸', 'voopoo', 'Hitaste', '悅客', '精工芯', 'Jellybox', 'CISOO', 'HeBat', 'lana', 'motx', 'relx', 'SALT', 'SHAQ', 'Nfix', 'novo', '丁鹽', '小煙套裝', '加熱菸', '加熱煙', '尼古丁鹽', '瓦拉丁', '咖哩棒', '思博瑞', '悅克', '悅刻', '菸油', '煙油', '菸彈', '煙彈', '菸蛋', '電子果汁', '哩亞', '鯊克', '鹽博士', '霧化芯', '烤菸器', '烤煙器', 'SHAO', '空油倉', '成品芯', '微風', '海神', '宙斯', 'zeus', 'GG2GK', 'nord', '帕Po拉RD德', 'O起xv源a', '鸚B', '鵡V', '螺C', 'pnp', 'tpp', '卡裏蹦', 'warlock', 'peas', '霧化口服液', '霧化器', '暴脾氣', '鹽立方', 'VGOD鹽', '皮卡丘七彩杯', 'Vavape', '廚師佳釀', 'Dotmod', '草本鹽彈', 'Yooz', 'Moti', '魔笛', 'nevoks', 'ILIA', 'IQOS', 'LEME', 'nrx', 'sp2', 'SP2S', 'spacesmoke', 'smoke', 'vape', '大煙', '小煙', '尼古丁', '尼威', '石中劍', '沙小', '彩鯊', '殺小', '喜貝', '電子蒸汽', '電子蒸氣', '糖果主機', '鹽油', 'HALO鹽', '沙克', '北極鹽', '鹽語', '檸檬之淚', '茶語', '老冰棍', '居家擴香瓶', '味覺達人', 'BAOS', 'Smok', '熱芯', 'cosmo', '霧化', '發熱芯', '一代二代', '氣pro泡', 'pal', 'Aegis', '菲林', '佩奇', 'pops', '自由派', '果凍盒子', '酪梨寶寶', '克萊普頓', 'IUO', '寶家', 'mighty', '威猛機器人', '火表', '彩程', '生茶', '純艾', '艾灸', '艾草', '艾柱', '蘄艾', '艾條', '試紙檢測', '尿液', '尿酮', '肌酐', '橡皮糖', '軟糖', '油糖', '混裝糖', '理療儀', '電療器', '隱血', '尿常規', 'hiv', 'hpv', '唇蜜', '唇釉', '棒棒糖', '口紅', 'burberry', 'Butterfly', 'Device', '雙G', 'MARMONT', '膨大海', '咽炎', '羅漢果', '清肺茶', '菊花茶', '甘草', '潤肺', '清肺', '金銀花', '枇杷', '雪梨茶', 'YSL/y/s/l', '鮮蔬', '香菇', '麻鴨', '臘鴨', '臘味', '鹽焗', '鹹鴨', '風乾', '翅膀', '板鴨', '手撕', '鎖鮮', '鴨脖', '粽子', '餡料', '高湯', '自熱', '燒烤', '火鍋', '自助', '速食', '牛肚', '麻辣', '夜宵', '友味來', '百草味', '秘制', '味道', '秋林', '裡道斯', '巨型大禮包', '免疫', '蚊香', '風味', 'iqos周邊', '滅火藥劑', '玩具刀', 'koko2', '緩眼疲勞', 'rizoma', '茯苓丸', '諾孕酮', '木瓜葛根', '雲南白藥', '糖果杆', '奇力', '毒品及吸毒用品', '蟑飛', '虎指', 'Tifany', '卡西歐', 'PHILIPPE', '武器', '便祕排毒', '血糖機', '鴛鴦刀', '傲勝', '薑黃素', 'IWC', '植物', '益芳', 'temani', '必理痛', 'y家', '滅蟑乳', '減肥', '透骨', '風濕膏', 'Marni', '三體', 'ejuice', '弓城', '卡柄槍', 'MARGIELA', '除毛機', '活血', '數位攝影機', '沖洗液', '專利', '馬吉拉', '逍遙', '水量計', '溫補腎陽', '海狗丸', '睪丸', '排泄物', '簡報筆', '人參條片', 'loew', '腳氣膏', '老鼠', '針灸', '糖果', '酒精', '泡沫噴頭', '感冒', '奧利司他', '掌上', '清腸', '空倉', 'lc', '火災警報器', '腎陽', '卵子', '象牙製品', 'loe', '藥', '軍警用品', '觀星', '睪丸素', '商標', '電擊棒', '出口標示燈', '甲硝唑', '防身棍', '諾美婷', '新百倫', '制氧機', 'ysyl', 'MSM', '魚餌', '天珠', '指扣', '警棍', '蟑', 'rootco', '男性保健', '樟腦', 'IQO', '豐胸霜', 'pillow', '力朗', '火警標示燈', '機關槍', '小彼恩', '鳳爪', '富士', '牛鞭', '海綿寶寶', '網路攝像頭', '愛犬心寶', '火砲', 'n字', '螞蟻藥', '殺菌劑', '薑黃', '出售水貨的藥品', '寶可夢', '逍遙丸', 'EMS微電流刺激器', '止痛膏', '淫羊藿', '三宅一生', 'UWELL', '林迪', '血糖', '溫槍', '頸大師', '消防', '白蕓豆', '及時樂', '一點絕', '順天堂', '樂酸克', '止癢貼', '緊急照明燈', '瓦斯槍', '恐龍蛋', '剪標品', '罌粟', 'babygo', '左炔諾', '護肝片', 'Panerai', 'protone', '茯苓', 'A星', '助勃', '吸食器', '肌內效', '犀利士', '醫療器', '電擊器', 'VLTN', 'kpopblackpi', '菸品', '衍宗', '角膜放大片', '增強免疫', '延時增大持久增粗', 'kask', '美乳霜', '藥水', '甩棍', 'hobo', '警銬', 'smarken', '緩眼', '環境用藥', '熊掌', '隱形眼鏡清潔液', '玩具膠囊', '額溫槍', 'decathlon', '清潔液', 'Wireless', '有線電話無線主副機', '疲勞', '鹿鞭', 'HUBLOT', '衛生棉', '波拉提', '楊樹林', 'ophidia', '消防水帶用快速接頭', '叮噹', '殺鼠', 'ua', '淫羊', '瑪咖', 'off-white', '模擬槍', '煙霧彈', 'nadle', '殺菌', '玩具聲光槍', '口袋彈弓', '手槍', '養胃', '標本', '權利車', '斑龍', '嗎啡', '武器玩具', '膠囊海綿', '蛇刀', '滅火器', '善存', 'Aplinestars', '遠視眼鏡', '手扣', '碎脂', '洗眼', '藥品', '蟲', 'MONCLER', '水晶寶寶', '人參', '水彈珠', '霧化杆', '輪椅', '止痛', '紗布', '衍宗丸', '密閉式撒水頭', 'ooz', '緊急廣播設備用揚聲器', '吸鐵石', '宜家', '古柯鹼', '電光炮', '隱形眼鏡清洗機', '葛根豐胸', '血氧', '止咳化痰', '犬心', '額耳溫槍', '斑龍片', '骨骼', '西瓜', '大龍炮', 'LINDY', '食品級矽藻土', '治療器', '玩具劍', '活體', '蟑螂餌', '鹿鞭片', '吸水變大玩具', '鹿鞭丸', '電信管制射頻器材', '吐氣棒', '電流刺激器', '濕疹膏', '老鼠炮', '除草醚', '餌', '水鬼', '獵槍', '武士刀', '鋼筆刀', '體溫計', '諾為', '壯陽調理', '灌腸', '殺蟲劑', '香奶奶', '馬槍', '低周波治療器', '牛寶', '活昆蟲', '消防用水帶', '白鳳丸', '蟋蟀', '噴霧殺蟲劑', '酒精棉片', '倍脈心', '合成樟腦丸', '農藥', 'ppf', '蜂炮', '動物', '奇力片', '增大', '二氯苯等防蟲藥劑', '愛普生', '蒂芙尼', '仙境兔', '行動數據設備', '菸膏', '蘇茵茵', '電擊槍', '泡水膨脹玩具', '西瓜霜', '消供蟑', '驗孕試紙', '醫療口罩', '迪通拿', '遛娃神器', '電氣警棍', '褪黑', '鞭炮', '悅可婷', '火警受信總機', '垃圾袋', '沖天炮', '隱形眼鏡盒', '護肝', '洗眼水', '血氧機', 'ikea', '毓婷', '美逸', '百倫', '血壓', '解毒丸', '蟲類', '四星彩', '補腎丸', '水鴛鴦', '血糖試紙', '泰國青草膏', '外幣', '迪奧', '男人茶', '殺蹣', '宣稱有療效的天珠', '飛智', 'emberton', '酸痛', '褪黑激素', '起泡膠', '延時', '逍遙散', '化瘀丹', '海狗', '電動自行車充電器', '伸縮棍', '數據機', '愛犬', '增粗', '鼻炎', '體脂計', '玩具水槍', '褪黑素', 'BV', '牛寶膠囊', '近視眼鏡', 'wf-sp920', '迪卡儂', '一齊開放閥', 'OK繃', '生根', '消防幫浦', '玩具飛彈', '甲硝', '衕仁堂', 'n字鞋', '去火', '達克', 'utopia', '麻醉槍', '專用垃圾袋', '柔沛', '自動步槍', '璐迪', '清熱', 'n標', '不動產', '透骨膏', '蘿蔔刀', '護肝養肝', '普通步槍', 'V家', '玩具泡泡槍', 'diese', '流水檢知裝置', '卡地亞', '角膜', '顏料', '生根粉', '美洲豹皮草', '雪茄', '冷兵器', '維骨素', 'FM2', '古柯', 'ys.i', '魚槍', 'v扣', '中華電信ADSL', '血液', '行動電話機', '鴉片', 'ostrich', '避孕套', 'QUECHUA', '痛風', '點痣筆', '補胃養胃', '清熱去火', '坐骨神經', '碎脂機', '仙女棒', '膠囊', '可婷', '樂透彩', '血壓計', '警棒', '止癢膏', '針灸針', '抑菌乳膏', '正露丸', '娛樂交通票券', '贓物或僅有使用權之商品', '三體牛鞭', '眼藥水', '養肝', '海洛因', '驗孕棒', '肝', 'Charger', '地黃', '手杖刀', '動物處方用', 'relax', 'petkit', '電蚊香', '宇舶', '口嚼菸', 'adia', '電動機車用充電器', 'alpinestars', '電話手錶', '久咳丸', '銀杏', '瑪尼', '耳溫槍', '避難方向指示燈', '匕首', 'ultimatewaterbeads', '蟑螂', '液體電蚊香', '灌腸器', '威而鋼', '體脂', '溫補', '醫療', '醫療護具', '鳳凰電波', '按摩膏', '泰國', 'Counterpain', '汽電子霧化器', 'shock', '扁鑽', '化痰', '老花眼鏡', 'bts', '緩降機', '百蟲殺', 'Project', '保健', '電子霧化器', '腹帶', '摔炮', 'aliexpress', 'gg', 'Laser', 'Viartril', '薄荷棒', '導入儀', '頸炎', 'mextand', 'JIL', '黃金閃', '螞蟻', '標刀', '玩具彈弓', '彩券', 'citizen', '鋼鞭', '鐵鞭', '精子', '蚤不到', '代謝片', '十字弓', '火警發信機', '保存液', 'LSY', '螞蟻餌', '乳薊草', '避孕藥', '痘膏', 'longchamp', '比多樂', '人體器官', '史萊姆', '納豆', '保險', '液體創可貼', 'HOLIDAYSalt', '玻璃水', '低周', '止痛貼', '大麻', '柚子2代', 'Spotlight', '肩射武器', '月經量杯', '皮膚膏', '便祕', '火箭炮', '砲', '癬膏', '影刺', '碧波', '棉條', '男性滋補', '蜈蚣膏', '犬心寶', '解毒', '華倫', '洗眼液', '同仁堂', '翡麗', '安全套', '補胃', '緊潤丹', 'BIMBAYLOLA', '減脂機', '老鼠藥', '鹿鞭膏', 'epson', 'RUDY', 'cartier', '盆栽', '指虎', '熱威樂素', '滴眼液', '補腎', '酸痛貼布', 'SANDER', '玩具棍', '玩具砲', '非農用掃刀', '火警警鈴', '醫療用彈性襪', '蚤', '制氧儀', 'gg家', '減體脂膠囊', 'PowerBank', '衝鋒槍', '螃蟹', '雙c', '驗孕', '瘦身清腸', '阿媽牌', '安非他命', '威而剛', '殺蟲', '多菌靈', '壯陽', 'ck', '數位式錄放影機', '百達', '食用', '緊潤', 'modulo', '火警探測器', '刀械', '止痛藥', 'OSIM', '固精丸', '火警中繼器', '殺蹣劑', '蟑螂藥', '葛根', '丹尼斯', '達克羅寧', 'dainese', '玩具彩帶槍', '彈藥', '脈衝頸椎治療儀', '膨脹玩具', '軍糧', '烏托邦', '回春堂', '銀杏葉', '奶薊', '泡水恐龍蛋', '防暴網', '落建', 'VUJADE', '護膽', '有看頭', '煙膏', 'ET95SN', '金屬制避難梯', '地黃丸', '補腦', '嬰兒配方奶粉', '夢特嬌', '維骨力', '報稅憑證', '手指虎', '止咳', '愛滋病', '骨齒目', '空氣槍', '生髮', '護膽片', '爆竹煙火', '左旋肉堿', '蔘片', '殺鼠劑', '體溫', '電子菸', '玩具弓箭', '衛生棉條', '保險套', '祖醫堂', '低周波原理產品', '小佩', '殺小糖果', '鐵拳卡', '古奇', '槍砲', '免縫膠帶', '肉', '磨牙棒', '維格利', '凝露', '軟骨素', '疣', '畜', '禽', '魚肉', '火腿', '培根', '香腸', '血腸', '醃制', '啤酒', '煙火', '爆竹', '器官', '憑證', '報稅', '處方', '醫用', '贓物', '活物', '保育', '抵價券', '小米酒', '食品', '牙齒', '口腔', '黏膜', '奶粉', '票券', '電擊', '防暴', '電話機', '副機', '發射器', '滅火', '泡沫', '火警', '衛生套', '棉塞', '優碘', '海綿', '月經', '耳鼻', '洗鼻', '鼻用', '耳溫', '蛋白錠', '月事', '月亮杯', '凡士林', '口罩', '手術', '騾', '驢', '駱駝', '綿羊', '山羊', '豬', '犬', '火雞', '吳郭魚', '虱目魚', '鮭', '鱒', '屍體', '內臟', '脂肪', '生乳', '血粉', '卵', '精液', '胚', '房地產', '白酒', '葡萄酒', '蒸餾', '黃酒', '配置酒', '果酒', '曲酒', '藥酒', '洋酒', '料酒', '泥螺', '行李箱', '旅行箱', 'CeivlmKlain', 'strider', '美孚', '糧食', '成犬', '小型犬', '泰迪', '罐頭', '主食', '成幼', '醫院', '肥牛', '即食', '香辣', '牛油', '自煮', '嫩牛', '自嗨鍋', '警械', '手銬', '嗓子', '喉嚨', '疼痛', 'chocola', '大閘蟹', '醉蟹', '快感液', '孕測', '排卵', '寄居蟹', '蝦滑', '星巴克', '磨牙', '雞圈', '甜甜圈', '大型犬', '冰鮮', '水餃', '新鮮', '雨衣', '鴨腿', '雞腿', '奧爾良', '琵琶腿', '烤腿', '油炸', '冷凍', '半成品', '預製', '終極水珠', 'ultimate', '吸水變大', '霧化桿', 'HOLIDAY', 'H牌', 'S牌', 'M牌', '空彈', '佩特裏', '奶茶杯', 'S糖', '主機', '斯萊克', 'Slyeek', 'qos', '鯨魚網購', 'vision', '膳魔師', 'MK', 'Y字母', '字母Y', '口味', '濕糧', 'V字母', '膠原', '糧包', '幼小', '湯罐', '保濕', '當當狸', '桂花鴨', '醬鴨', '特產', '滷味', '真空包裝', '熟食', '港式', '燒鵝', '烤鴨', '高濃度', '伏特加', '雞尾酒', '果凍酒', '布丁', '清真', '健康', '餐譽', '特童', '炒饃', '豆麵豆', '點心', '鴨爪', '雞爪', '番茄', '脆皮', '豬肉', '豬皮', '豬蹄', '豬胰', '前肘', '後肘', '豬心', '豬肺', '豬大腸', '豬肝', '豬腰', '豬血', '豬肚', '豬舌', '豬大骨', '豬排', '豬小腸', '豬筒骨', '豬腦', '牛肉', '牛筋', '牛蹄', '牛胰', '牛心', '牛肝', '牛血', '牛舌', '牛百葉', '西冷', 'T骨', '牛柳', '肉眼', '牛仔骨', '米龍', '黃瓜', '黃小瓜條', '牛腱子', '牛前展', '牛後展', '金錢展', '胸叉肉', '牛丸', '牛骨髓', '牛尾', '羊心', '羊肝', '羊肉餡', '羊血', '羊肚', '羊舌', '驢鞭', '鴿子', '黃喉', '鹿肉', '鹿茸', '柴雞', '母雞', '公雞', '雞頭', '烏雞', '雞翅', '雞胸', '雞肝', '雞肣', '鴨架子', '鴨舌', '鴨頭', '糕點', '零食', '年貨', '麵包', '成品', '整切', '天婦羅', '肉食', '排骨', '蒜香', '炸雞', '鹵味', '宰殺', '鮮凍', '小吃', '原料', '現殺', '鮮活', '海鮮', '水產', '速凍', '食材', '糯米', '廣式', '海苔', '蝦餅', '帶骨', '原切', '灌湯', '蔬菜', '維C', '蔗糖', '飲料', '飲品', '汽水', '解渴', '椰子', '無添加', '補水', '解酒', '壓榨', '食物', '法藤', 'phiten', 'minotti', '小/佩', '番茄醬', '果凍', '帕拉德', 'ohm', '腦電波', '替換芯', '酒神包', '果乾', '堅果', '豚骨', '泡面', '速溶', '紅糖', '海產品', '魚乾', '乾貨', '紫菜花', '鮮暇', '核桃', '芝麻', '黑豆', '代餐', '早餐', '酸辣粉', '螺螄粉', '方便麵', '桶裝麵', '優樂美', '香飄飄', '鷄爪', '泡椒', '辣椒', '墨魚乾', '榨菜', '帶魚', '凍品', '底料', '章魚', '大腸', '裏脊', '肘子', '餃子', '雲吞', '包子', '烤腸', '雙匯', '肥腸', '螺肉', '芝士', '周黑鴨', '絕味', '煌上煌', '醬香', '烤鷄', '聖農', '丸子', '魔芋爽', '芋圓', '魚捲', '水煮', '低脂', '臘肉', '乳酪', '優酪乳', '熟肉', '肉製品', '牛腱', '毛肚', '金錢肚', '牛筋丸', '鴿', '乾貝', '海帶', '紫菜', '水母', '海蜇', '蟹', '青蟹', '梭子蟹', '蟹肉', '鴨翅', '鴨胗', '鴨健', '鴨腸', '鵝腸', '獅頭鵝', '自熱米飯', '鵝肝', '兔頭', '駝奶', '羊奶', '牛奶', '牛乳', '象牙', '羊腿', '海產', '生蠔', '燕窩', '鱔魚', '鰻魚', '魷魚乾', '籽', '魚膠', '鵝肉', '兔肉', '鷄胸肉', '鴨胸', '肉脯', '醬肉', '鷄肝', '鵪鶉', '倉鼠', '金絲熊', '烏龜', '草龜', '飼料', '鸚鵡', '火腿腸', '羊肉', '鷄肉', '鴨肉', '驢肉', '虎皮', '扇貝', '蛤蜊', '鮑魚', '貝柱', '青口貝', '牡蠣', '龍蝦', '波士頓', '生鮮', '海參', '涼菜', '蝦乾', '魷魚', '魚籽', '五香', '鎖骨', '脆骨', '皮蛋', '羊肉卷', '海底撈', '羊蠍子', '烏鷄', '和牛', '牛排', '牛腩', '菲力', '安格斯', '醃肉', '熏肉', '有機', '餛飩', '翅中', '鷄柳', '骨肉相連', '千層肚', '蛋餃', '佛跳墻', '鷄雜', '牛雜', '去皮', '原味', '鴨鎖骨', '炸鷄', '鱈魚', '蝦仁', '良品鋪子', '三隻松鼠', '康師傅', '統一', '火雞麵', '重慶小麵', '紅燒', '達利園', '白象', '今麥郎', '農心', '高鈣', '全脂', '麵粉', '蛋糕', '黃油', '伊利', '蒙牛', '金鑼', '雨潤', '鮮肉', '凍肉', '乳製品', '蜂蜜', '辣條', '辣片', '衛龍', '盼盼', '高潮液', '流油', '整箱', '鴨蛋', '雞蛋', '惠顧', '端午', '五花', '純手工', '戰斧', '飼養', '海燕', '海星', '骨折', '骨裂', '跌打損傷', '貼膏', '軟組織', '扭傷', '巴適美特', '武士刃', '羅蔔', '豆豆', '羅蔔刀', '蔔寶劍', '伸縮劍', '米酒', '發酵酒', '鮮榨', '古法', '釀造', '茅臺酒', '水銀', '蘿菠刀', '草莓刀', '葡萄', '配製酒', '紅酒', '低度酒', '爽口', '酸甜', '香蕉刀', '氮化鎵', '山茶花', '洗面乳', '洗面奶', '迪士妮', '巴布豆', '記錄筆', '驅鼠膏', '濾菸器', '濾煙器', '戒煙器', '水煙', '水煙膏', '水煙壺', '口含煙', '口含菸', '斑點龜', '水龜', '魚缸龜', '槐樹', '嫁接', '金絲垂', 'telfar', 'Lancome', '蘭蔻', 'Tresor', 'IDOLE', '巖蘭', '亞曼尼', 'vetiverdhiver', '石斛', '花苞', '花苗', '苔蘚', '易活', '花卉', '流量卡', '上網卡', '電話卡', '蘭花', '綠植', '家常菜', '炒醬', '調味料', '米線', '米粉', '袋裝', '0g', '捏捏樂', '紫檀實木', 'ODINZEUS', '銅師傅', '皇家橡樹', '萬孚', '淋病', '抗原', '梅毒', '自檢', '自測', '唇煙', '鼻煙', 'v字扣', '微景觀', '赤楠', '盆景', 'siltech', 'tangle', '53度', '52度', '茅臺', '迎賓酒', '42度', '50度', '醇酒', '清香型', '濃香型', '醬香型', '鼠魚', '清道夫', '綠藻', '褐藻', '吸鰍', '契爾氏', '精華乳', '試用包', 'A醇', '雷士', '牛角', 'ruyan', 'vuicr', 'ublox', '悅ke', '硫酸', 'ploom', 'xadnced', 'CHAIKAKILTER', '舒壓擠痘痘', '紓壓擠痘痘', '擠痘痘玩具', '萌寵擠痘痘', '擠痘痘注射器', '青草膏', '乳膏', '點痣', '清顆粒', '疤痕', '肚臍貼', '活洛油', '清涼油', '草藥膏', '繃帶', '正骨水', '褥瘡貼', '項圈', '脖圈', '跳蚤', '恩諾', '口服液', '甲肖唑', '食剋', '甲嘧磺', '爛根劑', '氟胺氰', '除草劑', '生根原液', '灰黴清', '靈白粉', '硼肥片', '氮磷鉀', '磷鉀肥', '二氫鉀', '激素', '肉乾', '肉鬆', '肉燕皮', '酸肉', '熱狗', '鹹水鴨', '鴨腎', '雞翅鳳爪', '肉粽', '肉包', '肉捲', '肉丸', '貢丸', '精肉', '披薩', '月餅', '杏仁餅', '雞仔餅', '三明治', '漢堡', '醬板鴨', '江蘇特產', '燒鴨烤鴨', '廣式特產', '米飯', '煲仔飯', '鴨掌', '檸檬', '牛脊骨', '牛蠍子', '牛骨', '黃粽', '粽禮', '五花粽', '風乾鴨', '分享器', '安卓機', '智慧機', '止血帶', '美國威而', '睡眠片', '精力糖', '飛馬糖', '能量糖', '悍馬糖', '鼻立通', '瑩珠膏', '膠布', '軟膏', '油膏', '黃連膏', '寧痛膏', '化痰散', '救肺丸', '清肺散', '救肺散', '藥布', '紫花油', '藥油', '心率', '抑菌液', '止疼片', '止癢液', '青草油', '生春堂', '貼布', '炎貼片', '叮咬膏', '除毛儀', '西汀片', '至寶丸', '普樂安片', '蛤蚧精', '紅花油', '甩脂貼', '艾草貼', '疤痕膠', '桑黃', '克/罐', 'g/罐', '炎噴霧', '凝膠', '糙米飯', '八寶粥', '臘八粥', '粗糧', '皮卡丘', '劍橋英語', '超人隊長', 'skip', 'dogman', '掌機', 'captain', '治眼袋', '黑眼圈', '眼膜', '孔雀魚', '純種', 'LOUIS', 'VUITTON', 'Ettinger', 'prada', 'bally', 'Chanel', 'Hermes', 'versace', 'Gabbana', 'celine', 'Rolex', 'G字母', '古家', '字母BB', 'Xperia', '索尼', 'G扣', '侃爺', '一字扣', 'ulzzang', '字母異形', 'Bella', 'Drejew', '三星', 'monogramme', 'VSL', '葆蝶家', 'Dior', 'Fendi', 'Givenchy', 'Valentino', 'Michael', 'Kors', 'Kate', 'Spade', 'Coach', 'Marc', 'Jacobs', 'Tory', 'Burch', 'Rebecca', 'Minkoff', 'Ted', 'Baker', 'MCM', 'Moschino', 'Zara', 'H&M', 'Mango', 'Topshop', 'ASOS', 'Island', 'Urban', 'Outfitters', 'Aldo', 'Forever', 'Under', 'Armour', 'Balance', 'Reebok', 'Fila', 'Converse', 'Vans', 'McCartney', 'Dolce', 'Jimmy', 'Choo', 'Miu', '香奈兒', '路易威登', '愛馬仕', '古馳', '普拉達', '博柏利', 'Armani', '阿瑪尼', '拉爾夫', 'Ralph', '聖羅蘭', '範思哲', '芬迪', '華倫天奴', '紀梵希', 'Hilfiger', '希爾費格', '高仕', 'Tiffany', 'Harry', 'Winston', '溫斯頓', 'Buccellati', '布佳拉提', 'Graff', '葛洛夫', 'Arpels', '梵克', 'Piaget', '伯爵', 'Chopard', '蕭邦', 'Bvlgari', '寶格麗', 'Mikimoto', '百達翡麗', 'Audemars', '愛彼', 'Vacheron', 'Constantin', '江詩丹頓', 'Breguet', '寶齊萊', 'Breitling', '百年靈', 'LeCoultre', '積家', 'Omega', '歐米茄', 'Schaffhausen', '萬國表', 'Blancpain', '寶珀', '嬌蘭', '雷朋', 'Oakley', '奧克利', 'Clicquot', 'Hennessy', '軒尼詩', 'Mizuno', '美津濃', 'UnderArmour', '安德瑪', 'JORDAN', 'Saucony', '索康尼', '斐樂', 'BROOKS', 'Veneta鮮蔬', '眼鏡', '須檢驗之商品', '玩具槍', '境外應施檢疫物', '電動自行車鋰電池', 'agv', '電度錶', '黴素片', '真菌', '八顆球', '磁鐵', '巴克球', '釹鐵硼', '魔力球', '魔方球', '過濾器', '小米', '芯子/代/通配', '守宮', '高版本', '利拉德', '仿真玩具/仿真/玩具', '瑞士勞/勞/力', '瑞士浪/浪/琴', '浪-琴/浪/琴', '阿瑪', '天梭', 'tissot', '現摘', '迷你廚房', '迷你小廚房', '老班章', '電子秤', 'PoRD', 'Oxva', '起源', 'VGOD', 'delightpool', '魚子醬', '點讀', 'beats', 'SolidWorks', '庫奇', '養生茶', '洗衣機/迷你/自動/摺疊', '禪定花園', 'YAO', '避孕/口服/避孕', '遮瑕', '提取物', '泰諾健', '山崎', '電錶', '水果片', '優酪乳杯', '蒲公英', '養肺', '擠痘痘', 'spotpopper', '孔明鎖', '魯班鎖', '搖搖杯', '鈣爾奇', '潤喉', '護嗓', '含片', '草珊瑚', '西洋參', '花旗參', '洗髮露', '沐浴露', '洗髮水', 'audio-technica', '鐵三角', '國四', '國五', '國六', '燃油', '三輪機車', '高爾夫車', '四輪車', '三輪車', '電噴', 'Catrice', 'poliform', '庫裡', '水錶', '三指拳', 'lesserafim', '老瘋楊', '消毒液', '消毒水', 'curry', 'HUMAN', '比爾斯', '王妃梳', '面巾紙', '妙三多', '疫苗', '紅豆', '薏米茶', '脾胃', '美津', 'oneboy', 'visiopn', '瑞士', '名牌', 'cembre', '森博爾', 'Caliburn', '發熱網芯', '包蕾斯', '輝瑞', '支氣管', '病毒', '噴霧', '威士卡', '梅花灸', '全息灸', '艾棒', '灸棒', 'Tommy', '火灸', '透灸', '火龍罐', '陳柱', '紅花葯', '多味草', '本艾', '灸柱', '溫灸', '脹氣', '健脾', '放屁', '消化', 'CHANE', '味事達', '味極鮮', '蝴蝶大巴', '竹罐', '竹筒', '竹子', '火罐', '拔罐', '中養生', '吸痧', 'Metmo', '金龍魚', 'Lovetodream', '椰奶', '椰汁', '西米露', '椰漿', '東北大米', '五常大米', '珍珠米', '香稻大米', 'sixpad', 'refa', '黎琺', '跳蛛', '挖土機/果園/農用/履帶/工地', '微挖', '蝴蝶', '消毒', '冷藏', '洗衣機', 'mg', '純原', '原版頭層', '羽絨', '羅蒙', '筷子', '頭層', 'SMN', '濕巾', 'maxrun', '去水垢', '聖路易', 'hermas', 'gucc', 'common', '金多樂', '凍幹', '幼糧', 'ITSK', '天絲', '葉黃素', '藍莓', 'migswitch', '米格', '二手', '力士', '勞家', 'watch4pro', '高跟鞋', '英國王妃', '腋下包', '去痰', '溼茶', '去濕茶', '濕氣', '扣帶包', '手包', '護髮素', '酷奇全包', '席妍', 'sunnycolor', 'Leaderfins', '名創優品', '奧康', '黑武士', '仰望U8', '石雕', '浮雕', '手術室', '急診', '化糞池', '隔油池', '清運車', '搬運車', '拉貨車', '拖車', '充氣船', '遊艇', '橡皮艇', '皮划艇', '衝鋒舟', '氣墊船', '綠鬆石', '高瓷烏', '一體三通', '皺紋', '抬頭紋', '面霜', '抗衰老', '護膚品', '祛痘', '珍珠膏', '素顏霜', '貴婦膏', '特護乳', '保溼乳', '修復霜', '水乳', '精華水', '乳酸', '啫喱霜', '乳霜', '眼霜', '抗皺', '細紋', '抗老', '乳液', '保溼', '海藍之謎', 'ml', '爽膚水', '神仙水', '紫檀', '葉檀', '黃柏木', '檀香', '種子', '腔道', '潤滑鏡', '胃鏡', '腸鏡', '己基', '磺酸鉀', '草本抑菌', '抑菌膏', '皮膚外用', '深層修護', '船舶', '充氣模型', '香蕉船', '摩託艇', '登陸艇', '巡洋艦', '摺疊船', '充氣艇', '皮劃', '腳踏船', '拖拉船', '快艇', '鉤船', '潛水器', '艦船', '航空母艦', '竹葉船', '支架船', '唇木模', '冰峰', 'G~家', '震旦', '利物浦', 'C廠', 'CASENO', '胎生魚', '紅太陽魚', '紅瑪麗魚', '紅皮球魚', '紅劍魚', '花生米', 'DORCO', '多樂', 'CHRISTOFLE', '昆庭', '伊甸花園', '愛家彼', '皇家離岸', 'AP15710', '桌球服', '花瓣坐墊', '髮蠟', '髮泥', '電度表', '商用臺稱', '電子稱', '計價稱', '快遞磅', '電子計價', '計價磅', '計價', '電能表', 'iluma', '花嫁中野', '日誌型', '稱重', '臺稱', '小型磅', '捏捏球', '防火菸', '雪燕', '皂角米', '桃膠', '玻尿酸', '面膜', '提拉緊緻', '滋潤收斂', '抗皺套裝', '磁力', 'HOTO', '小猴', 'ebmpapst', 'SOMFY', 'KEYGO', 'undue', 'anchor', '拉杆箱', '蠟瓶', '捏捏', 'CUKTECH', '酷科', '菸袋', 'zegna', 'APEXEL', '足球服', '切爾西', '阿森納', '望遠鏡', '鏡頭', 'ecco', '愛步', '日化色素', '原粉', '工廠', '無線pc平板', '手推車', '列印機', '泡泡', '口袋車', '黃飛紅', '替菸棒', '戒菸棒', '三豐', 'mitutoyo', 'ofwave', '索芙', '守夢者', '防狼戒', '防身暗器', '鈦鋼戒指', '腦波儀', '血脂', 'catchteenieping', 'sup遊戲機', '顯微鏡', '賽代克', 'CELdek', '放大鏡', 'Munters', '手機鏡頭', '電影鏡頭', '床護欄', '康復機', '假煙', '肥料', '百利達', 'tanita', '造粒機', 'CONTITECH', '床欄杆', '床圍欄', '護欄圍', '護欄杆', '戒菸貼', '戒菸靈', '訓練泵', '微型火炮', '回膛減震大炮', '回膛大炮', '義大利炮', '迷你迫擊砲', '小香風', '小香家', '杏花村', '紅蓋', '黃蓋', '減震大炮', '螢光棒', '發光棒', '捲菸器', '空煙管', 'YETI', '踩雷磁力', '戒菸', '捲菸', '鎳科', '固化', '牙科', '假牙', 'Bathmate', 'Hurom', '惠人', 'snus', 'snok', '戒煙', '咽', '口含yan', 'velo', '悠米', '唇替', '戒yan', 'neocedar', '玻璃倉', '電烙鐵', '發熱絲', '線圈', '陶瓷芯', '電焊筆', '棉花', '電池桿', '電熱線', '電阻絲', '加熱器', 'nkyumapuff', 'ekifee', 'sigelei', 'eved twist', 'backwoodsi', 'brass knuckles', 'bestia', 'taifun', 'zeu xm', '510通用', '510適用', '圓絲', '素絲', '烙鐵', '電焊', '電烙', 'ni70', 'ni80', 'osprey', 'Daylite', 'NK', 'Yumapuff', 'evod twist', 'taifun 颱風 GT4', 'Zeu x m', '510 通用', '510 適用', '510 介面', '去皮雞', '鮮兔', '熟飯', '生骨', 'ps4遊戲手柄', 'ps4無線遊戲手柄', 'ps4私模手柄', '防身棒', '甩棒', '三節棍', '防狼器', '體重計', '體重秤', '防狼棍', '嬰兒餐椅', '安全座椅', '安全椅', '嬰兒搖椅', '兒童躺椅', '家家酒', '過家家', '學習椅子', '成長椅', '安羅拉', '防曬乳', '防曬霜', '水潤', '發膏', '清爽呵護', '防曬噴霧', '發霜', '黛爾熙', '染發劑', '潤彩霜', '公安部', '毛髮檢測', '毒物', '尿檢', '毒品檢紙', '驗尿', '尿檢板', '測毒', '驗尿板', '依託米酯', '煙蛋', '測試試紙', '監測檢測儀', 'to_', '大嘴巴嘟嘟', '紫草油', '紅屁屁', '淹紅', '熱疹', '初生嬰兒', '詩馨語', '修容盤', '修顏液', '鼻眼影', '液體修容', 'coco', '小香', 'leband', '樂班', '熱養儀', '經絡疏通', '太赫茲', '胰島素', '優泌樂', '優泌林', '優思靈', '優伴筆', '酥油', '燈油', '天地鉸鏈', 'APM', 'Monaco', '薩酈奇', 'ag.v', '莧菜紅', '手工大炮', 'CAAPE', 'GOOSE', '龍骨膏', '草本膏', '愛麗德', '拌麵', '蕎麥麵', '電視面', '祛斑霜', '老年斑', '淡化色斑', '雀斑', '面膏', '巴家三代', '克羅心', 'ozyeti', 'Massimo', '膝關節', 'CPM-B', '髖關節', '術後修復', '康復器']
        title = self.source["globalData"]["tempModel"]["offerTitle"]
        # for word in title_word_prohibited:
        #     if word in title:
        #         return {'status': False, 'data': word}
        for word in title_word_replacement:
            title = title.replace(word, "")
        return title

    def get_main_images(self):
        """获取主图"""
        # images 键不存在
        if "images" not in self.source["globalData"]:
            return []
        # 获取主图组装成列表
        images_data = [
            i["fullPathImageURI"] if "fullPathImageURI" in i else i["imgUrl"]
            for i in self.source["globalData"]["images"]
        ]
        main_images = []
        # 获取主图的前 8 张
        for i in images_data[:8]:
            response = self.request_function(i, headers=self.headers)
            # 主图出现 404 异常
            if response.status_code == 404 or response.status_code == 403:
                return []
            # 主图正常
            elif response.status_code == 200:
                # 获取图片的像素，如果图片的长和宽都大于 200，则满足条件
                img = Image.open(BytesIO(response.content))
                if img.size[0] >= 200 and img.size[1] >= 200:
                    main_images.append(i.split("?")[0])
        return main_images

    def get_unit_weight(self):
        """获取商品的重量"""
        try:
            # 尝试获取 unit_weight
            unit_weight = self.source["globalData"]["skuModel"]["extraInfo"][
                "freightInfo"
            ]["unitWeight"]
            # 如果 unit_weight 为 0，从 skuWeight 中提取第一个值
            if unit_weight == 0:
                unit_weight = next(
                    iter(
                        self.source["globalData"]["skuModel"]["extraInfo"][
                            "freightInfo"
                        ]["skuWeight"].values()
                    ),
                    None,
                )
            # 如果 unit_weight 小于等于 0.01，返回 None
            if unit_weight is not None and unit_weight <= 0.01:
                return None
            # 返回有效的 unit_weight
            return unit_weight
        except Exception:
            # 发生异常时返回 None
            return None

    def get_current_price(self):
        """获取商品价格，针对部分单规格商品"""
        data = self.first_non_empty_item_in_data("priceModel")
        if data and "priceModel" in data:
            return data["priceModel"]["currentPrices"][0]["price"]

    def get_detail_images(self):
        """获取详情图片，并做特殊过滤"""
        data = self.first_non_empty_item_in_data("detailUrl")
        image_sources = []
        if data and "detailUrl" in data:
            # 请求 detailUrl 获取详情数据
            detail_data = self.request_function(
                data["detailUrl"], headers=self.headers
            ).text
            soup = BeautifulSoup(detail_data, "html.parser")
            for img in soup.find_all("img"):
                if "src" in img.attrs:
                    # 格式化 src
                    src = img["src"].strip('\\"').split("?")[0].rstrip('\\"/')
                    # 判断图片是否满足条件
                    if "cbu01" not in src:
                        continue
                    # 拼装新的 src，防止 url 错误
                    index = src.find("cbu01")
                    src = "https://" + src[index:]
                    response = self.request_function(src, headers=self.headers)
                    # 获取图片的像素，如果图片的长大于 700，宽大于 600，并且长/宽的比例效益3，则满足条件
                    img = Image.open(BytesIO(response.content))
                    if img.size[0] >= 700 and img.size[1] >= 600:
                        if img.size[1] / img.size[0] <= 3:
                            image_sources.append(src)
            return image_sources

    def get_product_attribute(self):
        """获取详情文字"""
        # web端
        # data = self.first_non_empty_item_in_data('values')
        # app端
        data = self.first_non_empty_item_in_data("propsList")
        if data is not None:
            filter_words = [
                "专利",
                "跨境",
                "货号",
                "下游",
                "订制",
                "地区",
                "授权",
                "进口",
                "LOGO",
                "上市",
                "是否",
                "加工",
                "货源",
                "产地",
                "形象",
                "代理",
                "售后",
            ]
            attribute_list = [(f"{x['name']} : {x['value']}") for x in data["propsList"]
                              if all(word not in x["name"] for word in filter_words)
                              and x["value"] != "/"
                              ]
            return attribute_list
        return None

    def get_video(self):
        """获取视频"""
        data = self.first_non_empty_item_in_data("videoUrl")
        if data:
            return data["videoUrl"]

    def get_start_amount(self):
        """获取起批数"""
        data = self.source["globalData"]["orderParamModel"]["orderParam"]["beginNum"]
        return data

    def build_product_package(self):
        """开始组装数据包"""
        self.source = self.get_data_packet_by_1688()
        if self.source:
            # 获取主图列表
            main_images = self.get_main_images()

            # 如果主图列表为空，则主图异常
            if len(main_images) == 0:
                return {
                    "platform": "1688",
                    "code": 3,
                    "message": "主图异常",
                    "product_id": self.product_id,
                }

            # 主图正常
            if len(main_images) != 0:
                # 获取 skuProps 的参数
                sku_props = self.source["globalData"]["skuModel"].get("skuProps", [])
                # 规格数为 0
                if not sku_props:
                    specifications = 0
                    stock = random.randint(900, 1000)
                    if "skuRangePrices" not in self.source["globalData"]["orderParamModel"]["orderParam"]["skuParam"]:
                        return {
                            "platform": "1688",
                            "code": 4,
                            "message": "商品数据包异常",
                            "product_id": self.product_id,
                        }
                    # 设置sku_has_image状态
                    sku_has_image = True
                    # 获取价格
                    price = self.source["globalData"]["orderParamModel"]["orderParam"]["skuParam"]["skuRangePrices"][0]["price"]
                    # 组装sku_assembly
                    sku_assembly = {"sku_data": {"price": price, "stock": stock}}

                # 规格数为 1
                elif len(sku_props) == 1:
                    specifications = 1
                    # 判断prop键是否存在
                    if "prop" not in self.source["globalData"]["skuModel"]["skuProps"][0]:
                        return {
                            "platform": "1688",
                            "code": 4,
                            "message": "商品数据包异常",
                            "product_id": self.product_id,
                        }
                    # 判获取 sku1 的名称
                    sku1_property_name = self.source["globalData"]["skuModel"]["skuProps"][0]["prop"].replace("产品", "")

                    # 组装 sku_assembly
                    sku_assembly = {
                        "sku_data": {
                            "sku_property_name": {
                                "sku1_property_name": sku1_property_name
                            },
                            "sku_parameter": [],
                        }
                    }
                    # 获取 sku_props 和 sku_maps 数据包
                    sku_props = self.source["globalData"]["skuModel"]["skuProps"]
                    sku_maps = self.source["globalData"]["skuModel"]["skuInfoMap"]

                    # 通过sku_props判断商品包是否异常
                    if sku_props[0]["value"] == [{}]:
                        return {
                            "platform": "1688",
                            "code": 4,
                            "message": "商品数据包异常",
                            "product_id": self.product_id,
                        }

                    # 遍历数据 sku1 的详细参数
                    for i in sku_props[0]["value"]:
                        if "name" not in i:
                            return {
                                "platform": "1688",
                                "code": 4,
                                "message": "商品数据包异常",
                                "product_id": self.product_id,
                            }
                        sku_value = i["name"]
                        image_url = i.get("imageUrl", None)
                        if sku_value in sku_maps:
                            price = (
                                    sku_maps[sku_value].get("discountPrice")
                                    or sku_maps[sku_value].get("price")
                                    or self.get_current_price()
                            )
                            skus = {
                                "remote_id": self.product_id + "_" + self.generate_random_string(10),
                                "name": sku_value,
                                "imageUrl": image_url,
                                "price": price,
                                "stock": random.randint(900, 1000),
                            }
                            sku_assembly["sku_data"]["sku_parameter"].append(skus)

                    # 设置sku_has_image状态
                    sku_has_image = True if image_url else False

                # 规格数为 2
                elif len(sku_props) == 2:
                    specifications = 2
                    # 判断 prop 键是否存在
                    if "prop" not in self.source["globalData"]["skuModel"]["skuProps"][1]:
                        return {
                            "platform": "1688",
                            "code": 4,
                            "message": "商品数据包异常",
                            "product_id": self.product_id,
                        }
                    # 获取 sku1 的名称
                    sku1_property_name = self.source["globalData"]["skuModel"]["skuProps"][0]["prop"].replace("产品",
                                                                                                              "")
                    # 获取 sku2 的名称
                    sku2_property_name = self.source["globalData"]["skuModel"]["skuProps"][1]["prop"].replace("产品",
                                                                                                              "")
                    # 获取 sku_props 和 sku_maps 数据包
                    sku_props = self.source["globalData"]["skuModel"]["skuProps"]
                    sku_maps = self.source["globalData"]["skuModel"]["skuInfoMap"]
                    # 组装 sku_assembly
                    sku_assembly = {
                        "sku_data": {
                            "sku_property_name": {
                                "sku1_property_name": sku1_property_name,
                                "sku2_property_name": sku2_property_name,
                            },
                            "sku_parameter": [],
                        }
                    }
                    # 遍历数据 sku1 和sku2 的详细参数
                    for i in sku_props[0]["value"]:
                        image_url = i.get("imageUrl", None)
                        for j in sku_props[1]["value"]:
                            sku_value = i["name"] + "&gt;" + j["name"]
                            if sku_value in sku_maps:
                                price = (
                                        sku_maps[sku_value].get("discountPrice")
                                        or sku_maps[sku_value].get("price")
                                        or self.get_current_price()
                                )
                                skus = {
                                    "remote_id": self.product_id + "_" + self.generate_random_string(10),
                                    "name": i["name"] + "||" + j["name"],
                                    "imageUrl": image_url,
                                    "price": price,
                                    "stock": random.randint(900, 1000),
                                }
                                sku_assembly["sku_data"]["sku_parameter"].append(skus)

                    # 设置sku_has_image状态
                    sku_has_image = True if image_url else False

                #
                else:
                    return {
                        "platform": "1688",
                        "code": 5,
                        "message": "sku规格数超出",
                        "product_id": self.product_id,
                    }

                # 组装数据包
                product_package = {
                    "product_id": self.product_id,
                    "specifications": specifications,
                    "unit_weight": self.get_unit_weight(),
                    "start_amount": self.get_start_amount(),
                    "title": self.get_title(),
                    "main_images": main_images,
                    "skumodel": sku_assembly,
                    "video": self.get_video(),
                    "details_text_description": self.get_product_attribute(),
                    "detailed_picture": self.get_detail_images(),
                    "other_parameters": {
                        "sku_has_image": sku_has_image,
                    }
                }

                # 返回数据包
                return {
                    "platform": "1688",
                    "code": 0,
                    "message": "请求成功",
                    "data": product_package,
                }

        else:
            return {
                "platform": "1688",
                "code": -1,
                "message": "商品下架或离线",
                "product_id": self.product_id,
            }


if __name__ == "__main__":
    res = Alibaba("894540636861")
    try:
        res1 = res.build_product_package()
        print(res1)
    except Exception as e:
        print(e)
