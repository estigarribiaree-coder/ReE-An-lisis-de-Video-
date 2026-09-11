import os
import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog
from PIL import Image, ImageTk
import cv2
import numpy as np

class ReEAnalisisVideoApp:
    def __init__(self, root):
        self.root = root
        self.root.title("ReE Análisis de Video v1.1")
        self.root.geometry("1280=720".replace('=', 'x'))
        self.root.config(bg="#1e1e1e")

        # Variables de video y estado
        self.video_path = None
        self.cap = None
        self.total_frames = 0
        self.fps = 30.0
        self.current_frame = 0
        self.is_playing = False
        self.ancho_original = 1280
        self.alto_original = 720
        
        # Elementos tácticos y herramientas
        self.elementos_tacticos = [] # Lista de diccionarios con anotaciones
        self.herramienta_activa = "ninguno" # 'foco_jugador', 'linea_defensiva_pts', 'triangulo_pts', 'rombo_pts', etc.
        self.puntos_temp_creacion = []
        self.elemento_seleccionado_idx = None
        
        # Plantel de jugadores por defecto
        self.plantel = [f"Jugador {i}" for i in range(1, 12)]
        self.jugador_seleccionado = "Jugador 1"

        # Interfaz inicial (Splash / Menú Principal)
        self.crear_pantalla_bienvenida()

    def crear_pantalla_bienvenida(self):
        self.limpiar_ventana()
        
        frame_welcome = tk.Frame(self.root, bg="#1e1e1e")
        frame_welcome.pack(expand=True, fill=tk.BOTH)

        lbl_titulo = tk.Label(frame_welcome, text="ReE Análisis de Video", fg="white", bg="#1e1e1e", font=("Arial", 24, "bold"))
        lbl_titulo.pack(pady=40)

        btn_cargar = tk.Button(frame_welcome, text="Cargar Video Táctico", command=self.cargar_video_dialogo, bg="#27ae60", fg="white", font=("Arial", 12, "bold"), padx=20, pady=10, relief=tk.FLAT)
        btn_cargar.pack(pady=10)

        btn_salir = tk.Button(frame_welcome, text="Salir", command=self.root.quit, bg="#c0392b", fg="white", font=("Arial", 10), padx=10, pady=5, relief=tk.FLAT)
        btn_salir.pack(pady=20)

    def limpiar_ventana(self):
        for widget in self.root.winfo_children():
            widget.destroy()

    def cargar_video_dialogo(self):
        file_path = filedialog.askopenfilename(title="Seleccionar Video Táctico", filetypes=[("Archivos de Video", "*.mp4 *.avi *.mov *.mkv")])
        if file_path:
            self.video_path = file_path
            self.inicializar_motor_video()
            self.iniciar_interfaz_trabajo()

    def inicializar_motor_video(self):
        if self.cap:
            self.cap.release()
        self.cap = cv2.VideoCapture(self.video_path)
        self.total_frames = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
        self.fps = self.cap.get(cv2.CAP_PROP_FPS)
        if self.fps <= 0:
            self.fps = 30.0
        self.ancho_original = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        self.alto_original = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        self.current_frame = 0

    def iniciar_interfaz_trabajo(self):
        self.limpiar_ventana()

        # Layout Principal
        self.top_bar = tk.Frame(self.root, bg="#2c3e50", height=40)
        self.top_bar.pack(side=tk.TOP, fill=tk.X)

        self.canvas_container = tk.Frame(self.root, bg="black")
        self.canvas_container.pack(side=tk.TOP, expand=True, fill=tk.BOTH)

        self.canvas_video = tk.Canvas(self.canvas_container, bg="black", cursor="cross")
        self.canvas_video.pack(expand=True, fill=tk.BOTH)
        self.canvas_video.bind("<Button-1>", self.clic_en_video)
        self.canvas_video.bind("<Button-3>", self.clic_derecho_en_video)

        self.bottom_bar = tk.Frame(self.root, bg="#2c3e50", height=60)
        self.bottom_bar.pack(side=tk.BOTTOM, fill=tk.X)

        # --- Controles Barra Superior (Herramientas Tácticas) ---
        tk.Button(self.top_bar, text="Volver Menú", command=self.crear_pantalla_bienvenida, bg="#7f8c8d", fg="white", font=("Arial", 8, "bold"), relief=tk.FLAT).pack(side=tk.LEFT, padx=5, pady=5)
        
        tools_overlay = tk.Frame(self.top_bar, bg="#2c3e50")
        tools_overlay.pack(side=tk.LEFT, padx=10)

        tk.Button(tools_overlay, text="Foco Jugador", command=lambda: self.activar_herramienta("foco_jugador"), bg="#f39c12", fg="white", font=("Arial", 7, "bold"), relief=tk.FLAT).pack(side=tk.LEFT, padx=2)
        tk.Button(tools_overlay, text="Línea Defensiva (Pts)", command=lambda: self.activar_herramienta("linea_defensiva_pts"), bg="#e74c3c", fg="white", font=("Arial", 7, "bold"), relief=tk.FLAT).pack(side=tk.LEFT, padx=2)
        tk.Button(tools_overlay, text="Triángulo", command=lambda: self.activar_herramienta("triangulo_pts"), bg="#3498db", fg="white", font=("Arial", 7, "bold"), relief=tk.FLAT).pack(side=tk.LEFT, padx=2)
        tk.Button(tools_overlay, text="Rombo", command=lambda: self.activar_herramienta("rombo_pts"), bg="#9b59b6", fg="white", font=("Arial", 7, "bold"), relief=tk.FLAT).pack(side=tk.LEFT, padx=2)
        tk.Button(tools_overlay, text="Borrar Todo", command=self.borrar_todos_elementos, bg="#c0392b", fg="white", font=("Arial", 7, "bold"), relief=tk.FLAT).pack(side=tk.LEFT, padx=10)

        # --- Controles Barra Inferior (Timeline y Reproducción) ---
        self.btn_play = tk.Button(self.bottom_bar, text="▶ Play", command=self.toggle_play, bg="#27ae60", fg="white", font=("Arial", 9, "bold"), relief=tk.FLAT, width=8)
        self.btn_play.pack(side=tk.LEFT, padx=10, pady=15)

        self.slider_timeline = tk.Scale(self.bottom_bar, from_=0, to=max(1, self.total_frames - 1), orient=tk.HORIZONTAL, command=self.on_slider_move, bg="#2c3e50", fg="white", highlightbackground="#2c3e50", troughcolor="#1a252f")
        self.slider_timeline.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=10)

        self.lbl_tiempo = tk.Label(self.bottom_bar, text="00:00 / 00:00", bg="#2c3e50", fg="white", font=("Arial", 9))
        self.lbl_tiempo.pack(side=tk.RIGHT, padx=15)

        # Iniciar bucle de actualización visual
        self.actualizar_frame_actual()

    def activar_herramienta(self, herramienta):
        self.herramienta_activa = herramienta
        self.puntos_temp_creacion = []
        messagebox.showinfo("Herramienta Activa", f"Herramienta seleccionada: {herramienta.upper().replace('_', ' ')}")

    def toggle_play(self):
        self.is_playing = not self.is_playing
        if self.is_playing:
            self.btn_play.config(text="❚❚ Pause", bg="#e67e22")
            self.reproducir_video()
        else:
            self.btn_play.config(text="▶ Play", bg="#27ae60")

    def reproducir_video(self):
        if self.is_playing and self.cap:
            if self.current_frame < self.total_frames - 1:
                self.current_frame += 1
                self.slider_timeline.set(self.current_frame)
                self.actualizar_frame_actual()
                delay = int(1000 / self.fps)
                self.root.after(delay, self.reproducir_video)
            else:
                self.is_playing = False
                self.btn_play.config(text="▶ Play", bg="#27ae60")

    def on_slider_move(self, val):
        if not self.is_playing and self.cap:
            self.current_frame = int(val)
            self.actualizar_frame_actual()

    def actualizar_frame_actual(self):
        if not self.cap:
            return
        self.cap.set(cv2.CAP_PROP_POS_FRAMES, self.current_frame)
        ret, frame = self.cap.read()
        if not ret:
            return

        # Renderizar elementos tácticos activos en este frame
        frame = self.renderizar_elementos_en_frame(frame)

        # Convertir frame de OpenCV (BGR) a formato compatible con Tkinter (RGB/ImageTk)
        cv_img = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h_canvas = self.canvas_video.winfo_height()
        w_canvas = self.canvas_video.winfo_width()

        if h_canvas > 10 and w_canvas > 10:
            # Mantener relación de aspecto
            img_pil = Image.fromarray(cv_img)
            img_pil = img_pil.resize((w_canvas, h_canvas), Image.Resampling.LANCZOS)
            self.photo_img = ImageTk.PhotoImage(image=img_pil)
            self.canvas_video.delete("all")
            self.canvas_video.create_image(0, 0, anchor=tk.NW, image=self.photo_img)

        # Previsualización de puntos activos durante creación con clics sucesivos
        if self.puntos_temp_creacion and h_canvas > 10:
            scale_x = w_canvas / self.ancho_original
            scale_y = h_canvas / self.alto_original
            for pt in self.puntos_temp_creacion:
                cx_w, cy_w = int(pt[0] * scale_x), int(pt[1] * scale_y)
                self.canvas_video.create_oval(cx_w-4, cy_w-4, cx_w+4, cy_w+4, fill="#00ffff", outline="black")

        # Actualizar etiqueta de tiempo
        seg_actual = int(self.current_frame / self.fps)
        seg_total = int(self.total_frames / self.fps)
        self.lbl_tiempo.config(text=f"{seg_actual//60:02d}:{seg_actual%60:02d} / {seg_total//60:02d}:{seg_total%60:02d}")

    def convertir_coordenadas_widget_a_video(self, wx, wy):
        w_canvas = self.canvas_video.winfo_width()
        h_canvas = self.canvas_video.winfo_height()
        if w_canvas <= 0 or h_canvas <= 0:
            return wx, wy
        vx = int(wx * (self.ancho_original / w_canvas))
        vy = int(wy * (self.alto_original / h_canvas))
        return vx, vy

    def clic_en_video(self, event):
        if not self.cap:
            return
        vx, vy = self.convertir_coordenadas_widget_a_video(event.x, event.y)

        # Creación de Línea Defensiva por puntos múltiples
        if self.herramienta_activa == "linea_defensiva_pts":
            self.puntos_temp_creacion.append([vx, vy])
            self.actualizar_frame_actual()
            return

        # Creación por clics sucesivos (Triángulos / Rombos)
        if self.herramienta_activa in ["triangulo_pts", "rombo_pts"]:
            self.puntos_temp_creacion.append([vx, vy])
            target_pts = 3 if self.herramienta_activa == "triangulo_pts" else 4
            if len(self.puntos_temp_creacion) == target_pts:
                elem = {
                    "tipo": "poligono_custom",
                    "puntos": list(self.puntos_temp_creacion),
                    "modo": "normal",
                    "color": "amarillo",
                    "frame_inicio": self.current_frame,
                    "frame_fin": self.current_frame + int(self.fps * 5)
                }
                self.puntos_temp_creacion = []
                self.solicitar_duracion_nuevo_elemento(elem)
                self.herramienta_activa = "ninguno"
            self.actualizar_frame_actual()
            return

        # Creación de Foco Moderno de Jugador
        if self.herramienta_activa == "foco_jugador":
            elem = {
                "tipo": "foco_jugador",
                "x1": vx, "y1": vy,
                "x2": vx + 45, "y2": vy + 45,
                "texto": self.jugador_seleccionado,
                "color": "amarillo",
                "opacidad_sombra": 0.3,
                "frame_inicio": self.current_frame,
                "frame_fin": self.current_frame + int(self.fps * 5)
            }
            self.solicitar_duracion_nuevo_elemento(elem)
            self.herramienta_activa = "ninguno"
            self.actualizar_frame_actual()
            return

    def clic_derecho_en_video(self, event):
        if not self.cap:
            return
        
        # Finalizar Línea Defensiva con Clic Derecho si hay al menos 2 puntos
        if self.herramienta_activa == "linea_defensiva_pts" and len(self.puntos_temp_creacion) >= 2:
            elem = {
                "tipo": "linea_defensiva",
                "puntos": list(self.puntos_temp_creacion),
                "color": "amarillo",
                "frame_inicio": self.current_frame,
                "frame_fin": self.current_frame + int(self.fps * 5)
            }
            self.puntos_temp_creacion = []
            self.herramienta_activa = "ninguno"
            self.solicitar_duracion_nuevo_elemento(elem)
            self.actualizar_frame_actual()
            return

        if self.puntos_temp_creacion:
            self.puntos_temp_creacion = []
            self.herramienta_activa = "ninguno"
            self.actualizar_frame_actual()

    def solicitar_duracion_nuevo_elemento(self, elem):
        self.elementos_tacticos.append(elem)
        self.actualizar_frame_actual()

    def renderizar_elementos_en_frame(self, frame):
        for elem in self.elementos_tacticos:
            if elem["frame_inicio"] <= self.current_frame <= elem["frame_fin"]:
                frame = self.renderizar_elemento_cv2(frame, elem)
        return frame

    def renderizar_elemento_cv2(self, frame, elem):
        tipo = elem["tipo"]
        color_map = {
            "amarillo": (0, 255, 255),
            "rojo": (0, 0, 255),
            "azul": (255, 0, 0),
            "blanco": (255, 255, 255)
        }
        col = color_map.get(elem.get("color", "amarillo"), (0, 255, 255))

        if tipo == "foco_jugador":
            cx, cy = int(elem["x1"]), int(elem["y1"])
            r = int(max(20, np.hypot(elem["x2"] - cx, elem["y2"] - cy)))
            alpha_val = float(elem.get("opacidad_sombra", 0.3))
            
            # Círculo semitransparente estilo foco moderno
            overlay = frame.copy()
            cv2.circle(overlay, (cx, cy), r, col, -1)
            cv2.addWeighted(overlay, alpha_val, frame, 1.0 - alpha_val, 0, frame)
            cv2.circle(frame, (cx, cy), r, col, 2, cv2.LINE_AA)
            cv2.circle(frame, (cx, cy), r + 6, col, 1, cv2.LINE_AA)
            
            # Etiqueta flotante editable con nombre
            nombre = elem.get("texto", "Jugador")
            if nombre:
                (tw, th), _ = cv2.getTextSize(nombre, cv2.FONT_HERSHEY_SIMPLEX, 0.55, 1)
                tag_x = cx - (tw // 2)
                tag_y = cy - r - 10
                cv2.rectangle(frame, (tag_x - 6, tag_y - th - 6), (tag_x + tw + 6, tag_y + 6), (20, 20, 20), -1, cv2.LINE_AA)
                cv2.rectangle(frame, (tag_x - 6, tag_y - th - 6), (tag_x + tw + 6, tag_y + 6), col, 1, cv2.LINE_AA)
                cv2.putText(frame, nombre, (tag_x, tag_y), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 255), 1, cv2.LINE_AA)

        elif tipo == "linea_defensiva":
            pts = np.array(elem["puntos"], np.int32)
            if len(pts) > 1:
                cv2.polylines(frame, [pts], isClosed=False, color=col, thickness=2, lineType=cv2.LINE_AA)
                for i, pt in enumerate(pts):
                    cv2.circle(frame, tuple(pt), 6, col, -1, cv2.LINE_AA)
                    cv2.putText(frame, f"J{i+1}", (pt[0] + 6, pt[1] - 6), cv2.FONT_HERSHEY_SIMPLEX, 0.5, col, 1, cv2.LINE_AA)

        elif tipo == "poligono_custom":
            pts = np.array(elem["puntos"], np.int32)
            if len(pts) >= 3:
                cv2.polylines(frame, [pts], isClosed=True, color=col, thickness=2, lineType=cv2.LINE_AA)

        return frame

    def borrar_todos_elementos(self):
        self.elementos_tacticos = []
        self.puntos_temp_creacion = []
        self.actualizar_frame_actual()

if __name__ == "__main__":
    root = tk.Tk()
    app = ReE Análisis de Video si fuera necesario o se mantiene como ReEAnalisisVideoApp
    app = ReEAnalisisVideoApp(root)
    root.mainloop()
