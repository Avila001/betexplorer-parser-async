import sqlite3
from sqlite3 import Error


def create_connection(db_file):
    """ create a database connection to the SQLite database
        specified by the db_file
    :param db_file: database file
    :return: Connection object or None
    """
    conn = None
    try:
        conn = sqlite3.connect(db_file)
    except Error as e:
        print(e)

    return conn


def update_table(conn, task):
    sql = '''    UPDATE Sofascore
                 SET home_team_exp_xg = ? ,
                     away_team_exp_xg = ?, 
                     exp_diff = ?
                 WHERE home_team = ?
                 AND away_team = ?
                 AND season = ?'''
    cur = conn.cursor()
    cur.execute(sql, task)
    conn.commit()
