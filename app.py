from flask import Flask, render_template, request, jsonify, Response
import cv2
import threading
import time
import json
from datetime import datetime

app = Flask(__name__)


# Estado global
class AppState:
    def __init__(self):
        self.base_prompt = {
            "role": "system",
            "content": "Eres un asistente profesional con capacidad de análisis visual.",
            "context": {
                "style": "profesional",
                "responses": "precisas y técnicas"
            }
        }
        self.conversation = []
        self.camera_active = False
        self.frame = None
        
    def add_message(self, role, content):
        self.conversation.append({
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat()
        })
        
    def clear_conversation(self):
        self.conversation = []

app_state = AppState()

# Configuración de la cámara
camera = cv2.VideoCapture(0)
if camera.isOpened():
    app_state.camera_active = True

def generate_frames():
    while app_state.camera_active:
        success, frame = camera.read()
        if not success:
            break
        else:
            ret, buffer = cv2.imencode('.jpg', frame)
            frame = buffer.tobytes()
            app_state.frame = frame
        time.sleep(0.03)

# Iniciar hilo de la cámara
if app_state.camera_active:
    camera_thread = threading.Thread(target=generate_frames)
    camera_thread.daemon = True
    camera_thread.start()

@app.route('/')
def index():
    return render_template('index.html', camera_active=app_state.camera_active)

@app.route('/video_feed')
def video_feed():
    def generate():
        while app_state.camera_active:
            if app_state.frame is not None:
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + app_state.frame + b'\r\n')
            time.sleep(0.03)
    
    return Response(generate(),
                   mimetype='multipart/x-mixed-replace; boundary=frame')
@app.route('/send_message', methods=['POST'])
def send_message():
    data = request.json
    user_input = data.get('message', '').strip()
    
    if user_input:
        # Usando el nuevo método add_message
        app_state.add_message("user", user_input)
        
        # Simular respuesta de IA
        app_state.add_message("assistant", f"Recibí: '{user_input}'. Contexto actualizado correctamente.")
        
        # Preparar respuesta para el cliente
        display_messages = [
            f"{'Tú' if msg['role'] == 'user' else 'Asistente'}: {msg['content']}"
            for msg in app_state.conversation
        ]
        
        return jsonify({
            "status": "success",
            "messages": display_messages
        })
    
    return jsonify({"status": "error", "message": "Mensaje vacío"})

@app.route('/new_prompt', methods=['POST'])
def new_prompt():
    app_state.clear_conversation()  # Usando el nuevo método
    return jsonify({
        "status": "success",
        "message": "Contexto reiniciado. Puedes comenzar una nueva conversación."
    })

@app.route('/get_conversation', methods=['GET'])
def get_conversation():
    display_messages = []
    for msg in app_state.conversation:  # Cambiado a acceso por punto
        if msg["role"] == "user":
            display_messages.append(f"Tú: {msg['content']}")
        else:
            display_messages.append(f"Asistente: {msg['content']}")
    
    return jsonify({
        "messages": display_messages,
        "camera_active": app_state.camera_active  # Cambiado a acceso por punto
    })

if __name__ == '__main__':
    try:
        app.run(host='0.0.0.0', port=5000, threaded=True)
    finally:
        app_state["camera_active"] = False
        if camera.isOpened():
            camera.release()