import sqlite3

# Connect to database
conn = sqlite3.connect('tejas_qna.db')
c = conn.cursor()

# USERS table (User, Trainer, SME, Admin)
c.execute('''
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    email TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,
    role TEXT CHECK (role IN ('User', 'Trainer', 'SME', 'Admin')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
''')

# PRODUCTS table
c.execute('''
CREATE TABLE IF NOT EXISTS products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL
)
''')

# QUESTIONS table
c.execute('''
CREATE TABLE IF NOT EXISTS questions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    product_id INTEGER,
    question_text TEXT NOT NULL,
    status TEXT DEFAULT 'Pending',  -- Pending, Answered, Escalated, Validated
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    trainer_id INTEGER,
    sme_id INTEGER,
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (product_id) REFERENCES products(id),
    FOREIGN KEY (trainer_id) REFERENCES users(id),
    FOREIGN KEY (sme_id) REFERENCES users(id)
)
''')

# ANSWERS table
c.execute('''
CREATE TABLE IF NOT EXISTS answers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    question_id INTEGER,
    answered_by INTEGER,
    answer_text TEXT NOT NULL,
    validated INTEGER DEFAULT 0,
    overridden INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (question_id) REFERENCES questions(id),
    FOREIGN KEY (answered_by) REFERENCES users(id)
)
''')

# NOTIFICATIONS table
c.execute('''
CREATE TABLE IF NOT EXISTS notifications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    message TEXT,
    type TEXT DEFAULT 'in-app',  -- in-app or email
    is_read INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
)
''')

conn.commit()
conn.close()
print("Database and tables created successfully.")