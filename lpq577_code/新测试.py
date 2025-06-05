from googletrans import Translator
import concurrent.futures

# 每个线程独立创建Translator实例
def translate_text(text):
    translator = Translator(service_urls=['translate.google.com'])
    try:
        return translator.translate(text, src='zh-cn', dest='ur').text
    except Exception as e:
        print(f"翻译失败: {e}")
        return text  # 失败时返回原文

texts = ["你好", "谢谢", "再见", "今天天气真好"]

with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
    results = list(executor.map(translate_text, texts))

print(results)