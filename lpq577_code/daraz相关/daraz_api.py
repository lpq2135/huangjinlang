import json
import re
import time
import hashlib
import hmac
import urllib.parse
import random
import xmltodict
import itertools
import math

from lpq577_code.电商平台爬虫api.basic_assistanc import BaseCrawler
from datetime import datetime


class DarazBase:
    """
    Daraz平台的API接口基类，封装了通用的请求方法和签名逻辑。
    所有Daraz API相关的操作都应继承此类。
    """

    def __init__(self):
        """初始化API基础配置"""
        # 各国家/地区的API端点
        self.regions = {
            "mm": "https://api.shop.com.mm/rest",  # 缅甸
            "bd": "https://api.daraz.com.bd/rest",  # 孟加拉国
            "pk": "https://api.daraz.pk/rest",  # 巴基斯坦
            "lk": "https://api.daraz.lk/rest",  # 斯里兰卡
            "np": "https://api.daraz.com.np/rest",  # 尼泊尔
        }
        self.app_key = "502742"  # 开发者应用Key
        self.app_secret = "0XGyiUMf0obAP9FueDD16fid4M5xgmaV"  # 开发者应用密钥

    @property
    def timestamp(self):
        """获取当前时间戳（毫秒级）"""
        return int(time.time() * 1000)

    def sign(self, parameters, api_path):
        """
        生成API请求签名（HMAC-SHA256）

        Args:
            parameters: 请求参数键值对
            api_path: API接口路径

        Returns:
            大写的16进制签名字符串
        """
        # 1. 参数按字典序排序
        sort_dict = sorted(parameters)

        # 2. 拼接签名字符串：API路径 + 排序后的参数键值对
        parameters_str = "%s%s" % (
            api_path,
            str().join("%s%s" % (key, parameters[key]) for key in sort_dict),
        )

        # 3. 使用HMAC-SHA256计算签名
        h = hmac.new(
            self.app_secret.encode(),
            parameters_str.encode(),
            digestmod=hashlib.sha256,
        )

        return h.hexdigest().upper()  # 返回大写的签名

    def build_url(self, parameters, api_path):
        """
        构建完整的API请求URL（含签名）

        Args:
            parameters: 请求参数
            api_path: API接口路径

        Returns:
            完整的请求URL
        """
        # 1. 对参数进行URL编码
        query_string = "&".join(
            f"{urllib.parse.quote(k, safe='')}={urllib.parse.quote(str(v), safe='')}"
            for k, v in parameters.items()
        )

        # 2. 处理空格编码（Daraz API特殊要求）
        query_string = query_string.replace("%20", "+")

        # 3. 拼接基础URL
        url = f"{self.site_url}{api_path}?{query_string}"

        # 4. 追加签名参数
        return f"{url}&sign={self.sign(parameters, api_path)}"


class DarazProduct(DarazBase, BaseCrawler):
    """
    daraz上货处理的相关代码，基于daraz后台开放文档一系列的API
    """

    def __init__(self, access_token=None, upload_site=None, attrs=None):
        super().__init__()
        self.upload_site = upload_site  # 上货站点
        self.site_url = self.regions[self.upload_site]  # 获取站点的对应的url
        self.access_token = access_token  # 店铺对应的access_token
        self.attrs = attrs  # 上货数据包
        self.product_id = self.attrs.get("product_id") if self.attrs else None  # 商品ID（编辑时必需）
        self.category_attributes = (
            self.get_category_attributes() if self.attrs else None
        )   # 分类属性（延迟加载）

    def generate_access_token(self, code):
        """
        通过code生成用来获取access_token

        Args:
            code: 店铺的申请代码，用来获取access_token

        Returns:
            店铺的相关参数，包扣ID和过期时间等等
        """
        parameters = {
            "app_key": self.app_key,
            "app_secret": self.app_secret,
            "sign_method": "sha256",
            "timestamp": self.timestamp,
            "code": code,
        }
        url = self.build_url(parameters, "/auth/token/create")
        response = self.request_function(url, "post")
        return response

    def upload_image(self, file_path, photo_name):
        """
        上传本地图片到daraz服务器

        Args:
            file_path: 文件路径
            photo_name: 文件名

        Returns:
            上传后的daraz服务器的图片链接
        """
        parameters = {
            "access_token": self.access_token,
            "app_key": self.app_key,
            "sign_method": "sha256",
            "timestamp": self.timestamp,
        }
        url = self.build_url(parameters, "/image/upload")

        # 打开文件（二进制模式）
        with open(file_path, "rb") as f:
            files = {"image": (photo_name, f)}
            try:
                response = self.request_function(url, "post", files=files)
                image_url = response["data"]["image"]["url"]
                return image_url
            except Exception as e:
                logging.warning(f"daraz本地图片上传失败: {e}")

    def migrate_images(self, images):
        """
        一次性上传多张图片至daraz服务器

        Args:
            images: 图片列表

        Returns:

        """
        photo_data = {"Request": {"Images": {"Url": images}}}

        # 将photo_data的json数据转化成xml格式
        xml_photo_data = xmltodict.unparse(photo_data)
        parameters = {
            "payload": xml_photo_data,
            "access_token": self.access_token,
            "app_key": self.app_key,
            "sign_method": "sha256",
            "timestamp": self.timestamp,
        }
        url = self.build_url(parameters, "/images/migrate")
        response = self.request_function(url, "post")

        # 获取batch_id用于获取图片的响应
        batch_id = response["batch_id"]
        result = self.image_response_get(batch_id)
        if result["status_code"] == 0:
            logging.info(
                f"{self.product_id}-{self.upload_site}-图片上传daraz服务器成功"
            )
            return result["data"]
        elif result["status_code"] == 1:
            retry += 1
            time.sleep(2)
            logging.warning(
                f"{self.product_id}-{self.upload_site}-daraz网络图片重新获取, 重试第{retry}次"
            )
        elif result["status_code"] == 2:
            return None

    def migrate_image(self, images):
        """上传单张网络图片"""
        photo_data = {"Request": {"Image": {"Url": images}}}
        # 将 json 转化成 xml 格式
        xml_photo_data = xmltodict.unparse(photo_data)
        parameters = {
            "payload": xml_photo_data,
            "access_token": self.access_token,
            "app_key": self.app_key,
            "sign_method": "sha256",
            "timestamp": self.timestamp,
        }
        url = self.build_url(parameters, "/image/migrate")
        try:
            response = self.request_function(url, "post")
            return response["data"]["url"]
        except Exception as e:
            logging.warning(f"{self.product_id}-daraz网络图片上传失败（单张）: {e}")

    def image_response_get(self, batch_id):
        """
        针对MigrateImages API的返回信息
        """
        for _ in range(3):
            parameters = {
                "batch_id": batch_id,
                "access_token": self.access_token,
                "app_key": self.app_key,
                "sign_method": "sha256",
                "timestamp": self.timestamp,
            }
            url = self.build_url(parameters, "/image/response/get")
            try:
                time.sleep(3)
                response = self.perform_request(url, "get")
                if response["code"] == "0":
                    images = [i["url"] for i in response["data"]["images"]]
                    return {"status_code": 0, "data": images}
                elif response["code"] == "1000":
                    return {"status_code": 1, "data": None}
                elif response["code"] == "301":
                    return {"status_code": 2, "data": None}
                else:
                    logging.warning(
                        f"{self.product_id}-{self.upload_site}-daraz网络图片获取异常（多张）,重试第{_ + 1}次"
                    )
                    time.sleep(3)
            except Exception:
                logging.warning(
                    f"{self.product_id}-{self.upload_site}-daraz网络图片获取异常（多张）,重试第{_ + 1}次"
                )
                time.sleep(3)
        return {"status_code": 1, "data": None}

    def get_category_attributes(self):
        """
        获取类别属性
        :return:
        """
        parameters = {
            "access_token": self.access_token,
            "app_key": self.app_key,
            "sign_method": "sha256",
            "timestamp": self.timestamp,
            "primary_category_id": self.attrs.get("primary_category"),
            "language_code": "en_US",
        }
        url = self.build_url(parameters, "/category/attributes/get")
        time.sleep(2)
        for _ in range(5):
            try:
                result = self.perform_request(url, "get")
                if result["code"] == "0":
                    is_mandatory_attributes = {
                        "data": [
                            x
                            for x in result["data"]
                            if x["attribute_type"] == "normal"
                            and x["is_mandatory"] == 1
                            and x["name"] != "name"
                            and x["name"] != "name_en"
                            and x["name"] != "short_description"
                            and x["name"] != "short_description_en"
                            and x["name"] != "description_en"
                            and x["name"] != "brand"
                        ]
                    }
                    is_mandatory_sku = [
                        x
                        for x in result["data"]
                        if x["attribute_type"] == "sku"
                        and x["is_sale_prop"] == 1
                        and x["name"] != "SellerSku"
                        and x["name"] != "price"
                        and x["name"] != "package_weight"
                        and x["name"] != "package_length"
                        and x["name"] != "package_width"
                        and x["name"] != "package_height"
                        and x["name"] != "__images__"
                        and x["name"] != "quantity"
                        and x["name"] != "special_price"
                        and x["name"] != "special_from_date"
                        and x["name"] != "special_to_date"
                        and x["name"] != "seller_promotion"
                        and x["name"] != "package_content"
                    ]
                    return is_mandatory_attributes, is_mandatory_sku
                elif result["code"] == "4228":
                    return {"status": False, "data": "此类目在该站点不合法"}
                elif result["code"] == "4227":
                    return {"status": False, "data": "此类目在该站点不存在"}
                elif result["code"] == "IllegalAccessToken":
                    return {"status": False, "data": "access_token异常"}
            except Exception as e:
                logging.warning(
                    f"{self.product_id}-获取类目属性失败，重试第{_ + 1}次，错误信息：{e}"
                )
                time.sleep(2)
        return None

    def assembly_attributes(self, sku_transformation_list):
        """
        对详情进行处理，若需要在详情展示sku属性信息，则判断sku属性的数量进行拆分，列表项最多为10；若不需要在详情展示sku属性信息，则填充在
        【veiw more】 的详情页面
        """

        # 列表处理函数
        def split_into_tens(number):
            base = math.floor(number / 10)
            larger_number = math.ceil(number / 10)
            larger_number_count = number % 10
            result = [larger_number] * larger_number_count + [base] * (
                10 - larger_number_count
            )
            return result

        # 拆分列表
        def split_list_into_tens(lst):
            divisions = split_into_tens(len(lst))
            it = iter(lst)
            output = [list(itertools.islice(it, i)) for i in divisions]
            return output

        dict_attributes = self.category_attributes[0]
        # 获取标题
        title = (self.attrs.get("title").replace(",", "")).replace('"', "")
        # 获取白底图
        promotion_whitebkg_image = self.attrs.get("promotion_whitebkg_image")
        if promotion_whitebkg_image:
            photo_name = promotion_whitebkg_image["photo_name"]
            photo_xpath = (
                r"D:/Daraz运营工具/Daraz采集组装工具/附件库/图片下载/" + photo_name
            )
        # 获取详情文字
        details_text_description = (
            self.attrs.get("details_text_description")
            if self.attrs.get("details_text_description")
            else []
        )
        # 处理详情图片成html格式
        detailed_picture_html = "".join(
            f'<img src="{url}" alt="Image">'
            for url in self.attrs.get("detailed_picture")
        )

        # 处理最终的html格式
        if sku_transformation_list:
            if len(sku_transformation_list) <= 10:
                sku_text_description_html = (
                    "<ul>"
                    + "".join(f"<li>{item}</li>" for item in sku_transformation_list)
                    + "</ul>"
                )
            else:
                sku_output = split_list_into_tens(sku_transformation_list)
                sku_text_description_html = (
                    "<ul>"
                    + "".join(
                        f'<li>{"  ?  ".join(map(str, i))}</li>' for i in sku_output
                    )
                    + "</ul>"
                )
            # 处理详情文字html格式
            details_text_description_html = (
                '<article class="lzd-article" style="white-space:break-spaces"><p style="line-height:1.7;text-align:left;text-indent:0;margin-left:0;margin-top:0;margin-bottom:0"><span style="font-weight:bold;background-color:rgb(153, 204, 255);font-size:18pt">Product Introduction:</span></p>'
                + "".join(
                    f'<p style="font-size:12pt">● {item}</p>'
                    for item in details_text_description
                )
                + "</ul>"
            )
            html_all = details_text_description_html + "<br/>" + detailed_picture_html
            # 组装上货属性值
            product_Attributes = {
                "name": title,
                "name_en": title,
                "short_description": sku_text_description_html,
                "short_description_en": sku_text_description_html,
                "description": html_all,
                "description_en": html_all,
                "brand": "No Brand",
                "promotion_whitebkg_image": (
                    self.upload_image(photo_xpath, photo_name)
                    if promotion_whitebkg_image
                    else None
                ),
            }
        else:
            if len(details_text_description) <= 10:
                details_text_description_html = (
                    "<ul>"
                    + "".join(f"<li>{item}</li>" for item in details_text_description)
                    + "</ul>"
                )
            else:
                details_text_output = split_list_into_tens(details_text_description)
                details_text_description_html = (
                    "<ul>"
                    + "".join(
                        f'<li>{"  ?  ".join(map(str, i))}</li>'
                        for i in details_text_output
                    )
                    + "</ul>"
                )
            # 组装上货属性值
            product_Attributes = {
                "name": title,
                "name_en": title,
                "short_description": details_text_description_html,
                "short_description_en": details_text_description_html,
                "description": detailed_picture_html,
                "description_en": detailed_picture_html,
                "brand": "No Brand",
                "promotion_whitebkg_image": (
                    self.upload_image(photo_xpath, photo_name)
                    if promotion_whitebkg_image
                    else None
                ),
            }
        for x in dict_attributes["data"]:
            if x["name"] == "warranty_type":
                product_Attributes[x["name"]] = "No Warranty"
            elif "options" in x:
                if any("Not Specified" in option.values() for option in x["options"]):
                    product_Attributes[x["name"]] = "Not Specified"
                elif any("Standard" in option.values() for option in x["options"]):
                    product_Attributes[x["name"]] = "Standard"
                elif any("-" in option.values() for option in x["options"]):
                    product_Attributes[x["name"]] = "-"
                else:
                    product_Attributes[x["name"]] = x["options"][0]["name"]
            else:
                product_Attributes[x["name"]] = "See description"

        return product_Attributes

    def assembly_skus(self):
        """
        声明自定义变体，组装sku数据
        """

        def formatted_time():
            current_time = datetime.now()
            formatted_time = current_time.strftime("%Y-%m-%d")
            return formatted_time

        def add_quantity():
            return random.randint(500, 999)

        def add_images():
            return None if i["imageUrl"] is None else {"Image": i["imageUrl"]}

        def process_sku(
            specifications,
            i,
            sku1_property=None,
            sku1_property_value=None,
            sku2_property=None,
            sku2_property_value=None,
        ):
            sale_prop = (
                {sku1_property: sku1_property_value}
                if specifications == 1
                else {
                    sku1_property: sku1_property_value,
                    sku2_property: sku2_property_value,
                }
            )
            skus = {
                "SellerSku": self.generate_random_number(8),
                "quantity": add_quantity(),
                "price": i["price"],
                "special_price": int(i["price"] * 0.97),
                "special_from_date": formatted_time(),
                "special_to_date": "2029-12-31",
                "package_length": self.attrs.get("length"),
                "package_height": self.attrs.get("height"),
                "package_weight": self.attrs.get("weight"),
                "package_width": self.attrs.get("width"),
                "package_content": self.product_id,
                "Images": add_images(),
                "saleProp": sale_prop,
            }
            return skus

        def process_variation(specifications, sku1_property=None, sku2_property=None):
            is_mandatory_sku = self.category_attributes[1]
            name_list = [item["name"] for item in is_mandatory_sku]
            hasImage = (
                True if sku_data["sku_parameter"][0]["imageUrl"] is not None else False
            )
            properties = [
                prop for prop in [sku1_property, sku2_property] if prop is not None
            ]
            customize = not all(
                any(prop in name for name in name_list) for prop in properties
            )
            if customize:
                sku1_property = sku1_property.title()
                sku2_property = sku2_property.title() if sku2_property else None
            else:
                sku1_property = next(x for x in name_list if sku1_property in x)
                sku2_property = (
                    next(
                        x
                        for x in (item["name"] for item in is_mandatory_sku)
                        if sku2_property in x
                    )
                    if sku2_property
                    else None
                )
            if specifications == 2:
                if sku1_property == sku2_property:
                    customize = True
                    sku1_property = "Variants_1"
                    sku2_property = "Variants_2"
            variation1 = {
                "name": sku1_property,
                "hasImage": hasImage,
                "customize": customize,
                "options": {"option": []},
            }
            if specifications == 1:
                variation = {"variation1": variation1}
                return variation, hasImage, sku1_property
            elif specifications == 2:
                variation2 = {
                    "name": sku2_property,
                    "hasImage": False,
                    "customize": customize,
                    "options": {"option": []},
                }
                variation = {"variation1": variation1, "variation2": variation2}
                return variation, hasImage, sku1_property, sku2_property

        def process_tips(
            specifications,
            hasImage,
            price,
            sku1_property,
            sku1_property_value,
            sku2_property=None,
            sku2_property_value=None,
        ):
            skus_under_description = {
                "SellerSku": self.generate_random_number(8),
                "quantity": 0,
                "package_length": 10,
                "package_height": 10,
                "package_weight": 0.1,
                "package_width": 10,
                "price": price,
                "special_from_date": formatted_time(),
                "special_to_date": "2029-12-31",
                "Images": (
                    {
                        "Image": (
                            "https://static-01.daraz.pk/p/3c32f9a77a8232967e996a93524d459a.jpg"
                            if self.upload_site == "pk"
                            else "https://static-01.daraz.com.bd/p/3c32f9a77a8232967e996a93524d459a.jpg"
                        )
                    }
                    if hasImage
                    else None
                ),
                "package_content": self.product_id,
            }
            if specifications == 1:
                skus_under_description.update(
                    {"saleProp": {sku1_property: sku1_property_value}}
                )
            elif specifications == 2:
                skus_under_description.update(
                    {
                        "saleProp": {
                            sku1_property: sku1_property_value,
                            sku2_property: sku2_property_value,
                        }
                    }
                )
            return skus_under_description

        sku_data = self.attrs.get("skumodel")["sku_data"]
        product_Skus = {"Sku": []}
        specifications = self.attrs.get("specifications")
        sku_transformation_list = []
        sku1_transformation_list = []
        sku2_transformation_list = []
        sku_deduplication = set()
        # 无规格
        if specifications == 0:
            skus = {
                "SellerSku": self.generate_random_number(8),
                "quantity": random.randint(500, 999),
                "price": sku_data["price"],
                "special_price": int(sku_data["price"] * 0.97),
                "special_from_date": formatted_time(),
                "special_to_date": "2029-12-31",
                "package_length": self.attrs.get("length"),
                "package_height": self.attrs.get("height"),
                "package_weight": self.attrs.get("weight"),
                "package_width": self.attrs.get("width"),
                "package_content": self.product_id,
            }
            product_Skus["Sku"].append(skus)
            variation = {}
        # 单规格
        elif specifications == 1:
            count = 1
            sku_percentage = self.check_sku(specifications)
            sku1_property = sku_data["sku_property_name"]["sku1_property_name"]
            variation, hasImage, sku1_property = process_variation(
                specifications, sku1_property
            )
            for i in sku_data["sku_parameter"]:
                if i["name"] in sku_deduplication:
                    continue
                sku_deduplication.add(i["name"])
                if hasImage and i["imageUrl"] is None:
                    continue
                if len(i["name"]) > 20 and sku_percentage["sku1_percentage"] <= 0.2:
                    continue
                sku1_property_value = (
                    i["name"]
                    if sku_percentage["sku1_percentage"] <= 0.2
                    else sku1_property.title() + "_" + str(count)
                )
                skus = process_sku(
                    specifications, i, sku1_property, sku1_property_value
                )
                product_Skus["Sku"].insert(0, skus)
                if (
                    sku1_property_value
                    not in variation["variation1"]["options"]["option"]
                ):
                    variation["variation1"]["options"]["option"].append(
                        sku1_property_value
                    )
                if sku_percentage["sku1_percentage"] > 0.2:
                    sku1_transformation_list.append(
                        sku1_property_value + ": " + i["name"]
                    )
                    count += 1
            if sku_percentage["sku1_percentage"] > 0.2:
                skus_under_description = process_tips(
                    specifications,
                    hasImage,
                    i["price"],
                    sku1_property,
                    "Skus in details",
                )
                product_Skus["Sku"].append(skus_under_description)
                variation["variation1"]["options"]["option"].append("Skus in details")
            sku_transformation_list = sku1_transformation_list
            return product_Skus, variation, sku_transformation_list

        # 双规格
        elif specifications == 2:
            unique_sku1, unique_sku2 = {}, {}
            count1 = 1
            count2 = 1
            sku_percentage = self.check_sku(specifications)
            sku1_property = sku_data["sku_property_name"]["sku1_property_name"]
            sku2_property = sku_data["sku_property_name"]["sku2_property_name"]
            variation, hasImage, sku1_property, sku2_property = process_variation(
                specifications, sku1_property, sku2_property
            )
            for i in sku_data["sku_parameter"]:
                if i["name"] in sku_deduplication:
                    continue
                sku_deduplication.add(i["name"])
                if hasImage and i["imageUrl"] is None:
                    continue
                sku1_value, sku2_value = i["name"].split("||")
                if len(sku1_value) > 20 and sku_percentage["sku1_percentage"] <= 0.2:
                    continue
                if sku1_value not in unique_sku1:
                    unique_sku1[sku1_value] = count1
                    count1 += 1
                sku1_property_value = (
                    sku1_value
                    if sku_percentage["sku1_percentage"] <= 0.2
                    else sku1_property.title() + "_" + str(unique_sku1[sku1_value])
                )
                if len(sku2_value) > 20 and sku_percentage["sku2_percentage"] <= 0.2:
                    continue
                if sku2_value not in unique_sku2:
                    unique_sku2[sku2_value] = count2
                    count2 += 1
                sku2_property_value = (
                    sku2_value
                    if sku_percentage["sku2_percentage"] <= 0.2
                    else sku2_property.title() + "_" + str(unique_sku2[sku2_value])
                )

                skus = process_sku(
                    specifications,
                    i,
                    sku1_property,
                    sku1_property_value,
                    sku2_property,
                    sku2_property_value,
                )
                if (
                    sku1_property_value
                    not in variation["variation1"]["options"]["option"]
                ):
                    variation["variation1"]["options"]["option"].append(
                        sku1_property_value
                    )
                if (
                    sku2_property_value
                    not in variation["variation2"]["options"]["option"]
                ):
                    variation["variation2"]["options"]["option"].append(
                        sku2_property_value
                    )
                if sku_percentage["sku1_percentage"] > 0.2:
                    if (
                        sku1_property_value + ": " + sku1_value
                        not in sku1_transformation_list
                    ):
                        sku1_transformation_list.append(
                            sku1_property_value + ": " + sku1_value
                        )
                if sku_percentage["sku2_percentage"] > 0.2:
                    if (
                        sku2_property_value + ": " + sku2_value
                        not in sku2_transformation_list
                    ):
                        sku2_transformation_list.append(
                            sku2_property_value + ": " + sku2_value
                        )
                product_Skus["Sku"].insert(0, skus)
            if sku_percentage["sku1_percentage"] > 0.2:
                skus_under_description = process_tips(
                    specifications,
                    hasImage,
                    i["price"],
                    sku1_property,
                    "Skus in details",
                    sku2_property,
                    variation["variation2"]["options"]["option"][0],
                )
                product_Skus["Sku"].append(skus_under_description)
                variation["variation1"]["options"]["option"].append("Skus in details")
            else:
                if sku_percentage["sku2_percentage"] > 0.2:
                    skus_under_description = process_tips(
                        specifications,
                        hasImage,
                        i["price"],
                        sku1_property,
                        variation["variation1"]["options"]["option"][0],
                        sku2_property,
                        "Skus in details",
                    )
                    product_Skus["Sku"].append(skus_under_description)
                    variation["variation2"]["options"]["option"].append(
                        "Skus in details"
                    )
            sku_transformation_list = (
                sku1_transformation_list + sku2_transformation_list
            )
        return product_Skus, variation, sku_transformation_list

    def get_category_tree(self):
        """
        获取类目树
        :return:系统中所有产品类别的列表
        """
        parameters = {
            "access_token": self.access_token,
            "app_key": self.app_key,
            "sign_method": "sha256",
            "timestamp": self.timestamp,
        }
        url = self.build_url(parameters, "/category/tree/get")
        return self.perform_request(url, "post")

    def create_product(self):
        """
        创建产品
        """
        if "status" not in self.category_attributes:
            product_Skus, variation, sku_transformation_list = self.assembly_skus()
            images = self.migrate_images(self.attrs.get("main_images"))
            if images:
                json_product_data = {
                    "Request": {
                        "Product": {
                            "PrimaryCategory": self.attrs.get("primary_category"),
                            "Images": {"Image": images},
                            "Attributes": self.assembly_attributes(
                                sku_transformation_list
                            ),
                            "Skus": product_Skus,
                        }
                    }
                }
                if variation:
                    json_product_data["Request"]["Product"]["variation"] = variation
                xml_product_data = xmltodict.unparse(json_product_data)
                parameters = {
                    "payload": xml_product_data,
                    "app_key": self.app_key,
                    "sign_method": "sha256",
                    "access_token": self.access_token,
                    "timestamp": self.timestamp,
                }
                sign = self.sign(parameters, "/product/create")
                url = self.site_url + "/product/create"
                parameters["sign"] = sign
                time.sleep(3)
                for _ in range(6):
                    result = self.perform_request(url, "post", data=parameters)
                    if result["code"] == "0":
                        return {
                            "upload_site": self.upload_site,
                            "upload_code": 0,
                            "product_id": self.product_id,
                            "data": "商品上传成功",
                            "item_id": result["data"]["item_id"],
                        }
                    elif result["code"] == "ApiCallLimit":
                        time.sleep(3)
                    elif result["code"] == "500":
                        return {
                            "upload_site": self.upload_site,
                            "upload_code": -1,
                            "product_id": self.product_id,
                            "data": "商品上传出现状态码500错误",
                        }
                    elif result["code"] == "IllegalAccessToken":
                        return {
                            "upload_site": self.upload_site,
                            "upload_code": -2,
                            "product_id": self.product_id,
                            "data": "accesstoken错误",
                        }
                    elif result["code"] == "4221":
                        return {
                            "upload_site": self.upload_site,
                            "upload_code": -3,
                            "product_id": self.product_id,
                            "data": "平台限制产品上传(可能违规)",
                        }
                    elif result["code"] == "5":
                        return {
                            "upload_site": self.upload_site,
                            "upload_code": -4,
                            "product_id": self.product_id,
                            "data": "数据包错误(异常请求)",
                        }
                    elif result["code"] == "209":
                        return {
                            "upload_site": self.upload_site,
                            "upload_code": -9,
                            "product_id": self.product_id,
                            "data": "规格的长度超过50",
                        }
                    else:
                        return {
                            "upload_site": self.upload_site,
                            "upload_code": -5,
                            "product_id": self.product_id,
                            "data": "上传未知异常",
                        }
            else:
                return {
                    "upload_site": self.upload_site,
                    "upload_code": -6,
                    "product_id": self.product_id,
                    "data": "商品主图出现304异常",
                }
        return {
            "upload_site": self.upload_site,
            "upload_code": -7,
            "product_id": self.product_id,
            "data": self.category_attributes["data"],
        }

    def get_product_list(self):
        """
        获取产品的详细信息
        :return: 产品信息
        """
        parameters = {
            "access_token": self.access_token,
            "app_key": self.app_key,
            "sign_method": "sha256",
            "timestamp": self.timestamp,
            "filter": "live",
        }
        url = self.build_url(parameters, "/products/get")
        return self.request_function(url).json()

    def product_remove(self, sku_id_list):
        """
        获取产品的详细信息
        :return: 产品信息
        """
        parameters = {
            "access_token": self.access_token,
            "app_key": self.app_key,
            "sign_method": "sha256",
            "timestamp": self.timestamp,
            "sku_id_list": json.dumps(sku_id_list),
        }
        url = self.build_url(parameters, "/product/remove")
        return self.request_function(url, "post")


class DarazPrice:
    """daraz价格计算"""

    def calculate_local_price(self, upload_site, original_price, weight):
        """
        根据站点进行定价计算

        Args:
            upload_site: 上传站点
            original_price: 原始价格
            weight: 重量

        Returns:
            计算后的当地货币的价格
        """
        """
        根据站点进行定价计算
        """
        usd_to_cny = 7.14  # 美元-人民币汇率
        label_fee = 2.5  # 贴单
        additional_fee_by_1688 = 5  # 1688产生的额外费用
        if upload_site == "pk":
            acceptance_rate = 0.7  # 签收率
            dommission_rate = 0.0978  # 产品佣金（类目）
            us_to_local = 278.8  # 巴基斯坦卢比-美金 汇率
            order_handling_fee = 0.07  # usd
            final_freight_vat = 0.1  # usd
            payment_fee = 0.08  # 回款手续费
            first_leg_cross_border_freight = (
                65 / usd_to_cny * weight if weight <= 0.15 else 80 / usd_to_cny * weight
            )  # 头程跨境运费
        elif upload_site == "bd":
            acceptance_rate = 0.7  # 签收率
            dommission_rate = 0.089  # 产品佣金（类目）
            us_to_local = 119.15  # 孟加拉塔卡-美金 汇率
            order_handling_fee = 0.05  # usd
            final_freight_vat = 0.12  # usd
            payment_fee = 0.085  # 回款手续费
            first_leg_cross_border_freight = (
                90 / usd_to_cny * weight if weight <= 0.15 else 95 / usd_to_cny * weight
            )  # 头程跨境运费
        price = float(original_price)
        # 物流操作费
        logistics_operation_fee = 2 / usd_to_cny if weight <= 0.15 else 3.5 / usd_to_cny
        # 头程运费总计
        total_first_leg_freight = (
            first_leg_cross_border_freight + logistics_operation_fee
        )
        # 根据采购价计算利润
        profit = 10 if price <= 10 else price
        # 采购价 + 利润
        fod = (profit + price + label_fee + additional_fee_by_1688) / usd_to_cny
        # 美金售价
        price_in_us_dollars = (
            total_first_leg_freight + fod + order_handling_fee + final_freight_vat
        ) / (1 - payment_fee - dommission_rate)
        # 当地售价
        price_in_pk_dollars = price_in_us_dollars * us_to_local
        # 最终售价
        final_price_in_pk_dollars = price_in_pk_dollars / acceptance_rate

        return int(final_price_in_pk_dollars)




class DarazMessages(DarazBase):
    def __init__(self, upload_site, access_token):
        super().__init__()
        self.app_key = "503292"
        self.app_secret = "XOjMikmEOqQ6YEyhUM8EDGfaS1QH3Axp"
        self.upload_site = upload_site
        self.site_url = self.regions[self.upload_site]
        self.access_token = access_token

    def get_session_list(self):
        parameters = {
            "access_token": self.access_token,
            "app_key": self.app_key,
            "app_secret": self.app_secret,
            "sign_method": "sha256",
            "timestamp": self.timestamp,
            "start_time": self.timestamp,
            "page_size": "20",
        }
        session_list = []
        url = self.build_url(parameters, "/im/session/list")
        for _ in range(5):
            result = self.perform_request(url, "get")
            if result["code"] == "0":
                for i in result["data"]["session_list"]:
                    if i["title"] == "Daraz Official":
                        continue
                    session_list.append(i)
                return len(session_list)


if __name__ == "__main__":
    daraz_product = DarazProduct(
        "50000401a20jg2sqgXDCq9NvYkmIuJve1f79a538vTIiXAspFtOWpsrY8dGioe", "pk"
    )
    product_data = daraz_product.products_get()
    print(product_data)
