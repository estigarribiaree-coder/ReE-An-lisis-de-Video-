import streamlit as st
import cv2
import numpy as np
import tempfile
from PIL import Image

# Configuración de la página web
st.set_page_config(
    page_title="ReE Análisis de Video",
    page_icon="⚽",
    layout="wide"
)

st.title("⚽ ReE Análisis de Video - Táctico")
st.markdown("Plataforma web de análisis deportivo, foco de jugadores y líneas tácticas.")

# Sección de carga de archivos en Streamlit
uploaded_file = st.file_uploader("Sube tu video táctico (MP4, AVI, MOV, MKV)", type=["mp4", "avi", "mov", "mkv"])

if uploaded_file is not None:
    # Guardar el video temporalmente para procesarlo con OpenCV
    tfile = tempfile.NamedTemporaryFile(delete=False, suffix='.mp4')
    tfile.write(uploaded_file.read())
    video_path = tfile.name

    # Inicializar motor de video
    cap = cv2.VideoCapture(video_path)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    fps = cap.get(cv2.CAP_PROP_FPS)
    if fps <= 0:
        fps = 30.0
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    # Panel de control lateral
    st.sidebar.header("🎛️ Controles de Video")
    frame_idx = st.sidebar.slider("Fotograma actual", 0, max(0, total_frames - 1), 0)

    # Leer el fotograma seleccionado
    cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
    ret, frame = cap.read()

    if ret:
        st.sidebar.header("🛠️ Herramientas Tácticas")
        herramienta = st.sidebar.selectbox(
            "Seleccionar Herramienta", 
            ["Ninguna", "Foco Jugador (Moderno)", "Línea Defensiva / Fuera de Juego"]
        )

        # Lógica para Foco Jugador
        if herramienta == "Foco Jugador (Moderno)":
            nombre_jugador = st.sidebar.text_input("Nombre del Jugador", "Jugador 1")
            fx = st.sidebar.slider("Posición X (Foco)", 0, width, width // 2)
            fy = st.sidebar.slider("Posición Y (Foco)", 0, height, height // 2)
            
            # Dibujar el foco moderno sobre el frame de OpenCV
            color_foco = (0, 255, 255) # Amarillo en BGR
            cv2.circle(frame, (fx, fy), 35, color_foco, 2)
            cv2.circle(frame, (fx, fy), 41, color_foco, 1)
            
            # Etiqueta de nombre editable
            if nombre_jugador:
                (tw, th), _ = cv2.getTextSize(nombre_jugador, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)
                tag_x = fx - (tw // 2)
                tag_y = fy - 50
                cv2.rectangle(frame, (tag_x - 8, tag_y - th - 8), (tag_x + tw + 8, tag_y + 8), (20, 20, 20), -1)
                cv2.rectangle(frame, (tag_x - 8, tag_y - th - 8), (tag_x + tw + 8, tag_y + 8), color_foco, 1)
                cv2.putText(frame, nombre_jugador, (tag_x, tag_y), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

        # Lógica para Línea Defensiva
        elif herramienta == "Línea Defensiva / Fuera de Juego":
            st.sidebar.info("Ajusta los puntos de referencia defensiva:")
            x1 = st.sidebar.slider("Jugador 1 - Posición X", 0, width, width // 4)
            y1 = st.sidebar.slider("Jugador 1 - Posición Y", 0, height, height // 2)
            x2 = st.sidebar.slider("Jugador 2 - Posición X", 0, width, width // 2)
            y2 = st.sidebar.slider("Posición Y (Línea)", 0, height, height // 2)
            
            color_linea = (0, 0, 255) # Rojo en BGR
            cv2.line(frame, (x1, y1), (x2, y2), color_linea, 3)
            cv2.circle(frame, (x1, y1), 7, color_linea, -1)
            cv2.circle(frame, (x2, y2), 7, color_linea, -1)
            cv2.putText(frame, "J1", (x1 + 10, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color_linea, 2)
            cv2.putText(frame, "J2", (x2 + 10, y2 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color_linea, 2)

        # Renderizar la imagen procesada en la interfaz web de Streamlit
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        st.image(frame_rgb, caption=f"Fotograma {frame_idx} de {total_frames}", use_column_width=True)
    
    cap.release()
else:
    st.info("👆 Por favor, sube un video en formato MP4 o AVI usando el botón superior para comenzar tu análisis.")
