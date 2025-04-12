import datetime
from flask_dance.contrib.github import make_github_blueprint,github
from flask import Flask, render_template, request, redirect, session, url_for, flash,jsonify
import sqlite3
import google.generativeai as genai
from nltk import sent_tokenize, word_tokenize, FreqDist
from nltk.corpus import stopwords
from werkzeug.security import generate_password_hash, check_password_hash
import re,os
import time,json
import base64
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders


app = Flask(__name__)
app.secret_key = 'supersecretkey'

github_bprint=make_github_blueprint(client_id='Ov23liuMhMUiP4XvXpXc',
                                    client_secret='d885ef6b013700824f1aa5201a0e89d01345fe2c')

sender_email = 'sripadkarthik@gmail.com'
password = 'tljl ermy eptq psjg'


def convert_paragraph_to_points(paragraph, num_points=5):
    sentences = sent_tokenize(paragraph)
    words = word_tokenize(paragraph.lower())
    stop_words = set(stopwords.words('english'))
    filtered_words = [word for word in words if word.isalnum() and word not in stop_words]
    freq_dist = FreqDist(filtered_words)
    sentence_scores = {}
    for sentence in sentences:
        sentence_word_tokens = word_tokenize(sentence.lower())
        sentence_word_tokens = [word for word in sentence_word_tokens if word.isalnum()]
        score = sum(freq_dist.get(word, 0) for word in sentence_word_tokens)
        sentence_scores[sentence] = score
    sorted_sentences = sorted(sentence_scores, key=sentence_scores.get, reverse=True)
    key_points = sorted_sentences[:num_points]
    return key_points

def clean_text(text):
    return re.sub(r'\*\*|\*', '', text)

def get_db():
    conn = sqlite3.connect('tejas_qna.db')
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/',methods=['GET'])
def index():
    return render_template('index.html')

@app.route('/login',methods=['GET','POST'])
def logs():
    return render_template('auth/login.html')

sql_db=sqlite3.connect('users.db',check_same_thread=False)
connection=sql_db.cursor()


@app.route('/logins', methods=['GET', 'POST'])
def log_in():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        query = 'SELECT * FROM user_reg WHERE email = ?'
        execution = connection.execute(query, (email,)).fetchone()
        if execution:
            if execution[2]==password:
                session['username'] = execution[0]
                session['email'] = execution[1]
                return redirect('/dashboard')
            else:
                flash('password miss match','danger')
        else:
            flash('Please login or register first.', 'danger')
            return redirect('/signup')


db_con_question=sqlite3.connect('questions.db',check_same_thread=False)
question=db_con_question.cursor()

@app.route('/logout',methods=['GET','POST'])
def log_out():
    session.clear()
    return redirect('/login')

@app.route('/dashboard',methods=['GET','POST'])
def dashboards():
    if 'username' not in session:
        flash('Go and Login first ',category='danger')
        return redirect('/login')

    if request.method == 'POST':
        questions = request.form['question']
        query = 'INSERT INTO question(question, date, username, email) VALUES(?, ?, ?, ?)'
        values = (questions, datetime.date.today(), session['username'], session['email'])

        if question.execute(query, values):
            db_con_question.commit()
            flash('Question submitted successfully!', 'success')

            # Fetch all questions from the database
            queri="SELECT question, date, username, email FROM question where  username=(?) and email=(?)"
            params=(session['username'],session['email'])
            query = question.execute(queri, params).fetchall()

            print('----------------------------------------------')
            print("All questions:", query)
            print('-------------------------------------------------')

            return render_template('dash_board.html', output=query)
        else:
            flash('Failed to submit question', 'danger')
            return redirect(url_for('dashboard'))

    return render_template('dash_board.html',username=session['username'],email=session['email'])


@app.route('/signup',methods=['GET','POST'])
def signup():
    return render_template('auth/signup.html')

@app.route('/signups',methods=['GET','POST'])
def register():
    if request.method=='POST':
        username=request.form['username']
        email=request.form['email']
        password=request.form['password']
        print(username)
        print('-------------------')
        print(password)
        print('------------')
        print(email)
        query='insert into user_reg(username, email, password) values (?,?,?)'
        parms=(username,email,password)
        if connection.execute(query,parms):
            sql_db.commit()
            flash('User registration done successfully')
            return redirect('/login')

@app.route('/expert_reg',methods=['GET','POST'])
def exp_register():
    return render_template('auth/exp_reg.html')

conn=sqlite3.connect('expert_logs.db',check_same_thread=False)
cursor=conn.cursor()

@app.route('/exp_register',methods=['POST'])
def register_exp():
    if request.method=='POST':
        name=request.form['name']
        email=request.form['email']
        role=request.form['role']
        password=request.form['password']
        table='insert into exper_logs(name,email,role,password) values (?,?,?,?)'
        params=(name,email,role,password)
        if cursor.execute(table,params):
            conn.commit()
            print('s')
            return redirect('/administrator/expert_sme')
        else:
            flash('insert into correct details')
            return redirect('/expert_reg')

@app.route('/administrator/expert_sme',methods=['GET','POST'])
def expert():
    return render_template('auth/admin_expert.html')

@app.route('/admin_expert',methods=['POST'])
def exp_log():
    if request.method=='POST':
        username=request.form['username']
        password=request.form['password']
        query='select * from exper_logs where name=(?) and password=(?)'
        params=(username,password)
        query_execution=cursor.execute(query,params).fetchone()
        print(query_execution)
        if query_execution:
            if query_execution[0]==username and query_execution[3]==password:
                print('s')
                session['exp_username']=username
                session['exp_role']=query_execution[2]
                session['exp_email']=query_execution[1]
                return redirect('/dashboard_expert')
        else:
            print('did not do')
            flash('make a proper login')
            return redirect('/expert_reg')

@app.route('/admin_logout',methods=['GET','POST'])
def admin_logout():
    session.clear()
    flash('Logged out successfully.', 'info')
    return redirect('/administrator/expert_sme')

def send_email(sender_email, password, recipient_email, role, question, answer):
    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = recipient_email
    msg['Subject'] = f"The Answer for submitted question {question} sent by {role}"
    msg.attach(MIMEText(answer, 'html'))

    with smtplib.SMTP("smtp.gmail.com", 587) as server:
        server.starttls()
        server.login(sender_email, password)
        server.send_message(msg)

    return "Email submitted successfully"

q_sub=sqlite3.connect('questions.db',check_same_thread=False)
que=q_sub.cursor()

def get_unanswered_questions():
    conn = sqlite3.connect('questions.db')
    cursor = conn.cursor()

    cursor.execute("""
        SELECT q.question, q.email, q.date, q.username
        FROM question q
        LEFT JOIN answers_given a ON q.question = a.question AND q.email = a.email
        WHERE a.question IS NULL
        ORDER BY q.date DESC
    """)
    questions = cursor.fetchall()
    conn.close()
    return questions

@app.route('/dashboard_expert',methods=['GET',"POST"])
def exp():
    if 'exp_username' not in session:
        flash("Go and register for Trainer or Subject Matter expert")

    questions=get_unanswered_questions()
    return render_template('questions/dash_exp.html',user=session['exp_username'],role=session['exp_role'],email=session['exp_email'],questions=questions)

db_con=sqlite3.connect('questions.db',check_same_thread=False)
conne=db_con.cursor()

@app.route('/question_submit', methods=['GET', 'POST'])
def q_submit():
    if request.method == 'POST':
            email = request.form['email']
            role = request.form['role']
            question_text = request.form['question']
            answer_text = request.form['answer']
            print(email)
            print('-----------------')
            print(role)
            print('----------')

            insert_query = """INSERT INTO answers_given (question, email, answer,role) 
                             VALUES (?, ?, ?)"""

            params = (question_text, email, answer_text)
            conne.execute(insert_query, params)
            db_con.commit()

            submission = send_email(
                sender_email=sender_email,
                password=password,
                role=role,
                recipient_email=email,
                question=question_text,
                answer=answer_text
            )
            print("True" if submission else "False")

            flash('Answer submitted successfully' if submission else 'Answer saved but email failed')
            return redirect('/dashboard_expert')
    else:
        redirect('/admin_logout')


@app.route('/answered_questions',methods=['GET','POST'])
def answered_questions():
    cursor = conne.execute("SELECT question, email, role answer FROM answers_given")
    answered_questions = cursor.fetchall()

    # Convert to list of dictionaries
    columns = [desc[0] for desc in cursor.description]
    answered_questions = [dict(zip(columns, row)) for row in answered_questions]

    return render_template('questions/answered.html',
                           answered_questions=answered_questions)


'''@app.route('/logins', methods=['POST'])
def logins():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        conn = get_db()
        user = conn.execute('SELECT * FROM users WHERE email = ?', (email,)).fetchone()
        conn.close()
        if user and check_password_hash(user['password'], password):
            session['user_id'] = user['id']
            session['role'] = user['role']
            flash('Logged in successfully!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid credentials', 'danger')
            return redirect(url_for('logs'))

@app.route('/signup',methods=['GET','POST'])
def signup():
    return render_template('auth/signup.html')

@app.route('/signups', methods=['POST'])
def register():
    if request.method == 'POST':
        name = request.form['username']
        email = request.form['email']
        password = request.form['password']
        role=request.form['role']
        conn = get_db()
        try:
            conn.execute('INSERT INTO users (name, email, password, role) VALUES (?, ?, ?, ?)',
                         (name, email, password,role))
            conn.commit()
            flash('Registration successful. Please log in.', 'success')
            print("ufffffffffffffffffffff")
            return redirect(url_for('logs'))
        except sqlite3.IntegrityError:
            flash('Email already registered.', 'danger')
        finally:
            conn.close()
        return render_template('auth/signup.html')

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    role = session['role']
    return render_template('dashboard.html', role=role)


@app.route('/ask_ai',methods=['GET','POST'])
def education_legal():
    return render_template('questions/ask_ai.html')

@app.route('/leg_inp',methods=['POST'])
def edu():
    if request.method=='POST':
        user_message=request.form['legal_bot']
        genai.configure(api_key='AIzaSyBN7JmNK8ly4tmfS3JhkYAgrEpyFRdhVt8')
        model = genai.GenerativeModel('gemini-1.5-flash')
        content = model.generate_content(f"Is this question {user_message} related to Networking give me reponse as  true or false only")
        generated_text = content.text
        key_points = convert_paragraph_to_points(generated_text)
        key_points = [clean_text(item) for item in key_points]
        print(key_points)
        if key_points[0]=='True' or key_points[0]=='true':
            content = model.generate_content(f'{user_message}')
            generated_text = content.text
            key_points = convert_paragraph_to_points(generated_text)
            key_points = [clean_text(item) for item in key_points]
            return jsonify({"response":key_points})
        else:
            bot_response="Please about the Networking  related questions not other question"
            return jsonify({"response":bot_response})

@app.route('/logout')
def logout():
    session.clear()
    flash('Logged out successfully.', 'info')
    return redirect(url_for('index'))
'''
if __name__ == '__main__':
    app.run(debug=True)