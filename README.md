# backend-gps
Repositorio para gps con traccar

| 🟢 Baja | 5. Compartir ubicación | Bajo | Medio |
## 5. Compartir Ubicación en Tiempo Real

*Qué es*: Generar link público temporal para compartir la posición de una unidad sin login.

*Por qué encaja*: Cloudflare Tunnel ya expone el backend públicamente — solo falta un endpoint de token temporal.

*Funcionalidades*:
- Botón "Compartir" en FloatingInfoCard (ícono de share)
- Genera URL con token de 24h: https://api-gps.digitactivo.com/track/TOKEN
- Vista pública minimal: mapa con un solo marcador, nombre de unidad y última actualización
- Opción de expiración: 1h / 6h / 24h / hasta que se desactive
- Revocar link desde la misma card
| 🟢 Baja | 8. Heatmap | Bajo | Medio |
## 8. Heatmap de Actividad

*Qué es*: Capa visual en el mapa que muestra zonas de mayor densidad de tráfico de la flota.

*Por qué encaja*: LiveMap.tsx ya tiene acceso a MapLibre GL — que soporta heatmap layers nativamente.

*Funcionamiento*:
- Toggle en toolbar del mapa: "Calor" / "Estándar"
- Acumula posiciones históricas del día/semana y las pasa a una capa heatmap-layer de MapLibre
- Gradiente: azul → amarillo → rojo (intensidad de paso)
- Selector de período: hoy / esta semana / mes
- Se desactiva automáticamente al seleccionar una unidad

| 🟢 Baja | 7. Notificaciones push | Medio | Alto |
## 7. Notificaciones Push / Webhooks

*Qué es*: Enviar alertas en tiempo real a canales externos cuando ocurren eventos.

*Por qué encaja*: El backend ya procesa los eventos de Traccar — solo falta el dispatcher.

*Canales*:
- *WhatsApp* via Twilio o WhatsApp Business API
- *Telegram* bot (más simple: solo token + chat_id)
- *Email* (SMTP)
- *Webhook genérico* (POST con payload JSON a cualquier URL)

*UI*: Nueva sección en "Configuración" — tarjeta por canal con toggle on/off, selector de eventos a notificar y campo de destino.
| 🟢 Baja | 13. Multi-usuario | Alto | Alto |
## 13. Multi-usuario con Roles

*Qué es*: Sistema de autenticación con roles diferenciados.

*Por qué encaja*: El backend ya tiene configuración de credenciales via .env — expandirlo a un sistema de usuarios es el paso natural para operación comercial.

*Roles propuestos*:
- *Admin*: acceso total (configuración, usuarios, todos los dispositivos)
- *Supervisor*: ver todo, gestionar conductores y geofences, no puede eliminar dispositivos
- *Operador*: solo ver mapa y alertas en tiempo real, sin acceso a reportes ni gestión
- *Conductor* (mobile-ready): solo ver su propia unidad y recibir mensajes

*UI*: Login screen con glass-panel, selector de rol visual en onboarding, navbar muestra nombre + avatar inicial.
| 🟢 Baja | 14. Alertas programadas | Alto | Alto |
## 14. Alertas Programadas — "Tareas de Seguimiento"

*Qué es*: Crear checks automáticos que revisan condiciones y disparan alertas si no se cumplen.

*Ejemplos reales*:
- "Si Unidad 3 no llega a Zona B antes de las 18:00 → alertar"
- "Si alguna unidad lleva más de 2h sin movimiento en horario laboral → alertar"
- "Si la velocidad promedio de un viaje supera 100 km/h → notificar al supervisor"

*UI*: Nueva sección en "Configuración" — lista de reglas con toggle, builder visual con condiciones encadenadas (dispositivo → condición → umbral → canal de notificación).

| ⚪ Futuro | 9. Modo patrulla | Alto | Medio |
## 9. Modo Patrulla — Seguimiento de Múltiples Unidades

*Qué es*: Dividir el mapa en paneles para seguir varias unidades simultáneamente.

*Por qué encaja*: MapLibre permite múltiples instancias — agregar como layout alternativo.

*Variantes*:
- *Modo split 2×1*: dos mini-mapas cada uno fijo a una unidad
- *Modo tabla*: lista con fila expandible que muestra mini-mapa inline al hacer hover
- Selector de unidades para el modo patrulla desde DevicesSidebar
- Cada panel muestra: nombre, velocidad actual, conductor, última alerta
| ⚪ Futuro | 12. Corredor de ruta | Alto | Medio |
## 12. Geocerca de Ruta (Corredor)

*Qué es*: Definir una ruta esperada como corredor — alertar si el vehículo se desvía.

*Por qué encaja*: Geozones.tsx ya renderiza polígonos WKT — un corredor es un polígono buffer alrededor de una polilínea.

*Funcionamiento*:
- Nueva herramienta en MapEditToolbar: "Trazar corredor"
- El usuario dibuja la ruta esperada como línea → backend genera buffer de X metros
- Si el vehículo sale del buffer → alerta en AlertsPanel tipo routeDeviation
- Configurable: ancho del corredor en metros, horario activo

| ⚪ Futuro | 15. Chat con conductor | Alto | Medio |
## 15. Chat Interno / Mensajería al Conductor

*Qué es*: Enviar mensajes de texto al conductor directamente desde el dashboard (vía app móvil o SMS).

*Por qué encaja*: FloatingInfoCard ya muestra el conductor asignado — agregar botón de mensaje es incremental.

*Funcionamiento*:
- Botón "Mensaje" en FloatingInfoCard → modal con textarea y enviar
- Historial de mensajes por unidad/conductor (scrollable, como chat básico)
- Backend: webhook a Telegram bot / WhatsApp / SMS (Twilio)
- Estado de lectura: enviado / visto (si hay app móvil)