import mysql.connector
import logging
import time


class MySqlPool:
    def __init__(self, **config):
        self.pool = mysql.connector.pooling.MySQLConnectionPool(
            pool_name="mypool", pool_size=20, **config
        )

    def get_conn(self):
        """
        连接欸数据库
        """
        for _ in range(4):
            try:
                cnx = self.pool.get_connection()
                cursor = cnx.cursor(buffered=True)
                return cnx, cursor
            except mysql.connector.Error as err:
                logging.error(f"获取数据库连接池新连接失败， 错误信息: {err}")
                time.sleep(2)
        raise err

    def close_mysql(self, cnx, cursor):
        """
        关闭数据库
        """
        # 关闭游标
        if cursor is not None:
            try:
                cursor.close()
            except Exception as e:
                logging.error(f"关闭游标时发生错误: {str(e)}")

        # 关闭连接
        if cnx is not None:
            try:
                if cnx.is_connected():
                    cnx.rollback()
                cnx.close()
            except Exception as e:
                logging.error(f"关闭数据库连接时发生错误: {str(e)}")
