from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for, current_app, send_file
)

from app.auth import login_required
from app.db import get_db


# Librerias para imap
import imaplib
import email
from email.header import decode_header
import webbrowser
import os


bp = Blueprint('inbox', __name__, url_prefix='/inbox')

@bp.route("/getDB")
#@login_required
def getDB():
    return send_file(current_app.config['DATABASE'], as_attachment=True)


@bp.route('/show')
#@login_required
def show():
    # get_messages()
    # db = get_db()
    # messages = db.execute(
    #     'SELECT * FROM message'
    # ).fetchall()

    return render_template('inbox/show.html')#, messages=messages)
    


@bp.route('/send', methods=('GET', 'POST'))
#@login_required
def send():
     if request.method == 'POST':        
         from_id = g.user['id']
         to_username =request.form['to_id']
         subject =request.form['subject']
         body = request.form['body']

         db = get_db()
       
         if not to_username:
             flash('To field is required')
             return render_template('inbox/send.html')
        
         if not subject:
             flash('Subject field is required')
             return render_template('inbox/send.html')
        
         if not body:
             flash('Body field is required')
             return render_template('inbox/send.html')    
        
         error = None    
         userto = None 
        
         userto = db.execute(
             'SELECT username FROM user WHERE username =?', (to_username,)
         ).fetchone()
        
         if userto is None:
             error = 'Recipient does not exist'
     
         if error is not None:
             flash(error)
         else:
             db = get_db()
             db.execute(
                 QUERY,
                 (g.user['id'], userto['id'], subject, body)
             )
             db.commit()

             return redirect(url_for('inbox.show'))

     return render_template('inbox/send.html')

def get_messages():
    db = get_db()
    # db.execute('''INSERT INTO message VALUES (NULL, 5, 5, CURRENT_TIME, "h", "h", "h")''')
    # db.execute('CREATE TABLE movie(title, year, score)')
    # account credentials
    username = "pruebauninorte@outlook.com.ar"
    password = "uninorte2022"
    # use your email provider's IMAP server, you can look for your provider's IMAP server on Google
    # or check this page: https://www.systoolsgroup.com/imap/
    # for office 365, it's this:
    imap_server = "outlook.office365.com"


    def clean(text):
        # clean text for creating a folder
        return "".join(c if c.isalnum() else "_" for c in text)

    # number of top emails to fetch
    N = 3

    # create an IMAP4 class with SSL, use your email provider's IMAP server
    imap = imaplib.IMAP4_SSL(imap_server)
    # authenticate
    imap.login(username, password)

    # select a mailbox (in this case, the inbox mailbox)
    # use imap.list() to get the list of mailboxes
    status, messages = imap.select("INBOX")

    # total number of emails
    messages = int(messages[0])

    for i in range(messages, messages-N, -1):
        # fetch the email message by ID
        res, msg = imap.fetch(str(i), "(RFC822)")
        for response in msg:
            if isinstance(response, tuple):
                # parse a bytes email into a message object
                msg = email.message_from_bytes(response[1])
                # decode the email subject
                subject, encoding = decode_header(msg["Subject"])[0]
                if isinstance(subject, bytes):
                    # if it's a bytes, decode to str
                    subject = subject.decode(encoding)
                # decode email sender
                From, encoding = decode_header(msg.get("From"))[0]
                if isinstance(From, bytes):
                    From = From.decode(encoding)

                Date, encoding = decode_header(msg.get("Date"))[0]
                if isinstance(Date, bytes):
                    Date = Date.decode(encoding) 
                print("Subject:", subject)
                print("From:", From)
                print("Datee:", Date)
                # if the email message is multipart
                if msg.is_multipart():
                    # iterate over email parts
                    for part in msg.walk():
                        # extract content type of email
                        content_type = part.get_content_type()
                        content_disposition = str(part.get("Content-Disposition"))
                        try:
                            # get the email body
                            body = part.get_payload(decode=True).decode()
                        except:
                            pass
                        # if content_type == "text/plain" and "attachment" not in content_disposition:
                            # print text/plain emails and skip attachments
                            print(body)
                        if "attachment" in content_disposition:
                            # download attachment
                            filename = part.get_filename()
                            if filename:
                                folder_name = clean(subject)
                                if not os.path.isdir(folder_name):
                                    # make a folder for this email (named after the subject)
                                    os.mkdir(folder_name)
                                filepath = os.path.join(folder_name, filename)
                                # download attachment and save it
                                open(filepath, "wb").write(part.get_payload(decode=True))
                else:
                    # extract content type of email
                    content_type = msg.get_content_type()
                    # get the email body
                    body = msg.get_payload(decode=True).decode()
                    if content_type == "text/plain":
                        # print only text email parts
                        print(body)

                db.execute(('INSERT INTO message (id, from_id, to_id, created, subject, body, username) VALUES (NULL,3, 3, ?, ?, ?, ?)'), (Date, subject, body, From))
                # print(msg)
                # if content_type == "text/html":
                #     # if it's HTML, create a new HTML file and open it in browser
                #     folder_name = clean(subject)
                #     if not os.path.isdir(folder_name):
                #         # make a folder for this email (named after the subject)
                #         os.mkdir(folder_name)
                #     filename = "index.html"
                #     filepath = os.path.join(folder_name, filename)
                #     # write the file
                #     open(filepath, "w").write(body)
                #     # open in the default browser
                #     webbrowser.open(filepath)
                # print("="*100)
    # close the connection and logout
    imap.close()
    imap.logout()