unit_weight = 0.3
mysql_weight = 0.4
if unit_weight is None:
    weight = mysql_weight
else:
    weight = min(float(unit_weight), mysql_weight)
print(weight)