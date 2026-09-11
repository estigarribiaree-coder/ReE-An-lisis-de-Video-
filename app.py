# -*- coding: utf-8 -*-
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import cv2
import os
import json
from PIL import Image, ImageTk
import numpy as np
import threading
import time

try:
    from reportlab.lib.pagesizes import letter
    from reportlab.pdfgen import canvas as pdf_canvas
    REPORTLAB_DISPONIBLE = True
except ImportError:
    REPORTLAB_DISPONIBLE = False

class VideoAnalisisReEApp:
    def __init__(self, root):
        self.root = root
        self.root.title("ReE Análisis de Video - Versión 1.0 (Diseño y Desarrollo: Raúl Eduardo Estigarribia Cel: 3777681259)")
        
        try:
            self.root.state('zoomed')
        except:
            self.root.geometry("1366x768")
            
        self.root.configure(bg="#121212")
        
        # Estado del Proyecto
        self.proyecto_nombre = "Partido Oficial"
        self.equipo_local = "Local"
        self.equipo_visitante = "Visitante"
        self.plantel = ["1. Arquero", "2. Defensor", "3. Defensor", "4. Lateral", "5. Mediocampista", 
                        "6. Mediocampista", "7. Extremo", "8. Volante", "9. Delantero", "10. Enganche", "11. Extremo"]
        
        self.cap = None
        self.video_path = ""
        self.fps = 25.0
        self.total_frames = 0
        self.current_frame = 0
        self.playing = False
        self.eventos = []
        self.frame_actual_img = None
        
        # Buffer seguro y control de tiempo real
        self.frame_siguiente_raw = None
        self._lock = threading.Lock()
        
        # Herramientas de dibujo y Grabación
        self.herramienta_activa = "ninguno"
        self.elementos_dibujo = []
        self.grabando_video = False
        self.video_writer = None
        
        # Puntos temporales para creación por clics sucesivos (Triangulaciones / Rombos)
        self.puntos_temp_creacion = []

        # Control interactivo de creación y arrastre/edición en pantalla
        self.figura_temp_inicio = None
        
        # Control de Selección y Arrastre de Figuras Existentes
        self.elemento_seleccionado = None  
        self.elemento_en_arrastre = None
        self.tipo_arrastre_punto = None 
        self.offset_arrastre = (0, 0)

        # Lista para almacenar los cortes de congelación de imagen (marcos estáticos insertados)
        self.cortes_congelacion = []

        # Mostrar Splash Screen inicial con la imagen 1001216501_2.png antes del menú principal
        self.mostrar_splash_screen()

    def limpiar_ventana(self):
        for widget in self.root.winfo_children():
            widget.destroy()

    # ==========================================
    # 0. SPLASH SCREEN (PANTALLA DE BIENVENIDA)
    # ==========================================
    def mostrar_splash_screen(self):
        self.limpiar_ventana()
        
        splash_frame = tk.Frame(self.root, bg="#121212")
        splash_frame.pack(fill=tk.BOTH, expand=True)

        try:
            img_splash = Image.open("1001216501_2.png").resize((950, 480), Image.Resampling.LANCZOS)
            self.splash_img = ImageTk.PhotoImage(img_splash)
            lbl_splash = tk.Label(splash_frame, image=self.splash_img, bg="#121212")
            lbl_splash.pack(expand=True, pady=10)
        except Exception as e:
            lbl_err = tk.Label(splash_frame, text="ReE Análisis de Video\nVersión 1.0\nDiseño y Desarrollo: Raúl Eduardo Estigarribia", bg="#121212", fg="white", font=("Arial", 20, "bold"), justify="center")
            lbl_err.pack(expand=True)

        btn_entrar = tk.Button(splash_frame, text="Iniciar Aplicación", command=self.mostrar_menu_principal,
                               bg="#007acc", fg="white", font=("Arial", 11, "bold"), padx=20, pady=10, relief=tk.FLAT)
        btn_entrar.pack(pady=20)

    # ==========================================
    # 1. MENÚ PRINCIPAL
    # ==========================================
    def mostrar_menu_principal(self):
        self.limpiar_ventana()
        
        menu_frame = tk.Frame(self.root, bg="#0d1117")
        menu_frame.pack(fill=tk.BOTH, expand=True)
        
        try:
            bg_img_path = "1001216889_2.jpg"
            if os.path.exists(bg_img_path):
                pil_bg = Image.open(bg_img_path).resize((1366, 768), Image.Resampling.LANCZOS)
                self.bg_photo = ImageTk.PhotoImage(pil_bg)
                lbl_bg = tk.Label(menu_frame, image=self.bg_photo)
                lbl_bg.place(x=0, y=0, relwidth=1, relheight=1)
        except Exception:
            pass

        top_bar = tk.Frame(menu_frame, bg="#0d1117" if not hasattr(self, 'bg_photo') else None, height=40)
        top_bar.pack(side=tk.TOP, fill=tk.X, padx=20, pady=10)
        
        btn_pref = tk.Button(top_bar, text="Preferencias", command=lambda: messagebox.showinfo("Preferencias", "Configuración general de ReE Análisis de Video."),
                             bg="#1f2428", fg="#c9d1d9", font=("Arial", 9), relief=tk.FLAT, padx=10, pady=5)
        btn_pref.pack(side=tk.RIGHT)

        centro_frame = tk.Frame(menu_frame, bg="#0d1117" if not hasattr(self, 'bg_photo') else None)
        centro_frame.pack(expand=True)

        lbl_titulo = tk.Label(centro_frame, text="ReE Análisis de Video", bg="#0d1117" if not hasattr(self, 'bg_photo') else None, fg="#ffffff", font=("Arial", 22, "bold"))
        lbl_titulo.pack(pady=(0, 2))
        
        lbl_sub = tk.Label(centro_frame, text="Diseño y Desarrollo: Raúl Eduardo Estigarribia\nVersión 1.0", bg="#0d1117" if not hasattr(self, 'bg_photo') else None, fg="#8b949e", font=("Arial", 10), justify="center")
        lbl_sub.pack(pady=(0, 25))

        grid_frame = tk.Frame(centro_frame, bg="#0d1117" if not hasattr(self, 'bg_photo') else None)
        grid_frame.pack(pady=10)

        botones_data = [
            ("Nuevo Proyecto", self.crear_nuevo_proyecto),
            ("Abrir Proyecto", self.abrir_proyecto),
            ("Importar ReE", self.importar_datos),
            ("Ver", self.ver_proyectos),
            ("Equipos y Plantles", self.gestionar_equipos),
            ("Paneles Dashboard", self.gestionar_dashboards)
        ]

        for i, (texto, comando) in enumerate(botones_data):
            fila = i // 3
            columna = i % 3
            btn = tk.Button(grid_frame, text=texto, command=comando,
                            bg="#161b22", fg="#c9d1d9", font=("Arial", 10, "bold"),
                            width=20, height=3, relief=tk.FLAT, bd=0,
                            activebackground="#1f6feb", activeforeground="white")
            btn.grid(row=fila, column=columna, padx=12, pady=12)

    def crear_nuevo_proyecto(self):
        win = tk.Toplevel(self.root)
        win.title("Nuevo Proyecto - ReE Análisis de Video")
        win.geometry("400x320")
        win.configure(bg="#1e1e1e")
        
        tk.Label(win, text="Nombre del Partido / Proyecto:", bg="#1e1e1e", fg="white", font=("Arial", 9)).pack(pady=5)
        e_match = tk.Entry(win, width=32, font=("Arial", 9))
        e_match.insert(0, "Partido Oficial")
        e_match.pack(pady=2)
        
        tk.Label(win, text="Equipo Local:", bg="#1e1e1e", fg="white", font=("Arial", 9)).pack(pady=5)
        e_local = tk.Entry(win, width=32, font=("Arial", 9))
        e_local.insert(0, "Local")
        e_local.pack(pady=2)

        tk.Label(win, text="Equipo Visitante:", bg="#1e1e1e", fg="white", font=("Arial", 9)).pack(pady=5)
        e_vis = tk.Entry(win, width=32, font=("Arial", 9))
        e_vis.insert(0, "Visitante")
        e_vis.pack(pady=2)
        
        def seleccionar_y_continuar():
            path = filedialog.askopenfilename(filetypes=[("Archivos de Video", "*.mp4 *.avi *.mov *.mkv")])
            if path:
                self.proyecto_nombre = e_match.get()
                self.equipo_local = e_local.get()
                self.equipo_visitante = e_vis.get()
                self.video_path = path
                win.destroy()
                self.cargar_motor_video(path)
                self.iniciar_interfaz_trabajo()

        tk.Button(win, text="Seleccionar Video y Comenzar", command=seleccionar_y_continuar,
                  bg="#007acc", fg="white", font=("Arial", 9, "bold"), pady=6).pack(pady=15)

    def abrir_proyecto(self):
        path = filedialog.askopenfilename(filetypes=[("Proyecto ReE (JSON)", "*.json"), ("Todos los archivos", "*.*")])
        if path:
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                self.proyecto_nombre = data.get("proyecto_nombre", "Partido Oficial")
                self.equipo_local = data.get("equipo_local", "Local")
                self.equipo_visitante = data.get("equipo_visitante", "Visitante")
                self.plantel = data.get("plantel", self.plantel)
                self.eventos = data.get("eventos", [])
                self.elementos_dibujo = data.get("elementos_dibujo", [])
                self.cortes_congelacion = data.get("cortes_congelacion", [])
                v_path = data.get("video_path", "")
                
                if os.path.exists(v_path):
                    self.video_path = v_path
                else:
                    self.video_path = filedialog.askopenfilename(title="Localizar archivo de video original", filetypes=[("Archivos de Video", "*.mp4 *.avi *.mov *.mkv")])
                
                if self.video_path:
                    self.cargar_motor_video(self.video_path)
                    self.iniciar_interfaz_trabajo()
                    for e in self.eventos:
                        seg = e["frame"] / self.fps
                        m, s = int(seg // 60), int(seg % 60)
                        texto = f"[{m:02d}:{s:02d}] {e['sub']} ({e['jugador']})"
                        self.lista_eventos.insert(tk.END, texto)
                    self.draw_timeline()
                    messagebox.showinfo("Proyecto", "Proyecto cargado con éxito!")
            except Exception as ex:
                messagebox.showerror("Error", f"No se pudo abrir el archivo de proyecto: {ex}")

    def importar_datos(self):
        messagebox.showinfo("Importar", "Módulo de importación de datos tácticos.")

    def ver_proyectos(self):
        messagebox.showinfo("Proyectos", "Historial de proyectos guardados.")

    def gestionar_equipos(self):
        self.editar_plantel_dialogo()

    def gestionar_dashboards(self):
        messagebox.showinfo("Paneles", "Editor de botones tácticos.")

    def editar_plantel_dialogo(self):
        win = tk.Toplevel(self.root)
        win.title("Gestión y Edición de Plantel")
        win.geometry("380x380")
        win.configure(bg="#1e1e1e")
        
        tk.Label(win, text="Editar Nombres del Plantel (11 Jugadores):", bg="#1e1e1e", fg="white", font=("Arial", 9, "bold")).pack(pady=8)
        
        entries = []
        frame_list = tk.Frame(win, bg="#1e1e1e")
        frame_list.pack(fill=tk.BOTH, expand=True, padx=10)
        
        for i, jug in enumerate(self.plantel):
            f = tk.Frame(frame_list, bg="#1e1e1e")
            f.pack(fill=tk.X, pady=1)
            tk.Label(f, text=f"J{i+1}:", bg="#1e1e1e", fg="#aaa", width=4).pack(side=tk.LEFT)
            e = tk.Entry(f, width=26, font=("Arial", 9))
            e.insert(0, jug)
            e.pack(side=tk.RIGHT, expand=True, fill=tk.X)
            entries.append(e)
            
        def guardar_cambios():
            self.plantel = [e.get() for e in entries]
            self.jugador_seleccionado = self.plantel[0]
            messagebox.showinfo("Plantel", "Plantel actualizado correctamente!")
            win.destroy()
            if self.cap:
                self.iniciar_interfaz_trabajo()

        tk.Button(win, text="Guardar Cambios", command=guardar_cambios, bg="#007acc", fg="white", font=("Arial", 9, "bold"), pady=4).pack(pady=8)

    # ==========================================
    # OPCIÓN DE FOTOGRAMA (ÚNICAMENTE JPG - Sin PDF)
    # ==========================================
    def accion_fotograma_jpg(self):
        if not self.cap:
            messagebox.showwarning("Aviso", "No hay ningún video cargado.")
            return

        self.playing = False
        if hasattr(self, 'btn_play'):
            self.btn_play.config(text=">")

        output_jpg = filedialog.asksaveasfilename(
            defaultextension=".jpg",
            filetypes=[("Imagen JPG", "*.jpg"), ("Todos los archivos", "*.*")],
            initialfile=f"{self.proyecto_nombre.replace(' ', '_')}_fotograma_{self.current_frame}.jpg"
        )
        if not output_jpg:
            return

        with self._lock:
            self.cap.set(cv2.CAP_PROP_POS_FRAMES, self.current_frame)
            ret, frame = self.cap.read()
        
        if not ret or frame is None:
            messagebox.showerror("Error", "No se pudo extraer el fotograma actual del video.")
            return

        for elem in self.elementos_dibujo:
            if elem["frame_inicio"] <= self.current_frame <= elem["frame_fin"]:
                self.renderizar_elemento_cv2(frame, elem)

        cv2.imwrite(output_jpg, frame)
        messagebox.showinfo("Exportación Exitosa", f"Fotograma guardado correctamente como JPG en:\n{output_jpg}")

    # ==========================================
    # ACTUALIZADO: HERRAMIENTA DE CONGELAR IMAGEN INCORPORADA AL VIDEO (.MP4)
    # ==========================================
    def accion_congelar_imagen(self):
        if not self.cap:
            messagebox.showwarning("Aviso", "No hay ningún video cargado.")
            return

        self.playing = False
        if hasattr(self, 'btn_play'):
            self.btn_play.config(text=">")

        win_freeze = tk.Toplevel(self.root)
        win_freeze.title("Congelar Imagen (Freeze Frame Incorporado)")
        win_freeze.geometry("340x190")
        win_freeze.configure(bg="#1e1e1e")
        win_freeze.transient(self.root)
        win_freeze.grab_set()

        tk.Label(win_freeze, text="Duración de la Congelación en el Video:", bg="#1e1e1e", fg="#00a8ff", font=("Arial", 9, "bold")).pack(pady=10)
        
        f_in = tk.Frame(win_freeze, bg="#1e1e1e")
        f_in.pack(pady=5)
        tk.Label(f_in, text="Segundos:", bg="#1e1e1e", fg="white", font=("Arial", 9)).pack(side=tk.LEFT, padx=5)
        
        e_seg = tk.Entry(f_in, width=8, font=("Arial", 9))
        e_seg.insert(0, "3.0")
        e_seg.pack(side=tk.LEFT, padx=5)
        e_seg.focus_set()
        e_seg.select_range(0, tk.END)

        def confirmar_congelacion():
            try:
                segundos = float(e_seg.get())
                if segundos <= 0:
                    raise ValueError
                
                duracion_frames = int(segundos * self.fps)
                
                corte = {
                    "frame_inicio": self.current_frame,
                    "duracion_frames": duracion_frames
                }
                self.cortes_congelacion.append(corte)
                
                win_freeze.destroy()
                messagebox.showinfo("Congelación Incorporada", f"Corte de congelación de {segundos}s añadido al fotograma {self.current_frame}!\nQuedará incorporado permanentemente al exportar el video.")
            except ValueError:
                messagebox.showerror("Error", "Por favor, introduce un valor numérico válido en segundos.")

        tk.Button(win_freeze, text="Registrar y Guardar Corte", command=confirmar_congelacion, bg="#e67e22", fg="white", font=("Arial", 9, "bold"), relief=tk.FLAT, pady=6).pack(pady=10)

    # ==========================================
    # OPCIÓN TEXTO AL VIDEO
    # ==========================================
    def accion_agregar_texto_video(self):
        if not self.cap:
            messagebox.showwarning("Aviso", "Cargue un video primero.")
            return

        win = tk.Toplevel(self.root)
        win.title("Añadir / Editar Texto al Video")
        win.geometry("360x320")
        win.configure(bg="#1e1e1e")
        win.transient(self.root)
        win.grab_set()

        tk.Label(win, text="Texto a mostrar en pantalla:", bg="#1e1e1e", fg="white", font=("Arial", 9, "bold")).pack(pady=8)
        e_texto = tk.Entry(win, width=32, font=("Arial", 10))
        e_texto.insert(0, "Presión Alta!")
        e_texto.pack(pady=4)

        f_opc = tk.Frame(win, bg="#1e1e1e")
        f_opc.pack(pady=4)

        tk.Label(f_opc, text="Color:", bg="#1e1e1e", fg="white", font=("Arial", 8)).grid(row=0, column=0, padx=5, sticky="w")
        color_var = tk.StringVar(value="amarillo")
        cb_color = ttk.Combobox(f_opc, textvariable=color_var, values=["amarillo", "verde", "rojo", "azul", "blanco", "naranja", "celeste", "violeta"], state="readonly", width=12)
        cb_color.grid(row=0, column=1, padx=5)

        tk.Label(f_opc, text="Alineación:", bg="#1e1e1e", fg="white", font=("Arial", 8)).grid(row=1, column=0, padx=5, pady=4, sticky="w")
        align_var = tk.StringVar(value="centro")
        cb_align = ttk.Combobox(f_opc, textvariable=align_var, values=["izquierda", "centro", "derecha"], state="readonly", width=12)
        cb_align.grid(row=1, column=1, padx=5, pady=4)

        tk.Label(f_opc, text="Tamaño Fuente:", bg="#1e1e1e", fg="white", font=("Arial", 8)).grid(row=2, column=0, padx=5, sticky="w")
        size_var = tk.DoubleVar(value=0.9)
        cb_size = ttk.Combobox(f_opc, textvariable=size_var, values=[0.6, 0.8, 0.9, 1.2, 1.5, 2.0], state="readonly", width=12)
        cb_size.grid(row=2, column=1, padx=5)

        tk.Label(win, text="Duración (Segundos):", bg="#1e1e1e", fg="white", font=("Arial", 8)).pack(pady=2)
        e_dur = tk.Entry(win, width=10, font=("Arial", 9))
        e_dur.insert(0, "5")
        e_dur.pack(pady=2)

        def guardar_texto():
            try:
                dur = float(e_dur.get())
            except ValueError:
                dur = 5.0

            elem = {
                "tipo": "texto_personalizado",
                "x1": 200, "y1": 200,
                "texto": e_texto.get(),
                "color": color_var.get(),
                "alineacion": align_var.get(),
                "tam_fuente": float(size_var.get()),
                "sombra": False,
                "opacidad_sombra": 0.35,
                "frame_inicio": self.current_frame,
                "frame_fin": self.current_frame + int(dur * self.fps)
            }
            self.elementos_dibujo.append(elem)
            self.elemento_seleccionado = elem
            win.destroy()
            messagebox.showinfo("Texto Añadido", "Texto incorporado. Puedes arrastrarlo con el ratón en la pantalla.")

        tk.Button(win, text="Agregar Texto", command=guardar_texto, bg="#007acc", fg="white", font=("Arial", 8, "bold"), relief=tk.FLAT).pack(pady=12)

    # ==========================================
    # EXPORTACIÓN Y RENDERIZADO DE VIDEO (.MP4) CON CONGELAMIENTO INCORPORADO
    # ==========================================
    def descargar_proyecto_json(self):
        if not self.cap or not self.video_path:
            messagebox.showerror("Error", "No hay ningún video cargado para exportar.")
            return

        output_path = filedialog.asksaveasfilename(
            defaultextension=".mp4",
            filetypes=[("Archivo de Video MP4", "*.mp4"), ("Todos los archivos", "*.*")],
            initialfile=f"{self.proyecto_nombre.replace(' ', '_')}_exportado.mp4"
        )
        
        if output_path:
            try:
                pos_actual_original = self.cap.get(cv2.CAP_PROP_POS_FRAMES)
                cap_export = cv2.VideoCapture(self.video_path)
                fps_exp = cap_export.get(cv2.CAP_PROP_FPS) or 25.0
                total_frames_exp = int(cap_export.get(cv2.CAP_PROP_FRAME_COUNT))
                
                width = int(cap_export.get(cv2.CAP_PROP_FRAME_WIDTH) or 1280)
                height = int(cap_export.get(cv2.CAP_PROP_FRAME_HEIGHT) or 720)
                
                fourcc = cv2.VideoWriter_fourcc(*'mp4v')
                writer = cv2.VideoWriter(output_path, fourcc, fps_exp, (width, height))
                
                progress_win = tk.Toplevel(self.root)
                progress_win.title("Exportando Video...")
                progress_win.geometry("350x120")
                progress_win.configure(bg="#1e1e1e")
                progress_win.transient(self.root)
                progress_win.grab_set()
                
                lbl_prog = tk.Label(progress_win, text="Renderizando video con análisis y congelamientos...\nPor favor espere.", bg="#1e1e1e", fg="white", font=("Arial", 9))
                lbl_prog.pack(pady=20)
                
                pb = ttk.Progressbar(progress_win, orient="horizontal", length=300, mode="determinate", maximum=total_frames_exp if total_frames_exp > 0 else 100)
                pb.pack(pady=5)
                progress_win.update()

                frame_idx = 0
                ultimo_frame_valido = None

                while cap_export.isOpened():
                    ret, frame = cap_export.read()
                    if not ret or frame is None:
                        break
                    
                    ultimo_frame_valido = frame.copy()

                    duracion_congelar = 0
                    for corte in self.cortes_congelacion:
                        if corte["frame_inicio"] == frame_idx:
                            duracion_congelar = corte["duracion_frames"]
                            break

                    self._escribir_frame_procesado(writer, frame, frame_idx)
                    frame_idx += 1

                    if duracion_congelar > 0 and ultimo_frame_valido is not None:
                        for _ in range(duracion_congelar):
                            frame_congelado_copia = ultimo_frame_valido.copy()
                            self._escribir_frame_procesado(writer, frame_congelado_copia, frame_idx)
                            frame_idx += 1

                    if frame_idx % 30 == 0:
                        pb['value'] = min(frame_idx, total_frames_exp)
                        progress_win.update()

                cap_export.release()
                writer.release()
                progress_win.destroy()
                self.cap.set(cv2.CAP_PROP_POS_FRAMES, pos_actual_original)
                
                messagebox.showinfo("Exportación Exitosa", f"El video analizado con los congelamientos incorporados se ha guardado correctamente en:\n{output_path}")
            except Exception as e:
                if 'progress_win' in locals():
                    try:
                        progress_win.destroy()
                    except:
                        pass
                messagebox.showerror("Error", f"No se pudo exportar el video: {e}")

    def _escribir_frame_procesado(self, writer, frame, frame_idx):
        for elem in self.elementos_dibujo:
            if elem["frame_inicio"] <= frame_idx <= elem["frame_fin"]:
                self.renderizar_elemento_cv2(frame, elem)

        logo_path = "1001194780.png"
        if os.path.exists(logo_path):
            logo_img = cv2.imread(logo_path, cv2.IMREAD_UNCHANGED)
            if logo_img is not None:
                logo_img = cv2.resize(logo_img, (120, 55), interpolation=cv2.INTER_CUBIC)
                h_l, w_l, _ = logo_img.shape
                fh, fw, _ = frame.shape
                y_offset, x_offset = 15, fw - w_l - 15
                if logo_img.shape[2] == 4:
                    alpha = logo_img[:, :, 3] / 255.0
                    for c in range(3):
                        frame[y_offset:y_offset+h_l, x_offset:x_offset+w_l, c] = (
                            alpha * logo_img[:, :, c] + (1 - alpha) * frame[y_offset:y_offset+h_l, x_offset:x_offset+w_l, c]
                        )
                else:
                    frame[y_offset:y_offset+h_l, x_offset:x_offset+w_l] = logo_img

        writer.write(frame)

    # ==========================================
    # SISTEMA DE HERRAMIENTAS GEOMÉTRICAS Y ESTÉTICAS
    # ==========================================
    def obtener_color_rgb(self, color_str):
        colores = {
            "amarillo": (0, 255, 255),
            "verde": (0, 255, 0),
            "rojo": (0, 0, 255),
            "azul": (255, 0, 0),
            "celeste": (255, 200, 0),
            "blanco": (255, 255, 255),
            "naranja": (0, 165, 255),
            "violeta": (255, 0, 140)
        }
        return colores.get(color_str.lower(), (0, 255, 255))

    def renderizar_elemento_cv2(self, frame, elem, seleccionado=False):
        tipo = elem["tipo"]
        color_custom = elem.get("color", "amarillo")
        col = (0, 255, 255) if seleccionado else self.obtener_color_rgb(color_custom)
        
        if tipo == "texto_personalizado":
            tx, ty = int(elem.get("x1", 100)), int(elem.get("y1", 100))
            texto_str = elem.get("texto", "")
            alineacion = elem.get("alineacion", "centro")
            tam_fuente = float(elem.get("tam_fuente", 0.9))
            
            (ancho_texto, alto_texto), _ = cv2.getTextSize(texto_str, cv2.FONT_HERSHEY_SIMPLEX, tam_fuente, 2)
            pos_x = tx
            if alineacion == "centro":
                pos_x = tx - (ancho_texto // 2)
            elif alineacion == "derecha":
                pos_x = tx - ancho_texto

            cv2.putText(frame, texto_str, (pos_x, ty), cv2.FONT_HERSHEY_SIMPLEX, tam_fuente, col, 2, cv2.LINE_AA)
            if seleccionado:
                cv2.rectangle(frame, (pos_x - 6, ty - int(25 * tam_fuente)), (pos_x + ancho_texto + 6, ty + int(12 * tam_fuente)), (0, 255, 255), 1, cv2.LINE_AA)
            return

        elif tipo == "linea":
            p1 = (int(elem["x1"]), int(elem["y1"]))
            p2 = (int(elem["x2"]), int(elem["y2"]))
            cv2.line(frame, p1, p2, col, 2, cv2.LINE_AA)
            if seleccionado:
                cv2.circle(frame, p1, 6, (0, 255, 255), -1, cv2.LINE_AA)
                cv2.circle(frame, p2, 6, (0, 255, 255), -1, cv2.LINE_AA)
                pm = (int((p1[0]+p2[0])/2), int((p1[1]+p2[1])/2))
                cv2.circle(frame, pm, 6, (255, 0, 255), -1, cv2.LINE_AA)
        
        elif tipo == "flecha_recta":
            p1 = (int(elem["x1"]), int(elem["y1"]))
            p2 = (int(elem["x2"]), int(elem["y2"]))
            cv2.line(frame, p1, p2, col, 2, cv2.LINE_AA)
            angle = np.arctan2(p2[1] - p1[1], p2[0] - p1[0])
            p_left = (int(p2[0] - 12 * np.cos(angle - np.pi/6)), int(p2[1] - 12 * np.sin(angle - np.pi/6)))
            p_right = (int(p2[0] - 12 * np.cos(angle + np.pi/6)), int(p2[1] - 12 * np.sin(angle + np.pi/6)))
            cv2.line(frame, p2, p_left, col, 2, cv2.LINE_AA)
            cv2.line(frame, p2, p_right, col, 2, cv2.LINE_AA)
            if seleccionado:
                cv2.circle(frame, p1, 6, (0, 255, 255), -1, cv2.LINE_AA)
                cv2.circle(frame, p2, 6, (0, 255, 255), -1, cv2.LINE_AA)
                pm = (int((p1[0]+p2[0])/2), int((p1[1]+p2[1])/2))
                cv2.circle(frame, pm, 6, (255, 0, 255), -1, cv2.LINE_AA)

        elif tipo == "flecha_curva":
            p1 = np.array([elem["x1"], elem["y1"]], dtype=float)
            p2 = np.array([elem["x2"], elem["y2"]], dtype=float)
            ctrl = np.array([elem["cx"], elem["cy"]], dtype=float)
            t_vals = np.linspace(0, 1, 30)
            curve_points = [(1-t)**2 * p1 + 2*(1-t)*t * ctrl + t**2 * p2 for t in t_vals]
            for i in range(len(curve_points) - 1):
                pt1 = (int(curve_points[i][0]), int(curve_points[i][1]))
                pt2 = (int(curve_points[i+1][0]), int(curve_points[i+1][1]))
                cv2.line(frame, pt1, pt2, col, 2, cv2.LINE_AA)
            end_pt = curve_points[-1]
            prev_pt = curve_points[-2]
            angle = np.arctan2(end_pt[1] - prev_pt[1], end_pt[0] - prev_pt[0])
            p_left = (int(end_pt[0] - 12 * np.cos(angle - np.pi/6)), int(end_pt[1] - 12 * np.sin(angle - np.pi/6)))
            p_right = (int(end_pt[0] - 12 * np.cos(angle + np.pi/6)), int(end_pt[1] - 12 * np.sin(angle + np.pi/6)))
            cv2.line(frame, (int(end_pt[0]), int(end_pt[1])), p_left, col, 2, cv2.LINE_AA)
            cv2.line(frame, (int(end_pt[0]), int(end_pt[1])), p_right, col, 2, cv2.LINE_AA)
            if seleccionado:
                cv2.circle(frame, (int(p1[0]), int(p1[1])), 6, (0, 255, 255), -1, cv2.LINE_AA)
                cv2.circle(frame, (int(p2[0]), int(p2[1])), 6, (0, 255, 255), -1, cv2.LINE_AA)
                cv2.circle(frame, (int(ctrl[0]), int(ctrl[1])), 6, (255, 0, 255), -1, cv2.LINE_AA)

        elif tipo == "circulo":
            cx, cy = int(elem["x1"]), int(elem["y1"])
            r = int(max(5, np.hypot(elem["x2"] - cx, elem["y2"] - cy)))
            modo = elem.get("modo", "normal")
            alpha_val = float(elem.get("opacidad_sombra", 0.35))
            
            if modo == "foco" or elem.get("sombra", False):
                overlay = frame.copy()
                cv2.circle(overlay, (cx, cy), r, col, -1)
                cv2.addWeighted(overlay, alpha_val, frame, 1.0 - alpha_val, 0, frame)
                
            cv2.circle(frame, (cx, cy), r, col, 2, cv2.LINE_AA)
            if seleccionado:
                cv2.circle(frame, (cx, cy), 6, (0, 255, 255), -1, cv2.LINE_AA)
                cv2.circle(frame, (int(elem["x2"]), int(elem["y2"])), 6, (255, 0, 255), -1, cv2.LINE_AA)
                cv2.circle(frame, (cx - r, cy), 6, (0, 255, 255), -1, cv2.LINE_AA)
                cv2.circle(frame, (cx + r, cy), 6, (0, 255, 255), -1, cv2.LINE_AA)
                cv2.circle(frame, (cx, cy - r), 6, (0, 255, 255), -1, cv2.LINE_AA)
                cv2.circle(frame, (cx, cy + r), 6, (0, 255, 255), -1, cv2.LINE_AA)

        elif tipo == "cuadrado":
            cx, cy = int(elem["x1"]), int(elem["y1"])
            w = int(max(10, abs(elem["x2"] - cx)))
            h = int(max(10, abs(elem["y2"] - cy)))
            x1, y1 = cx - w, cy - h
            x2, y2 = cx + w, cy + h
            modo = elem.get("modo", "normal")
            alpha_val = float(elem.get("opacidad_sombra", 0.35))
            
            if modo == "foco" or elem.get("sombra", False):
                overlay = frame.copy()
                cv2.rectangle(overlay, (x1, y1), (x2, y2), col, -1)
                cv2.addWeighted(overlay, alpha_val, frame, 1.0 - alpha_val, 0, frame)

            cv2.rectangle(frame, (x1, y1), (x2, y2), col, 2, cv2.LINE_AA)
            if seleccionado:
                cv2.circle(frame, (cx, cy), 6, (0, 255, 255), -1, cv2.LINE_AA)
                cv2.circle(frame, (int(elem["x2"]), int(elem["y2"])), 6, (255, 0, 255), -1, cv2.LINE_AA)
                cv2.circle(frame, (x1, y1), 6, (0, 255, 255), -1, cv2.LINE_AA)
                cv2.circle(frame, (x2, y2), 6, (0, 255, 255), -1, cv2.LINE_AA)

        elif tipo == "rombo":
            cx, cy = int(elem["x1"]), int(elem["y1"])
            rx = int(max(10, abs(elem["x2"] - cx)))
            ry = int(max(10, abs(elem["y2"] - cy)))
            pts = np.array([
                [cx, cy - ry],
                [cx + rx, cy],
                [cx, cy + ry],
                [cx - rx, cy]
            ], np.int32)
            
            modo = elem.get("modo", "normal")
            alpha_val = float(elem.get("opacidad_sombra", 0.35))
            
            if modo == "foco" or elem.get("sombra", False):
                overlay = frame.copy()
                cv2.fillPoly(overlay, [pts], col)
                cv2.addWeighted(overlay, alpha_val, frame, 1.0 - alpha_val, 0, frame)

            cv2.polylines(frame, [pts], isClosed=True, color=col, thickness=2, lineType=cv2.LINE_AA)
            if seleccionado:
                cv2.circle(frame, (cx, cy), 6, (0, 255, 255), -1, cv2.LINE_AA)
                cv2.circle(frame, (int(elem["x2"]), int(elem["y2"])), 6, (255, 0, 255), -1, cv2.LINE_AA)
                cv2.circle(frame, (cx, cy - ry), 6, (0, 255, 255), -1, cv2.LINE_AA)
                cv2.circle(frame, (cx + rx, cy), 6, (0, 255, 255), -1, cv2.LINE_AA)

        elif tipo == "triangulo":
            cx, cy = int(elem["x1"]), int(elem["y1"])
            base = int(max(10, abs(elem["x2"] - cx)))
            altura = int(max(10, abs(elem["y2"] - cy)))
            pts = np.array([
                [cx, cy - altura],
                [cx + base, cy + altura],
                [cx - base, cy + altura]
            ], np.int32)
            
            modo = elem.get("modo", "normal")
            alpha_val = float(elem.get("opacidad_sombra", 0.35))
            
            if modo == "foco" or elem.get("sombra", False):
                overlay = frame.copy()
                cv2.fillPoly(overlay, [pts], col)
                cv2.addWeighted(overlay, alpha_val, frame, 1.0 - alpha_val, 0, frame)

            cv2.polylines(frame, [pts], isClosed=True, color=col, thickness=2, lineType=cv2.LINE_AA)
            if seleccionado:
                cv2.circle(frame, (cx, cy), 6, (0, 255, 255), -1, cv2.LINE_AA)
                cv2.circle(frame, (int(elem["x2"]), int(elem["y2"])), 6, (255, 0, 255), -1, cv2.LINE_AA)
                cv2.circle(frame, (cx, cy - altura), 6, (0, 255, 255), -1, cv2.LINE_AA)
                cv2.circle(frame, (cx + base, cy + altura), 6, (0, 255, 255), -1, cv2.LINE_AA)

        elif tipo == "poligono_custom":
            pts = np.array(elem["puntos"], np.int32)
            modo = elem.get("modo", "normal")
            alpha_val = float(elem.get("opacidad_sombra", 0.35))
            
            if modo == "foco" or elem.get("sombra", False):
                overlay = frame.copy()
                cv2.fillPoly(overlay, [pts], col)
                cv2.addWeighted(overlay, alpha_val, frame, 1.0 - alpha_val, 0, frame)

            cv2.polylines(frame, [pts], isClosed=True, color=col, thickness=2, lineType=cv2.LINE_AA)
            if seleccionado:
                for pt in pts:
                    cv2.circle(frame, tuple(pt), 6, (0, 255, 255), -1, cv2.LINE_AA)

    def comprobar_clic_sobre_elemento(self, vx, vy, elem):
        tipo = elem["tipo"]
        if tipo == "texto_personalizado":
            return np.hypot(vx - elem["x1"], vy - elem["y1"]) < 40
        elif tipo == "linea":
            if np.hypot(vx - elem["x1"], vy - elem["y1"]) < 20 or np.hypot(vx - elem["x2"], vy - elem["y2"]) < 20 or \
               np.hypot(vx - (elem["x1"]+elem["x2"])/2, vy - (elem["y1"]+elem["y2"])/2) < 20:
                return True
            x1, y1, x2, y2 = elem["x1"], elem["y1"], elem["x2"], elem["y2"]
            p_line = np.hypot(x2 - x1, y2 - y1)
            if p_line == 0:
                return np.hypot(vx - x1, vy - y1) < 20
            u = ((vx - x1) * (x2 - x1) + (vy - y1) * (y2 - y1)) / (p_line ** 2)
            u = max(0, min(1, u))
            ix = x1 + u * (x2 - x1)
            iy = y1 + u * (y2 - y1)
            return np.hypot(vx - ix, vy - iy) < 20
        elif tipo == "flecha_recta":
            if np.hypot(vx - elem["x1"], vy - elem["y1"]) < 20 or np.hypot(vx - elem["x2"], vy - elem["y2"]) < 20 or \
               np.hypot(vx - (elem["x1"]+elem["x2"])/2, vy - (elem["y1"]+elem["y2"])/2) < 20:
                return True
            x1, y1, x2, y2 = elem["x1"], elem["y1"], elem["x2"], elem["y2"]
            p_line = np.hypot(x2 - x1, y2 - y1)
            if p_line == 0:
                return np.hypot(vx - x1, vy - y1) < 20
            u = ((vx - x1) * (x2 - x1) + (vy - y1) * (y2 - y1)) / (p_line ** 2)
            u = max(0, min(1, u))
            ix = x1 + u * (x2 - x1)
            iy = y1 + u * (y2 - y1)
            return np.hypot(vx - ix, vy - iy) < 20
        elif tipo == "flecha_curva":
            if np.hypot(vx - elem["x1"], vy - elem["y1"]) < 20 or \
               np.hypot(vx - elem["x2"], vy - elem["y2"]) < 20 or \
               np.hypot(vx - elem.get("cx", elem["x1"]), vy - elem.get("cy", elem["y1"])) < 20:
                return True
            p1 = np.array([elem["x1"], elem["y1"]], dtype=float)
            p2 = np.array([elem["x2"], elem["y2"]], dtype=float)
            ctrl = np.array([elem["cx"], elem["cy"]], dtype=float)
            t_vals = np.linspace(0, 1, 20)
            for t in t_vals:
                pt = (1-t)**2 * p1 + 2*(1-t)*t * ctrl + t**2 * p2
                if np.hypot(vx - pt[0], vy - pt[1]) < 15:
                    return True
            return False
        elif tipo == "circulo":
            cx, cy = elem["x1"], elem["y1"]
            r = max(5, np.hypot(elem["x2"] - cx, elem["y2"] - cy))
            if np.hypot(vx - cx, vy - cy) < 20 or np.hypot(vx - elem["x2"], vy - elem["y2"]) < 20 or \
               np.hypot(vx - (cx - r), vy - cy) < 18 or np.hypot(vx - (cx + r), vy - cy) < 18 or \
               np.hypot(vx - cx, vy - (cy - r)) < 18 or np.hypot(vx - cx, vy - (cy + r)) < 18:
                return True
            return np.hypot(vx - cx, vy - cy) <= r + 15
        elif tipo == "cuadrado":
            cx, cy = elem["x1"], elem["y1"]
            w = abs(elem["x2"] - cx)
            h = abs(elem["y2"] - cy)
            x1, y1 = cx - w, cy - h
            x2, y2 = cx + w, cy + h
            return (x1 - 15 <= vx <= x2 + 15) and (y1 - 15 <= vy <= y2 + 15)
        elif tipo == "rombo":
            cx, cy = elem["x1"], elem["y1"]
            rx = abs(elem["x2"] - cx)
            ry = abs(elem["y2"] - cy)
            return (cx - rx - 15 <= vx <= cx + rx + 15) and (cy - ry - 15 <= vy <= cy + ry + 15)
        elif tipo == "triangulo":
            cx, cy = elem["x1"], elem["y1"]
            base = abs(elem["x2"] - cx)
            altura = abs(elem["y2"] - cy)
            return (cx - base - 15 <= vx <= cx + base + 15) and (cy - altura - 15 <= vy <= cy + altura + 15)
        elif tipo == "poligono_custom":
            pts = elem["puntos"]
            for pt in pts:
                if np.hypot(vx - pt[0], vy - pt[1]) < 20:
                    return True
            xs = [p[0] for p in pts]
            ys = [p[1] for p in pts]
            return (min(xs) - 15 <= vx <= max(xs) + 15) and (min(ys) - 15 <= vy <= max(ys) + 15)
        return False

    def cargar_motor_video(self, path):
        if self.cap:
            self.cap.release()
        self.cap = cv2.VideoCapture(path)
        self.fps = self.cap.get(cv2.CAP_PROP_FPS) or 25.0
        if self.fps <= 0:
            self.fps = 25.0
        self.total_frames = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
        self.current_frame = 0
        self.playing = True

    def iniciar_interfaz_trabajo(self):
        self.limpiar_ventana()
        
        top_menu = tk.Frame(self.root, bg="#1e1e1e", height=28)
        top_menu.pack(side=tk.TOP, fill=tk.X)
        
        tk.Button(top_menu, text="Menu", command=self.mostrar_menu_principal, bg="#333", fg="white", font=("Arial", 7), relief=tk.FLAT).pack(side=tk.LEFT, padx=4, pady=2)
        tk.Button(top_menu, text="Video", command=self.crear_nuevo_proyecto, bg="#007acc", fg="white", font=("Arial", 7), relief=tk.FLAT).pack(side=tk.LEFT, padx=4, pady=2)
        tk.Button(top_menu, text="Plantel", command=self.editar_plantel_dialogo, bg="#28a745", fg="white", font=("Arial", 7, "bold"), relief=tk.FLAT).pack(side=tk.LEFT, padx=4, pady=2)
        tk.Button(top_menu, text="Exportar Video MP4", command=self.descargar_proyecto_json, bg="#ffc107", fg="black", font=("Arial", 7, "bold"), relief=tk.FLAT).pack(side=tk.LEFT, padx=10, pady=2)
        tk.Button(top_menu, text="Opciones de Figura Seleccionada", command=self.abrir_menu_personalizacion_elemento, bg="#9b59b6", fg="white", font=("Arial", 7, "bold"), relief=tk.FLAT).pack(side=tk.LEFT, padx=5, pady=2)

        tk.Button(top_menu, text="Fotograma (JPG)", command=self.accion_fotograma_jpg, bg="#17a2b8", fg="white", font=("Arial", 7, "bold"), relief=tk.FLAT).pack(side=tk.LEFT, padx=3, pady=2)
        tk.Button(top_menu, text="Congelar Imagen", command=self.accion_congelar_imagen, bg="#e67e22", fg="white", font=("Arial", 7, "bold"), relief=tk.FLAT).pack(side=tk.LEFT, padx=3, pady=2)
        tk.Button(top_menu, text="Texto al Video", command=self.accion_agregar_texto_video, bg="#34495e", fg="white", font=("Arial", 7, "bold"), relief=tk.FLAT).pack(side=tk.LEFT, padx=3, pady=2)

        tk.Label(top_menu, text=f"Proyecto: {self.proyecto_nombre} ({self.equipo_local} vs {self.equipo_visitante})", bg="#1e1e1e", fg="#00a8ff", font=("Arial", 7, "bold")).pack(side=tk.RIGHT, padx=8)
        
        main_layout = tk.Frame(self.root, bg="#121212")
        main_layout.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        left_panel = tk.Frame(main_layout, bg="#1a1a1a", width=240)
        left_panel.pack(side=tk.LEFT, fill=tk.Y, padx=2, pady=2)
        left_panel.pack_propagate(False)

        tk.Label(left_panel, text="Playlist de Eventos", bg="#1a1a1a", fg="white", font=("Arial", 8, "bold")).pack(pady=4)
        self.lista_eventos = tk.Listbox(left_panel, bg="#121212", fg="white", font=("Arial", 8), bd=0, highlightthickness=0)
        self.lista_eventos.pack(fill=tk.BOTH, expand=True, padx=3, pady=3)
        self.lista_eventos.bind("<Double-Button-1>", self.ir_a_evento)

        tk.Label(left_panel, text="Gestor de Gráficos / Duración", bg="#1a1a1a", fg="#00a8ff", font=("Arial", 8, "bold")).pack(pady=2)
        btn_editar_grafico = tk.Button(left_panel, text="Ajustar Duración / Borrar Gráfico", command=self.abrir_dialogo_editar_grafico, bg="#333", fg="white", font=("Arial", 7), relief=tk.FLAT)
        btn_editar_grafico.pack(fill=tk.X, padx=4, pady=2)

        right_panel = tk.Frame(main_layout, bg="#121212")
        right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=2, pady=2)

        video_frame = tk.Frame(right_panel, bg="black", height=120)
        video_frame.pack(side=tk.TOP, fill=tk.X, padx=2, pady=1)
        
        self.video_label = tk.Label(video_frame, bg="black")
        self.video_label.pack(fill=tk.BOTH, expand=True)
        
        self.video_label.bind("<Button-1>", self.clic_en_video)
        self.video_label.bind("<B1-Motion>", self.arrastrar_en_video)
        self.video_label.bind("<ButtonRelease-1>", self.soltar_en_video)
        self.video_label.bind("<Button-3>", self.clic_derecho_en_video) 

        tools_overlay = tk.Frame(right_panel, bg="#1e1e1e", height=30)
        tools_overlay.pack(side=tk.TOP, fill=tk.X, padx=2, pady=1)
        tk.Label(tools_overlay, text="Dibujo:", bg="#1e1e1e", fg="#aaa", font=("Arial", 7)).pack(side=tk.LEFT, padx=4)
        
        tk.Button(tools_overlay, text="Línea", command=lambda: self.activar_herramienta("linea"), bg="#1abc9c", fg="white", font=("Arial", 7, "bold"), relief=tk.FLAT).pack(side=tk.LEFT, padx=2)
        tk.Button(tools_overlay, text="Flecha", command=lambda: self.activar_herramienta("flecha_recta"), bg="#28a745", fg="white", font=("Arial", 7, "bold"), relief=tk.FLAT).pack(side=tk.LEFT, padx=2)
        tk.Button(tools_overlay, text="Curva", command=lambda: self.activar_herramienta("flecha_curva"), bg="#17a2b8", fg="white", font=("Arial", 7, "bold"), relief=tk.FLAT).pack(side=tk.LEFT, padx=2)
        tk.Button(tools_overlay, text="Círculo", command=lambda: self.activar_herramienta("circulo"), bg="#e67e22", fg="white", font=("Arial", 7, "bold"), relief=tk.FLAT).pack(side=tk.LEFT, padx=2)
        tk.Button(tools_overlay, text="Cuadrado", command=lambda: self.activar_herramienta("cuadrado"), bg="#d35400", fg="white", font=("Arial", 7, "bold"), relief=tk.FLAT).pack(side=tk.LEFT, padx=2)
        tk.Button(tools_overlay, text="Rombo", command=lambda: self.activar_herramienta("rombo"), bg="#8e44ad", fg="white", font=("Arial", 7, "bold"), relief=tk.FLAT).pack(side=tk.LEFT, padx=2)
        tk.Button(tools_overlay, text="Triángulo", command=lambda: self.activar_herramienta("triangulo"), bg="#2980b9", fg="white", font=("Arial", 7, "bold"), relief=tk.FLAT).pack(side=tk.LEFT, padx=2)
        
        # NUEVAS HERRAMIENTAS DE CLIC A CLIC PARA TRIANGULACIONES Y ROMBOS
        tk.Button(tools_overlay, text="Triángulo (3pts)", command=lambda: self.activar_herramienta("triangulo_pts"), bg="#2980b9", fg="white", font=("Arial", 7, "bold"), relief=tk.FLAT).pack(side=tk.LEFT, padx=2)
        tk.Button(tools_overlay, text="Rombo (4pts)", command=lambda: self.activar_herramienta("rombo_pts"), bg="#8e44ad", fg="white", font=("Arial", 7, "bold"), relief=tk.FLAT).pack(side=tk.LEFT, padx=2)

        tk.Button(tools_overlay, text="Borrar Todo", command=self.borrar_dibujos, bg="#dc3545", fg="white", font=("Arial", 7), relief=tk.FLAT).pack(side=tk.RIGHT, padx=4)

        ctrl_bar = tk.Frame(right_panel, bg="#1e1e1e", height=28)
        ctrl_bar.pack(side=tk.TOP, fill=tk.X, padx=2, pady=1)

        self.btn_play = tk.Button(ctrl_bar, text="||", command=self.toggle_play, bg="#007acc", fg="white", font=("Arial", 8, "bold"), width=3, relief=tk.FLAT)
        self.btn_play.pack(side=tk.LEFT, padx=3)

        self.btn_rec = tk.Button(ctrl_bar, text="REC Clip", command=self.toggle_grabacion, bg="#dc3545", fg="white", font=("Arial", 7, "bold"), relief=tk.FLAT)
        self.btn_rec.pack(side=tk.LEFT, padx=6)

        self.lbl_time = tk.Label(ctrl_bar, text="00:00 / 00:00", bg="#1e1e1e", fg="white", font=("Arial", 7, "bold"))
        self.lbl_time.pack(side=tk.RIGHT, padx=6)

        self.timeline_canvas = tk.Canvas(right_panel, height=16, bg="#111", highlightthickness=0)
        self.timeline_canvas.pack(side=tk.TOP, fill=tk.X, padx=2, pady=1)
        self.timeline_canvas.bind("<Button-1>", self.click_timeline)

        bottom_dash = tk.Frame(right_panel, bg="#181a1b")
        bottom_dash.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=2, pady=2)

        cancha_frame = tk.Frame(bottom_dash, bg="#143d24", width=340)
        cancha_frame.pack(side=tk.LEFT, fill=tk.Y, padx=2, pady=2)
        cancha_frame.pack_propagate(False)

        top_cancha_header = tk.Frame(cancha_frame, bg="#143d24")
        top_cancha_header.pack(fill=tk.X, padx=3, pady=2)
        tk.Label(top_cancha_header, text="Plantel", bg="#143d24", fg="white", font=("Arial", 7, "bold")).pack(side=tk.LEFT)
        tk.Button(top_cancha_header, text="Editar", command=self.editar_plantel_dialogo, bg="#28a745", fg="white", font=("Arial", 6, "bold"), relief=tk.FLAT).pack(side=tk.RIGHT)
        
        grid_cancha = tk.Frame(cancha_frame, bg="#143d24")
        grid_cancha.pack(expand=True)
        
        for idx, jugador in enumerate(self.plantel):
            fila = idx // 3
            columna = idx % 3
            btn_jug = tk.Button(grid_cancha, text=jugador, command=lambda j=jugador: self.seleccionar_jugador(j),
                                bg="#28a745", fg="white", font=("Arial", 6, "bold"), width=10, relief=tk.FLAT)
            btn_jug.grid(row=fila, column=columna, padx=1, pady=1)

        acciones_frame = tk.Frame(bottom_dash, bg="#181a1b")
        acciones_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=2, pady=2)

        tk.Label(acciones_frame, text="Panel de Botones Tácticos", bg="#181a1b", fg="white", font=("Arial", 7, "bold")).pack(pady=2)
        
        categorias = [
            ("Ataque Directo / Transición", "#28a745"),
            ("Pressing Bloque Alto", "#dc3545"),
            ("Balón Parado / Córner", "#ffc107")
        ]

        for cat, color in categorias:
            btn_cat = tk.Button(acciones_frame, text=cat, command=lambda c=cat, col=color: self.registrar_evento_tactico(c, col),
                                bg=color, fg="black" if color=="#ffc107" else "white", font=("Arial", 7, "bold"), 
                                anchor="w", padx=8, pady=3, relief=tk.FLAT)
            btn_cat.pack(fill=tk.X, padx=4, pady=1)

        self.hilo_activo = True
        threading.Thread(target=self.motor_hilo_video, daemon=True).start()
        self.actualizar_interfaz_gui()

    # ==========================================
    # MENÚ DE PERSONALIZACIÓN PARA TEXTO Y FIGURAS
    # ==========================================
    def abrir_menu_personalizacion_elemento(self):
        if not self.elemento_seleccionado:
            messagebox.showwarning("Selección", "Primero haz clic sobre una figura o texto en el video para seleccionarla.")
            return

        win = tk.Toplevel(self.root)
        win.title("Personalizar Elemento Seleccionado")
        win.geometry("380x480")
        win.configure(bg="#1e1e1e")
        win.transient(self.root)
        win.grab_set()

        elem = self.elemento_seleccionado

        tk.Label(win, text=f"Editando: {elem['tipo'].upper()}", bg="#1e1e1e", fg="#00a8ff", font=("Arial", 9, "bold")).pack(pady=8)

        entry_texto = None
        cb_align = None
        cb_size = None
        scale_opacidad = None
        cb_relleno_figura = None

        if elem["tipo"] == "texto_personalizado":
            tk.Label(win, text="Texto:", bg="#1e1e1e", fg="white", font=("Arial", 8)).pack(pady=2)
            entry_texto = tk.Entry(win, width=32, font=("Arial", 9))
            entry_texto.insert(0, elem.get("texto", ""))
            entry_texto.pack(pady=2)

            tk.Label(win, text="Alineación / Centrado:", bg="#1e1e1e", fg="white", font=("Arial", 8)).pack(pady=2)
            cb_align = ttk.Combobox(win, values=["izquierda", "centro", "derecha"], state="readonly", width=18)
            cb_align.set(elem.get("alineacion", "centro"))
            cb_align.pack(pady=2)

            tk.Label(win, text="Tamaño de Letra:", bg="#1e1e1e", fg="white", font=("Arial", 8)).pack(pady=2)
            cb_size = ttk.Combobox(win, values=[0.6, 0.8, 0.9, 1.2, 1.5, 2.0], state="readonly", width=18)
            cb_size.set(elem.get("tam_fuente", 0.9))
            cb_size.pack(pady=2)

        elif elem["tipo"] in ["circulo", "cuadrado", "rombo", "triangulo", "poligono_custom"]:
            tk.Label(win, text="Relleno de Figura (Foco):", bg="#1e1e1e", fg="white", font=("Arial", 8)).pack(pady=2)
            cb_relleno_figura = ttk.Combobox(win, values=["normal", "foco"], state="readonly", width=18)
            cb_relleno_figura.set(elem.get("modo", "normal"))
            cb_relleno_figura.pack(pady=2)

            tk.Label(win, text="Opacidad del Relleno:", bg="#1e1e1e", fg="white", font=("Arial", 8)).pack(pady=2)
            scale_opacidad = ttk.Scale(win, from_=0.1, to=0.9, value=elem.get("opacidad_sombra", 0.35), orient="horizontal", length=200)
            scale_opacidad.pack(pady=2)

        tk.Label(win, text="Color:", bg="#1e1e1e", fg="white", font=("Arial", 8)).pack(pady=2)
        color_var = tk.StringVar(value=elem.get("color", "amarillo"))
        colores_disp = ["amarillo", "verde", "rojo", "azul", "celeste", "blanco", "naranja", "violeta"]
        cb_color = ttk.Combobox(win, textvariable=color_var, values=colores_disp, state="readonly", width=18)
        cb_color.pack(pady=2)

        def aplicar_cambios():
            if entry_texto is not None:
                elem["texto"] = entry_texto.get()
            if cb_align is not None:
                elem["alineacion"] = cb_align.get()
            if cb_size is not None:
                elem["tam_fuente"] = float(cb_size.get())
            if cb_relleno_figura is not None:
                elem["modo"] = cb_relleno_figura.get()
                elem["sombra"] = (cb_relleno_figura.get() == "foco")
            if scale_opacidad is not None:
                elem["opacidad_sombra"] = float(scale_opacidad.get())
            elem["color"] = color_var.get()
            messagebox.showinfo("Actualizado", "Elemento actualizado con éxito.")
            win.destroy()

        tk.Button(win, text="Guardar Cambios", command=aplicar_cambios, bg="#007acc", fg="white", font=("Arial", 8, "bold"), relief=tk.FLAT).pack(pady=15)

    def seleccionar_jugador(self, jugador):
        self.jugador_seleccionado = jugador

    def activar_herramienta(self, herramienta):
        self.herramienta_activa = herramienta
        self.elemento_seleccionado = None
        self.puntos_temp_creacion = []
        if herramienta == "triangulo_pts":
            messagebox.showinfo("Herramienta Activa", "Modo Triangulación:\nHaz clic en 3 puntos sucesivos sobre el video para formar el triángulo.")
        elif herramienta == "rombo_pts":
            messagebox.showinfo("Herramienta Activa", "Modo Rombo / Cuadrilátero:\nHaz clic en 4 puntos sucesivos sobre el video para formar la figura.")
        else:
            messagebox.showinfo("Herramienta Activa", f"Herramienta seleccionada: {herramienta.upper()}.\nHaz clic en el video para colocarla.")

    def borrar_dibujos(self):
        self.elementos_dibujo.clear()
        self.puntos_temp_creacion = []
        self.elemento_seleccionado = None

    def toggle_grabacion(self):
        if not self.grabando_video:
            output_path = filedialog.asksaveasfilename(defaultextension=".mp4", filetypes=[("MP4 Video", "*.mp4")])
            if output_path:
                fourcc = cv2.VideoWriter_fourcc(*'mp4v')
                self.video_writer = cv2.VideoWriter(output_path, fourcc, self.fps, (1280, 720))
                self.grabando_video = True
                self.btn_rec.config(bg="yellow", fg="black", text="DETENER")
        else:
            self.grabando_video = False
            if self.video_writer:
                self.video_writer.release()
            self.btn_rec.config(bg="#dc3545", fg="white", text="REC Clip")

    def convertir_coordenadas_widget_a_video(self, event_x, event_y):
        fw = self.cap.get(cv2.CAP_PROP_FRAME_WIDTH) or 1280
        fh = self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT) or 720
        widget_w = self.video_label.winfo_width() or 760
        widget_h = self.video_label.winfo_height() or 420
        vx = int(event_x * (fw / widget_w))
        vy = int(event_y * (fh / widget_h))
        return vx, vy

    def solicitar_duracion_nuevo_elemento(self, elem):
        was_playing = self.playing
        self.playing = False
        self.btn_play.config(text=">")

        win_dur = tk.Toplevel(self.root)
        win_dur.title("Duración del Gráfico")
        win_dur.geometry("300x160")
        win_dur.configure(bg="#1e1e1e")
        win_dur.transient(self.root)
        win_dur.grab_set()

        tk.Label(win_dur, text=f"Definir duración para: {elem['tipo']}", bg="#1e1e1e", fg="#00a8ff", font=("Arial", 9, "bold")).pack(pady=10)
        
        f_in = tk.Frame(win_dur, bg="#1e1e1e")
        f_in.pack(pady=5)
        tk.Label(f_in, text="Duración en Segundos:", bg="#1e1e1e", fg="white", font=("Arial", 8)).pack(side=tk.LEFT, padx=5)
        
        e_seg = tk.Entry(f_in, width=8, font=("Arial", 9))
        e_seg.insert(0, "5")
        e_seg.pack(side=tk.LEFT, padx=5)
        e_seg.focus_set()
        e_seg.select_range(0, tk.END)

        def confirmar():
            try:
                segundos = float(e_seg.get())
                if segundos <= 0:
                    raise ValueError
                elem["frame_fin"] = elem["frame_inicio"] + int(segundos * self.fps)
            except ValueError:
                elem["frame_fin"] = elem["frame_inicio"] + int(5 * self.fps)
            
            self.elementos_dibujo.append(elem)
            self.elemento_seleccionado = elem  
            win_dur.destroy()

        tk.Button(win_dur, text="Aceptar", command=confirmar, bg="#007acc", fg="white", font=("Arial", 8, "bold"), width=12, relief=tk.FLAT).pack(pady=10)
        win_dur.protocol("WM_DELETE_WINDOW", confirmar)

    def clic_en_video(self, event):
        if not self.cap:
            return
        vx, vy = self.convertir_coordenadas_widget_a_video(event.x, event.y)

        # GESTIÓN DE HERRAMIENTA POR CLICS SUCESIVOS (Triangulaciones / Rombos)
        if self.herramienta_activa in ["triangulo_pts", "rombo_pts"]:
            self.puntos_temp_creacion.append([vx, vy])
            target_pts = 3 if self.herramienta_activa == "triangulo_pts" else 4
            if len(self.puntos_temp_creacion) == target_pts:
                elem = {
                    "tipo": "poligono_custom",
                    "puntos": list(self.puntos_temp_creacion),
                    "modo": "normal",
                    "color": "amarillo",
                    "sombra": False,
                    "opacidad_sombra": 0.35,
                    "frame_inicio": self.current_frame,
                    "frame_fin": self.current_frame + int(self.fps * 5)
                }
                self.puntos_temp_creacion = []
                self.solicitar_duracion_nuevo_elemento(elem)
                self.herramienta_activa = "ninguno"
            return

        if self.herramienta_activa != "ninguno":
            self.elemento_seleccionado = None
        else:
            clicked_element = None
            for elem in self.elementos_dibujo:
                if elem["frame_inicio"] <= self.current_frame <= elem["frame_fin"]:
                    if self.comprobar_clic_sobre_elemento(vx, vy, elem):
                        clicked_element = elem
                        break

            if clicked_element:
                self.elemento_seleccionado = clicked_element
                self.elemento_en_arrastre = clicked_element
                tipo = clicked_element["tipo"]
                
                if tipo == "texto_personalizado":
                    self.tipo_arrastre_punto = "mover_todo"
                    self.offset_arrastre = (clicked_element["x1"] - vx, clicked_element["y1"] - vy)
                elif tipo in ["circulo", "cuadrado", "rombo", "triangulo"]:
                    cx, cy = clicked_element["x1"], clicked_element["y1"]
                    if np.hypot(vx - clicked_element["x2"], vy - clicked_element["y2"]) < 25:
                        self.tipo_arrastre_punto = "punto_2" 
                    elif np.hypot(vx - cx, vy - cy) < 20:
                        self.tipo_arrastre_punto = "mover_centro"
                        self.offset_arrastre = (cx - vx, cy - vy)
                    else:
                        self.tipo_arrastre_punto = "mover_todo"
                        self.offset_arrastre = (vx, vy)
                elif tipo in ["linea", "flecha_recta", "flecha_curva"]:
                    if np.hypot(vx - clicked_element["x1"], vy - clicked_element["y1"]) < 20:
                        self.tipo_arrastre_punto = "punto_1"
                    elif np.hypot(vx - clicked_element["x2"], vy - clicked_element["y2"]) < 20:
                        self.tipo_arrastre_punto = "punto_2"
                    elif np.hypot(vx - (clicked_element["x1"]+clicked_element["x2"])/2, vy - (clicked_element["y1"]+clicked_element["y2"])/2) < 20:
                        self.tipo_arrastre_punto = "flecha_medio"
                    elif tipo == "flecha_curva" and np.hypot(vx - clicked_element.get("cx", clicked_element["x1"]), vy - clicked_element.get("cy", clicked_element["y1"])) < 20:
                        self.tipo_arrastre_punto = "punto_control"
                    else:
                        self.tipo_arrastre_punto = "mover_todo"
                        self.offset_arrastre = (vx, vy)
                elif tipo == "poligono_custom":
                    self.tipo_arrastre_punto = "mover_todo"
                    self.offset_arrastre = (vx, vy)
                else:
                    self.tipo_arrastre_punto = "mover_todo"
                    self.offset_arrastre = (vx, vy)
                return
            else:
                self.elemento_seleccionado = None

        if self.herramienta_activa in ["circulo", "cuadrado", "rombo", "triangulo"]:
            elem = {
                "tipo": self.herramienta_activa, 
                "x1": vx, "y1": vy, 
                "x2": vx + 50, "y2": vy + 50,
                "modo": "normal",
                "color": "amarillo",
                "sombra": False,
                "opacidad_sombra": 0.35,
                "frame_inicio": self.current_frame,
                "frame_fin": self.current_frame + int(self.fps * 5)
            }
            self.solicitar_duracion_nuevo_elemento(elem)
            self.herramienta_activa = "ninguno"

        elif self.herramienta_activa == "linea":
            tam = 40
            elem = {
                "tipo": "linea", 
                "x1": vx - tam, "y1": vy - tam, 
                "x2": vx + tam, "y2": vy + tam,
                "color": "amarillo",
                "sombra": False,
                "opacidad_sombra": 0.35,
                "frame_inicio": self.current_frame,
                "frame_fin": self.current_frame + int(self.fps * 5)
            }
            self.solicitar_duracion_nuevo_elemento(elem)
            self.herramienta_activa = "ninguno"

        elif self.herramienta_activa == "flecha_recta":
            tam = 40
            elem = {
                "tipo": self.herramienta_activa, 
                "x1": vx - tam, "y1": vy - tam, 
                "x2": vx + tam, "y2": vy + tam,
                "modo": "normal",
                "color": "amarillo",
                "sombra": False,
                "opacidad_sombra": 0.35,
                "frame_inicio": self.current_frame,
                "frame_fin": self.current_frame + int(self.fps * 5)
            }
            self.solicitar_duracion_nuevo_elemento(elem)
            self.herramienta_activa = "ninguno"

        elif self.herramienta_activa == "flecha_curva":
            elem = {
                "tipo": "flecha_curva", 
                "x1": vx - 40, "y1": vy + 30, 
                "x2": vx + 40, "y2": vy + 30, 
                "cx": vx, "cy": vy - 40,
                "color": "amarillo",
                "sombra": False,
                "opacidad_sombra": 0.35,
                "frame_inicio": self.current_frame,
                "frame_fin": self.current_frame + int(self.fps * 5)
            }
            self.solicitar_duracion_nuevo_elemento(elem)
            self.herramienta_activa = "ninguno"

    def arrastrar_en_video(self, event):
        if not self.cap or not self.elemento_en_arrastre:
            return
        vx, vy = self.convertir_coordenadas_widget_a_video(event.x, event.y)
        elem = self.elemento_en_arrastre
        
        if self.tipo_arrastre_punto == "mover_todo":
            if elem["tipo"] == "texto_personalizado":
                elem["x1"] = vx + self.offset_arrastre[0]
                elem["y1"] = vy + self.offset_arrastre[1]
            elif elem["tipo"] in ["circulo", "cuadrado", "rombo", "triangulo"]:
                dx = vx - self.offset_arrastre[0]
                dy = vy - self.offset_arrastre[1]
                elem["x1"] += dx
                elem["y1"] += dy
                elem["x2"] += dx
                elem["y2"] += dy
                self.offset_arrastre = (vx, vy)
            elif elem["tipo"] in ["linea", "flecha_recta", "flecha_curva"]:
                dx = vx - self.offset_arrastre[0]
                dy = vy - self.offset_arrastre[1]
                elem["x1"] += dx
                elem["y1"] += dy
                elem["x2"] += dx
                elem["y2"] += dy
                if "cx" in elem:
                    elem["cx"] += dx
                    elem["cy"] += dy
                self.offset_arrastre = (vx, vy)
            elif elem["tipo"] == "poligono_custom":
                dx = vx - self.offset_arrastre[0]
                dy = vy - self.offset_arrastre[1]
                for pt in elem["puntos"]:
                    pt[0] += dx
                    pt[1] += dy
                self.offset_arrastre = (vx, vy)
        
        elif self.tipo_arrastre_punto == "mover_centro" and elem["tipo"] in ["circulo", "cuadrado", "rombo", "triangulo"]:
            elem["x1"] = vx + self.offset_arrastre[0]
            elem["y1"] = vy + self.offset_arrastre[1]
            elem["x2"] = elem["x1"] + 50
            elem["y2"] = elem["y1"] + 50

        elif self.tipo_arrastre_punto == "punto_2":
            elem["x2"] = vx
            elem["y2"] = vy

        elif self.tipo_arrastre_punto in ["punto_1", "punto_2", "punto_control"] and elem["tipo"] in ["linea", "flecha_recta", "flecha_curva"]:
            if self.tipo_arrastre_punto == "punto_1":
                elem["x1"] = vx
                elem["y1"] = vy
            elif self.tipo_arrastre_punto == "punto_2":
                elem["x2"] = vx
                elem["y2"] = vy
            elif self.tipo_arrastre_punto == "punto_control":
                elem["cx"] = vx
                elem["cy"] = vy

    def soltar_en_video(self, event):
        self.elemento_en_arrastre = None
        self.tipo_arrastre_punto = None

    def clic_derecho_en_video(self, event):
        if not self.cap:
            return
        vx, vy = self.convertir_coordenadas_widget_a_video(event.x, event.y)
        
        # Si hay puntos temporales marcados, cancelar creación actual
        if self.puntos_temp_creacion:
            self.puntos_temp_creacion = []
            self.herramienta_activa = "ninguno"
            return

        if self.elemento_seleccionado and self.comprobar_clic_sobre_elemento(vx, vy, self.elemento_seleccionado):
            if self.elemento_seleccionado in self.elementos_dibujo:
                self.elementos_dibujo.remove(self.elemento_seleccionado)
            self.elemento_seleccionado = None
            return

        for elem in list(self.elementos_dibujo):
            if elem["frame_inicio"] <= self.current_frame <= elem["frame_fin"]:
                if self.comprobar_clic_sobre_elemento(vx, vy, elem):
                    self.elementos_dibujo.remove(elem)
                    if self.elemento_seleccionado == elem:
                        self.elemento_seleccionado = None
                    return

    def abrir_dialogo_editar_grafico(self):
        if not self.elementos_dibujo:
            messagebox.showinfo("Editor", "No hay gráficos activos en el proyecto.")
            return

        win = tk.Toplevel(self.root)
        win.title("Gestión de Duración y Eliminación de Gráficos")
        win.geometry("520x380")
        win.configure(bg="#1e1e1e")

        tk.Label(win, text="Selecciona el gráfico para modificar su duración o eliminarlo:", bg="#1e1e1e", fg="white", font=("Arial", 9, "bold")).pack(pady=8)
        
        lb = tk.Listbox(win, bg="#121212", fg="white", font=("Arial", 8), width=75, height=10)
        lb.pack(padx=10, pady=5)

        for i, el in enumerate(self.elementos_dibujo):
            detalles = f"Tipo: {el['tipo']} [Color: {el.get('color','amarillo')}]"
            seg_ini = el['frame_inicio'] / self.fps
            seg_fin = el['frame_fin'] / self.fps
            desc = f"[{i+1}] {detalles} | Inicio: {int(seg_ini//60):02d}:{int(seg_ini%60):02d} - Fin: {int(seg_fin//60):02d}:{int(seg_fin%60):02d}"
            lb.insert(tk.END, desc)

        frame_duracion = tk.Frame(win, bg="#1e1e1e")
        frame_duracion.pack(pady=5)
        
        tk.Label(frame_duracion, text="Nuevo Fin (Frame):", bg="#1e1e1e", fg="white", font=("Arial", 8)).pack(side=tk.LEFT, padx=5)
        e_fin = tk.Entry(frame_duracion, width=10, font=("Arial", 8))
        e_fin.pack(side=tk.LEFT, padx=5)

        def actualizar_duracion():
            sel = lb.curselection()
            if sel:
                try:
                    self.elementos_dibujo[sel[0]]["frame_fin"] = int(e_fin.get())
                    messagebox.showinfo("Éxito", "Duración actualizada.")
                    win.destroy()
                except ValueError:
                    messagebox.showerror("Error", "Frame inválido.")

        def eliminar_seleccionado():
            sel = lb.curselection()
            if sel:
                elem_borrar = self.elementos_dibujo[sel[0]]
                if self.elemento_seleccionado == elem_borrar:
                    self.elemento_seleccionado = None
                del self.elementos_dibujo[sel[0]]
                win.destroy()
                messagebox.showinfo("Eliminado", "Gráfico borrado con éxito.")

        tk.Button(frame_duracion, text="Actualizar", command=actualizar_duracion, bg="#007acc", fg="white", font=("Arial", 8, "bold"), relief=tk.FLAT).pack(side=tk.LEFT, padx=5)
        tk.Button(win, text="Eliminar Gráfico Seleccionado", command=eliminar_seleccionado, bg="#dc3545", fg="white", font=("Arial", 8, "bold"), pady=4, relief=tk.FLAT).pack(pady=10)

    def registrar_evento_tactico(self, subcategoria, color):
        if not self.cap:
            return
        seg = self.current_frame / self.fps
        m, s = int(seg // 60), int(seg % 60)
        
        evento = {
            "sub": subcategoria,
            "frame": self.current_frame,
            "jugador": self.jugador_seleccionado,
            "color": color
        }
        self.eventos.append(evento)
        
        texto = f"[{m:02d}:{s:02d}] {subcategoria} ({self.jugador_seleccionado})"
        self.lista_eventos.insert(tk.END, texto)
        self.lista_eventos.see(tk.END)
        self.draw_timeline()

    def ir_a_evento(self, event):
        sel = self.lista_eventos.curselection()
        if sel and self.cap:
            with self._lock:
                self.current_frame = self.eventos[sel[0]]["frame"]
                self.cap.set(cv2.CAP_PROP_POS_FRAMES, self.current_frame)

    def draw_timeline(self):
        self.timeline_canvas.delete("all")
        w = self.timeline_canvas.winfo_width()
        if w <= 1 or self.total_frames <= 0:
            return
        for e in self.eventos:
            x = (e["frame"] / self.total_frames) * w
            self.timeline_canvas.create_line(x, 1, x, 15, fill=e["color"], width=3)
        x_act = (self.current_frame / self.total_frames) * w
        self.timeline_canvas.create_line(x_act, 0, x_act, 16, fill="white", width=2)

    def click_timeline(self, event):
        if self.total_frames > 0:
            w = self.timeline_canvas.winfo_width()
            ratio = event.x / w
            with self._lock:
                self.current_frame = int(ratio * self.total_frames)
                if self.cap:
                    self.cap.set(cv2.CAP_PROP_POS_FRAMES, self.current_frame)

    def toggle_play(self):
        if self.cap:
            self.playing = not self.playing
            self.btn_play.config(text=">" if not self.playing else "||")

    def motor_hilo_video(self):
        frame_time = 1.0 / self.fps
        next_frame_time = time.time()

        while getattr(self, 'hilo_activo', True):
            if self.cap and self.cap.isOpened():
                if self.playing:
                    with self._lock:
                        ret, frame = self.cap.read()
                        if ret and frame is not None:
                            self.current_frame = int(self.cap.get(cv2.CAP_PROP_POS_FRAMES))
                            self._ultimo_frame_congelado = frame.copy()
                            self.frame_siguiente_raw = frame
                        else:
                            self.current_frame = 0
                            self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                            next_frame_time = time.time()

                    next_frame_time += frame_time
                    sleep_time = next_frame_time - time.time()
                    if sleep_time > 0:
                        time.sleep(sleep_time)
                    else:
                        next_frame_time = time.time()
                else:
                    with self._lock:
                        self.cap.set(cv2.CAP_PROP_POS_FRAMES, self.current_frame)
                        ret, frame = self.cap.read()
                        if ret and frame is not None:
                            self._ultimo_frame_congelado = frame.copy()
                            self.frame_siguiente_raw = frame
                    next_frame_time = time.time()
                    time.sleep(0.04)
            else:
                time.sleep(0.1)

    def actualizar_interfaz_gui(self):
        if self.frame_siguiente_raw is not None:
            with self._lock:
                frame = self.frame_siguiente_raw.copy()
                self.frame_siguiente_raw = None

            for elem in self.elementos_dibujo:
                if elem["frame_inicio"] <= self.current_frame <= elem["frame_fin"]:
                    es_seleccionado = (elem == self.elemento_seleccionado)
                    self.renderizar_elemento_cv2(frame, elem, seleccionado=es_seleccionado)

            # Previsualización de puntos al marcar triángulos o rombos por clics sucesivos
            if self.puntos_temp_creacion:
                pts_arr = np.array(self.puntos_temp_creacion, np.int32)
                for pt in pts_arr:
                    cv2.circle(frame, tuple(pt), 6, (0, 255, 255), -1, cv2.LINE_AA)
                if len(pts_arr) > 1:
                    for i in range(len(pts_arr) - 1):
                        cv2.line(frame, tuple(pts_arr[i]), tuple(pts_arr[i+1]), (0, 255, 255), 2, cv2.LINE_AA)

            try:
                logo_path = "1001194780.png"
                if os.path.exists(logo_path):
                    logo_img = cv2.imread(logo_path, cv2.IMREAD_UNCHANGED)
                    if logo_img is not None:
                        logo_img = cv2.resize(logo_img, (120, 55), interpolation=cv2.INTER_CUBIC)
                        h_l, w_l, _ = logo_img.shape
                        fh, fw, _ = frame.shape
                        y_offset, x_offset = 15, fw - w_l - 15
                        if logo_img.shape[2] == 4:
                            alpha = logo_img[:, :, 3] / 255.0
                            for c in range(3):
                                frame[y_offset:y_offset+h_l, x_offset:x_offset+w_l, c] = (
                                    alpha * logo_img[:, :, c] + (1 - alpha) * frame[y_offset:y_offset+h_l, x_offset:x_offset+w_l, c]
                                )
                        else:
                            frame[y_offset:y_offset+h_l, x_offset:x_offset+w_l] = logo_img
            except Exception as e:
                pass

            if self.grabando_video and self.video_writer:
                frame_rec = cv2.resize(frame, (1280, 720), interpolation=cv2.INTER_CUBIC)
                self.video_writer.write(frame_rec)

            frame_resized = cv2.resize(frame, (760, 420), interpolation=cv2.INTER_LINEAR)
            self.frame_actual_img = ImageTk.PhotoImage(Image.fromarray(cv2.cvtColor(frame_resized, cv2.COLOR_BGR2RGB)))
            self.video_label.config(image=self.frame_actual_img)
            
            sec = self.current_frame / self.fps if self.fps > 0 else 0
            tot = self.total_frames / self.fps if self.fps > 0 else 1
            t_act = f"{int(sec//60):02d}:{int(sec%60):02d}"
            t_tot = f"{int(tot//60):02d}:{int(tot%60):02d}"
            self.lbl_time.config(text=f"{t_act} / {t_tot}")
            self.draw_timeline()

        if getattr(self, 'hilo_activo', True):
            self.root.after(15, self.actualizar_interfaz_gui)

if __name__ == "__main__":
    root = tk.Tk()
    app = VideoAnalisisReEApp(root)
    root.mainloop()
