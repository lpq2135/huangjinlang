from opencc import OpenCC
converter = OpenCC('s2tw')  # 簡體→台灣繁體
text = "['fdgfd的法国队', 'dfgdfgdfl打开立法机关']"
result = converter.convert(text)
print(result)  # 輸出：簡體轉繁體工具