import streamlit as st
import cv2
import numpy as np
import tempfile
import base64

# Configuración de la página web
st.set_page_config(
    page_title="ReE Análisis de Video",
    page_icon="⚽",
    layout="wide"
)

# Función para fondo con imagen local (si existe)
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
            background-color: rgba(44, 62, 80, 0.88);
            padding: 30px;
            border-radius: 12px;
            text-align: center;
            color: white;
            box-shadow: 0px 4px 15px rgba(0,0,0,0.5);
        }}
        .reproductor-clasico {{
            background-color: #1e293b;
            padding: 10px;
            border-radius: 8px;
            border: 1px solid #475569;
        }}
        </style>
        """
        st.markdown(css, unsafe_allow_html=True)
    except FileNotFoundError:
        pass

# ==========================================
# INICIALIZACIÓN DE ESTADOS
# ==========================================
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

if "elementos_tacticos" not in st.session_state:
    st.session_state.elementos_tacticos = []

if "current_frame" not in st.session_state:
    st.session_state.current_frame = 0


# ==========================================
# PANTALLA 1: BIENVENIDA
# ==========================================
if st.session_state.pantalla == "bienvenida":
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
                <p><b>Diseño y Desarrollo:</b> Raúl Eduardo Estigarribia</p>
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
# PANTALLA 2: CONFIGURACIÓN Y CARGA
# ==========================================
elif st.session_state.pantalla == "configuracion_proyecto":
    st.title("📁 Configuración del Proyecto")
    st.write("Carga tu video y define los parámetros iniciales del análisis.")
    
    st.session_state.nombre_proyecto = st.text_input("Nombre del Proyecto", st.session_state.nombre_proyecto)
    
    col_eq1, col_eq2 = st.columns(2)
    with col_eq1:
        st.session_state.equipo_local = st.text_input("Equipo Local", st.session_state.equipo_local)
    with col_eq2:
        st.session_state.equipo_visita = st.text_input("Equipo Visitante", st.session_state.equipo_visita)
        
    uploaded_file = st.file_uploader("Cargar video del partido (MP4, AVI, MOV)", type=["mp4", "avi", "mov", "mkv"])
    
    if uploaded_file is not None:
        tfile = tempfile.NamedTemporaryFile(delete=False, suffix='.mp4')
        tfile.write(uploaded_file.read())
        st.session_state.video_path = tfile.name
        st.success("¡Video cargado correctamente!")

    st.markdown("<br>", unsafe_allow_html=True)
    
    col_btn1, col_btn2 = st.columns(2)
    with col_btn1:
        if st.button("➡️ Ir a la Pantalla de Trabajo", type="primary", use_container_width=True):
            if st.session_state.video_path is not None:
                st.session_state.pantalla = "trabajo"
                st.rerun()
            else:
                st.warning("Por favor, carga un video antes de continuar.")
    with col_btn2:
        if st.button("📂 Cargar Proyecto Guardado", use_container_width=True):
            st.info("Función de proyectos guardados lista para sincronizar.")

    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("⬅️ Volver a Bienvenida"):
        st.session_state.pantalla = "bienvenida"
        st.rerun()


# ==========================================
# PANTALLA 3: ÁREA DE TRABAJO TÁCTICO
# ==========================================
elif st.session_state.pantalla == "trabajo":
    col_nav1, col_nav2 = st.columns([6, 1])
    with col_nav1:
        st.title(f"🛠️ Proyecto: {st.session_state.nombre_proyecto}")
        st.markdown(f"**Partido:** {st.session_state.equipo_local} vs {st.session_state.equipo_visita}")
    with col_nav2:
        if st.button("🔄 Configuración"):
            st.session_state.pantalla = "configuracion_proyecto"
            st.rerun()

    st.markdown("---")

    if st.session_state.video_path:
        cap = cv2.VideoCapture(st.session_state.video_path)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        fps = cap.get(cv2.CAP_PROP_FPS)
        if fps <= 0: fps = 30.0
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        
        if width <= 0: width = 1280
        if height <= 0: height = 720

        # --- SECTOR DE HERRAMIENTAS (PANEL LATERAL) ---
        st.sidebar.header("🛠️ Sector de Herramientas")
        tipo_herramienta = st.sidebar.selectbox(
            "Seleccionar Herramienta", 
            ["Ninguna", "Foco Jugador", "Línea", "Flecha", "Círculo", "Triángulo", "Cuadrado", "Rombo"]
        )

        color_nombre = st.sidebar.selectbox("Color", ["Amarillo", "Rojo", "Azul", "Blanco", "Verde"])
        color_map = {
            "Amarillo": (0, 255, 255), "Rojo": (0, 0, 255), "Azul": (255, 0, 0),
            "Blanco": (255, 255, 255), "Verde": (0, 255, 0)
        }
        col_bgr = color_map[color_nombre]
        grosor = st.sidebar.slider("Grosor", 1, 8, 3)

        if tipo_herramienta != "Ninguna":
            st.sidebar.subheader("Coordenadas")
            x1 = st.sidebar.slider("Posición X", 0, width, width // 2)
            y1 = st.sidebar.slider("Posición Y", 0, height, height // 2)
            
            if st.sidebar.button("➕ Agregar al Fotograma"):
                nuevo_elem = {
                    "tipo": tipo_herramienta, "x1": x1, "y1": y1,
                    "color_rgb": col_bgr, "grosor": grosor,
                    "frame": st.session_state.current_frame
                }
                st.session_state.elementos_tacticos.append(nuevo_elem)
                st.sidebar.success("¡Agregado!")

        st.sidebar.markdown("---")
        if st.sidebar.button("🗑️ Limpiar Elementos"):
            st.session_state.elementos_tacticos = []
            st.rerun()

        # --- SECTOR DE FOTOGRAMA Y REPRODUCTOR CLÁSICO ---
        st.subheader("🎬 Reproductor de Video Clásico y Análisis")

        # Visualizador de fotograma con elementos tácticos
        cap.set(cv2.CAP_PROP_POS_FRAMES, st.session_state.current_frame)
        ret, frame = cap.read()

        if ret and frame is not None:
            for el in st.session_state.elementos_tacticos:
                if el["frame"] == st.session_state.current_frame:
                    t = el["tipo"]
                    c = el["color_rgb"]
                    g = el["grosor"]
                    x, y = int(el["x1"]), int(el["y1"])
                    
                    if t == "Foco Jugador":
                        cv2.circle(frame, (x, y), 45, c, g)
                    elif t == "Círculo":
                        cv2.circle(frame, (x, y), 60, c, g)
                    elif t == "Triángulo":
                        pts = np.array([[x, y - 50], [x - 50, y + 50], [x + 50, y + 50]], np.int32)
                        cv2.polylines(frame, [pts], True, c, g)
                    elif t == "Cuadrado":
                        pts = np.array([[x - 50, y - 50], [x + 50, y - 50], [x + 50, y + 50], [x - 50, y + 50]], np.int32)
                        cv2.polylines(frame, [pts], True, c, g)
                    elif t == "Rombo":
                        pts = np.array([[x, y - 50], [x + 50, y], [x, y + 50], [x - 50, y]], np.int32)
                        cv2.polylines(frame, [pts], True, c, g)

            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            st.image(frame_rgb, use_container_width=True)
        else:
            st.error("Error al leer el fotograma.")

        # --- BARRA DE CONTROL CLÁSICA (Estilo SMPlayer / Barra inferior) ---
        st.markdown("<div class='reproductor-clasico'>", unsafe_allow_html=True)
        
        b1, b2, b3, b4, b5, b6 = st.columns([1, 1, 1, 1, 1, 3])
        with b1:
            if st.button("⏮"):
                st.session_state.current_frame = max(0, st.session_state.current_frame - 10)
                st.rerun()
        with b2:
            if st.button("◀"):
                st.session_state.current_frame = max(0, st.session_state.current_frame - 1)
                st.rerun()
        with b3:
            if st.button("▶"):
                st.session_state.current_frame = min(total_frames - 1, st.session_state.current_frame + 1)
                st.rerun()
        with b4:
            if st.button("⏹"):
                st.session_state.current_frame = 0
                st.rerun()
        with b5:
            if st.button("⏭"):
                st.session_state.current_frame = min(total_frames - 1, st.session_state.current_frame + 10)
                st.rerun()
        with b6:
            current_time_sec = int(st.session_state.current_frame / fps)
            total_time_sec = int(total_frames / fps)
            t_curr = f"{current_time_sec // 60:02d}:{current_time_sec % 60:02d}"
            t_tot = f"{total_time_sec // 60:02d}:{total_time_sec % 60:02d}"
            st.markdown(f"<p style='color: white; text-align: right; margin-top: 8px;'><b>{t_curr} / {t_tot} (F: {st.session_state.current_frame})</b></p>", unsafe_allow_html=True)

        # Línea de tiempo clásica (Slider horizontal inferior)
        nuevo_frame = st.slider(
            "Línea de Tiempo",
            0,
            max(0, total_frames - 1),
            st.session_state.current_frame,
            label_visibility="collapsed"
        )
        if nuevo_frame != st.session_state.current_frame:
            st.session_state.current_frame = nuevo_frame
            st.rerun()

        st.markdown("</div>", unsafe_allow_html=True)
        
        cap.release()
    else:
        st.warning("No hay ningún video cargado. Vuelve a configuración.")
