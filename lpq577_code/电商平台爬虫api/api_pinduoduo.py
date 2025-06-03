import json
import ast
import random
from .basic_assistanc import BaseCrawler


class PinDuoDuo(BaseCrawler):
    """此类用于处理拼多多商品数据包"""

    def __init__(self, data):
        self.data = data
        self.product_id = self.get_product_id()
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
        }

    def get_title(self):
        """获取商品标题"""
        title = self.data["store"]["initDataObj"]["goods"]["goodsName"]
        return title

    def get_product_id(self):
        """获取商品id"""
        product_id = self.data["store"]["initDataObj"]["goods"]["goodsID"]
        return str(product_id)

    def get_main_images(self):
        """获取商品主图"""
        main_images = self.data["store"]["initDataObj"]["goods"]["viewImageData"][:8]
        return main_images

    def get_videos(self):
        """获取商品视频"""
        if "url" in self.data["store"]["initDataObj"]["goods"]["videoGallery"]:
            video = self.data["store"]["initDataObj"]["goods"]["videoGallery"][0]["url"]
            return video
        return None

    def get_product_attribute(self):
        """获取详情文字"""
        Filter_words = [
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
        goods_property = self.data["store"]["initDataObj"]["goods"]["goodsProperty"]
        # 若详情文字的标题包含过滤词则过滤
        description = [
            f"{i['key']} : {i['values'][0]}"
            for i in goods_property
            if not any(filter_word in i["key"] for filter_word in Filter_words)
        ]
        return description

    def get_product_detail_images(self):
        """获取详情图片"""
        detail_images = self.data["store"]["initDataObj"]["goods"]["detailGallery"]
        return [i["url"] for i in detail_images]

    def build_product_package(self):
        """组装数据包"""
        # specs 数据包包含了sku的详细信息
        skus_data = self.data["store"]["initDataObj"]["goods"]["skus"]
        # 规格数
        specifications = len(skus_data[0]["specs"])

        if specifications == 0:
            pass

        if specifications == 1:
            sku1_property_name = skus_data[0]["specs"][0]["spec_key"]
            sku_assembly = {
                "sku_data": {
                    "sku_property_name": {"sku1_property_name": sku1_property_name},
                    "sku_parameter": [],
                }
            }
            for i in skus_data:
                stock = i["quantity"]
                if stock == 0:
                    continue
                skus = {
                    "remote_id": self.product_id
                    + "_"
                    + self.generate_random_string(10),
                    "name": i["specs"][0]["spec_value"],
                    "imageUrl": i.get("thumbUrl", None),
                    "price": i["normalPrice"],
                    "stock": stock,
                }
                sku_assembly["sku_data"]["sku_parameter"].append(skus)

        elif specifications == 2:
            sku1_property_name = skus_data[0]["specs"][0]["spec_key"]
            sku2_property_name = skus_data[0]["specs"][1]["spec_key"]
            sku_assembly = {
                "sku_data": {
                    "sku_property_name": {
                        "sku1_property_name": sku1_property_name,
                        "sku2_property_name": sku2_property_name,
                    },
                    "sku_parameter": [],
                }
            }
            for i in skus_data:
                stock = i["quantity"]
                if stock == 0:
                    continue
                skus = {
                    "remote_id": self.product_id
                    + "_"
                    + self.generate_random_string(10),
                    "name": i["specs"][0]["spec_value"]
                    + "||"
                    + i["specs"][1]["spec_value"],
                    "imageUrl": i.get("thumbUrl", None),
                    "price": i["normalPrice"],
                    "stock": stock,
                }
                sku_assembly["sku_data"]["sku_parameter"].append(skus)

        else:
            return {
                "platform": "pinduoduo",
                "code": 5,
                "message": "sku规格数超出",
                "product_id": self.product_id,
            }

        product_package = {
            "product_id": self.product_id,
            "specifications": specifications,
            "unit_weight": None,
            "start_amount": None,
            "title": self.get_title(),
            "main_images": self.get_main_images(),
            "skumodel": sku_assembly,
            "video": self.get_videos(),
            "details_text_description": self.get_product_attribute(),
            "detailed_picture": self.get_product_detail_images(),
        }
        return {
            "platform": "pinduoduo",
            "code": 0,
            "message": "请求成功",
            "data": product_package,
        }
