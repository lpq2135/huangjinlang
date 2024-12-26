import mysql.connector

class MySqlPool:
    def __init__(self, **config):
        self.pool = mysql.connector.pooling.MySQLConnectionPool(pool_name="mypool", pool_size=20, **config)

    def get_conn(self):
        """
        连接欸数据库
        """
        cnx = self.pool.get_connection()
        cursor = cnx.cursor(buffered=True)
        return cnx, cursor

    def close_mysql(self, cnx, cursor):
        """
        关闭数据库
        """
        cursor.close()
        cnx.close()