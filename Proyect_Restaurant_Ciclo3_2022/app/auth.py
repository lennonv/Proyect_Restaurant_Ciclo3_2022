import functools
import random
import flask 

from . import utils

from pprint import pprint

from email.message import EmailMessage
import smtplib

from flask import (
    Blueprint, flash, g, redirect, render_template, request, session, url_for
)
from werkzeug.security import check_password_hash, generate_password_hash

from app.db import get_db

bp = Blueprint('auth', __name__, url_prefix='/auth')
#fixed up
@bp.route('/activate', methods=('GET', 'POST'))
def activate():
    try:
        if g.user:
            return redirect(url_for('inbox.show'))
        
        if request.method == 'GET': 
            number = request.args['auth']
            print(number)
            db = get_db()
            attempt = db.execute(
                'SELECT * FROM activationlink WHERE challenge = ? AND state = ?', 
                (number, utils.U_UNCONFIRMED)
            ).fetchone()

            if attempt is not None:
                db.execute(
                    'UPDATE activationlink SET state = ? WHERE id = ?',
                     (utils.U_CONFIRMED, attempt['id'])
                )
                db.execute(
                    'INSERT INTO user (username, password, salt, email) VALUES (?,?,?,?)',
                     (attempt['username'], attempt['password'], attempt['salt'], attempt['email'])##
                )
                db.commit()

        return redirect(url_for('auth.login'))
    except Exception as e:
        print(e)
        return redirect(url_for('auth.login'))

#fixed up
@bp.route('/register', methods=('GET', 'POST'))
def register():
     try:
        if g.user:
            return redirect(url_for('inbox.show'))
        if request.method == 'GET':
            return render_template('auth/register.html')
        if request.method == 'POST':    
            username = request.form['username']
            password = request.form['password']
            email = request.form['email']
            db = get_db()
            error = None

            if not username:
                error = 'Username is required.'
                flash(error)
                return render_template('auth/register.html')
            
            elif not utils.isUsernameValid(username):
                error = "Username should be alphanumeric plus '.','_','-'"
                flash(error)
                return render_template('auth/register.html')

            elif not password:
                error = 'Password is required.'
                flash(error)
                return render_template('auth/register.html')

            elif db.execute('SELECT username FROM user WHERE username = ?', (username,)).fetchone() or error is not None:
                error = 'User {} is already registered.'.format(username)
                flash(error)
                return render_template('auth/register.html')
            
            elif (not email or (not utils.isEmailValid(email))):
                error =  'Email address invalid.'
                flash(error)
                return render_template('auth/register.html')
            
            elif db.execute('SELECT id FROM user WHERE email = ?', (email,)).fetchone() or error is not None:
                error =  'Email {} is already registered.'.format(email)
                flash(error)
                return render_template('auth/register.html')
            
            elif (not utils.isPasswordValid(password)):
                 error = 'Password should contain at least a lowercase letter, an uppercase letter and a number with 8 characters long'
                 flash(error)
                 return render_template('auth/register.html')

            salt = str(hex(random.getrandbits(128))[2:])
            hashP = str(generate_password_hash(password + salt))
            number = int(random.getrandbits(32))

            db.execute(
                'INSERT INTO activationlink (challenge, state, username, password, salt, email ) VALUES (?, ?, ?, ?, ?, ?)',
                (number, utils.U_UNCONFIRMED, username, hashP, salt, email)
            )
            db.commit()

            credentials = db.execute(
                'SELECT user,password from credentials where name= ?', (utils.EMAIL_APP,)
            ).fetchone()

            content = 'Hello there, to activate your account, please click on this link ' + flask.url_for('auth.activate', _external=True) + '?auth=' + str(number)
            
            send_email(credentials, receiver=email, subject='Activate your account', message=content)
            
            flash('Please check in your registered email to activate your account')
            return render_template('auth/login.html') 

        return render_template('auth/register.html') 
     except:
        return render_template('auth/register.html')

    
@bp.route('/confirm', methods=('GET', 'POST'))
def confirm():
     try:
        #  if g.user:
        #      return redirect(url_for('inbox.show'))

         if request.method == 'POST': 
              password = request.form['password'] 
              password1 = request.form['password']
              authid = request.form['authid']

            #   if not authid:
            #       flash('Invalid')
            #       return render_template('auth/forgot.html')

              if not password:
                  flash('Password required')
                  return render_template('auth/change.html', number=authid)

              if not password1:
                  flash('Password confirmation required')
                  return render_template('auth/change.html', number=authid)

              if password != password1:
                  flash('Both values should be the same')
                  return render_template('auth/change.html', number=authid)

              if not utils.isPasswordValid(password):
                  error = 'Password should contain at least a lowercase letter, an uppercase letter and a number with 8 characters long.'
                  flash(error)
                  return render_template('auth/change.html', number=authid)

    #         db = get_db()
    #         attempt = db.execute(
    #             QUERY, (authid, utils.F_ACTIVE)
    #         ).fetchone()
            
    #         if attempt is not None:
    #             db.execute(
    #                 QUERY, (utils.F_INACTIVE, attempt['id'])
    #             )
    #             salt = hex(random.getrandbits(128))[2:]
    #             hashP = generate_password_hash(password + salt)   
    #             db.execute(
    #                 QUERY, (hashP, salt, attempt['userid'])
    #             )
    #             db.commit()
    #             return redirect(url_for('auth.login'))
    #         else:
    #             flash('Invalid')
    #             return render_template('auth/forgot.html')

         return render_template('auth/forgot.html')
     except:
         return render_template('auth/forgot.html')



@bp.route('/change', methods=('GET', 'POST'))
def change():
    try:
        if g.user:
            return redirect(url_for('inbox.show'))
        
        if request.method == 'POST': 
            number = request.args['auth'] 
            
            db = get_db()
            attempt = db.execute(
                'SELECT * FROM activationlink WHERE id =?', (number, utils.F_ACTIVE)
            ).fetchone()
            
            if attempt is not None:
                return render_template('auth/change.html', number=number)
        
        return render_template('auth/forgot.html')
    except:
        return render_template('auth/forgot.html')


@bp.route('/forgot', methods=('GET', 'POST'))
def forgot():
    try:
        if g.user:
            return redirect(url_for('inbox.show'))
        
        if request.method == 'POST':
            email = request.form['email']
            
            
            if (not email or (not utils.isEmailValid(email))):
                error = 'Email Address Invalid'
                flash(error)
                return render_template('auth/forgot.html')

            db = get_db()
            user = db.execute(
                'SELECT * FROM user WHERE email = ?',
                (email,)
            ).fetchone()

            if user is not None:
                number = hex(random.getrandbits(512))[2:]
                print(number, email)
                db.execute(
                    'INSERT INTO forgotlink (state, userid) VAlUES (?, ?)',
                    (utils.F_INACTIVE, user['id'])

                )
                db.execute(
                    'UPDATE forgotlink SET challenge = ? AND state = ? WHERE userid = ?',
                    (number, utils.F_ACTIVE, user['id'])
                )
                db.commit()
                
                credentials = db.execute(
                    'SELECT user,password from credentials where name= ?',(utils.EMAIL_APP,)
                ).fetchone()
                
                content = 'hi hi, to change your password, please click on this link ' + flask.url_for('auth.change', _external=True) + '?auth=' + number
                
                send_email(credentials, receiver=email, subject='New Password', message=content)
                
                flash('Please check in your registered email')
            else:
                error = 'Email is not registered'
                flash(error)            

        return render_template('auth/forgot.html')
    except:
        return render_template('auth/forgot.html')


@bp.route('/login', methods=('GET', 'POST'))
def login():
     try:
        if g.user:
            return redirect(url_for('inbox.show'))

        if request.method == 'GET':
            return render_template('auth/login.html')

        if request.method == 'POST':
            username = request.form['username']
            password = request.form['password']

            if not username:
                error = 'Username Field Required'
                flash(error)
                return render_template('auth/login.html')

            if not password:
                error = 'Password Field Required'
                flash(error)
                return render_template('auth/login.html')

            db = get_db()
            error = None
            user = db.execute(
                'SELECT * FROM user WHERE username = ?', (username,)
            ).fetchone()
            
            if user is None:
                error = 'Incorrect username or password'
            elif not check_password_hash(user['password'], password + user['salt']):
                error = 'Incorrect username or password'   

            if error is None:
                session.clear()
                print(user['id'])
                session['user_id'] = user['id']
                return redirect(url_for('inbox.show'))

            flash(error)

        return render_template('auth/login.html')
     except:
         return render_template('auth/login.html')
        

@bp.before_app_request
def load_logged_in_user(): 
    user_id = session.get(next)#pendiente verificar solución
    user_id = None

    if user_id is None:
        g.user = None
    else:
        g.user = get_db().execute(
            'SELECT * FROM forgotlink WHERE userid = ?', (user_id,)
        ).fetchone()

        
@bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('auth.login'))


def login_required(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None:
            return redirect(url_for('auth.login'))
        return view(**kwargs)
    return wrapped_view


def send_email(credentials, receiver, subject, message):
    # Create Email
    email = EmailMessage()
    email["From"] = credentials['user']
    email["To"] = receiver
    email["Subject"] = subject
    email.set_content(message)

    # Send Email
    smtp = smtplib.SMTP("smtp-mail.outlook.com", port=587)
    smtp.starttls()
    smtp.login(credentials['user'], credentials['password'])
    smtp.sendmail(credentials['user'], receiver, email.as_string())
    smtp.quit()