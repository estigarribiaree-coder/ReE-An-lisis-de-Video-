import streamlit as st
import cv2
import numpy as np
import tempfile
import os

# Configuración de la página
st.set_page_config(
    page_title="ReE Análisis de Video",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilos visuales personalizados
st.markdown("""
    <style>
    .main { background-color: #121212; color: white; }
    h1, h2, h3 { color: #00a8ff; }
    .stButton>button { width: 100%; border-radius: 5px; background-color: #00a8ff; color: white; }
    </style>
""", unsafe_allow_html=True)

# Título y Créditos
st.title("⚽ ReE Análisis de Video")
st.markdown("##### Versión Web - Diseño y Desarrollo: Raúl Eduardo Estigarribia (Cel: 3777681259)")
st.markdown("---")

# Barra lateral para configuración del proyecto
st.sidebar.header("⚙️ Configuración del Proyecto")
proyecto_nombre = st.sidebar.text_input("Nombre del Partido / Proyecto", "Partido Oficial")
equipo_local = st.sidebar.text_input("Equipo Local", "Local")
equipo_visitante = st.sidebar.text_input("Equipo Visitante", "Visitante")

st.sidebar.markdown("---")
st.sidebar.subheader("👥 Plantel / Jugadores")
plantel_texto = st.sidebar.text_area(
    "Lista de jugadores (uno por línea)",
    "1. Arquero\n2. Defensor\n3. Defensor\n4. Lateral\n5. Mediocampista\n6. Mediocampista\n7. Extremo\n8. Volante\n9. Delantero\n10. Enganche\n11. Extremo"
)
plantel = [j.strip() for j in plantel_texto.split("\n") if j.strip()]

# Área principal: Carga de video
st.subheader("📹 Cargar Archivo de Video")
archivo_video = st.file_uploader("Seleccioná un archivo de video", type=["mp4", "mov", "avi", "mkv"])

if archivo_video is not None:
    # Guardar el video subido en un archivo temporal para que OpenCV pueda leerlo
    tfile = tempfile.NamedTemporaryFile(delete=False)
    tfile.write(archivo_video.read())
    
    cap = cv2.VideoCapture(tfile.name)
    
    # Obtener propiedades del video
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    fps = cap.get(cv2.CAP_PROP_FPS)
    duracion = total_frames / fps if fps > 0 else 0
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Proyecto", proyecto_nombre)
    col2.metric("Enfrentamiento", f"{equipo_local} vs {equipo_visitante}")
    col3.metric("Duración del Video", f"{duracion:.2f} segundos")
    
    st.markdown("---")
    st.info("¡Video cargado correctamente! El entorno está listo para procesar fotogramas y realizar el análisis táctico.")
    
    # Reproductor básico o muestra del video
    st.video(archivo_video)
else:
    st.warning("⚠️ Por favor, sube un video para comenzar con el análisis.")
