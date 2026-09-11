import streamlit as st

st.set_page_config(
    page_title="Analizador de Video - Fútbol",
    layout="wide"
)

st.title("⚽ Analizador de Video Táctico (Offline)")
st.write("Herramienta de etiquetado y análisis para cuerpos técnicos.")

# Layout principal en dos columnas (Video y Dashboard)
col_video, col_dashboard = st.columns([2, 1])

with col_video:
    st.subheader("Reproductor de Video")
    
    # Subir archivo de video local
    video_file = st.file_uploader("Cargar video del partido (MP4, MOV)", type=["mp4", "mov", "mkv"])
    
    if video_file is not None:
        st.video(video_file)
        
        # Simulación de controles de precisión
        st.markdown("### Controles de Precisión")
        c1, c2, c3, c4, c5 = st.columns(5)
        with c1:
            if st.button("⏮ -1 Frame"):
                st.toast("Retrocediendo un fotograma...")
        with c2:
            if st.button("▶ Play / ⏸ Pause"):
                pass
        with c3:
            if st.button("⏭ +1 Frame"):
                st.toast("Avanzando un fotograma...")
        with c4:
            st.selectbox("Velocidad", ["0.25x", "0.5x", "1.0x"], index=2, label_visibility="collapsed")
        with c5:
            st.toggle("Modo Dibujo ✏️")
    else:
        st.info("👈 Sube un archivo de video para comenzar el análisis.")

with col_dashboard:
    st.subheader("Panel de Etiquetado")
    
    # Selector de jugador rápido
    jugador = st.selectbox("Jugador Asociado", ["Sin seleccionar", "#10 - Mac Allister", "#5 - Paredes", "#9 - Julián Álvarez"])
    
    st.markdown("---")
    st.markdown("**Acciones Ofensivas**")
    col_b1, col_b2 = st.columns(2)
    with col_b1:
        if st.button("⚽ Gol", use_container_width=True):
            st.success("¡Gol registrado!")
    with col_b2:
        if st.button("🎯 Disparo", use_container_width=True):
            st.info("Disparo registrado")

    if st.button("🔄 Recuperación", use_container_width=True):
        st.info("Recuperación registrada")
        
    if st.button("⚠️ Pérdida", use_container_width=True):
        st.warning("Pérdida registrada")

    st.markdown("---")
    st.subheader("Timeline / Eventos Guardados")
    st.write("*(Aquí aparecerán los recortes en orden cronológico)*")
    st.dataframe(
        data={"Minuto": ["12:45", "22:10"], "Evento": ["Gol", "Recuperación"], "Jugador": ["Julián Álvarez", "Paredes"]},
        use_container_width=True
    )
