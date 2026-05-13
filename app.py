from flask import Flask, jsonify, render_template, request, redirect, url_for, session, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from services.ruta_service import RutaService
from auth import admin_required
import os

app = Flask(__name__)

# IMPORTANTE: clave de sesión obligatoria
app.secret_key = os.getenv("SECRET_KEY", "supersecretkey")

# ===== BASE DE DATOS (Render PostgreSQL) =====
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv(
    "DATABASE_URL",
    "sqlite:///local.db"
)

app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)
migrate = Migrate(app, db)

# ===== MODELO USUARIO =====
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    tipo = db.Column(db.String(20), nullable=False)  # usuario / conductor / administrador

# ===== MODELO RUTA =====
class Ruta(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    origen = db.Column(db.String(100), nullable=False)
    destino = db.Column(db.String(100), nullable=False)
    horario = db.Column(db.String(20), nullable=False)
    tipo = db.Column(db.String(20), nullable=False, default='interna')
    
    # Nuevos campos para manejar la geometría de la ruta
    coordenadas_ida = db.Column(db.Text, nullable=True)  # JSON con coordenadas [lat,lng]
    coordenadas_vuelta = db.Column(db.Text, nullable=True)  # JSON con coordenadas
    duracion_ida = db.Column(db.Integer, nullable=True)  # en minutos
    duracion_vuelta = db.Column(db.Integer, nullable=True)  # en minutos
    distancia_ida = db.Column(db.Float, nullable=True)  # en km
    distancia_vuelta = db.Column(db.Float, nullable=True)  # en km
    
    def __repr__(self):
        return f'<Ruta {self.nombre}>'

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
            elif user.tipo == "conductor":
                return redirect(url_for('mapa_conductor'))
            elif user.tipo == "administrador":
                return redirect(url_for('admin_panel'))

        else:
            error = 'Correo o contraseña incorrectos'

    return render_template('login.html', error=error)
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

# ===== CREAR TABLAS =====
with app.app_context():
    db.create_all()

    # Verificar si ya existe un admin
    admin = User.query.filter_by(email="admin@cajica.com").first()
    if not admin:
        admin_user = User(
            nombre="Administrador",
            email="admin@cajica.com",
            password="admin123",  
            tipo="administrador"
        )
        db.session.add(admin_user)
        db.session.commit()


# ======= ADMINISTRADOR DEL SISTEMA =====
@app.route('/admin')
@admin_required
def admin_panel():
    usuarios = User.query.all()
    rutas = Ruta.query.all()
    
    # Calculate statistics
    stats = {
        'admin_count': len([u for u in usuarios if u.tipo == 'administrador']),
        'conductor_count': len([u for u in usuarios if u.tipo == 'conductor']),
        'usuario_count': len([u for u in usuarios if u.tipo == 'usuario']),
        'intermunicipal_count': len([r for r in rutas if r.tipo == 'intermunicipal']),
        'interna_count': len([r for r in rutas if r.tipo == 'interna']),
        'total_usuarios': len(usuarios),
        'total_rutas': len(rutas)
    }
    
    return render_template('admin_inicio.html', 
                         usuarios=usuarios, 
                         rutas=rutas,
                         stats=stats)


@app.route('/admin/rutas')
@admin_required
def admin_rutas():
    rutas = Ruta.query.all()
    return render_template('admin_rutas.html', rutas=rutas)

@app.route('/admin/usuarios')
@admin_required
def admin_usuarios():
    usuarios = User.query.all()
    return render_template('admin_usuarios.html', usuarios=usuarios)

@app.route('/admin/usuario/nuevo', methods=['POST'])
@admin_required
def crear_usuario():
    nombre = request.form['nombre']
    correo = request.form['correo']
    password = request.form['password']
    tipo = request.form['tipo']

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

    return redirect(url_for('admin_usuarios'))


# ===== CRUD USUARIOS =====
@app.route('/admin/usuario/eliminar/<int:id>')
@admin_required
def eliminar_usuario(id):
    usuario = User.query.get_or_404(id)
    db.session.delete(usuario)
    db.session.commit()
    return redirect(url_for('admin_panel'))

@app.route('/admin/usuario/editar/<int:id>', methods=['GET','POST'])
@admin_required
def editar_usuario(id):
    usuario = User.query.get_or_404(id)
    if request.method == 'POST':
        usuario.nombre = request.form['nombre']
        usuario.email = request.form['email']
        usuario.tipo = request.form['tipo']
        db.session.commit()
        return redirect(url_for('admin_panel'))
    return render_template('editar_usuario.html', usuario=usuario)
#====== API =======
@app.route('/api/rutas')
def api_rutas():
    rutas = Ruta.query.all()
    rutas_data = []
    for ruta in rutas:
        rutas_data.append({
            'id': ruta.id,
            'nombre': ruta.nombre,
            'origen': ruta.origen,
            'destino': ruta.destino,
            'tipo': ruta.tipo,
            'coordenadas_ida': ruta.coordenadas_ida,
            'coordenadas_vuelta': ruta.coordenadas_vuelta,
            'duracion_ida': ruta.duracion_ida,
            'duracion_vuelta': ruta.duracion_vuelta,
            'distancia_ida': ruta.distancia_ida,
            'distancia_vuelta': ruta.distancia_vuelta
        })
    return jsonify(rutas_data)

# ===== CRUD RUTAS =====
@app.route('/admin/ruta/nueva', methods=['GET','POST'])
@admin_required
def nueva_ruta():
    if request.method == 'POST':
        ruta = Ruta(
            nombre=request.form['nombre'],
            origen=request.form['origen'],
            destino=request.form['destino'],
            horario=request.form['horario'],
            tipo=request.form['tipo'],
            coordenadas_ida=request.form.get('coordenadas_ida'),
            coordenadas_vuelta=request.form.get('coordenadas_vuelta'),
            duracion_ida=request.form.get('duracion_ida', type=int),
            duracion_vuelta=request.form.get('duracion_vuelta', type=int),
            distancia_ida=request.form.get('distancia_ida', type=float),
            distancia_vuelta=request.form.get('distancia_vuelta', type=float)
        )
        db.session.add(ruta)
        db.session.commit()
        flash('Ruta creada exitosamente', 'success')
        return redirect(url_for('admin_panel'))
    return render_template('nueva_ruta.html')

@app.route('/admin/ruta/eliminar/<int:id>')
@admin_required
def eliminar_ruta(id):
    ruta = Ruta.query.get_or_404(id)
    db.session.delete(ruta)
    db.session.commit()
    return redirect(url_for('admin_panel'))

@app.route('/admin/ruta/editar/<int:id>', methods=['GET','POST'])
@admin_required
def editar_ruta(id):
    ruta = Ruta.query.get_or_404(id)
    if request.method == 'POST':
        ruta.nombre = request.form['nombre']
        ruta.origen = request.form['origen']
        ruta.destino = request.form['destino']
        ruta.horario = request.form['horario']
        db.session.commit()
        return redirect(url_for('admin_panel'))
    return render_template('editar_ruta.html', ruta=ruta)


# ===== LOGOUT =====
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))


# ===== UBICACIÓN CONDUCTOR =====
ubicacion_bus = {
    "lat": 4.9186,
    "lng": -74.0276
}

@app.route('/actualizar-ubicacion', methods=['POST'])
def actualizar_ubicacion():

    global ubicacion_bus

    data = request.get_json(silent=True)
    if not data or 'lat' not in data or 'lng' not in data:
        return jsonify({
            "mensaje": "Datos inválidos"
        }), 400

    ubicacion_bus['lat'] = data['lat']
    ubicacion_bus['lng'] = data['lng']

    return jsonify({
        "mensaje": "Ubicación actualizada"
    })


# ===== CREAR TABLAS =====
with app.app_context():
    db.create_all()


if __name__ == '__main__':
    app.run(debug=True)
    

