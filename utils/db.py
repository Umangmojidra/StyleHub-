"""
utils/db.py - Database helper using PyMySQL
Provides query_db() and get_connection() for the whole application.
"""
import pymysql
import pymysql.cursors
from config import Config


def get_connection():
    """Return a new PyMySQL connection using config values."""
    conn = pymysql.connect(
        host=Config.DB_HOST,
        port=Config.DB_PORT,
        user=Config.DB_USER,
        password=Config.DB_PASSWORD,
        database=Config.DB_NAME,
        charset='utf8mb4',
        cursorclass=pymysql.cursors.DictCursor,
        autocommit=False
    )
    return conn


def query_db(sql, args=(), one=False, commit=False):
    """
    Execute a SQL query and return results as dict(s).

    Parameters
    ----------
    sql    : str   – SQL statement
    args   : tuple – query parameters
    one    : bool  – if True, return single row (or None)
    commit : bool  – if True, commit after execution (for INSERT/UPDATE/DELETE)
    """
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(sql, args)
            if commit:
                conn.commit()
                return None
            result = cursor.fetchone() if one else cursor.fetchall()
            return result
    except Exception:
        if commit:
            conn.rollback()
        raise
    finally:
        conn.close()
