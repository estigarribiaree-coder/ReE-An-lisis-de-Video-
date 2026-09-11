import streamlit as st
import cv2
import numpy as np
import tempfile
from PIL import Image
import base64

# Configuración de la página web
st.set_page_config(
    page_title="ReE Análisis de Video",
    page_icon="⚽",
    layout="wide"
)

# Función para convertir la imagen local a Base64 y usarla como fondo CSS
def establecer_fondo(imagen_path):
    try:
        with open(imagen_path, "rb") as image_file:
            encoded_string = base64.b64encode(image_file.read()).decode()
        css = f"""
        <style>
        .stApp {{
            background-image: url("data:image/png;base64,{encoded_string}");
            background-size: cover;
            background-position: center;
            background-repeat: no-repeat;
        }}
        .tarjeta-bienvenida {{
            background-color: rgba(44, 62, 80, 0.85);
            padding: 30px;
            border-radius: 12px;
            text-align: center;
            color: white;
            box-shadow: 0px 4px 15px rgba(0,0,0,0.5);
        }}
        </style>
        """
        st.markdown(css, unsafe_allow_html=True)
    except FileNotFoundError:
        # Si no encuentra la imagen, usa un fondo oscuro por defecto
        pass

# Inicializar el estado de la navegación
if "pantalla" not in st.session_state:
    st.session_state.pantalla = "bienvenida"

if "nombre_proyecto" not in st.session_state:
    st.session_state.nombre_proyecto = "Nuevo Proyecto"

if "equipo_local" not in st.session_state:
    st.session_state.equipo_local = "Local"

if "equipo_visita" not in st.session_state:
    st.session_state.equipo_visita = "Visitante"

if "video_path" not in st.session_state:
    st.session_state.video_path = None


# ==========================================
# PANTALLA 1: BIENVENIDA / SPLASH SCREEN CON FONDO
# ==========================================
if st.session_state.pantalla == "bienvenida":
    # Asegúrate de guardar tu imagen en la carpeta como 'logo_fondo.png'
    establecer_fondo("logo_fondo.png")
    
    st.markdown("<br><br>", unsafe_allow_html=True)
    st.markdown("<h1 style='text-align: center; color: #ffffff; text-shadow: 2px 2px 4px #000000;'>⚽ ReE Análisis de Video</h1>", unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown(
            """
            <div class="tarjeta-bienvenida">
                <h2>Plataforma Táctica Profesional</h2>
                <hr style="border-color: #555;">
                <p><b>Desarrollado y Diseñado:</b> Raúl Eduardo Estigarribia</p>
                <p><b>Versión:</b> 1.0</p>
                <p><b>Año:</b> 2026</p>
            </div>
            """, 
            unsafe_allow_html=True
        )
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("🚀 Ingresar al Sistema", use_container_width=True, type="primary"):
            st.session_state.pantalla = "configuracion_proyecto"
            st.rerun()

# ==========================================
# PANTALLA 2: CONFIGURACIÓN Y CARGA DE PROYECTO
# ==========================================
elif st.session_state.pantalla == "configuracion_proyecto":
    st.title("📁 Gestión de Proyecto Táctico")
    st.write("Configura los detalles de tu análisis o carga un proyecto existente.")
    
    tab1, tab2 = st.tabs(["✨ Crear / Configurar Proyecto Nuevo", "📂 Proyectos Guardados"])
    
    with tab1:
        st.subheader("Detalles del Partido y Video")
        st.session_state.nombre_proyecto = st.text_input("Nombre del Proyecto", st.session_state.nombre_proyecto)
        
        col_eq1, col_eq2 = st.columns(2)
        with col_eq1:
            st.session_state.equipo_local = st.text_input("Equipo Local", st.session_state.equipo_local)
        with col_eq2:
            st.session_state.equipo_visita = st.text_input("Equipo Visitante", st.session_state.equipo_visita)
            
        uploaded_file = st.file_uploader("Sube el video táctico del partido (MP4, AVI, MOV)", type=["mp4", "avi", "mov", "mkv"])
        
        if uploaded_file is not None:
            tfile = tempfile.NamedTemporaryFile(delete=False, suffix='.mp4')
            tfile.write(uploaded_file.read())
            st.session_state.video_path = tfile.name
            st.success("¡Video cargado correctamente en el proyecto!")

        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("➡️ Ir a la Pantalla de Trabajo", type="primary", use_container_width=True):
            if st.session_state.video_path is not None:
                st.session_state.pantalla = "trabajo"
                st.rerun()
            else:
                st.warning("Por favor, sube un archivo de video antes de continuar.")

    with tab2:
        st.subheader("Proyectos Guardados Recientemente")
        st.info("Aquí se listarán tus proyectos guardados en el sistema.")
        proyecto_ejemplo = st.selectbox("Seleccionar proyecto guardado:", ["Ninguno", "Fecha 1 - Local vs Visitante (Demo)"])
        if proyecto_ejemplo != "Ninguno":
            if st.button("Cargar este Proyecto"):
                st.session_state.nombre_proyecto = proyecto_ejemplo
                st.success(f"Proyecto '{proyecto_ejemplo}' cargado con éxito.")
                
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("⬅️ Volver a Pantalla Principal"):
        st.session_state.pantalla = "bienvenida"
        st.rerun()

# ==========================================
# PANTALLA 3: ÁREA DE TRABAJO TÁCTICO
# ==========================================
elif st.session_state.pantalla == "trabajo":
    col_nav1, col_nav2 = st.columns([6, 1])
    with col_nav1:
        st.title(f"🛠️ Proyecto: {st.session_state.nombre_proyecto}")
        st.markdown(f"**Enfrentamiento:** {st.session_state.equipo_local} ⚔️ {st.session_state.equipo_visita}")
    with col_nav2:
        if st.button("🔄 Cambiar Proyecto"):
            st.session_state.pantalla = "configuracion_proyecto"
            st.rerun()

    st.markdown("---")

    if st.session_state.video_path:
        cap = cv2.VideoCapture(st.session_state.video_path)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        fps = cap.get(cv2.CAP_PROP_FPS)
        if fps <= 0:
            fps = 30.0
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

        st.sidebar.header("🎛️ Controles de Video")
        frame_idx = st.sidebar.slider("Fotograma actual", 0, max(0, total_frames - 1), 0)

        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
        ret, frame = cap.read()

        if ret and frame is not None:
            st.sidebar.header("🛠️ Herramientas Tácticas")
            herramienta = st.sidebar.selectbox(
                "Seleccionar Herramienta", 
                ["Ninguna", "Foco Jugador (Moderno)", "Línea Defensiva / Fuera de Juego"]
            )

            if herramienta == "Foco Jugador (Moderno)":
                nombre_jugador = st.sidebar.text_input("Nombre del Jugador", "Jugador 1")
                fx = st.sidebar.slider("Posición X (Foco)", 0, width if width > 0 else 1000, (width // 2) if width > 0 else 500)
                fy = st.sidebar.slider("Posición Y (Foco)", 0, height if height > 0 else 1000, (height // 2) if height > 0 else 500)
                
                color_foco = (0, 255, 255)
                cv2.circle(frame, (fx, fy), 35, color_foco, 2)
                cv2.circle(frame, (fx, fy), 41, color_foco, 1)
                
                if nombre_jugador:
                    (tw, th), _ = cv2.getTextSize(nombre_jugador, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)
                    tag_x = fx - (tw // 2)
                    tag_y = fy - 50
                    cv2.rectangle(frame, (tag_x - 8, tag_y - th - 8), (tag_x + tw + 8, tag_y + 8), (20, 20, 20), -1)
                    cv2.rectangle(frame, (tag_x - 8, tag_y - th - 8), (tag_x + tw + 8, tag_y + 8), color_foco, 1)
                    cv2.putText(frame, nombre_jugador, (tag_x, tag_y), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

            elif herramienta == "Línea Defensiva / Fuera de Juego":
                st.sidebar.info("Ajusta los puntos de referencia defensiva:")
                x1 = st.sidebar.slider("Jugador 1 - Posición X", 0, width if width > 0 else 1000, (width // 4) if width > 0 else 250)
                y1 = st.sidebar.slider("Jugador 1 - Posición Y", 0, height if height > 0 else 1000, (height // 2) if height > 0 else 500)
                x2 = st.sidebar.slider("Jugador 2 - Posición X", 0, width if width > 0 else 1000, (width // 2) if width > 0 else 500)
                y2 = st.sidebar.slider("Posición Y (Línea)", 0, height if height > 0 else 1000, (height // 2) if height > 0 else 500)
                
                color_linea = (0, 0, 255)
                cv2.line(frame, (x1, y1), (x2, y2), color_linea, 3)
                cv2.circle(frame, (x1, y1), 7, color_linea, -1)
                cv2.circle(frame, (x2, y2), 7, color_linea, -1)
                cv2.putText(frame, "J1", (x1 + 10, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color_linea, 2)
                cv2.putText(frame, "J2", (x2 + 10, y2 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color_linea, 2)

            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            st.image(frame_rgb, caption=f"Fotograma {frame_idx} de {total_frames}", use_container_width=True)
        else:
            st.error("No se pudo leer el fotograma del video.")
        
        cap.release()
    else:
        st.warning("No hay ningún video cargado. Vuelve a configuración para seleccionar un proyecto con video.")
