# from googletrans import Translator
#
# translator = Translator()
#
# text = ['品牌: null', '颜色: 艳冠群芳[中长],黑碟银链[中长],蓝山茶花[中长],银河蝴蝶[中长],魔镜爱心[中长],花飞碟舞[短款],粉驹兔子[短款],法式蝴蝶[中长],果冻葡萄[短款],蓝色爱心[中长],心心蝴蝶[短款],紫色云朵[中长],芭蕾爱心[中长],月光晕染[短款],珍珠爱心[中长],酒红银边[短款],长岛冰茶[短款],爱心腮红[中长],白边链条[长款]', '颜色分类:[胶水款],五件套[果冻胶+胶水+指甲锉+酒精棉+木棒]', '风格:甜美,辣妹,爆闪,简约,欧美,轻奢风,纯欲', '款式:长款,中款,穿戴式,芭蕾型', '图案:星空,蝴蝶', '品牌类型:国货品牌', '非特化妆品备案证号:无', '特殊用途化妆品:否', '适用人群:女士']
# translated = translator.translate(f"{text}", src='zh-cn', dest='en')
#
# print(f"原文: {text}")
# print(f"翻译: {translated.text}")
import ast

text = "['Brand: ','Color': blackmedium length"
text1 = ast.literal_eval(text)
print(text1)
