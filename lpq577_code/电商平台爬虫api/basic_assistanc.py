import requests
import random
import string

class BaseCrawler:
    """所有爬虫类的基类，包含共用方法"""
    def request_function(self, url, method='GET', headers=None, data=None, proxies=None, files=None, timeout=30, max_retries=5):
        """通用的请求方法"""
        # 进行最多max_retries次重试
        for attempt in range(max_retries):
            try:
                response = requests.request(
                    url=url,
                    method=method.upper(),
                    headers=headers,
                    data=data,
                    proxies=proxies,
                    files=files,
                    timeout=timeout
                )

                # 对于404或400状态码，直接返回响应对象
                if response.status_code in (404, 400):
                    return response

                # 检查HTTP状态码，如果不是2xx会抛出HTTPError异常
                response.raise_for_status()
                return response

            except ReadTimeout as e:
                # 单独处理超时错误
                logging.warning(f"请求超时 ({method}-{url}): {e}. 重试中... ({attempt + 1}/{max_retries})")
                time.sleep(2 ** attempt)  # 指数退避策略

            except RequestException as e:
                if hasattr(e, 'response') and e.response is not None:
                    if e.response.status_code in (404, 400):
                        return e.response
                logging.warning(f"请求错误 ({method}-{url}): {e}. 重试中... ({attempt + 1}/{max_retries})")
                time.sleep(2 ** attempt)

            except Exception as e:
                # 处理其他未知异常
                logging.error(f"未知错误 ({method}-{url}): {e}")
                return None

        logging.error(f"请求失败，已重试{max_retries}次: {url}")
        return None

    def generate_random_string(self, length=10):
        """生成随机字符串"""
        chars = string.ascii_letters + string.digits
        return ''.join(random.choice(chars) for _ in range(length))

    def generate_random_number(self, length=8):
        """生成指定位数的随机数字，第一位不为0"""
        first_digit = random.choice("123456789")  # 第一位1-9
        other_digits = ''.join(random.choices("0123456789", k=length - 1))  # 其余位0-9
        return first_digit + other_digits