import sys
import cv2
from PyQt5.QtCore import Qt, QThread, pyqtSignal, pyqtSlot
from PyQt5.QtGui import QImage, QPixmap, QFont, QColor, QPalette
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QTextEdit, QPushButton, QLabel, 
                             QLineEdit, QFrame)

class CameraThread(QThread):
    change_pixmap = pyqtSignal(QImage)
    
    def __init__(self):
        super().__init__()
        self._is_running = True
        self._cap = None
        
    def run(self):
        self._cap = cv2.VideoCapture(0)
        if not self._cap.isOpened():
            print("Error: No se pudo abrir la cámara")
            return
            
        while self._is_running:
            ret, frame = self._cap.read()
            if not ret:
                print("Error: No se pudo leer el frame de la cámara")
                break
                
            rgb_image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            h, w, ch = rgb_image.shape
            bytes_per_line = ch * w
            convert_to_qt_format = QImage(rgb_image.data, w, h, bytes_per_line, QImage.Format_RGB888)
            p = convert_to_qt_format.scaled(640, 480, Qt.KeepAspectRatio)
            self.change_pixmap.emit(p)
            self.msleep(30)
    
    def stop(self):
        self._is_running = False
        self.wait(500)
        if self._cap is not None:
            self._cap.release()
        self.quit()

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Asistente con Visión")
        self.setGeometry(100, 100, 1100, 650)
        
        # Estilo de la aplicación
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f5f5f5;
            }
            QTextEdit {
                background-color: white;
                border: 1px solid #ddd;
                border-radius: 5px;
                padding: 5px;
                font-size: 14px;
            }
            QLineEdit {
                background-color: white;
                border: 1px solid #ddd;
                border-radius: 5px;
                padding: 8px;
                font-size: 14px;
            }
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 10px;
                border-radius: 5px;
                font-size: 14px;
                min-width: 100px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton#newPromptBtn {
                background-color: #f44336;
            }
            QPushButton#newPromptBtn:hover {
                background-color: #d32f2f;
            }
            QLabel#cameraLabel {
                border: 2px solid #ddd;
                border-radius: 5px;
            }
        """)
        
        # Prompt base como diccionario interno
        self._base_prompt = {
            "role": "system",
            "content": "Eres un asistente profesional con capacidad de análisis visual.",
            "context": {
                "style": "profesional",
                "responses": "precisas y técnicas"
            }
        }
        
        self._conversation = []
        self._setup_ui()
        self._setup_camera()
    
    def _setup_ui(self):
        central_widget = QWidget()
        central_widget.setObjectName("centralWidget")
        layout = QHBoxLayout(central_widget)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(15)
        
        # Panel de cámara (izquierda)
        camera_frame = QFrame()
        camera_frame.setFrameShape(QFrame.StyledPanel)
        camera_layout = QVBoxLayout(camera_frame)
        camera_layout.setContentsMargins(5, 5, 5, 5)
        
        self.camera_label = QLabel()
        self.camera_label.setObjectName("cameraLabel")
        self.camera_label.setAlignment(Qt.AlignCenter)
        self.camera_label.setMinimumSize(640, 480)
        camera_layout.addWidget(self.camera_label)
        
        layout.addWidget(camera_frame, stretch=2)
        
        # Panel de chat (derecha)
        chat_frame = QFrame()
        chat_frame.setFrameShape(QFrame.StyledPanel)
        chat_layout = QVBoxLayout(chat_frame)
        chat_layout.setContentsMargins(10, 10, 10, 10)
        chat_layout.setSpacing(10)
        
        # Título del chat
        chat_title = QLabel("Chat con Asistente IA")
        chat_title.setFont(QFont("Arial", 16, QFont.Bold))
        chat_title.setAlignment(Qt.AlignCenter)
        chat_layout.addWidget(chat_title)
        
        # Área de chat
        self.chat_display = QTextEdit()
        self.chat_display.setPlaceholderText("La conversación aparecerá aquí...")
        chat_layout.addWidget(self.chat_display, stretch=1)
        
        # Entrada de mensaje
        self.message_input = QLineEdit()
        self.message_input.setPlaceholderText("Escribe tu mensaje y presiona Enter...")
        self.message_input.returnPressed.connect(self._send_message)
        chat_layout.addWidget(self.message_input)
        
        # Botones
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)
        
        self.new_prompt_btn = QPushButton("Nuevo Contexto")
        self.new_prompt_btn.setObjectName("newPromptBtn")
        self.new_prompt_btn.clicked.connect(self._reset_conversation)
        button_layout.addWidget(self.new_prompt_btn)
        
        self.send_btn = QPushButton("Enviar Mensaje")
        self.send_btn.clicked.connect(self._send_message)
        button_layout.addWidget(self.send_btn)
        
        chat_layout.addLayout(button_layout)
        layout.addWidget(chat_frame, stretch=1)
        
        self.setCentralWidget(central_widget)
    
    def _setup_camera(self):
        self.camera_thread = CameraThread()
        self.camera_thread.change_pixmap.connect(self._update_camera)
        self.camera_thread.finished.connect(self._camera_closed)
        self.camera_thread.start()
    
    @pyqtSlot(QImage)
    def _update_camera(self, image):
        self.camera_label.setPixmap(QPixmap.fromImage(image))
    
    @pyqtSlot()
    def _camera_closed(self):
        self.camera_label.setText("Cámara no disponible")
    
    def _send_message(self):
        user_input = self.message_input.text().strip()
        if not user_input:
            return
            
        # Guardar mensaje del usuario
        user_message = {
            "role": "user",
            "content": user_input
        }
        self._conversation.append(user_message)
        
        # Mostrar mensaje con estilo
        self.chat_display.append(f"<b style='color:#2c7be5'>Tú:</b> {user_input}")
        
        # Simular respuesta de IA
        ai_response = {
            "role": "assistant",
            "content": f"He recibido tu mensaje: '{user_input}'. Estoy procesando la información."
        }
        self._conversation.append(ai_response)
        self.chat_display.append(f"<b style='color:#00a854'>Asistente:</b> {ai_response['content']}<br>")
        
        self.message_input.clear()
        self.chat_display.verticalScrollBar().setValue(self.chat_display.verticalScrollBar().maximum())
    
    def _reset_conversation(self):
        self._conversation = []
        self.chat_display.append("<span style='color:#888'><i>--- Conversación reiniciada ---</i></span><br>")
    
    def closeEvent(self, event):
        if hasattr(self, 'camera_thread'):
            self.camera_thread.stop()
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # Establecer estilo general
    app.setStyle("Fusion")
    palette = QPalette()
    palette.setColor(QPalette.Window, QColor(240, 240, 240))
    app.setPalette(palette)
    
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())