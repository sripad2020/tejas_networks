import sqlite3

db_con=sqlite3.connect('questions.db')
question=db_con.cursor()


'''table='create table if not exists question(question text varchar(5000) NOT NULL,date DATE NOT NULL,username varchar(50) NOT NULL, email varchar(50) NOT NULL)'
question.execute(table)
db_con.commit()
'''

tables='create table if not exists answers_given(question text varchar(5000) NOT NULL,email varchar(50) NOT NULL, answer varchar(10000) NOT NULL,role text NOT NULL)'
question.execute(tables)
db_con.commit()


exe='select * from answers'
print(question.execute(exe).fetchall())