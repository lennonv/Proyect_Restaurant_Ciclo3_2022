from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for, current_app, send_file
)

from app.auth import login_required
from app.db import get_db

bp = Blueprint('inbox', __name__, url_prefix='/inbox')

@bp.route("/getDB")
@login_required
def getDB():
    return send_file(current_app.config['DATABASE'], as_attachment=True)


@bp.route('/show')
@login_required
def show():
    db = ?
    messages = db.execute(
        QUERY
    ).fetchall()

    return render_template(TEMP, messages=messages)


@bp.route('/send', methods=('GET', 'POST'))
@login_required
def send():
    if request.method == 'POST':        
        from_id = g.user['id']
        to_username = ?
        subject = ?
        body = ?

        db = ?
       
        if not to_username:
            flash('To field is required')
            return render_template(TEMP)
        
        if ?:
            flash('Subject field is required')
            return render_template('inbox/send.html')
        
        if ?:
            flash('Body field is required')
            return render_template(TEMP)    
        
        error = None    
        userto = None 
        
        userto = db.execute(
            QUERY, (to_username,)
        ).fetchone()
        
        if userto is None:
            error = 'Recipient does not exist'
     
        if error is not None:
            flash(error)
        else:
            db = ?
            db.execute(
                QUERY,
                (g.user['id'], userto['id'], subject, body)
            )
            db.commit()

            return redirect(url_for('inbox.show'))

    return render_template('inbox/send.html')