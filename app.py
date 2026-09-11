import streamlit as st
import cv2
import numpy as np
import tempfile
import os
st.set_page_config(
    page_title="ReE Análisis de Video - Web",
    page_icon="⚽",
    layout="centered",
    initial_sidebar_state="expanded"
)

st.markdown("""
    <style>
    .main { background-color: #121212; color: #ffffff; }
    .stButton>button { width: 100%; border-radius: 5px; font-weight: bold; }
    h1, h2, h3 { color: #00a8ff; }
    </style>
""", unsafe_allow_html=True)

if "plantel" not in st.session_state:
    st.session_state.plantel = [
        "1. Arquero", "2. Defensor", "3. Defensor", "4. Lateral", 
        "5. Mediocampista", "6. Mediocampista", "7. Extremo", 
        "8. Volante", "9. Delantero", "10. Enganche", "11. Extremo"
    ]

if "eventos" not in st.session_state:
    st.session_state.eventos = []

if "jugador_seleccionado" not in st.session_state:
    st.session_state.jugador_seleccionado = st.session_state.plantel[0]

with st.sidebar:
    st.image("https://img.icons8.com/color/96/000000/soccer-ball--v1.png", width=60)
    st.title("ReE Análisis")
    st.markdown("**Diseño y Desarrollo:** Raúl Eduardo Estigarribia")
    st.markdown("---")
    
    st.subheader("⚙️ Configuración del Partido")
    proyecto_nombre = st.text_input("Nombre del Partido", "Partido Oficial")
    equipo_local = st.text_input("Equipo Local", "Local")
    equipo_visitante = st.text_input("Equipo Visitante", "Visitante")
    
    st.markdown("---")
    st.subheader("👥 Gestión de Plantel")
    nuevo_jugador = st.text_input("Añadir Jugador / Modificar")
    if st.button("Actualizar Plantel (Añadir último)"):
        if nuevo_jugador:
            st.session_state.plantel.append(nuevo_jugador)
            st.success(f"¡{nuevo_jugador} añadido!")

    st.markdown("---")
    st.markdown("### 📋 Jugador Activo")
    st.session_state.jugador_seleccionado = st.selectbox(
        "Seleccione jugador para eventos:", 
        st.session_state.plantel
    )

st.title(f"⚽ {proyecto_nombre}")
st.subheader(f"📊 {equipo_local} vs {equipo_visitante}")

video_file = st.file_uploader("📂 Sube el video del partido (MP4, MOV, AVI):", type=["mp4", "mov", "avi"])

if video_file is not None:
    tfile = tempfile.NamedTemporaryFile(delete=False, suffix='.mp4')
    tfile.write(video_file.read())
    video_path = tfile.name

    cap = cv2.VideoCapture(video_path)
    fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    duracion_segundos = total_frames / fps if fps > 0 else 0

    st.success(f"¡Video cargado con éxito! Duración: {int(duracion_segundos // 60):02d}:{int(duracion_segundos % 60):02d}")

    frame_slider = st.slider(
        "Navegar por el fotograma del video:", 
        0, max(0, total_frames - 1), 0
    )

    cap.set(cv2.CAP_PROP_POS_FRAMES, frame_slider)
    ret, frame = cap.read()

    if ret and frame is not None:
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        col1, col2 = st.columns([2, 1])

        with col1:
            st.image(frame_rgb, channels="RGB", use_container_width=True, caption=f"Fotograma: {frame_slider} (Tiempo: {int((frame_slider/fps)//60):02d}:{int((frame_slider/fps)%60):02d})")

        with col2:
            st.markdown("### 🎛️ Panel Táctico")
            
            if st.button("🟢 Ataque Directo / Transición", use_container_width=True):
                tiempo_actual = frame_slider / fps
                st.session_state.eventos.append({
                    "tiempo": f"{int(tiempo_actual//60):02d}:{int(tiempo_actual%60):02d}",
                    "sub": "Ataque Directo",
                    "jugador": st.session_state.jugador_seleccionado,
                    "color": "Verde"
                })
                st.toast("¡Evento registrado con éxito!")

            if st.button("🔴 Pressing Bloque Alto", use_container_width=True):
                tiempo_actual = frame_slider / fps
                st.session_state.eventos.append({
                    "tiempo": f"{int(tiempo_actual//60):02d}:{int(tiempo_actual%60):02d}",
                    "sub": "Pressing Alto",
                    "jugador": st.session_state.jugador_seleccionado,
                    "color": "Rojo"
                })
                st.toast("¡Evento registrado con éxito!")

            if st.button("🟡 Balón Parado / Córner", use_container_width=True):
                tiempo_actual = frame_slider / fps
                st.session_state.eventos.append({
                    "tiempo": f"{int(tiempo_actual//60):02d}:{int(tiempo_actual%60):02d}",
                    "sub": "Balón Parado",
                    "jugador": st.session_state.jugador_seleccionado,
                    "color": "Amarillo"
                })
                st.toast("¡Evento registrado con éxito!")

    cap.release()

    st.markdown("---")
    st.subheader("📋 Playlist de Eventos Tácticos Registrados")
    
    if len(st.session_state.eventos) > 0:
        for i, ev in enumerate(st.session_state.eventos):
            st.markdown(f"**{i+1}. [{ev['tiempo']}]** — *{ev['sub']}* ({ev['jugador']})")
        
        if st.button("🗑️ Borrar Todos los Eventos"):
            st.session_state.eventos = []
            st.rerun()
    else:
        info_vacia = st.info("Aún no hay eventos tácticos registrados. Usa los botones del panel táctico mientras reproduces el video.")

else:
    st.info("👆 Por favor, sube un archivo de video de tu partido para comenzar el análisis.")
