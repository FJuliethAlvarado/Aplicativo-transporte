# RouteX 
### Plataforma de Transporte Inteligente con Diseño Responsive

![Status](https://img.shields.io/badge/status-en%20desarrollo-yellow)
![Responsive](https://img.shields.io/badge/design-responsive-green)
![Backend](https://img.shields.io/badge/backend-Flask-blue)
![Frontend](https://img.shields.io/badge/frontend-HTML%20%7C%20CSS%20%7C%20JS-orange)
![Database](https://img.shields.io/badge/database-SQLite-lightgrey)

---

##  Demo Visual

### Desktop
<img width="1828" height="891" alt="Captura de pantalla 2026-04-29 215140" src="https://github.com/user-attachments/assets/f32c6cf4-a5fb-4d6d-a3ea-04840bef6468" />
<img width="1507" height="872" alt="Captura de pantalla 2026-04-29 215151" src="https://github.com/user-attachments/assets/0ad64f0d-784b-4f18-a9e6-41f355f228ee" />

### Mobile

<img width="390" height="741" alt="Captura de pantalla 2026-04-29 215046" src="https://github.com/user-attachments/assets/102ad1c2-45ba-47d8-8a58-cb2fbba16b1c" />
<img width="360" height="803" alt="Captura de pantalla 2026-04-29 215007" src="https://github.com/user-attachments/assets/c21eef06-ae1d-48d4-bd65-25dc4fc9e234" />


---

## Objetivo
Hacer que la aplicación sea compatible tanto para **escritorio** como para **dispositivos móviles**, aplicando principios de **Responsive Web Design**.

---

##  Características Principales

### Mapa de Usuario
- Visualización de rutas en tiempo real  
- Simulación de buses en movimiento  
- Alternar sentido (Ida/Vuelta)  
- Búsqueda inteligente de rutas  
- Geolocalización del usuario  
- Notificaciones en tiempo real  

---

###  Panel de Administración
- Crear y editar rutas con mapa interactivo  
- Marcadores arrastrables  
- Geocodificación inversa  
- Cálculo automático de rutas  
- Información de distancia y duración  

---

## Responsive Design

### Breakpoints utilizados
| Dispositivo | Ancho |
|------------|------|
| Extra pequeño | 320px - 359px |
| Móvil | 360px - 480px |
| Móvil grande | 481px - 768px |
| Tablet | 769px - 1024px |
| Desktop | 1025px+ |

---

### Implementaciones Responsive

#### Login & Register
- Inputs full-width  
- Botones táctiles (≥ 44px)  
- Cards adaptables  
- Tipografía escalable  

#### Admin Panel
- Sidebar colapsable  
- Tablas con scroll horizontal  
- Dashboard en columna única en móvil  

#### Mapa Usuario
- Mapa full-screen  
- Sidebar tipo overlay  
- Bottom navigation táctil  
- Controles optimizados  

#### Editor de Rutas
- Layout 2 columnas → 1 columna  
- Mapa adaptable  
- Interfaz táctil optimizada  

---

##  Tecnologías Utilizadas

### Frontend
- HTML5  
- CSS3 (Flexbox + Grid)  
- JavaScript  

### Backend
- Python  
- Flask  

## APIs Externas

| API | Descripción | Uso en el proyecto |
|-----|-------------|-------------------|
| **Leaflet.js** | Biblioteca JavaScript para mapas interactivos | Renderizado del mapa, marcadores, capas, zoom/pan |
| **OpenStreetMap** | Base de datos cartográfica colaborativa | Provee las capas base del mapa (calles, terrenos) |
| **OSRM** | Motor de enrutamiento open-source | Cálculo de rutas, distancias y tiempos de viaje |
| **Nominatim** | Servicio de geocodificación | Conversión entre direcciones y coordenadas |

---

##  API Endpoints

| Endpoint | Método | Descripción |
|---------|--------|------------|
| `/api/rutas` | GET | Obtener rutas |
| `/admin/ruta/nueva` | GET/POST | Crear ruta |
| `/admin/ruta/guardar` | POST | Guardar ruta |

---

##  Funcionalidades JavaScript

### Usuario (Mapa)
```javascript
cargarRutas()           // Carga rutas desde la API
dibujarRuta()           // Dibuja la ruta en el mapa
alternarSentido()       // Cambia entre ida y vuelta
simularBus()            // Anima el bus en movimiento
mostrarNotificacion()   // Muestra alertas al usuario
initMap()               // Inicializa el mapa en Cajicá
setOrigen()             // Marca punto de origen
setDestino()            // Marca punto de destino
reverseGeocode()        // Convierte coordenadas a dirección
calcularRuta()          // Calcula ruta con OSRM
actualizarRuta()        // Dibuja ida y vuelta en el mapa
```

## Testing

### Navegadores
- Chrome DevTools  
- Firefox Developer  
- Safari (iOS)  
- Navegadores móviles  

---

## Checklist

- ✔️ Diseño responsive completo  
- ✔️ Mapa funcional en móvil  
- ✔️ Sin scroll horizontal (excepto tablas)  
- ✔️ Botones accesibles táctiles  
- ✔️ Simulación de buses  
- ✔️ CRUD de rutas  
- ✔️ Notificaciones  

---

##  Performance

- Mobile-first design  
- Uso de Flexbox y Grid  
- Lazy loading en mapas  
- Animaciones optimizadas (`requestAnimationFrame`)  
- Sin dependencias pesadas  

---

##  Problemas y Soluciones

| Problema | Solución |
|----------|----------|
| Botón no visible | Event listener dinámico |
| Coordenadas incorrectas | Validación + JSON parsing |
| Error en rutas | Separación de variables |

---

##  Roadmap

### Corto Plazo
- Mejorar UI del mapa  
- Optimizar imágenes  
- Panel de notificaciones  

###  Mediano Plazo
- PWA  
- Gestos táctiles  
- Modo offline parcial  

###  Largo Plazo
- Dark mode  
- Optimización avanzada  
- Testing automatizado  

---

##  Vista del Sistema

### Desktop
- Sidebar lateral  
- Dashboard completo  
- Mapa con controles  

### Tablet
- Sidebar horizontal  
- Layout adaptado  

### Móvil
- Menú hamburguesa  
- Controles compactos  
- Navegación táctil  

---

##  Referencias
- MDN Web Docs  
- W3C  
- Leaflet Docs  
- OSRM API  

---

##  Autores

**Julieth Alvarado & Laura Bernal**  
Proyecto académico - Sistema de transporte inteligente 
