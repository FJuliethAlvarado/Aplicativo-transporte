# Dashboards y Tableros de Análisis - RouteX

## Descripción General

Se ha implementado un sistema completo de **dashboards estadísticos** para usuarios, conductores y administradores. Cada tipo de usuario cuenta con visualizaciones personalizadas que muestran análisis detallados de su actividad.

---

## Características Implementadas

### 1. **Página de Perfil Unificada** (`/perfil`)
Todos los usuarios pueden acceder a su perfil personalizado con:
- Información de la cuenta (nombre, email, tipo de usuario)
- Estadísticas en tiempo real
- Gráficos interactivos
- Historial de rutas favoritas

### 2. **Modelo de Datos - Tabla `Trip`**
Se creó una nueva tabla para registrar viajes:
```python
class Trip(db.Model):
    - usuario_id: ID del pasajero
    - conductor_id: ID del conductor
    - ruta_id: ID de la ruta
    - fecha_hora: Timestamp del viaje
    - duracion_minutos: Duración total
    - distancia_km: Distancia recorrida
    - costo: Tarifa pagada
    - calificacion: Rating (1-5)
    - comentario: Feedback del usuario
    - estado: completado/cancelado
```

---

## Estadísticas por Tipo de Usuario

### **Para Usuarios (Pasajeros)**

#### Tarjetas de Información:
1. **Viajes Totales**
   - Total de viajes realizados
   - Desglose: completados vs cancelados

2. **Distancia Total**
   - Kilómetros recorridos
   - Promedio por viaje

3. **Tiempo en Transporte**
   - Horas totales en transporte
   - Promedio por viaje

4. **Calificación Promedio**
   - Rating: 1-5 estrellas
   - Clasificación: Excelente/Muy Bueno/Bueno/Aceptable

5. **Gasto Total**
   - Dinero invertido en viajes
   - Costo promedio por viaje

#### Visualizaciones:
- 📊 Gráfico de pastel: Estado de viajes (completados/cancelados)
- 📈 Estadísticas de distancia
- ⏱️ Tiempo de viaje
- ⭐ Top 5 rutas más frecuentes

---

### **Para Conductores**

#### Tarjetas de Información:
1. **Viajes Totales**
   - Total de viajes realizados
   - Desglose: completados vs cancelados

2. **Distancia Total**
   - Kilómetros recorridos
   - Promedio por viaje

3. **Tiempo en Transporte**
   - Horas totales trabajadas
   - Promedio por viaje

4. **Calificación Promedio**
   - Rating de pasajeros (1-5)
   - Reputación

5. **Ingreso Total**
   - Dinero ganado
   - Ingreso promedio por viaje

6. **Ruta Asignada**
   - Ruta actual de trabajo
   - Información de origen/destino

---

### **Para Administradores**

En `admin_inicio.html` ya se tenían estadísticas del sistema:
- Total de usuarios por tipo
- Total de rutas (internas/intermunicipales)
- Gráficos de distribución

Login conductor
Email: admin@cajica.com
Password: admin123

---

##  Cómo Usar

### 1. **Acceder al Perfil**

**Desde Usuario:**
```
Interfaz móvil → Bottom Navigation → Icono "Perfil" (👤) → Mi Perfil
O: URL directa /perfil

👤 Login pasajero
Email: pasajero@test.com
Password: 123456

```

**Desde Conductor:**
```
Panel conductor → Bottom Panel → Botón "Perfil" → Mi Perfil
O: URL directa /perfil

🚗 Login conductor
Email: conductor@test.com
Password: 123456
```

### 2. **Navegar los Dashboards**

1. **Tarjetas de Estadísticas**: Información rápida en tarjetas animadas
2. **Gráficos Interactivos**: Chart.js para visualizaciones
3. **Rutas Favoritas**: Lista de rutas más utilizadas
4. **Botones de Acción**: 
   - Volver a la interfaz principal
   - Cerrar sesión

---

## Diseño Visual

### Características de UI:
- **Tema Oscuro**: Consistente con el diseño general de RouteX
- **Gradient Cyan-Blue**: #0ea5e9 a #2563eb
- **Responsive Design**: Funciona en móvil, tablet y desktop
- **Animaciones**: Transiciones suaves, efectos hover
- **Gráficos Interactivos**: Con Chart.js
- **Icons Font Awesome**: Para mejor visualización

### Componentes Reutilizables:
```css
.card           /* Tarjetas de información */
.chart-container /* Contenedores de gráficos */
.stat-item      /* Items de estadísticas */
.ruta-item      /* Items de rutas */
.btn            /* Botones primarios/secundarios */
```

---

## Ejemplo de Datos Mostrados

### Usuario Pasajero:
```
Viajes Totales: 15
├─ Completados: 14
└─ Cancelados: 1

Distancia Total: 187.50 km
Promedio por viaje: 12.50 km

Tiempo Total: 420 minutos (7 horas)
Promedio por viaje: 28.0 minutos

Calificación: 4.7 / 5 ⭐

Gasto Total: $42,500
Promedio: $2,833 por viaje

Rutas Favoritas:
1. Centro - Periferia (8 viajes)
2. Estación - Universidad (5 viajes)
3. Mercado - Terminal (2 viajes)
```

### Conductor:
```
Viajes Realizados: 45
├─ Completados: 44
└─ Cancelados: 1

Ruta Asignada: Ruta Centro - Periferia

Calificación: 4.8 / 5 ⭐

Ingreso Total: $450,000
Promedio: $10,227 por viaje
```

---

## 🔧 Endpoints Disponibles

| Endpoint | Método | Descripción |
|----------|--------|-------------|
| `/perfil` | GET | Panel de perfil personalizado |
| `/api/add-sample-data` | GET | Agregar datos de ejemplo |
| `{{ url_for('perfil') }}` | - | Template function para links |

---

## 📝 Modificaciones a Archivos Existentes

### `app.py`
- ✅ Modelo `Trip` agregado
- ✅ Ruta `/perfil` implementada
- ✅ Lógica de estadísticas por tipo de usuario
- ✅ Endpoint `/api/add-sample-data`
- ✅ Columnas de Trip en db.create_all()

### `templates/usuario.html`
- ✅ Enlace al perfil en bottom-nav

### `templates/conductor.html`
- ✅ Botón de perfil en bottom-panel

### `templates/mi_perfil.html` (NUEVO)
- ✅ Dashboard completo responsivo
- ✅ Gráficos interactivos
- ✅ Estadísticas dinámicas

---

## Solución de Problemas

### Los gráficos no se cargan
→ Verificar que Chart.js esté cargado desde CDN
→ Revisar la consola del navegador (F12)

### Datos vacíos en el dashboard
→ Ejecutar `/api/add-sample-data` para agregar datos de ejemplo
→ Verificar que haya viajes en la base de datos

### Enlace del perfil no funciona
→ Verificar que la ruta esté registrada en app.py
→ Comprobar que el usuario esté autenticado (session['user_id'])

---

## Próximas Mejoras

- [ ] Exportar estadísticas a PDF
- [ ] Gráficos de tendencias históricos
- [ ] Comparativas mes a mes
- [ ] Sistema de logros/badges
- [ ] Recomendaciones basadas en datos
- [ ] Notificaciones de hitos alcanzados
- [ ] Integración con mapas para visualizar rutas

---

## Notas Importantes

1. **Datos de Ejemplo**: Se pueden agregar mediante `/api/add-sample-data`
2. **Autenticación**: Solo usuarios autenticados pueden ver su perfil
3. **Privacidad**: Cada usuario solo ve sus propias estadísticas
4. **Responsive**: El diseño se adapta a cualquier dispositivo
5. **Performance**: Los gráficos se cargan bajo demanda

---

## Soporte Técnico

Para cualquier duda o problema:
1. Revisar la consola del navegador (F12)
2. Verificar los logs de Flask
3. Confirmar que la base de datos esté actualizada
4. Ejecutar `flask db upgrade` si es necesario

---

**Última actualización:** Mayo 2026
**Versión:** 1.0.0
