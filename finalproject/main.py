from cs50 import SQL
from flask import Flask, render_template, request, url_for, session, redirect, flash
from werkzeug.security import generate_password_hash, check_password_hash
from flask_session import Session
import datetime
from functools import wraps

app =Flask(__name__)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)


db = SQL("sqlite:///notebuddy.db")

def login_required(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'logged_in' in session:
            return f(*args, **kwargs)
        else:
            return redirect(url_for('login'))

    return wrap

@app.route('/index', methods = ['GET','POST'])
@login_required
def index():
    FirstName = db.execute("SELECT FirstName FROM user WHERE id = ?", session["id"])
    LastName = db.execute("SELECT LastName FROM user WHERE id = ?", session["id"])
    TotalNotes = db.execute("SELECT COUNT(id) FROM notes where user_id = ?", session["id"] )
    TotalFav = db.execute("SELECT COUNT(id) FROM notes where user_id = ? AND favorites = 1", session["id"] )

    context = {
        'Nfirst': FirstName[0]['FirstName'],
        'Nlast': LastName[0]['LastName'],
        'totalNotes': TotalNotes[0]['COUNT(id)'],
        'totalFav': TotalFav[0]['COUNT(id)']
        }

    return render_template("index.html", context=context)

@app.route('/new', methods = ['GET','POST'])
@login_required
def new():
    if request.method == "POST":
        session_id = db.execute("SELECT id FROM user WHERE id = ?", session['id'])
        title = request.form.get("Ntitle")
        content = request.form.get("Ncontent")
        favorite = request.form.get("checkFav")
        post_date = datetime.datetime.now()

        if favorite == "on":
            favorite = 1
        else:
            favorite = 0

        db.execute("INSERT INTO notes(user_id, title, context, favorites, date) VALUES(?, ?, ?, ?, ?)", session_id[0]['id'], title, content, favorite, post_date)

        flash("New note successfully created")
        return redirect(url_for('new'))
    else:
        FirstName = db.execute("SELECT FirstName FROM user WHERE id = ?", session["id"])
        LastName = db.execute("SELECT LastName FROM user WHERE id = ?", session["id"])
        return render_template("new.html", firstname=FirstName[0]['FirstName'], lastname=LastName[0]['LastName'] )


@app.route('/edit/<note_id>', methods=['GET','POST'])
@login_required
def editPost(note_id):
    if request.method == "POST":
        Edtitle = request.form.get('edTitle')
        Edcontent = request.form.get("edContent")
        Edfavorite = request.form.get("checkEdFav")
        Edpost_date = datetime.datetime.now()

        if Edfavorite == "on":
            Edfavorite = 1
        else:
            Edfavorite = 0

        db.execute('UPDATE notes SET title = ?, context = ?, favorites = ?, date = ? WHERE id = ?', Edtitle, Edcontent, Edfavorite, Edpost_date, note_id)
        flash('Note successfully edited!')
        return redirect(url_for('viewNote'))

    else:
        note = db.execute('SELECT * FROM notes WHERE id = ?', note_id)
        author_Fname = db.execute("SELECT FirstName FROM user WHERE id = ?", session['id'])
        author_Lname = db.execute("SELECT LastName FROM user WHERE id = ?", session['id'])
        return render_template('edit.html', note=note, Fname=author_Fname[0]['FirstName'], Lname=author_Lname[0]['LastName'])

@app.route('/deleteConfirm/<note_id>', methods = ['GET', 'POST'])
@login_required
def delete_confirm(note_id):
    if request.method == 'POST':
        if request.form.get('btnConfirm'):
            db.execute('DELETE FROM notes WHERE id = ?', note_id)
            flash('Note sucessfully deleted!')
            return redirect(url_for('viewNote'))
        elif request.form.get('btnCancel'):
            return redirect(url_for('viewNote'))
    else:
        note = db.execute('SELECT * FROM notes WHERE id = ?', note_id)
        message = 'Are you sure you want to delete this note?'
        return render_template('deleteConf.html', note=note, message=message)

@app.route('/view', methods = ['GET', 'POST'])
@login_required
def viewNote():
    note = db.execute('SELECT * FROM notes WHERE user_id = ? ORDER BY date DESC', session["id"])
    author_Fname = db.execute("SELECT FirstName FROM user WHERE id = ?", session['id'])
    author_Lname = db.execute("SELECT LastName FROM user WHERE id = ?", session['id'])
    return render_template("View.html", note=note, Fname=author_Fname[0]['FirstName'], Lname=author_Lname[0]['LastName'])

@app.route('/favorites', methods = ['GET','POST'])
@login_required
def favorites():
    note = db.execute('SELECT * FROM notes WHERE user_id = ? ORDER BY date DESC', session["id"])
    count_fav = db.execute('SELECT * FROM  notes WHERE user_id = ? AND favorites = 1', session['id'])
    first_name = db.execute('SELECT FirstName FROM user WHERE id = ?', session["id"])
    last_name = db.execute('SELECT LastName FROM user WHERE id = ?', session["id"])
    return render_template("favorites.html", note=note, f_name = first_name[0]['FirstName'], l_name = last_name[0]['LastName'], count_fav=count_fav)

@app.route('/')
@app.route('/landingPage', methods = ['GET','POST'])
def landingPage():
    session['logged_in'] = False
    session['id'] = None
    print(session['logged_in'])
    print(session['id'])
    return render_template("landingPage.html")

@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == "POST":
        Uname = request.form.get('Uname')
        PassW = request.form.get('Pword')
        User = db.execute("SELECT * FROM user Where username = ?", Uname)

        if len(User) == 1:
            if check_password_hash(User[0]['password'], PassW):
                session['id'] = User[0]['id']
                session['logged_in'] = True
                flash('Account login Successful!')
                return redirect(url_for('index'))
            else:
                flash('Incorrect password', 'warning')
                return render_template('login.html')

        else:
            flash('Username not Found!')
            return render_template('login.html')
    else:
        return render_template("login.html")

@app.route('/signUp', methods=['GET','POST'])
def signUp():
    if request.method == 'POST':
        Fname = request.form.get('Fname')
        Lname = request.form.get('Lname')
        Uname = request.form.get('Uname')
        Password = request.form.get('Pword')
        ConfPassword = request.form.get('Cpass')

        User = db.execute('SELECT * FROM user where username = ?', Uname)


        if len(User) != 1:
            if ConfPassword == Password:
                newpass = generate_password_hash(Password)
                db.execute("INSERT INTO user(FirstName, LastName, username, password) VALUES(?, ?, ?, ?)", Fname, Lname, Uname, newpass)
                flash("Account Successfully created!")
                return render_template("landingPage.html")
            else:
                flash('Passwords has to match.')
                return render_template("signup.html")
        else:
            flash('This User already exist.')
            return render_template("signup.html")

    else:
        return render_template("signup.html")

@app.route('/About')
def about():
    return render_template("about.html")

@app.route('/logout', methods=['GET','POST'])
@login_required
def logout():
    if request.method == 'POST':
        if request.form.get('btnConfirm'):
            session['id'] = None
            session['logged_in'] = False
            flash('Account logout successful!')
            return redirect(url_for('landingPage'))
        elif request.form.get('btnCancel'):
            return redirect(url_for('viewNote'))

    else:
        message = 'Are you sure you wish to log out?'
        return render_template('logoutConf.html', message=message)




if __name__=="__main__":
    app.run(debug=True)
