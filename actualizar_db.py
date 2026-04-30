# actualizar_local_db.py
import sqlite3
import os

def actualizar_base_datos():
    # Buscar la base de datos local.db
    posibles_rutas = [
        'instance/local.db',
        'local.db',
        '../instance/local.db',
        'C:/Users/Admin/Documents/ucundinamarca/séptimo semestre/Comunicación de datos/transporte app/instance/local.db',
        'C:/Users/Admin/Documents/ucundinamarca/séptimo semestre/Comunicación de datos/transporte app/local.db'
    ]
    
    db_path = None
    for ruta in posibles_rutas:
        if os.path.exists(ruta):
            db_path = ruta
            break
    
    if not db_path:
        print("❌ No se encontró la base de datos local.db. Buscando...")
        # Buscar en todo el directorio
        for root, dirs, files in os.walk('.'):
            if 'local.db' in files:
                db_path = os.path.join(root, 'local.db')
                break
    
    if not db_path:
        print("❌ No se pudo encontrar la base de datos local.db")
        print("Creando nueva base de datos...")
        # Crear directorio instance si no existe
        os.makedirs('instance', exist_ok=True)
        db_path = 'instance/local.db'
    
    print(f"📁 Usando base de datos: {db_path}")
    
    # Conectar a la base de datos
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Verificar si la tabla ruta existe
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='ruta'")
    if not cursor.fetchone():
        print("❌ La tabla 'ruta' no existe. Creando tabla...")
        cursor.execute('''
            CREATE TABLE ruta (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre VARCHAR(100) NOT NULL,
                origen VARCHAR(100) NOT NULL,
                destino VARCHAR(100) NOT NULL,
                horario VARCHAR(20) NOT NULL
            )
        ''')
        print("✅ Tabla 'ruta' creada")
    else:
        print("✅ Tabla 'ruta' existe")
    
    # Obtener columnas actuales
    cursor.execute("PRAGMA table_info(ruta)")
    columnas = [col[1] for col in cursor.fetchall()]
    
    print(f"\n📋 Columnas actuales: {columnas}")
    
    # Agregar columnas faltantes
    nuevas_columnas = {
        'tipo': "ALTER TABLE ruta ADD COLUMN tipo VARCHAR(20) DEFAULT 'interna'",
        'coordenadas_ida': "ALTER TABLE ruta ADD COLUMN coordenadas_ida TEXT",
        'coordenadas_vuelta': "ALTER TABLE ruta ADD COLUMN coordenadas_vuelta TEXT",
        'duracion_ida': "ALTER TABLE ruta ADD COLUMN duracion_ida INTEGER",
        'duracion_vuelta': "ALTER TABLE ruta ADD COLUMN duracion_vuelta INTEGER",
        'distancia_ida': "ALTER TABLE ruta ADD COLUMN distancia_ida FLOAT",
        'distancia_vuelta': "ALTER TABLE ruta ADD COLUMN distancia_vuelta FLOAT"
    }
    
    print("\n🔧 Agregando columnas faltantes...")
    for col, sql in nuevas_columnas.items():
        if col not in columnas:
            try:
                cursor.execute(sql)
                print(f"  ✅ Columna '{col}' agregada")
            except Exception as e:
                print(f"  ❌ Error agregando '{col}': {e}")
        else:
            print(f"  ⏭️  Columna '{col}' ya existe")
    
    # Guardar cambios
    conn.commit()
    
    # Verificar resultado final
    cursor.execute("PRAGMA table_info(ruta)")
    columnas_finales = [col[1] for col in cursor.fetchall()]
    
    print(f"\n📋 Columnas finales: {columnas_finales}")
    
    # Mostrar datos existentes
    cursor.execute("SELECT COUNT(*) FROM ruta")
    count = cursor.fetchone()[0]
    print(f"\n📊 La tabla 'ruta' tiene {count} registros")
    
    if count > 0:
        print("\n📝 Primeras rutas:")
        cursor.execute("SELECT id, nombre, origen, destino, tipo FROM ruta LIMIT 5")
        for row in cursor.fetchall():
            print(f"  ID: {row[0]}, Nombre: {row[1]}, Origen: {row[2]}, Destino: {row[3]}, Tipo: {row[4] if row[4] else 'sin definir'}")
    
    conn.close()
    print("\n🎉 Actualización completada exitosamente!")

if __name__ == '__main__':
    actualizar_base_datos()