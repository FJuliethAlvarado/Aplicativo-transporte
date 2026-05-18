import asyncio
import os

try:
    from slixmpp import ClientXMPP
    SLIXMPP_AVAILABLE = True
except ImportError:
    SLIXMPP_AVAILABLE = False


class _SimpleXMPPClient(ClientXMPP):
    def __init__(self, jid, password, recipient, message):
        super().__init__(jid, password)
        self.recipient = recipient
        self.message = message
        self.add_event_handler('session_start', self.start)

    async def start(self, event):
        self.send_message(mto=self.recipient, mbody=self.message, mtype='chat')
        self.disconnect()


class XMPPService:
    def __init__(self):
        self.jid = os.getenv('XMPP_JID')
        self.password = os.getenv('XMPP_PASSWORD')
        self.server = os.getenv('XMPP_SERVER')
        self.port = int(os.getenv('XMPP_PORT', 5222))
        self.bot_jid = os.getenv('XMPP_BOT_JID')
        self.support_jid = os.getenv('XMPP_SUPPORT_JID')
        self.enabled = SLIXMPP_AVAILABLE and bool(self.jid and self.password and self.server)

    def is_configured(self):
        return self.enabled

    def send_message(self, to_jid, body):
        if not self.is_configured() or not to_jid:
            return False

        try:
            xmpp = _SimpleXMPPClient(self.jid, self.password, to_jid, body)
            if self.server:
                connected = xmpp.connect((self.server, self.port))
            else:
                connected = xmpp.connect()

            if not connected:
                return False

            xmpp.process(forever=False)
            return True
        except Exception as e:
            print(f"XMPP sending failed: {e}")
            return False

    def send_to_bot(self, profile, message):
        if not self.bot_jid:
            return False
        return self.send_message(self.bot_jid, f"[{profile}] {message}")

    def notify_support(self, subject, body):
        if not self.support_jid:
            return False
        return self.send_message(self.support_jid, f"{subject}\n\n{body}")

    def generate_reply(self, message, profile):
        prompt = (message or '').lower()

        if profile == 'usuario':
            if any(word in prompt for word in ('ruta', 'horario', 'destino', 'origen', 'llegada', 'salida')):
                return (
                    '👋 Hola, soy tu asistente de movilidad. Puedes usar el mapa para ver las rutas disponibles, ' 
                    'sus horarios y trayectos. Si quieres, dime la ruta o el destino y te cuento más detalles.'
                )
            if any(word in prompt for word in ('costo', 'precio', 'tarifa', 'valor')):
                return (
                    'Las tarifas dependen del tipo de ruta. Las rutas internas suelen ser más económicas y las intermunicipales ' 
                    'se calculan según la distancia. Verifica la ruta en el mapa para conocer su costo estimado.'
                )
            if any(word in prompt for word in ('seguro', 'seguridad', 'covid', 'salud')):
                return (
                    'Tu seguridad es importante. Si ves alguna situación irregular, por favor repórtala al administrador o desde el chat ' 
                    'para que el equipo de soporte pueda intervenir.'
                )
            if any(word in prompt for word in ('problema', 'ayuda', 'soporte', 'duda')):
                return (
                    'Estoy aquí para ayudarte. Cuéntame qué necesitas: rutas, horarios, costos, o cómo usar el mapa, y te respondo.'
                )
            return (
                'Hola, estoy listo para ayudarte con la información de rutas y horarios. ' 
                'Escríbeme qué necesitas saber y te orientaré.'
            )

        if profile == 'conductor':
            if any(word in prompt for word in ('reporte', 'incidencia', 'accidente', 'cierre', 'problema')):
                return (
                    'Para reportar una incidencia, utiliza el formulario en tu panel de conductor. ' 
                    'También puedo notificar a soporte si necesitas asistencia urgente.'
                )
            if any(word in prompt for word in ('ruta', 'ruta asignada', 'trayecto', 'itinerario')):
                return (
                    'Tu ruta asignada aparece en la tarjeta de información del panel. ' 
                    'Puedes alternar el sentido y activar el modo online para simular tu trayecto.'
                )
            if any(word in prompt for word in ('online', 'estado', 'servicio', 'bus')):
                return (
                    'Usa el botón de estado en tu panel para marcar el bus como online o offline. ' 
                    'Cuando estés en servicio, el sistema actualizará tu ubicación automáticamente.'
                )
            if any(word in prompt for word in ('ayuda', 'duda', 'soporte')):
                return (
                    'Estoy aquí para apoyarte con tu ruta y los reportes. ' 
                    'Describe tu situación y te indicaré cuál es el mejor paso a seguir.'
                )
            return (
                'Puedo ayudarte con información de tu ruta asignada, cómo reportar incidencias y cómo usar tu panel de conductor.'
            )

        if profile == 'administrador':
            if any(word in prompt for word in ('usuarios', 'conductores', 'rutas', 'actividad', 'logs', 'reportes')):
                return (
                    'Revisa el panel de administración para gestionar usuarios, conductores, rutas y actividad. ' 
                    'También puedes ver el historial de logs y exportar reportes cuando lo necesites.'
                )
            if any(word in prompt for word in ('soporte', 'incidencia', 'error', 'problema')):
                return (
                    'Si hay un problema en el sistema, puedes notificar a soporte y revisar los registros del historial de actividad. ' 
                    'Estoy listo para ayudarte a identificar dónde está el incidente.'
                )
            return (
                'Soy tu asistente administrativo. Puedo ayudarte a entender el estado del sistema, ' 
                'las métricas de uso y cómo navegar el panel de administración.'
            )

        return (
            'Hola, estoy listo para ayudarte. Describe tu consulta con detalle y te responderé lo mejor posible.'
        )
