# auth.py
from functools import wraps
from flask import session, redirect, url_for

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get('tipo') != 'administrador':
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function