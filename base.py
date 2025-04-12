import sqlite3

db=sqlite3.connect('users.db')
cursor=db.cursor()

#user registration
query='create table if not exists user_reg(username varchar(50), email varchar(50), password varchar(50))'
cursor.execute(query)

