# import json
# import string
# import random
#
# data_json = {'platform': 'ruten', 'code': 0, 'message': '请求成功', 'data': {'product_id': '22350344904512', 'specifications': 2, 'unit_weight': None, 'start_amount': None, 'title': '3D立體隔音海綿 隔音棉 吸音棉 消音棉 隔音貼 隔音泡棉 自粘隔音海綿 高密度阻燃 全頻吸音降噪隔音', 'main_images': ['https://gcs.rimg.com.tw/g4/080/213/izrv31/e/d3/40/22350344904512_521.jpg', 'https://gcs.rimg.com.tw/g4/080/213/izrv31/e/d3/40/22350344904512_504.jpg', 'https://gcs.rimg.com.tw/g4/080/213/izrv31/e/d3/40/22350344904512_862.jpg', 'https://gcs.rimg.com.tw/g4/080/213/izrv31/e/d3/40/22350344904512_872.jpg', 'https://gcs.rimg.com.tw/g4/080/213/izrv31/e/d3/40/22350344904512_999.jpg', 'https://gcs.rimg.com.tw/g4/080/213/izrv31/e/d3/40/22350344904512_311.jpg', 'https://gcs.rimg.com.tw/g4/080/213/izrv31/e/d3/40/22350344904512_271.jpg', 'https://gcs.rimg.com.tw/g4/080/213/izrv31/e/d3/40/22350344904512_553.jpg'], 'skumodel': {'sku_data': {'sku_property_name': {'sku1_property_name': '規格', 'sku2_property_name': '項目'}, 'sku_parameter': [{'remote_id': '22350344904512_H8Bq2rKxxf', 'name': '8cm厚-高密度防燃【不帶背膠】||黃色', 'imageUrl': None, 'price': 857, 'stock': 292}, {'remote_id': '22350344904512_0xwoxpcoGz', 'name': '8cm厚-高密度防燃【不帶背膠】||黑色', 'imageUrl': None, 'price': 857, 'stock': 280}, {'remote_id': '22350344904512_dYf61KJxRC', 'name': '8cm厚-高密度防燃【不帶背膠】||灰色', 'imageUrl': None, 'price': 857, 'stock': 270}, {'remote_id': '22350344904512_Nn7LeHFQj0', 'name': '8cm厚-高密度防燃【不帶背膠】||藍色', 'imageUrl': None, 'price': 857, 'stock': 283}, {'remote_id': '22350344904512_pCBXbhXuc0', 'name': '8cm厚-高密度防燃【自帶背膠】||藍色', 'imageUrl': None, 'price': 954, 'stock': 300}, {'remote_id': '22350344904512_w9aXUWQjUt', 'name': '8cm厚-高密度防燃【自帶背膠】||灰色', 'imageUrl': None, 'price': 954, 'stock': 273}, {'remote_id': '22350344904512_RdydVrQoGW', 'name': '8cm厚-高密度防燃【自帶背膠】||黃色', 'imageUrl': None, 'price': 954, 'stock': 289}, {'remote_id': '22350344904512_TV14Zx4rhN', 'name': '8cm厚-高密度防燃【自帶背膠】||黑色', 'imageUrl': None, 'price': 954, 'stock': 287}, {'remote_id': '22350344904512_jkz1Zt4Fqo', 'name': '3.5cm厚高密度防燃【不帶背膠】||黑色', 'imageUrl': None, 'price': 506, 'stock': 290}, {'remote_id': '22350344904512_n97apbCHaq', 'name': '3.5cm厚高密度防燃【不帶背膠】||黃色', 'imageUrl': None, 'price': 506, 'stock': 284}, {'remote_id': '22350344904512_kVN8KrdxZy', 'name': '3.5cm厚高密度防燃【不帶背膠】||灰色', 'imageUrl': None, 'price': 506, 'stock': 296}, {'remote_id': '22350344904512_m01xA02eXl', 'name': '3.5cm厚高密度防燃【不帶背膠】||藍色', 'imageUrl': None, 'price': 506, 'stock': 267}, {'remote_id': '22350344904512_z6mMfLV5e0', 'name': '5cm厚-高密度防燃【不帶背膠】||黃色', 'imageUrl': None, 'price': 624, 'stock': 284}, {'remote_id': '22350344904512_7ciIwsTmIT', 'name': '5cm厚-高密度防燃【不帶背膠】||灰色', 'imageUrl': None, 'price': 624, 'stock': 253}, {'remote_id': '22350344904512_8JE5EZEaNj', 'name': '5cm厚-高密度防燃【不帶背膠】||藍色', 'imageUrl': None, 'price': 624, 'stock': 263}, {'remote_id': '22350344904512_41M11WknTB', 'name': '5cm厚-高密度防燃【不帶背膠】||黑色', 'imageUrl': None, 'price': 624, 'stock': 264}, {'remote_id': '22350344904512_0bSShWcw0s', 'name': '5cm厚-高密度防燃【自帶背膠】||灰色', 'imageUrl': None, 'price': 727, 'stock': 277}, {'remote_id': '22350344904512_4ohzLnUZ6K', 'name': '5cm厚-高密度防燃【自帶背膠】||黃色', 'imageUrl': None, 'price': 727, 'stock': 279}, {'remote_id': '22350344904512_mGTVcQurFe', 'name': '5cm厚-高密度防燃【自帶背膠】||黑色', 'imageUrl': None, 'price': 727, 'stock': 260}, {'remote_id': '22350344904512_hXRk9njhTt', 'name': '5cm厚-高密度防燃【自帶背膠】||藍色', 'imageUrl': None, 'price': 727, 'stock': 291}, {'remote_id': '22350344904512_FMESKyp7oR', 'name': '2cm厚-高密度防燃【不帶背膠】||黃色', 'imageUrl': None, 'price': 410, 'stock': 282}, {'remote_id': '22350344904512_7YiuweRyUo', 'name': '2cm厚-高密度防燃【不帶背膠】||藍色', 'imageUrl': None, 'price': 410, 'stock': 284}, {'remote_id': '22350344904512_3jeksQ7EyK', 'name': '2cm厚-高密度防燃【不帶背膠】||黑色', 'imageUrl': None, 'price': 410, 'stock': 277}, {'remote_id': '22350344904512_cQrhsgUEbT', 'name': '2cm厚-高密度防燃【不帶背膠】||灰色', 'imageUrl': None, 'price': 410, 'stock': 269}, {'remote_id': '22350344904512_Kwnt8vO5cc', 'name': '2cm厚-高密度防燃【自帶背膠】||藍色', 'imageUrl': None, 'price': 514, 'stock': 290}, {'remote_id': '22350344904512_e8t7CWIa37', 'name': '2cm厚-高密度防燃【自帶背膠】||灰色', 'imageUrl': None, 'price': 514, 'stock': 263}, {'remote_id': '22350344904512_kHQ8OxVrGT', 'name': '2cm厚-高密度防燃【自帶背膠】||黃色', 'imageUrl': None, 'price': 514, 'stock': 274}, {'remote_id': '22350344904512_U3z15gqTxw', 'name': '2cm厚-高密度防燃【自帶背膠】||黑色', 'imageUrl': None, 'price': 514, 'stock': 273}, {'remote_id': '22350344904512_tQRuLsAE4D', 'name': '3.5cm厚高密度防燃【自帶背膠】||黑色', 'imageUrl': None, 'price': 597, 'stock': 292}, {'remote_id': '22350344904512_XEJaqJ5TEy', 'name': '3.5cm厚高密度防燃【自帶背膠】||灰色', 'imageUrl': None, 'price': 597, 'stock': 266}, {'remote_id': '22350344904512_OANpzWWJnA', 'name': '3.5cm厚高密度防燃【自帶背膠】||藍色', 'imageUrl': None, 'price': 597, 'stock': 289}, {'remote_id': '22350344904512_VDBGtzeeR9', 'name': '3.5cm厚高密度防燃【自帶背膠】||黃色', 'imageUrl': None, 'price': 597, 'stock': 276}]}}, 'video': None, 'details_text_description': '\n<style type="text/css"><!--\nspan.tidied-202311073445-3 {font-size: 14pt;}\n span.tidied-202311073445-2 {color: rgba(0, 0, 0, 0.8); font-family: helvetica, arial, lihei pro, microsoft jhenghei; background-color: #ffffff;}\n span.tidied-202311073445-1 {font-family: inherit;} span.tidied-202312221842-2 {font-size: 14pt;}\n span.tidied-202312221842-1 {color: rgba(0, 0, 0, 0.8); font-family: helvetica, arial, lihei pro, microsoft jhenghei; background-color: #ffffff;}\n--></style><div>\n<div>\n<p><a href="https://www.ruten.com.tw/store/izrv31/" target="_blank"><img alt="" border="0" src="https://ruten-hk-1318392256.cos.ap-hongkong.myqcloud.com/57a9f4a5ba284a33b3e4358651ebfd38.gif"/><img alt="" border="0" src="https://ruten-hk-1318392256.cos.ap-hongkong.myqcloud.com/42e7125355594e20b53112d684c97dce.jpg"/><img alt="" border="0" src="https://ruten-1318392256.cos.ap-singapore.myqcloud.com/%E5%88%86%E9%9A%942.gif"/></a></p>\n</div>\n<p><span class="tidied-202312117205-2"><span class="tidied-202312117205-1"><strong>?【產品名稱】：3D立體隔音棉</strong></span></span></p>\n<p><span class="tidied-202312117205-2"><span class="tidied-202312117205-1"><strong>?【產品風格】：現代簡約</strong></span></span></p>\n<p><span class="tidied-202312117205-2"><span class="tidied-202312117205-1"><strong>?【產品材質】：聚氨酯</strong></span></span></p>\n<p><span class="tidied-202312117205-2"><span class="tidied-202312117205-1"><strong>?【產品尺寸】：50CM*50CM*2CM/3.5CM/5CM/8CM</strong></span></span></p>\n<p><span class="tidied-202312117205-2"><span class="tidied-202312117205-1"><strong>?【產品數量】：10張/套</strong></span></span></p>\n<p><span class="tidied-202312117205-2"><span class="tidied-202312117205-1"><strong>?【產品功能】：全頻隔音、吸音、降噪/阻火防燃/室內裝飾/改善音質</strong></span></span></p>\n<p><span class="tidied-202312117205-2"><span class="tidied-202312117205-1"><strong>?全頻吸音降噪：用於隔音，讓您的家居和商業場所更加安靜和寧靜。</strong></span></span></p>\n<p><span class="tidied-202312117205-2"><span class="tidied-202312117205-1"><strong>?一體成型設計：提供卓越的隔音效果，裝修更加簡便快捷，也更加美觀。</strong></span></span></p>\n<p><span class="tidied-202312117205-2"><span class="tidied-202312117205-1"><strong>?環保無味：選用環保無味的材料，在保障健康同時，讓您的裝修更加環保。</strong></span></span></p>\n<p><span class="tidied-202312117205-2"><span class="tidied-202312117205-1"><strong>?阻火防燃：隔音棉具有阻火性能，避免發生火災事故並保護您和您的家人的生命安全。</strong></span></span></p>\n<p><span class="tidied-202312117205-2"><span class="tidied-202312117205-1"><strong>?自帶背膠：裝修更加簡單方便，無需專業人員，DIY即可完成您想要的隔音效果。</strong></span></span></p>\n<p><img alt="" border="0" src="https://ruten-product-1318392256.cos.ap-hongkong.myqcloud.com/296240d008a94e17904f24f0043e0efd.jpg" width="800"/></p>\n</div>\n', 'detailed_picture': None}}
#
#
# def generate_random_number(length=8):
#     """生成指定位数的随机数字，第一位不为0"""
#     first_digit = random.choice("123456789")  # 第一位1-9
#     other_digits = ''.join(random.choices("0123456789", k=length - 1))  # 其余位0-9
#     return first_digit + other_digits
#
#
# # d1 = []
# # d2 = []
# # structure = {}
# # specs = {}
# # sku_dict = {i['name']: {'imageUrl': i['imageUrl'], 'price': i['price'], 'stock': i['stock']} for i in
# #             data_json['data']['skumodel']['sku_data']['sku_parameter']}
# # price_list = [int(i['price']) for i in data_json['data']['skumodel']['sku_data']['sku_parameter']]
# # min_price = min(price_list)
# # specifications = data_json['data']['specifications']
# # d_new = {}
# # if specifications == 1:
# #     for i in data_json['data']['skumodel']['sku_data']['sku_parameter']:
# #         temp1 = 'temp_' + generate_random_number()
# #         structure[temp1] = []
# #         specs_dict = {
# #             'spec_id': temp1,
# #             'parent_id': 0,
# #             'spec_name': i['name'],
# #             'spec_num': i['stock'],
# #             'spec_price': i['price'],
# #             'spec_status': 'Y',
# #             'childs': [],
# #             'spec_ext': {'goods_no': None}
# #         }
# #         specs[temp1] = specs_dict
# #
# # elif specifications == 2:
# #     for i in data_json['data']['skumodel']['sku_data']['sku_parameter']:
# #         sku1_value, sku2_value = i['name'].split('||')
# #         if sku1_value not in d1:  # 避免重复
# #             d1.append(sku1_value)
# #         if sku2_value not in d2:  # 避免重复
# #             d2.append(sku2_value)
# #     for i in d1:
# #         temp1 = 'temp_' + generate_random_number()
# #         d_new[temp1] = i
# #         d2_dict = {}
# #         for j in d2:
# #             temp2 = 'temp_' + generate_random_number()
# #             d_new[temp2] = j
# #             d2_dict[temp2] = []
# #         structure[temp1] = d2_dict
# #
# #     for key, vlaue in structure.items():
# #         specs_dict = {
# #             'spec_id': key,
# #             'parent_id': '0',
# #             'spec_name': d_new[key],
# #             'spec_num': '0',
# #             'spec_status': 'Y',
# #             'childs': vlaue,
# #             'spec_ext': {'goods_no': None}
# #         }
# #         specs[key] = specs_dict
# #
# #     for key, vlaue in structure.items():
# #         for key1 in vlaue.keys():
# #             total_name = d_new[key] + '||' + d_new[key1]
# #             if total_name in specs_dict:
# #                 spec_status = 'Y'
# #                 spec_num = specs_dict[total_name]['stock']
# #                 spec_price = specs_dict[total_name]['price']
# #             else:
# #                 spec_status = 'N'
# #                 spec_num = '499'
# #                 spec_price = min_price
# #             specs_dict = {
# #                 'spec_id': key1,
# #                 'parent_id': key,
# #                 'spec_name': d_new[key1],
# #                 'spec_num': spec_num,
# #                 'spec_price': spec_price,
# #                 'spec_status': spec_status,
# #                 'childs': [],
# #                 'spec_ext': {'goods_no': None}
# #             }
# #             specs[key1] = specs_dict
# #
# # spec_info = {
# #     'level': specifications,
# #     'structure': structure,
# #     'specs': specs
# # }
# # print(spec_info)
#
#
# def generate_spec_info(data_json):
#     # 提取基础数据
#     sku_parameters = data_json['data']['skumodel']['sku_data']['sku_parameter']
#     # 获取规格数
#     specifications = data_json['data']['specifications']
#
#     # 计算最低价格
#     price_list = [int(i['price']) for i in sku_parameters]
#     min_price = min(price_list) if price_list else 0
#
#     # 初始化数据结构
#     structure = {}
#     specs = {}
#     d_new = {}  # 临时ID映射
#
#     # 单规格处理
#     if specifications == 1:
#         for item in sku_parameters:
#             temp_id = 'temp_' + generate_random_number()
#             structure[temp_id] = []
#
#             specs[temp_id] = {
#                 'spec_id': temp_id,
#                 'parent_id': 0,
#                 'spec_name': item['name'],
#                 'spec_num': item['stock'],
#                 'spec_price': item['price'],
#                 'spec_status': 'Y',
#                 'childs': [],
#                 'spec_ext': {'goods_no': None}
#             }
#     # 双规格处理
#     elif specifications == 2:
#         d1, d2 = [], []  # 规格1和规格2的值列表
#
#         # 收集所有规格值并去重
#         for item in sku_parameters:
#             sku1_value, sku2_value = item['name'].split('||')
#             if sku1_value not in d1:
#                 d1.append(sku1_value)
#             if sku2_value not in d2:
#                 d2.append(sku2_value)
#
#         # 为每个规格值生成临时ID并构建结构
#         for spec1 in d1:
#             temp1 = 'temp_' + generate_random_number()
#             d_new[temp1] = spec1
#             structure[temp1] = {}
#
#             for spec2 in d2:
#                 temp2 = 'temp_' + generate_random_number()
#                 d_new[temp2] = spec2
#                 structure[temp1][temp2] = []
#
#         # 构建规格详情
#         for parent_id, children in structure.items():
#             specs[parent_id] = {
#                 'spec_id': parent_id,
#                 'parent_id': '0',
#                 'spec_name': d_new[parent_id],
#                 'spec_num': '0',
#                 'spec_status': 'Y',
#                 'childs': children,
#                 'spec_ext': {'goods_no': None}
#             }
#
#             for child_id in children.keys():
#                 combined_name = f"{d_new[parent_id]}||{d_new[child_id]}"
#                 sku_item = next((i for i in sku_parameters if i['name'] == combined_name), None)
#
#                 specs[child_id] = {
#                     'spec_id': child_id,
#                     'parent_id': parent_id,
#                     'spec_name': d_new[child_id],
#                     'spec_num': str(sku_item['stock']) if sku_item else '499',
#                     'spec_price': str(sku_item['price']) if sku_item else str(min_price),
#                     'spec_status': 'Y' if sku_item else 'N',
#                     'childs': [],
#                     'spec_ext': {'goods_no': None}
#                 }
#
#     return {
#         'level': specifications,
#         'structure': structure,
#         'specs': specs
#     }
#
#
# # 使用示例
# spec_info = generate_spec_info(data_json)
# print(spec_info)


# import json
#
# # 你的 JSON 数据（已去除前面的描述文字）
# json_data = {'level': 2, 'structure': {'temp_46840693': {'temp_37029562': [], 'temp_55336727': [], 'temp_45814825': [], 'temp_23437288': [], 'temp_78755141': []}, 'temp_53714483': {'temp_66485054': [], 'temp_36838485': [], 'temp_38154319': [], 'temp_13710018': [], 'temp_65940873': []}, 'temp_30102463': {'temp_69006148': [], 'temp_14980004': [], 'temp_67881195': [], 'temp_41537412': [], 'temp_75154279': []}, 'temp_22233345': {'temp_45900256': [], 'temp_88679395': [], 'temp_42982930': [], 'temp_39763140': [], 'temp_31845872': []}, 'temp_78178143': {'temp_81998848': [], 'temp_99515518': [], 'temp_89544101': [], 'temp_70953713': [], 'temp_59820525': []}}, 'specs': {'temp_46840693': {'spec_id': 'temp_46840693', 'parent_id': '0', 'spec_name': 'Lightning－白色', 'spec_num': '0', 'spec_status': 'Y', 'childs': {'temp_37029562': [], 'temp_55336727': [], 'temp_45814825': [], 'temp_23437288': [], 'temp_78755141': []}, 'spec_ext': {'goods_no': ''}}, 'temp_53714483': {'spec_id': 'temp_53714483', 'parent_id': '0', 'spec_name': '安卓micro－黑色', 'spec_num': '0', 'spec_status': 'Y', 'childs': {'temp_66485054': [], 'temp_36838485': [], 'temp_38154319': [], 'temp_13710018': [], 'temp_65940873': []}, 'spec_ext': {'goods_no': ''}}, 'temp_30102463': {'spec_id': 'temp_30102463', 'parent_id': '0', 'spec_name': '安卓micro－白色', 'spec_num': '0', 'spec_status': 'Y', 'childs': {'temp_69006148': [], 'temp_14980004': [], 'temp_67881195': [], 'temp_41537412': [], 'temp_75154279': []}, 'spec_ext': {'goods_no': ''}}, 'temp_22233345': {'spec_id': 'temp_22233345', 'parent_id': '0', 'spec_name': 'Type－C－白色', 'spec_num': '0', 'spec_status': 'Y', 'childs': {'temp_45900256': [], 'temp_88679395': [], 'temp_42982930': [], 'temp_39763140': [], 'temp_31845872': []}, 'spec_ext': {'goods_no': ''}}, 'temp_78178143': {'spec_id': 'temp_78178143', 'parent_id': '0', 'spec_name': 'Type－C－黑色', 'spec_num': '0', 'spec_status': 'Y', 'childs': {'temp_81998848': [], 'temp_99515518': [], 'temp_89544101': [], 'temp_70953713': [], 'temp_59820525': []}, 'spec_ext': {'goods_no': ''}}, 'temp_37029562': {'spec_id': 'temp_37029562', 'parent_id': 'temp_46840693', 'spec_name': '0.25M', 'spec_num': 495, 'spec_price': 18, 'spec_status': 'Y', 'childs': [], 'spec_ext': {'goods_no': ''}}, 'temp_55336727': {'spec_id': 'temp_55336727', 'parent_id': 'temp_46840693', 'spec_name': '1M', 'spec_num': 492, 'spec_price': 22, 'spec_status': 'Y', 'childs': [], 'spec_ext': {'goods_no': ''}}, 'temp_45814825': {'spec_id': 'temp_45814825', 'parent_id': 'temp_46840693', 'spec_name': '1.5M', 'spec_num': 493, 'spec_price': 28, 'spec_status': 'Y', 'childs': [], 'spec_ext': {'goods_no': ''}}, 'temp_23437288': {'spec_id': 'temp_23437288', 'parent_id': 'temp_46840693', 'spec_name': '2M', 'spec_num': 500, 'spec_price': 33, 'spec_status': 'Y', 'childs': [], 'spec_ext': {'goods_no': ''}}, 'temp_78755141': {'spec_id': 'temp_78755141', 'parent_id': 'temp_46840693', 'spec_name': '3M', 'spec_num': 499, 'spec_price': 18, 'spec_status': 'N', 'childs': [], 'spec_ext': {'goods_no': ''}}, 'temp_66485054': {'spec_id': 'temp_66485054', 'parent_id': 'temp_53714483', 'spec_name': '0.25M', 'spec_num': 499, 'spec_price': 18, 'spec_status': 'N', 'childs': [], 'spec_ext': {'goods_no': ''}}, 'temp_36838485': {'spec_id': 'temp_36838485', 'parent_id': 'temp_53714483', 'spec_name': '1M', 'spec_num': 480, 'spec_price': 22, 'spec_status': 'Y', 'childs': [], 'spec_ext': {'goods_no': ''}}, 'temp_38154319': {'spec_id': 'temp_38154319', 'parent_id': 'temp_53714483', 'spec_name': '1.5M', 'spec_num': 495, 'spec_price': 28, 'spec_status': 'Y', 'childs': [], 'spec_ext': {'goods_no': ''}}, 'temp_13710018': {'spec_id': 'temp_13710018', 'parent_id': 'temp_53714483', 'spec_name': '2M', 'spec_num': 497, 'spec_price': 33, 'spec_status': 'Y', 'childs': [], 'spec_ext': {'goods_no': ''}}, 'temp_65940873': {'spec_id': 'temp_65940873', 'parent_id': 'temp_53714483', 'spec_name': '3M', 'spec_num': 492, 'spec_price': 38, 'spec_status': 'Y', 'childs': [], 'spec_ext': {'goods_no': ''}}, 'temp_69006148': {'spec_id': 'temp_69006148', 'parent_id': 'temp_30102463', 'spec_name': '0.25M', 'spec_num': 499, 'spec_price': 18, 'spec_status': 'N', 'childs': [], 'spec_ext': {'goods_no': ''}}, 'temp_14980004': {'spec_id': 'temp_14980004', 'parent_id': 'temp_30102463', 'spec_name': '1M', 'spec_num': 485, 'spec_price': 22, 'spec_status': 'Y', 'childs': [], 'spec_ext': {'goods_no': ''}}, 'temp_67881195': {'spec_id': 'temp_67881195', 'parent_id': 'temp_30102463', 'spec_name': '1.5M', 'spec_num': 491, 'spec_price': 28, 'spec_status': 'Y', 'childs': [], 'spec_ext': {'goods_no': ''}}, 'temp_41537412': {'spec_id': 'temp_41537412', 'parent_id': 'temp_30102463', 'spec_name': '2M', 'spec_num': 497, 'spec_price': 33, 'spec_status': 'Y', 'childs': [], 'spec_ext': {'goods_no': ''}}, 'temp_75154279': {'spec_id': 'temp_75154279', 'parent_id': 'temp_30102463', 'spec_name': '3M', 'spec_num': 499, 'spec_price': 38, 'spec_status': 'Y', 'childs': [], 'spec_ext': {'goods_no': ''}}, 'temp_45900256': {'spec_id': 'temp_45900256', 'parent_id': 'temp_22233345', 'spec_name': '0.25M', 'spec_num': 122, 'spec_price': 18, 'spec_status': 'Y', 'childs': [], 'spec_ext': {'goods_no': ''}}, 'temp_88679395': {'spec_id': 'temp_88679395', 'parent_id': 'temp_22233345', 'spec_name': '1M', 'spec_num': 459, 'spec_price': 22, 'spec_status': 'Y', 'childs': [], 'spec_ext': {'goods_no': ''}}, 'temp_42982930': {'spec_id': 'temp_42982930', 'parent_id': 'temp_22233345', 'spec_name': '1.5M', 'spec_num': 488, 'spec_price': 28, 'spec_status': 'Y', 'childs': [], 'spec_ext': {'goods_no': ''}}, 'temp_39763140': {'spec_id': 'temp_39763140', 'parent_id': 'temp_22233345', 'spec_name': '2M', 'spec_num': 493, 'spec_price': 33, 'spec_status': 'Y', 'childs': [], 'spec_ext': {'goods_no': ''}}, 'temp_31845872': {'spec_id': 'temp_31845872', 'parent_id': 'temp_22233345', 'spec_name': '3M', 'spec_num': 489, 'spec_price': 38, 'spec_status': 'Y', 'childs': [], 'spec_ext': {'goods_no': ''}}, 'temp_81998848': {'spec_id': 'temp_81998848', 'parent_id': 'temp_78178143', 'spec_name': '0.25M', 'spec_num': 499, 'spec_price': 18, 'spec_status': 'N', 'childs': [], 'spec_ext': {'goods_no': ''}}, 'temp_99515518': {'spec_id': 'temp_99515518', 'parent_id': 'temp_78178143', 'spec_name': '1M', 'spec_num': 474, 'spec_price': 22, 'spec_status': 'Y', 'childs': [], 'spec_ext': {'goods_no': ''}}, 'temp_89544101': {'spec_id': 'temp_89544101', 'parent_id': 'temp_78178143', 'spec_name': '1.5M', 'spec_num': 485, 'spec_price': 28, 'spec_status': 'Y', 'childs': [], 'spec_ext': {'goods_no': ''}}, 'temp_70953713': {'spec_id': 'temp_70953713', 'parent_id': 'temp_78178143', 'spec_name': '2M', 'spec_num': 471, 'spec_price': 33, 'spec_status': 'Y', 'childs': [], 'spec_ext': {'goods_no': ''}}, 'temp_59820525': {'spec_id': 'temp_59820525', 'parent_id': 'temp_78178143', 'spec_name': '3M', 'spec_num': 491, 'spec_price': 38, 'spec_status': 'Y', 'childs': [], 'spec_ext': {'goods_no': ''}}}}
#
# # 转换为 Python 字典
# data_dict = json_data
# spec_num = 0
# for spec_value in data_dict['specs'].values():
#     spec_num += int(spec_value['spec_num'])
#
# print(spec_num)

future_to_index = {
    '1': 'a',
    '2': 'b'
}

for i in future_to_index:
    print(i)