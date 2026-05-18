import json
from flask import Flask, jsonify, render_template, request, redirect, url_for, session, flash
from flask_login import LoginManager, login_user, logout_user, login_required, current_user, UserMixin
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from sqlalchemy import text
from services.ruta_service import RutaService
from services.xmpp_service import XMPPService
from auth import admin_required
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv
from datetime import datetime, timedelta, timezone
import pytz  
import os

app = Flask(__name__)

# IMPORTANTE: clave de sesión obligatoria
app.secret_key = os.getenv("SECRET_KEY", "supersecretkey")

# ===== BASE DE DATOS (Render PostgreSQL) =====
load_dotenv()  # Cargar variables de entorno desde .env

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError("DATABASE_URL no está configurada")

# Fix obligatorio para Render
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URL
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

xmpp_service = XMPPService()

db = SQLAlchemy(app)
migrate = Migrate(app, db)

# ===== INICIALIZAR LOGIN MANAGER =====
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Por favor inicia sesión para acceder a esta página'

# ===== USER LOADER =====
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# ===== MODELO USUARIO =====
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    tipo = db.Column(db.String(20), nullable=False)
    ruta_asignada_id = db.Column(db.Integer, db.ForeignKey('ruta.id'), nullable=True)
    ruta_asignada = db.relationship('Ruta', backref='conductores', foreign_keys=[ruta_asignada_id])
    
    def get_id(self):
        return str(self.id)

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
    
    # Nuevo campo: conductor asignado
    conductor_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    conductor = db.relationship('User', foreign_keys=[conductor_id])
    
    def __repr__(self):
        return f'<Ruta {self.nombre}>'

# ===== MODELO VIAJE =====
class Trip(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    usuario = db.relationship('User', backref='viajes', foreign_keys=[usuario_id])
    ruta_id = db.Column(db.Integer, db.ForeignKey('ruta.id'), nullable=False)
    ruta = db.relationship('Ruta', backref='viajes')
    conductor_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    conductor = db.relationship('User', backref='viajes_conducidos', foreign_keys=[conductor_id])
    
    fecha_hora = db.Column(db.DateTime, default=db.func.now())
    duracion_minutos = db.Column(db.Integer, nullable=True)
    distancia_km = db.Column(db.Float, nullable=True)
    costo = db.Column(db.Float, nullable=True)
    calificacion = db.Column(db.Integer, nullable=True)  # 1-5 stars
    comentario = db.Column(db.String(500), nullable=True)
    estado = db.Column(db.String(20), default='completado')  # completado, cancelado
    
    def __repr__(self):
        return f'<Trip {self.id}>'

# ===== MODELO LOG TRANSACCIONAL =====
class TransactionalLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    usuario = db.relationship('User', backref='logs_transaccionales')
    
    accion = db.Column(db.String(100), nullable=False)  # login, logout, registro, ver_mapa, etc.
    descripcion = db.Column(db.Text, nullable=True)
    tipo_resultado = db.Column(db.String(20), default='exito')  # exito, fallo
    
    fecha_hora = db.Column(db.DateTime, default=db.func.now())
    ip_address = db.Column(db.String(45), nullable=True)  # IPv4 o IPv6
    user_agent = db.Column(db.String(255), nullable=True)
    
    datos_adicionales = db.Column(db.Text, nullable=True)  # JSON con info adicional
    
    def __repr__(self):
        return f'<Log {self.accion} - {self.usuario_id}>'

class ChatMessage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    usuario = db.relationship('User', backref='chat_messages')
    remitente = db.Column(db.String(50), nullable=False)
    receptor = db.Column(db.String(50), nullable=False)
    mensaje = db.Column(db.Text, nullable=False)
    canal = db.Column(db.String(20), nullable=False, default='xmpp')
    fecha_hora = db.Column(db.DateTime, default=db.func.now())

    def __repr__(self):
        return f'<ChatMessage {self.id} {self.remitente} -> {self.receptor}>'

#====== FUNCIÓN AUXILIAR PARA REGISTRAR ACTIVIDADES =====
def registrar_actividad(usuario_id, accion, descripcion='', tipo_resultado='exito', datos_adicionales=None):
    """
    Registra una actividad en el log transaccional.
    
    accion: login, logout, registro, ver_mapa, ver_rutas, alternar_sentido, simular_bus, geolocalización, etc.
    tipo_resultado: exito o fallo
    datos_adicionales: JSON string con info adicional (ruta_id, etc.)
    """
    try:
        log = TransactionalLog(
            usuario_id=usuario_id,
            accion=accion,
            descripcion=descripcion,
            tipo_resultado=tipo_resultado,
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent', ''),
            datos_adicionales=datos_adicionales
        )
        db.session.add(log)
        db.session.commit()
        print(f"✅ Log registrado: {accion} (Usuario: {usuario_id}, Resultado: {tipo_resultado})")
    except Exception as e:
        print(f"❌ Error registrando log: {e}")
        db.session.rollback()


def guardar_mensaje_chat(usuario_id, remitente, receptor, mensaje, canal='xmpp'):
    try:
        chat = ChatMessage(
            usuario_id=usuario_id,
            remitente=remitente,
            receptor=receptor,
            mensaje=mensaje,
            canal=canal
        )
        db.session.add(chat)
        db.session.commit()
        return chat
    except Exception as e:
        print(f"❌ Error guardando mensaje de chat: {e}")
        db.session.rollback()
        return None

# ===== HOME =====
@app.route('/')
def home():
    if session.get('user_id') and session.get('tipo'):
        if session['tipo'] == 'usuario':
            return redirect(url_for('mapa_usuario'))
        elif session['tipo'] == 'conductor':
            return redirect(url_for('mapa_conductor'))
        elif session['tipo'] == 'administrador':
            return redirect(url_for('admin_panel'))
    return render_template('home.html')

# ===== LOGIN =====
@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None

    if request.method == 'POST':
        correo = request.form['correo']
        password = request.form['password']

        user = User.query.filter_by(email=correo).first()

        if user and check_password_hash(user.password, password):
            session.clear()
            session['user_id'] = user.id
            session['tipo'] = user.tipo
            
           # ✅ Registrar actividad de login exitoso
            registrar_actividad(
                usuario_id=user.id,
                accion='login',
                descripcion=f'Inicio de sesión exitoso como {user.tipo}',
                datos_adicionales='{"email": "' + correo + '", "tipo": "' + user.tipo + '"}'
            )

            if user.tipo == "usuario":
                return redirect(url_for('mapa_usuario'))
            elif user.tipo == "conductor":
                return redirect(url_for('mapa_conductor'))
            elif user.tipo == "administrador":
                return redirect(url_for('admin_panel'))
        else:
            error = 'Correo o contraseña incorrectos'
            
            # ✅ Registrar intento de login fallido
            if user:
                registrar_actividad(
                    usuario_id=user.id,
                    accion='login',
                    descripcion='Intento de login fallido',
                    tipo_resultado='fallo'
                )

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
            registrar_actividad(0, 'registro_fallido', f'Intento de registro con email duplicado: {correo}', 'fallo')
            return "El usuario ya existe"

        nuevo_usuario = User(
            nombre=nombre,
            email=correo,
            password=generate_password_hash(password),
            tipo=tipo
        )

        db.session.add(nuevo_usuario)
        db.session.commit()
        
        # ✅ Registrar actividad de registro
        registrar_actividad(
            usuario_id=nuevo_usuario.id,
            accion='registro',
            descripcion=f'Usuario registrado como {tipo}',
            datos_adicionales='{"email": "' + correo + '", "tipo": "' + tipo + '"}'
        )

        return redirect(url_for('login'))

    return render_template('register.html')


# ===== MAPA USUARIO =====
@app.route('/mapa-usuario')
def mapa_usuario():
    if session.get('tipo') != "usuario":
        return redirect(url_for('login'))

    # ✅ Registrar acceso al mapa
    if session.get('user_id'):
        registrar_actividad(
            usuario_id=session['user_id'],
            accion='ver_mapa',
            descripcion='Accedió al mapa de usuario'
        )

    return render_template('usuario.html')


# ===== MAPA CONDUCTOR =====
@app.route('/mapa-conductor')
def mapa_conductor():
    if session.get('tipo') != "conductor":
        return redirect(url_for('login'))
    
    # REGISTRAR ACTIVIDAD - Acceso al mapa del conductor
    if session.get('user_id'):
        registrar_actividad(session['user_id'], 'ver_mapa_conductor', 'Accedió al mapa de conductor')

    conductor = None
    if session.get('user_id'):
            conductor = db.session.get(User, session['user_id'])  
    return render_template('conductor.html', conductor=conductor)

# ===== PERFIL DEL USUARIO =====
@app.route('/perfil')
def perfil():
    if not session.get('user_id'):
        return redirect(url_for('login'))
    
    user = User.query.get(session['user_id'])
    if not user:
        return redirect(url_for('login'))
    
    # Estadísticas según el tipo de usuario
    stats = {}
    
    if user.tipo == 'usuario':
        viajes = Trip.query.filter_by(usuario_id=user.id).all()
        stats['total_viajes'] = len(viajes)
        stats['viajes_completados'] = len([v for v in viajes if v.estado == 'completado'])
        stats['viajes_cancelados'] = len([v for v in viajes if v.estado == 'cancelado'])
        
        total_distancia = sum([v.distancia_km or 0 for v in viajes])
        stats['distancia_total'] = round(total_distancia, 2)
        
        total_tiempo = sum([v.duracion_minutos or 0 for v in viajes])
        stats['tiempo_total_minutos'] = total_tiempo
        stats['tiempo_promedio'] = round(total_tiempo / len(viajes), 1) if viajes else 0
        
        calificaciones = [v.calificacion for v in viajes if v.calificacion]
        stats['calificacion_promedio'] = round(sum(calificaciones) / len(calificaciones), 1) if calificaciones else 0
        
        costo_total = sum([v.costo or 0 for v in viajes])
        stats['costo_total'] = round(costo_total, 2)
        
        # Rutas más frecuentes
        rutas_count = {}
        for viaje in viajes:
            if viaje.ruta:
                rutas_count[viaje.ruta.nombre] = rutas_count.get(viaje.ruta.nombre, 0) + 1
        stats['rutas_frecuentes'] = sorted(rutas_count.items(), key=lambda x: x[1], reverse=True)[:5]
        
    elif user.tipo == 'conductor':
        viajes = Trip.query.filter_by(conductor_id=user.id).all()
        stats['total_viajes'] = len(viajes)
        stats['viajes_completados'] = len([v for v in viajes if v.estado == 'completado'])
        stats['viajes_cancelados'] = len([v for v in viajes if v.estado == 'cancelado'])
        
        total_distancia = sum([v.distancia_km or 0 for v in viajes])
        stats['distancia_total'] = round(total_distancia, 2)
        
        total_tiempo = sum([v.duracion_minutos or 0 for v in viajes])
        stats['tiempo_total_minutos'] = total_tiempo
        stats['tiempo_promedio'] = round(total_tiempo / len(viajes), 1) if viajes else 0
        
        calificaciones = [v.calificacion for v in viajes if v.calificacion]
        stats['calificacion_promedio'] = round(sum(calificaciones) / len(calificaciones), 1) if calificaciones else 0
        
        ingreso_total = sum([v.costo or 0 for v in viajes])
        stats['ingreso_total'] = round(ingreso_total, 2)
        
        stats['ruta_asignada'] = user.ruta_asignada.nombre if user.ruta_asignada else "No asignada"
    
    return render_template('mi_perfil.html', user=user, stats=stats)

# ===== CREAR TABLAS =====
with app.app_context():
    db.create_all()

    # Ensure DB has required columns when upgrading without migrations (SQLite-friendly)
    try:
        conn = db.engine.connect()

        def _has_column(table, column):
            res = conn.execute(text(f"PRAGMA table_info('{table}')")).fetchall()
            return any(r[1] == column for r in res)

        # Add user.ruta_asignada_id if missing
        if not _has_column('user', 'ruta_asignada_id'):
            conn.execute(text('ALTER TABLE user ADD COLUMN ruta_asignada_id INTEGER'))

        # Add ruta additional columns if missing
        ruta_cols = {
            'coordenadas_ida': "TEXT",
            'coordenadas_vuelta': "TEXT",
            'duracion_ida': "INTEGER",
            'duracion_vuelta': "INTEGER",
            'distancia_ida': "REAL",
            'distancia_vuelta': "REAL",
            'conductor_id': "INTEGER",
        }
        for col, coltype in ruta_cols.items():
            if not _has_column('ruta', col):
                conn.execute(text(f"ALTER TABLE ruta ADD COLUMN {col} {coltype}"))
        
        # Add trip columns if missing
        trip_cols = {
            'usuario_id': "INTEGER",
            'ruta_id': "INTEGER",
            'conductor_id': "INTEGER",
            'fecha_hora': "TIMESTAMP",
            'duracion_minutos': "INTEGER",
            'distancia_km': "REAL",
            'costo': "REAL",
            'calificacion': "INTEGER",
            'comentario': "TEXT",
            'estado': "TEXT",
        }
        for col, coltype in trip_cols.items():
            if not _has_column('trip', col):
                conn.execute(text(f"ALTER TABLE trip ADD COLUMN {col} {coltype}"))

    except Exception:
        # If any of these fail (e.g., DB locked), continue — migrations should be used in production
        pass

    # Verificar si ya existe un admin
    try:
        admin = User.query.filter_by(email="admin@cajica.com").first()
        if not admin:
            admin_user = User(
                nombre="Administrador",
                email="admin@cajica.com",
                password=generate_password_hash("admin123"),  
                tipo="administrador"
            )
            db.session.add(admin_user)
            db.session.commit()
    except Exception:
        # DB schema may be out of date (missing columns); skip admin auto-creation
        pass


# ======= ADMINISTRADOR DEL SISTEMA =====
@app.route('/admin')
@admin_required
def admin_panel():
    
    usuarios = User.query.all()
    rutas = Ruta.query.all()
    
    # Estadísticas básicas
    stats = {
        'admin_count': len([u for u in usuarios if u.tipo == 'administrador']),
        'conductor_count': len([u for u in usuarios if u.tipo == 'conductor']),
        'usuario_count': len([u for u in usuarios if u.tipo == 'usuario']),
        'intermunicipal_count': len([r for r in rutas if r.tipo == 'intermunicipal']),
        'interna_count': len([r for r in rutas if r.tipo == 'interna']),
        'total_usuarios': len(usuarios),
        'total_rutas': len(rutas)
    }
    
    # ===== ACTIVIDAD DIARIA =====
    # Usar UTC para que coincida con la BD
    utc_now = datetime.utcnow()
    
    actividad_diaria = {'labels': [], 'data': []}
    
    for i in range(6, -1, -1):
        fecha = utc_now - timedelta(days=i)
        fecha_inicio = datetime(fecha.year, fecha.month, fecha.day, 0, 0, 0)
        fecha_fin = datetime(fecha.year, fecha.month, fecha.day, 23, 59, 59)
        
        count = TransactionalLog.query.filter(
            TransactionalLog.fecha_hora >= fecha_inicio,
            TransactionalLog.fecha_hora <= fecha_fin
        ).count()
        
        actividad_diaria['labels'].append(fecha.strftime('%d/%m'))
        actividad_diaria['data'].append(count)
    
    # ===== ESTADÍSTICAS DEL MAPA =====
    mapa_stats = {
        'visualizaciones_rutas': TransactionalLog.query.filter_by(accion='ver_rutas').count(),
        'simulaciones_buses': TransactionalLog.query.filter_by(accion='simular_bus').count(),
        'geolocalizaciones': TransactionalLog.query.filter_by(accion='geolocalización').count()
    }
    
    # ===== LOG DE ACTIVIDAD =====
    fecha_actual = datetime.utcnow()
    fecha_inicio = request.args.get('inicio', (fecha_actual - timedelta(days=7)).strftime('%Y-%m-%d'))
    fecha_fin = request.args.get('fin', fecha_actual.strftime('%Y-%m-%d'))
    
    logs_actividad = db.session.query(
        TransactionalLog,
        User.nombre.label('usuario_nombre')
    ).join(User, TransactionalLog.usuario_id == User.id)\
     .filter(db.func.date(TransactionalLog.fecha_hora) >= fecha_inicio)\
     .filter(db.func.date(TransactionalLog.fecha_hora) <= fecha_fin)\
     .order_by(TransactionalLog.fecha_hora.desc())\
     .limit(50)\
     .all()
    
    logs_data = []
    for log, nombre in logs_actividad:
        logs_data.append({
            'usuario_nombre': nombre,
            'accion': log.accion,
            'descripcion': log.descripcion,
            'fecha': log.fecha_hora.strftime('%Y-%m-%d %H:%M:%S')
        })
    
    return render_template('admin_inicio.html', 
                         usuarios=usuarios, 
                         rutas=rutas,
                         stats=stats,
                         actividad_diaria=actividad_diaria,
                         mapa_stats=mapa_stats,
                         logs_actividad=logs_data,
                         fecha_inicio=fecha_inicio,
                         fecha_fin=fecha_fin)

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
        password=generate_password_hash(password),
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

# ==================== GESTIÓN DE CONDUCTORES ====================

@app.route('/admin/conductores')
@admin_required
def admin_conductores():
    conductores = User.query.filter_by(tipo='conductor').all()
    rutas = Ruta.query.all()
    return render_template('admin_conductores.html', conductores=conductores, rutas=rutas)

@app.route('/admin/conductor/asignar_ruta', methods=['POST'])
@admin_required
def admin_asignar_ruta_conductor():
    data = request.get_json()
    conductor = User.query.get(data['conductor_id'])
    ruta = Ruta.query.get(data['ruta_id'])
    
    if conductor and ruta:
        # Actualizar conductor y ruta
        conductor.ruta_asignada_id = ruta.id
        ruta.conductor_id = conductor.id
        db.session.commit()
        return jsonify({'status': 'ok', 'ruta_id': ruta.id, 'ruta_nombre': ruta.nombre})
    return jsonify({'status': 'error'}), 404

@app.route('/admin/crear_usuario', methods=['POST'])
@admin_required
def admin_crear_usuario():
    data = request.get_json()
    hashed_password = generate_password_hash(data['password'])
    user = User(
        username=data['nombre'],
        email=data['email'],
        password=hashed_password,
        tipo=data.get('tipo', 'usuario')
    )
    db.session.add(user)
    db.session.commit()
    return jsonify({'status': 'ok'})

@app.route('/admin/eliminar_usuario/<int:user_id>', methods=['DELETE'])
@admin_required
def admin_eliminar_usuario(user_id):
    user = User.query.get(user_id)
    if user:
        db.session.delete(user)
        db.session.commit()
        return jsonify({'status': 'ok'})
    return jsonify({'status': 'error'}), 404



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
            'horario': ruta.horario,
            'tipo': ruta.tipo,
            'coordenadas_ida': ruta.coordenadas_ida,
            'coordenadas_vuelta': ruta.coordenadas_vuelta,
            'duracion_ida': ruta.duracion_ida,
            'duracion_vuelta': ruta.duracion_vuelta,
            'distancia_ida': ruta.distancia_ida,
            'distancia_vuelta': ruta.distancia_vuelta
        })
    
    # Registrar consulta de rutas
    if session.get('user_id'):
        registrar_actividad(
            usuario_id=session['user_id'],
            accion='ver_rutas',
            descripcion=f'Visualizó {len(rutas_data)} rutas disponibles',
            datos_adicionales=f'{{"total_rutas": {len(rutas_data)}}}'
        )
    
    return jsonify(rutas_data)

@app.route('/api/chat/history')
def api_chat_history():
    if not session.get('user_id'):
        return jsonify({'error': 'No autorizado'}), 401

    mensajes = ChatMessage.query.filter_by(usuario_id=session['user_id']).order_by(ChatMessage.fecha_hora.asc()).all()
    mensajes_data = [
        {
            'id': mensaje.id,
            'remitente': mensaje.remitente,
            'receptor': mensaje.receptor,
            'mensaje': mensaje.mensaje,
            'fecha_hora': mensaje.fecha_hora.strftime('%Y-%m-%d %H:%M:%S')
        }
        for mensaje in mensajes
    ]

    return jsonify({'messages': mensajes_data})

@app.route('/api/chat/send', methods=['POST'])
def api_chat_send():
    if not session.get('user_id'):
        return jsonify({'error': 'No autorizado'}), 401

    data = request.get_json() or {}
    mensaje = (data.get('message') or '').strip()
    if not mensaje:
        return jsonify({'error': 'Mensaje vacío'}), 400

    remitente = session.get('tipo', 'usuario')
    guardar_mensaje_chat(session['user_id'], remitente, 'bot', mensaje)
    if xmpp_service.is_configured():
        xmpp_service.send_to_bot(remitente, mensaje)

    respuesta = xmpp_service.generate_reply(mensaje, remitente)
    guardar_mensaje_chat(session['user_id'], 'bot', remitente, respuesta)

    registrar_actividad(
        usuario_id=session['user_id'],
        accion='chatbot',
        descripcion=f'Interacción con chatbot desde perfil {remitente}',
        datos_adicionales=json.dumps({'mensaje': mensaje})
    )

    return jsonify({'reply': respuesta})

@app.route('/api/conductor/ubicacion', methods=['POST'])
def api_conductor_ubicacion():
    if session.get('tipo') != 'conductor':
        return jsonify({'error': 'No autorizado'}), 403

    data = request.get_json() or {}
    lat = data.get('lat')
    lng = data.get('lng')
    if lat is None or lng is None:
        return jsonify({'error': 'Datos inválidos'}), 400

    ubicacion_bus['lat'] = lat
    ubicacion_bus['lng'] = lng

    registrar_actividad(
        usuario_id=session['user_id'],
        accion='ubicacion',
        descripcion='Actualizó ubicación de conductor',
        datos_adicionales=json.dumps({'lat': lat, 'lng': lng, 'ruta_id': data.get('ruta_id')})
    )

    return jsonify({'status': 'ok'})

@app.route('/api/conductor/reporte', methods=['POST'])
def api_conductor_reporte():
    if session.get('tipo') != 'conductor':
        return jsonify({'error': 'No autorizado'}), 403

    data = request.get_json() or {}
    tipo = data.get('tipo', 'incidencia')
    descripcion = data.get('descripcion', '').strip()
    if not descripcion:
        return jsonify({'error': 'Descripción requerida'}), 400

    registrar_actividad(
        usuario_id=session['user_id'],
        accion='reporte_incidencia',
        descripcion=f'Tipo: {tipo} - {descripcion}',
        datos_adicionales=json.dumps({'ruta_id': data.get('ruta_id')})
    )

    if xmpp_service.is_configured():
        xmpp_service.notify_support(
            'Reporte conductor',
            f'Conductor ID {session.get("user_id")} ha reportado:\nTipo: {tipo}\nDescripción: {descripcion}'
        )

    return jsonify({'status': 'ok'})

@app.route('/api/conductor/ruta/<int:ruta_id>')
def api_conductor_ruta(ruta_id):
    """Obtener ruta asignada al conductor - Solo si es su ruta"""
    if session.get('tipo') != 'conductor':
        return jsonify({'error': 'No autorizado'}), 403

    if not session.get('user_id'):
        return jsonify({'error': 'No autorizado'}), 403

    conductor = db.session.get(User, session['user_id'])
    if not conductor or conductor.ruta_asignada_id != ruta_id:
        return jsonify({'error': 'No tienes acceso a esta ruta'}), 403

    ruta = db.session.get(Ruta, ruta_id)
    if ruta:
        return jsonify({
            'ruta': {
                'id': ruta.id,
                'nombre': ruta.nombre,
                'origen': ruta.origen,
                'destino': ruta.destino,
                'coordenadas_ida': ruta.coordenadas_ida,
                'coordenadas_vuelta': ruta.coordenadas_vuelta,
                'duracion_ida': ruta.duracion_ida,
                'duracion_vuelta': ruta.duracion_vuelta,
                'distancia_ida': ruta.distancia_ida,
                'distancia_vuelta': ruta.distancia_vuelta
            }
        })
    return jsonify({'error': 'Ruta no encontrada'}), 404

@app.route('/api/registrar_actividad', methods=['POST'])
def api_registrar_actividad():
    data = request.get_json()
    if session.get('user_id'):
        registrar_actividad(
            session['user_id'], 
            data.get('accion', 'accion'), 
            data.get('detalle', '')
        )
        return jsonify({'status': 'ok'})
    return jsonify({'status': 'error'}), 401
# ===== CRUD RUTAS =====
@app.route('/admin/ruta/nueva', methods=['GET','POST'])
@admin_required
def nueva_ruta():
    if request.method == 'POST':
        hora_inicio = request.form.get('hora_inicio', '').strip()
        hora_fin = request.form.get('hora_fin', '').strip()
        horario_texto = f"{hora_inicio} - {hora_fin}" if hora_inicio and hora_fin else hora_inicio or hora_fin

        ruta = Ruta(
            nombre=request.form['nombre'],
            origen=request.form['origen'],
            destino=request.form['destino'],
            horario=horario_texto,
            tipo=request.form['tipo'],
            coordenadas_ida=request.form.get('coordenadas_ida'),
            coordenadas_vuelta=request.form.get('coordenadas_vuelta'),
            duracion_ida=request.form.get('duracion_ida', type=int),
            duracion_vuelta=request.form.get('duracion_vuelta', type=int),
            distancia_ida=request.form.get('distancia_ida', type=float),
            distancia_vuelta=request.form.get('distancia_vuelta', type=float),
            conductor_id=request.form.get('conductor_id') or None  # Asignar conductor
        )
        db.session.add(ruta)
        db.session.commit()

        # Si se asignó un conductor, actualizar su ruta_asignada_id
        if ruta.conductor_id:
            conductor = User.query.get(ruta.conductor_id)
            if conductor:
                conductor.ruta_asignada_id = ruta.id
                db.session.commit()

         # ✅ Registrar creación de ruta
        registrar_actividad(
            usuario_id=session['user_id'],
            accion='crear_ruta',
            descripcion=f'Creó nueva ruta: {ruta.nombre}',
            datos_adicionales=f'{{"ruta_id": {ruta.id}, "nombre": "{ruta.nombre}"}}'
        )

        flash('Ruta creada exitosamente', 'success')
        return redirect(url_for('admin_panel'))
    
    # GET: Obtener lista de conductores
    conductores = User.query.filter_by(tipo='conductor').all()

    return render_template('nueva_ruta.html')

@app.route('/admin/ruta/eliminar/<int:id>')
@admin_required
def eliminar_ruta(id):
    ruta = Ruta.query.get_or_404(id)
    nombre_ruta = ruta.nombre
    
    db.session.delete(ruta)
    db.session.commit()
    
    # ✅ Registrar eliminación de ruta
    registrar_actividad(
        usuario_id=session['user_id'],
        accion='eliminar_ruta',
        descripcion=f'Eliminó la ruta: {nombre_ruta}',
        datos_adicionales=f'{{"ruta_id": {id}, "nombre": "{nombre_ruta}"}}'
    )
    
    return redirect(url_for('admin_panel'))

@app.route('/admin/ruta/editar/<int:id>', methods=['GET','POST'])
@admin_required
def editar_ruta(id):
    ruta = Ruta.query.get_or_404(id)
    if request.method == 'POST':
        hora_inicio = request.form.get('hora_inicio', '').strip()
        hora_fin = request.form.get('hora_fin', '').strip()
        ruta.nombre = request.form['nombre']
        ruta.origen = request.form['origen']
        ruta.destino = request.form['destino']
        ruta.horario = f"{hora_inicio} - {hora_fin}" if hora_inicio and hora_fin else hora_inicio or hora_fin
        db.session.commit()
        return redirect(url_for('admin_panel'))
    return render_template('editar_ruta.html', ruta=ruta)


# ===== LOGOUT =====
@app.route('/logout')
def logout():
    # ❌ REGISTRAR ACTIVIDAD DE LOGOUT
    if session.get('user_id'):
        registrar_actividad(session['user_id'], 'logout', 'Usuario cerró sesión')
    
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

# ===== OBTENER UBICACIÓN =====
@app.route('/obtener-ubicacion')
def obtener_ubicacion():
    return jsonify(ubicacion_bus)

# ===== API: OBTENER ACTIVIDADES RECIENTES (CON PAGINACIÓN) =====
@app.route('/api/admin/actividades', methods=['GET'])
@admin_required
def api_actividades():
    page = request.args.get('page', 1, type=int)
    per_page = 8  # 8 resultados por página
    
    # Obtener filtros opcionales
    usuario_id = request.args.get('usuario_id', type=int)
    accion = request.args.get('accion')
    tipo_resultado = request.args.get('tipo_resultado')
    
    query = TransactionalLog.query
    
    if usuario_id:
        query = query.filter_by(usuario_id=usuario_id)
    if accion:
        query = query.filter_by(accion=accion)
    if tipo_resultado:
        query = query.filter_by(tipo_resultado=tipo_resultado)
    
    # Ordenar por fecha descendente y paginar
    paginated = query.order_by(TransactionalLog.fecha_hora.desc()).paginate(page=page, per_page=per_page)
    
    logs_data = []
    for log in paginated.items:
        logs_data.append({
            'id': log.id,
            'usuario_nombre': log.usuario.nombre,
            'usuario_email': log.usuario.email,
            'accion': log.accion,
            'descripcion': log.descripcion,
            'tipo_resultado': log.tipo_resultado,
            'fecha_hora': log.fecha_hora.strftime('%Y-%m-%d %H:%M:%S'),
            'ip_address': log.ip_address,
            'datos_adicionales': log.datos_adicionales
        })
    
    return jsonify({
        'logs': logs_data,
        'total': paginated.total,
        'pages': paginated.pages,
        'current_page': page,
        'has_next': paginated.has_next,
        'has_prev': paginated.has_prev
    })

# ===== API: REGISTRAR EVENTO DESDE CLIENTE =====
@app.route('/api/log-event', methods=['POST'])
def api_log_event():
    """Endpoint para que el cliente (JS) registre eventos como alternar_sentido, simular_bus, etc."""
    if not session.get('user_id'):
        return jsonify({'error': 'No autorizado'}), 401
    
    data = request.get_json()
    accion = data.get('accion')
    descripcion = data.get('descripcion', '')
    datos_adicionales = data.get('datos_adicionales')
    
    registrar_actividad(session['user_id'], accion, descripcion, 'exito', datos_adicionales)
    
    return jsonify({'status': 'ok'})

# ===== PÁGINA ADMIN: VER ACTIVIDADES RECIENTES =====
@app.route('/admin/actividades')
@admin_required
def admin_actividades():
    usuarios = User.query.all()
    acciones_disponibles = [
        'login', 'logout', 'registro', 'registro_fallido',
        'ver_mapa', 'ver_mapa_conductor', 'ver_rutas',
        'alternar_sentido', 'simular_bus', 'geolocalización'
    ]
    
    return render_template('admin_actividades.html', 
                          usuarios=usuarios,
                          acciones=acciones_disponibles)

# ===== EXPORTAR REPORTE CSV =====
@app.route('/admin/actividades/exportar', methods=['GET'])
@admin_required
def exportar_actividades_csv():
    """Exporta el log de actividades a CSV"""
    import csv
    from io import StringIO
    
    # Obtener filtros
    usuario_id = request.args.get('usuario_id', type=int)
    accion = request.args.get('accion')
    tipo_resultado = request.args.get('tipo_resultado')
    fecha_inicio = request.args.get('fecha_inicio')
    fecha_fin = request.args.get('fecha_fin')
    
    query = TransactionalLog.query
    
    if usuario_id:
        query = query.filter_by(usuario_id=usuario_id)
    if accion:
        query = query.filter_by(accion=accion)
    if tipo_resultado:
        query = query.filter_by(tipo_resultado=tipo_resultado)
    if fecha_inicio:
        query = query.filter(TransactionalLog.fecha_hora >= fecha_inicio)
    if fecha_fin:
        query = query.filter(TransactionalLog.fecha_hora <= fecha_fin)
    
    logs = query.order_by(TransactionalLog.fecha_hora.desc()).all()
    
    # Crear CSV en memoria
    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(['ID', 'Usuario', 'Email', 'Acción', 'Descripción', 'Resultado', 'Fecha/Hora', 'IP'])
    
    for log in logs:
        writer.writerow([
            log.id,
            log.usuario.nombre,
            log.usuario.email,
            log.accion,
            log.descripcion or '',
            log.tipo_resultado,
            log.fecha_hora.strftime('%Y-%m-%d %H:%M:%S'),
            log.ip_address or ''
        ])
    
    # Preparar respuesta como archivo descargable
    from flask import make_response
    response = make_response(output.getvalue())
    response.headers['Content-Disposition'] = f'attachment; filename=reporte_actividades_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
    response.headers['Content-Type'] = 'text/csv'
    
    return response


if __name__ == '__main__':
    app.run(debug=True)