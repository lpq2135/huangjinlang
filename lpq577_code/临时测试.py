import mysql.connector


try:
    mysql_pool = MySqlPool(host='47.122.62.157', password='Qiang123@', user='daraz', database='daraz')
    a = 1
except Exception as e:
    raise e