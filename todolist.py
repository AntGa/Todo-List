import MySQLdb
from functools import wraps
from flask import Flask, render_template, request, redirect, jsonify, session, flash, logging
from flask_mysqldb import MySQL
app = Flask(__name__)

app.secret_key = 'thisisoursecretkey'

app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'antga001'
app.config['MYSQL_DB'] = 'todolist_database'

mysql = MySQL(app)


# Check if user logged in
def is_logged_in(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'loggedin' in session:
            return f(*args, **kwargs)
        else:
            flash('Unauthorized, Please login', 'danger')
            return redirect("/login")
    return wrap


#Displays the login screen to the user
@app.route('/login', methods=['POST','GET'])
def login_user():
    msg = ''
    if request.method == 'POST':

        #if the Sign Up button is pressed then redirect to Sign Up Page
        if request.form.get('signupButton') == 'signupButton':
            return redirect("/signup")
        else:
            
            user_details = request.form
            username = user_details['username']
            password = user_details['password']
            cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            cur.execute('SELECT * FROM profile_table WHERE username = %s AND password = %s', (username, password,))
            account = cur.fetchone()
            # If account exists in accounts table in out database
            if account:
                # Create session data, we can access this data in other routes
                session['loggedin'] = True
                session['id'] = account['id']
                session['username'] = account['username']
                session['first_name'] = account['first_name']
                session['last_name'] = account['last_name']
                # Redirect to home page
                return redirect("/")
            else:
                # Account doesnt exist or username/password incorrect
                msg = 'Incorrect username/password!'
    # Show the login form with message (if any)
    return render_template('LoginPage.html', msg=msg)

 #Main To Do List PAge
@app.route('/')
@is_logged_in
def main():
    user = session['username']
    cur = mysql.connection.cursor()
    cur2 = mysql.connection.cursor()
    cur.execute("SELECT status, subject, task, priority, id, username FROM tasks_table WHERE username = %s", [user])
    rv = cur.fetchall()
    cur2.execute("SELECT DISTINCT subject FROM tasks_table WHERE username = %s", [user])
    rv2 = cur2.fetchall()

    return render_template('index.html', rows=rv, rows2=rv2)

#Add Tasks to the Database
@app.route('/', methods=['POST','GET'])
def new_task():
    if request.method == 'POST':
        
        #fetch form data
        task_details = request.form
        status = task_details['status']
        subject = task_details['subject']
        task = task_details['task']
        priority = task_details['priority']
        extra_notes = task_details['extra_notes']
        username = session['username']
        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO tasks_table(status, subject, task, priority, username, extra_notes) VALUES(%s, %s, %s, %s, %s, %s)",(status, subject, task, priority, username, extra_notes))
        mysql.connection.commit()
        cur.close()
        return redirect("/")
    
#View the data in a task
@app.route("/ajaxViewTask",methods=["POST","GET"])
def ajaxViewtask():
    cur = mysql.connection.cursor()
    cur2 = mysql.connection.cursor()
    if request.method == 'POST':
        taskid = request.form['taskid']
        cur.execute("SELECT status, subject, task, priority, id, extra_notes FROM tasks_table WHERE id = %s", [taskid])
        cur2.execute("SELECT subject FROM subjects_table")
        viewTaskList = cur.fetchall() 
        subjects = cur2.fetchall()
    return jsonify({'htmlresponse': render_template('update_view_task.html',viewTaskList=viewTaskList, subjects=subjects )})


#Add Tasks to the Database
@app.route("/ajaxAddTask",methods=["POST","GET"])
def ajaxAddTask():
    cur = mysql.connection.cursor()
    cur.execute("SELECT subject FROM subjects_table")
    result = cur.fetchall()
    return render_template('AddNewTask.html', rows4=result)

#Edit or remove items into the database
@app.route('/ajaxUpdateTask', methods=['POST','GET'])
def update_view_item():
    if request.method == 'POST':
        #open database
        cur = mysql.connection.cursor()
        #if the delete button is pressed delete the data entry
        if request.form.get("deleteButton"):
            taskid = request.form['taskid']
            cur.execute ("DELETE from tasks_table WHERE id = %s", [taskid])
            mysql.connection.commit()
            cur.close()
            return redirect("/")
        #else update the data with the user's new data
        else:
              #fetch form data
            taskid = request.form['taskid']
            task_details = request.form
            status = task_details['status']
            subject = task_details['subject']
            task = task_details['task']
            priority = task_details['priority']
            extra_notes = task_details['extra_notes']
            username = session['username']
            cur = mysql.connection.cursor()  
            cur.execute("UPDATE tasks_table SET status=%s, subject =%s, task=%s, priority=%s, extra_notes=%s WHERE id=%s",(status, subject, task, priority, extra_notes, taskid))
            mysql.connection.commit()
            cur.close()
            return redirect("/")


#Search Subjects
@app.route('/ajaxSubjectTask', methods=['POST','GET'])
def search_subjects():
    if request.method == 'POST':
        
        username = session['username']
        cur2 = mysql.connection.cursor()
        cur2.execute("SELECT DISTINCT subject FROM tasks_table WHERE username = %s", [username])
        rv2 = cur2.fetchall()
        
        if request.form.get('submitSubject'):
            subjectValue = request.form.get('submitSubject') 

            username = session['username']
            cur = mysql.connection.cursor()
            cur.execute("SELECT status, subject, task, priority, id, extra_notes, username FROM tasks_table WHERE username = %s AND subject = %s", (username, subjectValue,))
            rv = cur.fetchall()
            return render_template('index.html', rows=rv, rows2=rv2)

        else:
            username = session['username']
            cur2 = mysql.connection.cursor()
            cur2.execute("SELECT DISTINCT subject FROM tasks_table WHERE username = %s", [username])
            rv2 = cur2.fetchall()
            cur = mysql.connection.cursor()
            cur.execute("SELECT status, subject, task, priority, id, extra_notes, username FROM tasks_table WHERE username = %s", [username])
            rv = cur.fetchall()
            return render_template('index.html', rows=rv, rows2=rv2)
    
#Sign Up New User
@app.route('/signup', methods=['POST','GET'])
def new_user ():
    if request.method == 'POST':
        
        #fetch form data
        user_details = request.form
        first_name = user_details['first_name']
        last_name = user_details['last_name']
        username = user_details['username']
        password = user_details['password']
        year_level = user_details['year_level']
        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO profile_table(first_name, last_name, username, password, year_level) VALUES(%s, %s, %s, %s, %s)",(first_name, last_name, username, password, year_level))
        mysql.connection.commit()
        cur.close()
        return redirect('/login')
    else:
        return render_template('SignUpPage.html')
    

# http://localhost:5000/logout - this will be the logout page
@app.route('/logout')
def logout():
    # Remove session data, this will log the user out
   session.pop('loggedin', None)
   session.pop('id', None)
   session.pop('username', None)
   # Redirect to login page
   return redirect("/login")

if __name__ == '__main__':
    app.run(debug=True)