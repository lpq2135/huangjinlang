import re

text = '()[]kfdjshbj||jkjh'
a = re.sub(r'[^\w\s.,!?:;\'"[\]+\-|]', '', text)
print(a)