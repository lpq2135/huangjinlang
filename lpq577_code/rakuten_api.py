import requests
import json
from 电商平台爬虫api.basic_assistanc import BaseCrawler


class RakutenProduct(BaseCrawler):
    def __init__(self, store, authorization):
        self.headers = {
            "Authorization": f"ESA {authorization}",
            "Content-Type": "application/json",
        }
        self.store = store

    def create_product(self):
        """新品上架"""
        url = "https://openapi-rms.global.rakuten.com/3.0/products/"
        data = {
            "baseSku": "abc123",
            "variantAttributeNames": {
                "attributeName1": {"zh_TW": "Color"},
                "attributeName2": {"zh_TW": "Size"},
            },
            "variants": "Variants[]",
            "shopCategories": "ShopCategories[]",
            "productListedShops": {
                "shopKey": {"marketplaceIdentifier": "tw", "shopUrl": self.store},
                "title": {"zh_TW": "Title Variant_Product"},
                "description": {"zh_TW": "Description Variant_Product"},
                "marketplaceRakutenCategoryId": "10009",
                "variantInfos": {
                    "Variant_Product_Blue": {"pricing": {"price": 123}},
                    "Variant_Product_Yellow": {"pricing": {"price": 123}},
                },
            },
        }

    def get_product(self):
        """获取商品详细信息"""
        url = "https://openapi-rms.global.rakuten.com/2.0/products/Normal_Product"

    def create_shop_categories(self):
        """创建后台商品分类"""
        url = "https://openapi-rms.global.rakuten.com/2.0/shopcategories/"
        data = {
            "shopKey": {"marketplaceIdentifier": "tw", "shopUrl": self.store},
            "shopCategory": {
                "parentCategoryId": None,
                "categoryName": {"zh_TW": "五金"},
                "shopCategoryId": self.generate_random_string(),
                "image": None,
                "description": {"zh_TW": None},
                "priority": 1,
                "childCategories": None,
            },
        }
        response = self.request_function(
            url, "post", headers=self.headers, data=json.dumps(data)
        ).json()
        return response

    def get_shop_categories(self):
        """获取后台商品分类"""
        url = f"https://openapi-rms.global.rakuten.com/2.0/shopcategories/?marketplaceIdentifier=tw&shopUrl={self.store}&depth=4"
        response = self.request_function(url, headers=self.headers).json()
        return response


if __name__ == "__main__":
    rakuten_istances = RakutenProduct(
        "luinte", "NnZqTGg3dERQVkxWaTN5ZDpIWDlzeGU5YkNUYkQyNTRv"
    )
    result = rakuten_istances.get_shop_categories()
    print(result)
