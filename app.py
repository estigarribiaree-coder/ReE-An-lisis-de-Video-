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

# Función para fondo con imagen local
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
# PANTALLA 1: BIENVENIDA / SPLASH SCREEN
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
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        
        if width <= 0: width = 1280
        if height <= 0: height = 720

        # --- PANEL LATERAL: HERRAMIENTAS Y FIGURAS TÁCTICAS ---
        st.sidebar.header("🛠️ Herramientas y Figuras")
        
        tipo_herramienta = st.sidebar.selectbox(
            "Seleccionar Herramienta", 
            ["Ninguna", "Foco Jugador (Moderno)", "Línea", "Flecha Recta", "Flecha Curva", "Círculo", "Triángulo", "Cuadrado", "Rombo"]
        )

        color_nombre = st.sidebar.selectbox("Color", ["Amarillo", "Rojo", "Azul", "Blanco", "Verde"])
        color_map = {
            "Amarillo": (0, 255, 255),
            "Rojo": (0, 0, 255),
            "Azul": (255, 0, 0),
            "Blanco": (255, 255, 255),
            "Verde": (0, 255, 0)
        }
        col_bgr = color_map[color_nombre]
        intensidad = st.sidebar.slider("Intensidad / Opacidad del Foco", 0.1, 1.0, 0.4, 0.1)
        grosor = st.sidebar.slider("Grosor de Línea", 1, 8, 3)

        if tipo_herramienta != "Ninguna":
            st.sidebar.subheader("Posición de la Figura")
            x1 = st.sidebar.slider("Posición X (Punto / Inicio)", 0, width, width // 2)
            y1 = st.sidebar.slider("Posición Y (Punto / Inicio)", 0, height, height // 2)
            
            if tipo_herramienta in ["Línea", "Flecha Recta", "Flecha Curva"]:
                x2 = st.sidebar.slider("Posición X Final", 0, width, (width // 2) + 150)
                y2 = st.sidebar.slider("Posición Y Final", 0, height, (height // 2) + 150)
            else:
                x2, y2 = x1 + 100, y1 + 100

            texto_foco = ""
            if tipo_herramienta == "Foco Jugador (Moderno)":
                texto_foco = st.sidebar.text_input("Nombre del Jugador", "Jugador 1")

            if st.sidebar.button("➕ Agregar al Fotograma Actual"):
                nuevo_elem = {
                    "tipo": tipo_herramienta,
                    "x1": x1, "y1": y1,
                    "x2": x2, "y2": y2,
                    "color_rgb": col_bgr,
                    "intensidad": intensidad,
                    "grosor": grosor,
                    "texto": texto_foco,
                    "frame": st.session_state.current_frame
                }
                st.session_state.elementos_tacticos.append(nuevo_elem)
                st.sidebar.success("¡Elemento agregado con éxito!")

        st.sidebar.markdown("---")
        st.sidebar.header("📋 Elementos Guardados")
        if st.session_state.elementos_tacticos:
            for idx, el in enumerate(st.session_state.elementos_tacticos):
                col_el1, col_el2 = st.sidebar.columns([3, 1])
                with col_el1:
                    st.text(f"{idx+1}. {el['tipo']} (F: {el['frame']})")
                with col_el2:
                    if st.button("❌", key=f"del_{idx}"):
                        st.session_state.elementos_tacticos.pop(idx)
                        st.rerun()
        else:
            st.sidebar.info("No hay elementos en este proyecto.")

        # --- SECCIÓN PRINCIPAL: REPRODUCTOR NATIVO Y EDITOR DE FOTOGRAMAS ---
        tab_rep, tab_edit = st.tabs(["🎬 Reproductor General (Play/Pausa)", "✏️ Editor de Fotograma y Figuras"])

        with tab_rep:
            st.subheader("Reproductor de Video del Partido")
            st.write("Usa los controles nativos del reproductor para reproducir, pausar o adelantar el video fluidamente.")
            st.video(st.session_state.video_path)

        with tab_edit:
            st.subheader("Editor de Fotograma con Herramientas Geométricas")
            st.write("Selecciona el fotograma exacto donde deseas incrustar una figura, triángulo, círculo o foco personalizado.")
            
            st.session_state.current_frame = st.slider(
                "Seleccionar Fotograma de Trabajo",
                0,
                max(0, total_frames - 1),
                st.session_state.current_frame
            )

            # Extraer y procesar el fotograma seleccionado con OpenCV
            cap.set(cv2.CAP_PROP_POS_FRAMES, st.session_state.current_frame)
            ret, frame = cap.read()

            if ret and frame is not None:
                # Renderizar los elementos tácticos que pertenecen a este fotograma
                for el in st.session_state.elementos_tacticos:
                    if el["frame"] == st.session_state.current_frame:
                        t = el["tipo"]
                        c = el["color_rgb"]
                        inte = el["intensidad"]
                        g = el["grosor"]
                        
                        if t == "Foco Jugador (Moderno)":
                            cx, cy = int(el["x1"]), int(el["y1"])
                            overlay = frame.copy()
                            cv2.circle(overlay, (cx, cy), 50, c, -1)
                            cv2.addWeighted(overlay, inte, frame, 1.0 - inte, 0, frame)
                            cv2.circle(frame, (cx, cy), 50, c, g)
                            cv2.circle(frame, (cx, cy), 58, c, 1)
                            if el["texto"]:
                                (tw, th), _ = cv2.getTextSize(el["texto"], cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)
                                tx, ty = cx - (tw // 2), cy - 65
                                cv2.rectangle(frame, (tx - 6, ty - th - 6), (tx + tw + 6, ty + 6), (20, 20, 20), -1)
                                cv2.putText(frame, el["texto"], (tx, ty), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

                        elif t == "Línea":
                            cv2.line(frame, (int(el["x1"]), int(el["y1"])), (int(el["x2"]), int(el["y2"])), c, g)

                        elif t == "Flecha Recta":
                            cv2.arrowedLine(frame, (int(el["x1"]), int(el["y1"])), (int(el["x2"]), int(el["y2"])), c, g, tipLength=0.2)

                        elif t == "Flecha Curva":
                            pt1 = (int(el["x1"]), int(el["y1"]))
                            pt2 = (int(el["x2"]), int(el["y2"]))
                            mid = ((pt1[0] + pt2[0]) // 2 + 50, (pt1[1] + pt2[1]) // 2 - 50)
                            pts_curve = np.array([pt1, mid, pt2], np.int32)
                            cv2.polylines(frame, [pts_curve], False, c, g)
                            cv2.circle(frame, pt2, 6, c, -1)

                        elif t == "Círculo":
                            radio = int(np.hypot(el["x2"] - el["x1"], el["y2"] - el["y1"]))
                            cv2.circle(frame, (int(el["x1"]), int(el["y1"])), max(15, radio), c, g)

                        elif t in ["Triángulo", "Cuadrado", "Rombo"]:
                            x, y = int(el["x1"]), int(el["y1"])
                            sz = 70
                            if t == "Triángulo":
                                pts = np.array([[x, y - sz], [x - sz, y + sz], [x + sz, y + sz]], np.int32)
                            elif t == "Cuadrado":
                                pts = np.array([[x - sz, y - sz], [x + sz, y - sz], [x + sz, y + sz], [x - sz, y + sz]], np.int32)
                            elif t == "Rombo":
                                pts = np.array([[x, y - sz], [x + sz, y], [x, y + sz], [x - sz, y]], np.int32)
                            cv2.polylines(frame, [pts], True, c, g)

                # Mostrar la imagen con las figuras dibujadas
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                st.image(frame_rgb, caption=f"Fotograma {st.session_state.current_frame} de {total_frames}", use_container_width=True)

                elementos_marcador = [e for e in st.session_state.elementos_tacticos if e["frame"] == st.session_state.current_frame]
                if elementos_marcador:
                    st.info(f"📌 {len(elementos_marcador)} elemento(s) táctico(s) activo(s) en este fotograma.")
            else:
                st.error("No se pudo leer el fotograma.")

        cap.release()
    else:
        st.warning("No hay ningún video cargado. Vuelve a configuración para seleccionar un proyecto con video.")
