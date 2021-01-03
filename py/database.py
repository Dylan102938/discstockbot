import mysql.connector
import time


def connect_db():
    db = mysql.connector.connect(
      host="localhost",
      user="root",
      password="Dylan@5188",
      database="stockbot"
    )

    cursor = db.cursor()
    return db, cursor

def add_user(db, cursor, name, oauth, expires_in, refresh):
    refresh_time = int(time.time()) + expires_in

    query = "SELECT id FROM accounts WHERE name=%s LIMIT 1"
    cursor.execute(query, (name,))
    exists = cursor.fetchall()

    if len(exists) == 1:
        query = "UPDATE accounts SET oauth=%s, refresh_time=%s, refresh=%s WHERE id=%s LIMIT 1"
        cursor.execute(query, (oauth, refresh_time, refresh, exists[0][0]))
        db.commit()
    else:
        query = "INSERT INTO accounts (name, oauth, refresh_time, refresh) VALUES (%s, %s, %s, %s)"
        cursor.execute(query, (name, oauth, refresh_time, refresh))
        db.commit()

def update_user(db, cursor, query, parameters):
    cursor.execute(query, parameters)
    db.commit()
