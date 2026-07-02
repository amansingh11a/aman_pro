import os, json

DB_TYPE = os.environ.get('DB_TYPE', 'mysql')

def _fix_sql(sql):
    return sql.replace('%s', '?') if DB_TYPE == 'sqlite' else sql

def get_conn():
    if DB_TYPE == 'sqlite':
        import sqlite3
        db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'portfolio.db')
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA foreign_keys=ON")
        return conn
    import pymysql
    from config import MYSQL_HOST, MYSQL_USER, MYSQL_PASSWORD, MYSQL_DB, MYSQL_PORT
    return pymysql.connect(
        host=MYSQL_HOST,
        port=MYSQL_PORT,
        user=MYSQL_USER,
        password=MYSQL_PASSWORD,
        database=MYSQL_DB,
        charset='utf8mb4',
        cursorclass=pymysql.cursors.DictCursor
    )

def to_dict(row):
    if row is None: return None
    return row if isinstance(row, dict) else dict(row)

def to_dicts(rows):
    return [to_dict(r) for r in rows]
