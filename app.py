from flask import Flask, render_template, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
import os

app = Flask(__name__)

# 🔥 IMPORTANTE: clave de sesión obligatoria
app.secret_key = os.getenv("SECRET_KEY", "supersecretkey")

# ===== BASE DE DATOS (Render PostgreSQL) =====
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv(
    "DATABASE_URL",
    "sqlite:///local.db"
)

app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

# ===== MODELO USUARIO =====
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    tipo = db.Column(db.String(20), nullable=False)  # usuario / conductor


# ===== LOGIN =====
@app.route('/', methods=['GET', 'POST'])
def login():
    error = None

    if request.method == 'POST':
        correo = request.form['correo']
        password = request.form['password']

        user = User.query.filter_by(email=correo, password=password).first()

        if user:
            # SESIÓN
            session.clear()
            session['user_id'] = user.id
            session['tipo'] = user.tipo

            # redirección por rol
            if user.tipo == "usuario":
                return redirect(url_for('mapa_usuario'))
            else:
                return redirect(url_for('mapa_conductor'))

        error = "Credenciales incorrectas"

    return render_template('login.html', error=error)


# ===== REGISTER =====
@app.route('/register', methods=['GET', 'POST'])
def register():

    if request.method == 'POST':
        nombre = request.form['nombre']
        correo = request.form['correo']
        password = request.form['password']
        tipo = request.form['userType']

        # evitar duplicados
        existe = User.query.filter_by(email=correo).first()
        if existe:
            return "El usuario ya existe"

        nuevo_usuario = User(
            nombre=nombre,
            email=correo,
            password=password,
            tipo=tipo
        )

        db.session.add(nuevo_usuario)
        db.session.commit()

        return redirect(url_for('login'))

    return render_template('register.html')


# ===== MAPA USUARIO =====
@app.route('/mapa-usuario')
def mapa_usuario():
    if session.get('tipo') != "usuario":
        return redirect(url_for('login'))

    return render_template('usuario.html')


# ===== MAPA CONDUCTOR =====
@app.route('/mapa-conductor')
def mapa_conductor():
    if session.get('tipo') != "conductor":
        return redirect(url_for('login'))

    return render_template('conductor.html')


# ===== LOGOUT =====
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))


# ===== CREAR TABLAS =====
with app.app_context():
    db.create_all()


if __name__ == '__main__':
    app.run(debug=True)