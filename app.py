import streamlit as st

# Configuración inicial para móviles (ancho adaptable)
st.set_page_config(
    page_title="Analizador Táctico Móvil",
    layout="centered"  # Ideal para pantallas de celular
)

# Estilos CSS personalizados para adaptar la interfaz en Android
st.markdown("""
    <style>
    .stButton button {
        width: 100%;
        border-radius: 8px;
        font-weight: bold;
    }
    /* Ocultar elementos sobrantes de Streamlit en mobile */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    </style>
""", unsafe_allow_html=True)

st.title("⚽ Tactical Video App")
st.markdown("---")

# 1. Cargar video
video_file = st.file_uploader("Cargar video del partido (MP4)", type=["mp4", "mov", "mkv"])

if video_file is not None:
    # Usamos un contenedor centrado para simular la pantalla de la app móvil
    st.subheader("📺 Reproductor Táctico")
    
    # Contenedor del video con controles limpios inferiores
    # Nota: st.video por defecto muestra los controles abajo si no se interactúa, 
    # pero para evitar el botón gigante central, estructuramos una botonera táctica directa.
    st.video(video_file)
    
    st.markdown("---")
    st.subheader("🎛️ Controles de Precisión y Dibujo")
    
    # Fila de controles adaptada para dedos (táctil en Android)
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("⏮ -Frame"):
            st.toast("Fotograma atrás")
    with col2:
        if st.button("⏯ Play/Pausa"):
            st.toast("Alternando reproducción")
    with col3:
        if st.button("⏭ +Frame"):
            st.toast("Fotograma adelante")

    # Sección de Dibujo / Telestrator (Ideal para marcar jugadores en mobile)
    st.markdown("---")
    st.subheader("✏️ Herramientas Tácticas (Telestrator)")
    
    herramienta = st.selectbox(
        "Seleccionar elemento a incorporar:",
        ["Sin selección", "🔴 Círculo / Jugador", "➡️ Flecha de Movimiento", "📏 Línea de Pase / Offside"]
    )
    
    if herramienta != "Sin selección":
        st.info(f"Modo activo: **{herramienta}**. Toca la pantalla para ubicarlo sobre el video.")

    st.markdown("---")
    st.subheader("📋 Panel de Etiquetado Rápido")
    
    # Botones grandes ideales para celulares
    jugador_tag = st.selectbox("Jugador", ["#10 - Mac Allister", "#5 - Paredes", "#9 - Julián Álvarez"])
    
    b_col1, b_col2 = st.columns(2)
    with b_col1:
        if st.button("⚽ Gol / Tiro", use_container_width=True):
            st.success("¡Registrado!")
    with b_col2:
        if st.button("⚠️ Pérdida / Falta", use_container_width=True):
            st.warning("¡Registrado!")

else:
    st.info("👆 Sube un video desde tu dispositivo para empezar el análisis.")
