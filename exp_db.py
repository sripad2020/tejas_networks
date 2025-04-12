import sqlite3

con=sqlite3.connect('expert_logs.db')
cursor=con.cursor()

table='create table if not exists exper_logs(name varchar(50)NOT NULL,email varchar(50) NOT NULL, role varchar(50) NOT NULL,password varchar(50) NOT NULL)'
cursor.execute(table)