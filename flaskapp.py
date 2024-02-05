import sqlite3
from flask import Flask, request, g, render_template, send_file

DATABASE = '/var/www/html/flaskapp/example.db'

app = Flask(__name__)
app.config.from_object(__name__)

def connect_to_database():
    return sqlite3.connect(app.config['DATABASE'])

def get_database():
    db_connection = getattr(g, '_database', None)
    if db_connection is None:
        db_connection = g._database = connect_to_database()
    return db_connection

@app.teardown_appcontext
def close_db_connection(exception):
    db_connection = getattr(g, '_database', None)
    if db_connection is not None:
        db_connection.close()

def run_query(query_template, params=()):
    db_cursor = get_database().execute(query_template, params)
    query_results = db_cursor.fetchall()
    db_cursor.close()
    return query_results

def commit_changes():
    get_database().commit()

@app.route("/")
def index():
    run_query("DROP TABLE IF EXISTS users")
    run_query("CREATE TABLE users (Username text, Password text, FirstName text, LastName text, Email text, Count integer)")
    return render_template('index.html')

@app.route('/login', methods=['POST', 'GET'])
def user_login():
    login_message = ''
    if request.method == 'POST' and request.form['username'] and request.form['password']:
        user_name = request.form['username']
        user_password = request.form['password']
        user_data = run_query("SELECT FirstName, LastName, Email, Count FROM users WHERE Username = ? AND Password = ?", (user_name, user_password))
        if user_data:
            for user_row in user_data:
                return display_user_info(user_row[0], user_row[1], user_row[2], user_row[3])
        else:
            login_message = 'Invalid Credentials!'
    elif request.method == 'POST':
        login_message = 'Please enter Credentials'
    return render_template('index.html', message=login_message)

@app.route('/register', methods=['GET', 'POST'])
def user_registration():
    registration_message = ''
    if request.method == 'POST' and all(request.form[key] for key in ['username', 'password', 'firstname', 'lastname', 'email']):
        new_username = request.form['username']
        new_password = request.form['password']
        new_firstname = request.form['firstname']
        new_lastname = request.form['lastname']
        new_email = request.form['email']
        file_upload = request.files['textfile']
        if file_upload:
            file_name = file_upload.filename
            word_count = count_words(file_upload)
        else:
            file_name = None
            word_count = None
        existing_user = run_query("SELECT * FROM users WHERE Username = ?", (new_username,))
        if existing_user:
            registration_message = 'User already registered!'
        else:
            run_query("INSERT INTO users (Username, Password, FirstName, LastName, Email, Count) VALUES (?, ?, ?, ?, ?, ?)", (new_username, new_password, new_firstname, new_lastname, new_email, word_count))
            commit_changes()
            new_user_data = run_query("SELECT FirstName, LastName, Email, Count FROM users WHERE Username = ? AND Password = ?", (new_username, new_password))
            if new_user_data:
                for user_row in new_user_data:
                    return display_user_info(user_row[0], user_row[1], user_row[2], user_row[3])
    elif request.method == 'POST':
        registration_message = 'Please fill in all fields!'
    return render_template('registration.html', message=registration_message)

@app.route("/download")
def download_file():
    file_path = "Limerick.txt"
    return send_file(file_path, as_attachment=True)

def count_words(file_stream):
    file_content = file_stream.read()
    words_list = file_content.split()
    return len(words_list)

def display_user_info(first_name, last_name, user_email, word_count):
    return f""" First Name: {first_name} <br> Last Name: {last_name} <br> Email: {user_email} <br> Word Count: {word_count} <br><br> <a href="/download">Download File</a> """

if name == '__main__':
    app.run()