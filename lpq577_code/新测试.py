def flatten_dict(d, parent_key='', sep='.'):
    """
    递归扁平化嵌套字典，将嵌套的字段使用 dot notation 连接，
    并将 None 转换为空字符串 ""。
    """
    items = []
    for k, v in d.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, dict):
            items.extend(flatten_dict(v, new_key, sep=sep).items())
        elif isinstance(v, list):
            # 如果是列表，将列表转换成字符串，表示空列表 "[]"
            items.append((new_key, str(v) if v else '[]'))
        else:
            # 将值转换成字符串，None 转换为空字符串 ""
            items.append((new_key, "" if v is None else str(v)))
    return dict(items)

# 你的原始数据
spec_info = {"level":2,"structure":{"temp_15668958":{"temp_74158999":[]}},"specs":{"temp_15668958":{"spec_id":"temp_15668958","parent_id":"0","spec_name":"sku1","spec_num":"0","spec_status":"Y","spec_ext":{"goods_no":None},"childs":{"temp_74158999":[]}},"temp_74158999":{"spec_id":"temp_74158999","parent_id":"temp_15668958","spec_name":"sku2","spec_num":"199","spec_price":"199","spec_status":"Y","spec_ext":{"goods_no":None},"childs":[]}}}

# 扁平化
flat_spec_info = flatten_dict(spec_info)

# 打印扁平化后的数据
print(flat_spec_info)
