import math


def split_list(input_list):
    # 将列表按照指定大小切分
    return [input_list[i:i + 50] for i in range(0, len(input_list), 50)]


orig_list = list(range(49))  # 假设的初始列表，有100个数
size = 50  # 切分列表的大小

number_of_lists = math.ceil(len(orig_list) / size)  # 计算需要切分的列表数量
sub_lists = split_list(orig_list)  # 切分列表
print(sub_lists)