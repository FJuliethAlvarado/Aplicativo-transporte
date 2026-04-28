// usuario.js

// Función para generar datos dinámicos simulados
function cargarInfoRuta016() {
  // Simulación de próximos buses (cada 10 min)
  const horaActual = new Date();
  const minutos = horaActual.getMinutes();
  const proximos = [
    `🚌 Bus 1: en servicio`,
    `🚌 Bus 2: sale en ${10 - (minutos % 10)} min`,
    `🚌 Bus 3: sale en ${20 - (minutos % 10)} min`
  ];

  document.getElementById("proximos-buses").innerHTML = `
    <b>Próximos buses:</b><br>
    ${proximos.join("<br>")}
  `;

  // Simulación de tiempos de llegada (se ajustan con un margen aleatorio)
  const tiempoChia = 15 + Math.floor(Math.random() * 3);   // 15 ± 2 min
  const tiempoCajica = 25 + Math.floor(Math.random() * 3); // 25 ± 2 min
  const tiempoPortal = 50 + Math.floor(Math.random() * 5); // 50 ± 4 min

  document.getElementById("tiempos-paradas").innerHTML = `
    <b>Tiempos de llegada:</b><br>
    📍 Chía: ~${tiempoChia} min<br>
    📍 Centro Cajicá: ~${tiempoCajica} min<br>
    📍 Portal del Norte: ~${tiempoPortal} min
  `;

  // Tarifas fijas
  document.getElementById("tarifas").innerHTML = `
    <b>Tarifas:</b><br>
    💰 Desde Cajicá: $7.200 COP<br>
    💰 Desde Chía: $5.000 COP<br>
    💰 Interno Cajicá: $2.500 COP
  `;
}

// Ejecutar al cargar la página
window.onload = () => {
  cargarInfoRuta016();
  // Actualizar cada 30 segundos
  setInterval(cargarInfoRuta016, 30000);
};
