# Cajicá en Ruta

Plataforma web para la visualización de rutas de transporte público en tiempo real en el municipio de Cajicá.  
**Diseño responsive** compatible con escritorio, tablet y dispositivos móviles.

![Status](https://img.shields.io/badge/status-en%20desarrollo-yellow)
![Responsive](https://img.shields.io/badge/design-responsive-green)
![Backend](https://img.shields.io/badge/backend-Flask-blue)
![Frontend](https://img.shields.io/badge/frontend-HTML%20%7C%20CSS%20%7C%20JS-orange)
![Database](https://img.shields.io/badge/database-SQLite-lightgrey)

---

## Descripción

Cajicá en Ruta es una aplicación web que permite a los usuarios consultar rutas de transporte público, visualizar la ubicación de los buses en tiempo real y conocer tiempos estimados de llegada.

El sistema busca mejorar la movilidad urbana, reducir tiempos de espera y brindar información confiable a los ciudadanos.

---

## Objetivo

Desarrollar una plataforma web que permita visualizar en tiempo real las rutas de transporte público en Cajicá, incluyendo recorridos internos y rutas hacia Bogotá, con un diseño totalmente responsive.

---

## Funcionalidades principales

### Mapa de Usuario
- Visualización de rutas en tiempo real
- Simulación de buses en movimiento
- Alternar sentido (Ida/Vuelta)
- Búsqueda inteligente de rutas
- Geolocalización del usuario
- Notificaciones en tiempo real

### Panel de Administración
- Crear y editar rutas con mapa interactivo
- Marcadores arrastrables
- Geocodificación inversa
- Cálculo automático de rutas
- Información de distancia y duración

### General
- Registro e inicio de sesión de usuarios
- Notificaciones del estado del servicio

---

## Responsive Design

### Breakpoints utilizados

| Dispositivo | Ancho |
|------------|-------|
| Extra pequeño | 320px - 359px |
| Móvil | 360px - 480px |
| Móvil grande | 481px - 768px |
| Tablet | 769px - 1024px |
| Desktop | 1025px+ |

### Implementaciones por pantalla

| Sección | Adaptaciones responsive |
|---------|------------------------|
| Login & Register | Inputs full-width, botones táctiles (≥44px), cards adaptables |
| Admin Panel | Sidebar colapsable, tablas con scroll horizontal, dashboard en columna única |
| Mapa Usuario | Mapa full-screen, sidebar tipo overlay, bottom navigation táctil |
| Editor de Rutas | Layout 2 columnas → 1 columna, interfaz táctil optimizada |

---

## Actores del sistema

- Usuarios del transporte público
- Conductores
- Administradores
- Entidad de movilidad

---

## Tecnologías utilizadas

### Frontend
- HTML5
- CSS3 (Flexbox + Grid)
- JavaScript

### Backend
- Python (Flask)

### Base de datos
- SQLite

### APIs Externas

| API | Descripción | Uso en el proyecto |
|-----|-------------|-------------------|
| **Leaflet.js** | Biblioteca JavaScript para mapas interactivos | Renderizado del mapa, marcadores, capas, zoom/pan |
| **OpenStreetMap** | Base de datos cartográfica colaborativa | Provee las capas base del mapa |
| **OSRM** | Motor de enrutamiento open-source | Cálculo de rutas, distancias y tiempos de viaje |
| **Nominatim** | Servicio de geocodificación | Conversión entre direcciones y coordenadas |

### Hosting
- Render

---

## API Endpoints

| Endpoint | Método | Descripción |
|----------|--------|-------------|
| `/api/rutas` | GET | Obtener rutas |
| `/admin/ruta/nueva` | GET/POST | Crear ruta |
| `/admin/ruta/guardar` | POST | Guardar ruta |

---

## Estructura del proyecto

```plaintext
proyecto/
│
├── app.py
├── requirements.txt
├── templates/
│   ├── login.html
│   ├── register.html
│   └── usuario.html
│
├── static/
│   ├── style.css
│   ├── img/
│   └── js/
