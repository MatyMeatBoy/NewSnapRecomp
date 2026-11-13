"""Local desktop launcher. Run with ``python -m newsnap.launcher``."""
from pathlib import Path
from datetime import datetime
import queue
import shutil
import subprocess
import threading
import tkinter as tk
import uuid
from tkinter import filedialog, messagebox, ttk

from . import launcher_settings as settings
from .paths import runtime_dir
from .upstream import ROOT

GREEN, CREAM, AMBER, INK = '#163d32', '#f5f1e5', '#dfa648', '#203c34'
PAGE_SIZE = 12
PRESENTATION_LABELS = {'Sincronizado': 'fifo', 'Fluido': 'mailbox', 'Sin sincronizar': 'immediate',
                       'Sincronizado adaptable': 'fifo_relaxed'}


class Launcher:
    def __init__(self, root, project=ROOT):
        from PIL import Image, ImageTk
        self.Image, self.ImageTk = Image, ImageTk
        self.root, self.project = root, Path(project)
        self.ini = runtime_dir(self.project) / 'astralchain.ini'
        self.profile = settings.load_profile(self.project)
        self.events = queue.Queue()
        self.busy = False
        self.process = None
        self.photos, self.thumbnails = [], []
        self.page, self.album_generation, self.preview_generation = 0, 0, 0
        self.preview = None
        self.root.title('NewSnap · 0.2 alpha · Cámara y álbum')
        self.root.geometry('1020x790')
        self.root.minsize(860, 730)
        self.root.configure(bg=CREAM)
        self.root.protocol('WM_DELETE_WINDOW', self.close)
        self._style()
        icon = self.project / 'assets/icons/newsnap.ico'
        if icon.is_file():
            try:
                self.root.iconbitmap(str(icon))
            except tk.TclError:
                pass
        header = tk.Frame(root, bg=GREEN, padx=28, pady=15)
        header.pack(fill='x')
        tk.Label(header, text='NewSnap', font=('Segoe UI', 27, 'bold'), fg=CREAM, bg=GREEN).pack(anchor='w')
        tk.Label(header, text='TU PRÓXIMA EXPEDICIÓN EMPIEZA AQUÍ', font=('Segoe UI', 10), fg=AMBER, bg=GREEN).pack(anchor='w')
        self.status = tk.StringVar(value='Listo para explorar')
        ttk.Label(root, textvariable=self.status, style='Status.TLabel', padding=(25, 9)).pack(side='bottom', fill='x')
        self.tabs = ttk.Notebook(root)
        self.tabs.pack(fill='both', expand=True, padx=22, pady=(12, 8))
        self.play_tab, self.album_tab, self.video_tab, self.audio_tab, self.game_tab, self.controls_tab = [ttk.Frame(self.tabs, padding=16) for _ in range(6)]
        for frame, title in zip((self.play_tab, self.album_tab, self.video_tab, self.audio_tab, self.game_tab, self.controls_tab), ('Jugar', 'Álbum', 'Vídeo', 'Audio', 'Juego', 'Controles')):
            self.tabs.add(frame, text=title)
        self._play()
        self._album()
        self._options()
        self.root.after(100, self._poll)
        self.refresh_album()

    def _style(self):
        style = ttk.Style(self.root)
        style.theme_use('clam')
        style.configure('.', font=('Segoe UI', 11), background=CREAM, foreground=INK)
        style.configure('TFrame', background=CREAM)
        style.configure('TNotebook', background=CREAM, borderwidth=0, tabmargins=(0, 0, 0, 0))
        style.configure('TNotebook.Tab', padding=(24, 10), background='#e5e5d9', expand=(0, 0, 0, 0))
        style.map('TNotebook.Tab', background=[('selected', GREEN)], foreground=[('selected', CREAM)],
                  padding=[('selected', (24, 10)), ('!selected', (24, 10))],
                  expand=[('selected', (0, 0, 0, 0)), ('!selected', (0, 0, 0, 0))])
        style.configure('TButton', padding=(15, 9), background='#e5e5d9')
        style.configure('Accent.TButton', background=GREEN, foreground=CREAM, font=('Segoe UI', 13, 'bold'), padding=(25, 14))
        style.map('Accent.TButton', background=[('active', '#245846'), ('disabled', '#84978c')])
        style.configure('Title.TLabel', font=('Segoe UI', 20, 'bold'))
        style.configure('Muted.TLabel', foreground='#597067')
        style.configure('Status.TLabel', background='#e5e5d9', font=('Segoe UI', 10))

    def _play(self):
        frame = self.play_tab
        hero = ttk.Frame(frame)
        hero.pack(fill='x', pady=(3, 22))
        icon_path = self.project / 'assets/icons/icon-128.png'
        if icon_path.is_file():
            with self.Image.open(icon_path) as image:
                self.hero_icon = self.ImageTk.PhotoImage(image.copy(), master=self.root)
            ttk.Label(hero, image=self.hero_icon).pack(side='right', padx=(18, 0))
        copy = ttk.Frame(hero)
        copy.pack(side='left', fill='both', expand=True)
        ttk.Label(copy, text='Una cámara.\nUn mundo por descubrir.', style='Title.TLabel').pack(anchor='w', pady=(3, 10))
        ttk.Label(copy, text='Continúa tu expedición con tu perfil local.\nTus fotografías te esperan en el álbum.',
                  style='Muted.TLabel', wraplength=560, justify='left').pack(anchor='w')
        ttk.Label(frame, text='PERFIL LOCAL', font=('Segoe UI', 9, 'bold')).pack(anchor='w')
        self.profile_text = tk.StringVar(value=str(self.profile))
        ttk.Label(frame, textvariable=self.profile_text, wraplength=770, style='Muted.TLabel').pack(anchor='w', pady=(7, 10))
        self.profile_button = ttk.Button(frame, text='Elegir perfil…', command=self.choose_profile)
        self.profile_button.pack(anchor='w')
        self.prepare = tk.BooleanVar(value=True)
        ttk.Checkbutton(frame, text='Preparar gráficos antes de jugar', variable=self.prepare).pack(anchor='w', pady=(18, 5))
        ttk.Label(frame, text='La primera preparación puede tardar. Algunas escenas pueden necesitar preparación adicional.',
                  wraplength=760, style='Muted.TLabel').pack(anchor='w')
        self.play_button = ttk.Button(frame, text='Iniciar expedición  →', style='Accent.TButton', command=self.launch)
        self.play_button.pack(anchor='w', pady=(17, 0))

    def _album(self):
        bar = ttk.Frame(self.album_tab)
        bar.pack(fill='x')
        ttk.Label(bar, text='Tu álbum', style='Title.TLabel').pack(side='left')
        self.refresh_button = ttk.Button(bar, text='Actualizar', command=self.refresh_album)
        self.refresh_button.pack(side='right')
        self.album_status = tk.StringVar(value='Buscando fotografías…')
        ttk.Label(self.album_tab, textvariable=self.album_status, style='Muted.TLabel', wraplength=800).pack(anchor='w', pady=(7, 12))
        self.grid = ttk.Frame(self.album_tab)
        for column in range(4):
            self.grid.columnconfigure(column, weight=1)
        navigation = ttk.Frame(self.album_tab)
        navigation.pack(side='bottom', fill='x', pady=(12, 0))
        self.grid.pack(fill='both', expand=True)
        self.previous = ttk.Button(navigation, text='← Anterior', command=lambda: self.change_page(-1))
        self.previous.pack(side='left')
        self.page_label = ttk.Label(navigation, text='')
        self.page_label.pack(side='left', padx=22)
        self.next = ttk.Button(navigation, text='Siguiente →', command=lambda: self.change_page(1))
        self.next.pack(side='right')

    def _options(self):
        values = settings.load_settings(self.ini)
        self.baseline = dict(values)
        self.syncing_options = False
        self.labeled_choices = {}
        self.variables = {key: tk.StringVar(value=value) for key, value in values.items()}
        ttk.Label(self.video_tab, text='Prepara tu pantalla', style='Title.TLabel').pack(anchor='w', pady=(0, 5))
        ttk.Label(self.video_tab, text='Todos los cambios se aplican al próximo inicio del juego.', style='Muted.TLabel').pack(anchor='w', pady=(0, 10))
        self.save_buttons = []
        actions = ttk.Frame(self.video_tab, padding=(0, 10, 0, 0))
        actions.pack(side='bottom', fill='x')
        save = ttk.Button(actions, text='Guardar ajustes', style='Accent.TButton', command=self.save_options)
        save.pack(side='left')
        self.save_buttons.append(save)
        sections = ttk.Notebook(self.video_tab)
        sections.pack(fill='both', expand=True)
        basic_tab, advanced_tab = ttk.Frame(sections), ttk.Frame(sections)
        sections.add(basic_tab, text='Básico')
        sections.add(advanced_tab, text='Avanzado')
        basic, advanced = self._scrolling_options(basic_tab), self._scrolling_options(advanced_tab)
        ttk.Checkbutton(basic, text='Pantalla completa', variable=self.variables['fullscreen'], onvalue='1', offvalue='0').pack(anchor='w', pady=(5, 10))
        self._choice(basic, 'Tamaño de ventana', 'window_size', ('1280x720', '1600x900', '1920x1080', '2560x1440', '3440x1440', '3840x2160'), editable=True,
                     help_text='Admite un tamaño propio como 2560x1080. Cambia la ventana, no la resolución interna ni la salida nativa.')
        self._choice(basic, 'Salida nativa del juego', 'operation_mode', {'TV · 1920 × 1080': 'docked', 'Portátil · 1280 × 720': 'handheld'},
                     help_text='El modo TV produce una salida de 1080p; el modo portátil, 720p. Una ventana 4K no convierte la salida nativa en 4K.')
        self._choice(basic, 'Límite de fotogramas', 'fps', {'30 FPS': '30', '60 FPS': '60'},
                     help_text='30 y 60 FPS son los límites disponibles. Más de 60 FPS sigue en investigación.')
        self.presentation = tk.StringVar(value=next(label for label, value in PRESENTATION_LABELS.items() if value == values['vk_present']))
        row = ttk.Frame(basic)
        row.pack(fill='x', pady=9)
        ttk.Label(row, text='Sincronización de imagen', width=29).pack(side='left')
        ttk.Combobox(row, textvariable=self.presentation, values=tuple(PRESENTATION_LABELS), state='readonly', width=25).pack(side='left')
        self._help(basic, 'Sincronizado evita cortes; Fluido prioriza respuesta. Sin sincronizar puede mostrar cortes. Adaptable permite cortes al caer por debajo del refresco; si no está disponible, el juego usa sincronización normal.')
        self._help(basic, 'La frecuencia variable (VRR, FreeSync o G-SYNC) depende del monitor, Windows y el controlador. Este launcher no ofrece un interruptor VRR comprobado.')
        self._choice(basic, 'Información de rendimiento', 'perf_overlay', {'Oculta': 'off', 'Solo FPS': 'fps', 'Completa': 'full'},
                     help_text='Muestra datos del runtime. La vista completa incluye tiempos de CPU/GPU y actividad de compilación cuando están disponibles.')
        self._heading(advanced, 'Resolución y reconstrucción')
        self._choice(advanced, 'Escala interna de la escena', 'render_scale', {'Según el juego': 'game', **{f'{n} %': str(n) for n in (50, 60, 70, 80, 90, 100)},
                     '1,25× (125 %) · experimental': '125', '1,5× (150 %) · experimental': '150', '2× (200 %) · experimental': '200'},
                     choice_width=31,
                     help_text='Hasta el 100 %, una escala menor favorece el rendimiento y pierde detalle; el HUD conserva su resolución de salida. 125 %, 150 % y 200 % son supersampling experimental exclusivo del modo TV: aumentan el detalle y el coste de GPU. Para modo portátil elige 100 % o menos; guardar una combinación incompatible muestra un error sin cambiar tu elección.')
        self._choice(advanced, 'Ampliación final de imagen', 'upscaler', {'FSR espacial': 'fsr', 'Bilineal': 'bilinear'},
                     help_text='Amplía la imagen completa hasta el tamaño de ventana, incluido el HUD. FSR es espacial; no equivale a DLSS ni a generación de fotogramas.')
        self._choice(advanced, 'Nitidez FSR · 0 a 100', 'sharpness', None,
                     help_text='Aumenta la definición del filtro FSR. Solo actúa cuando eliges FSR espacial; valores altos pueden acentuar bordes.')
        self._choice(advanced, 'Filtrado de texturas', 'aniso', {'Según el juego': 'game', **{f'{n}×': str(n) for n in (2, 4, 8, 16)}, 'Automático heredado': 'auto'},
                     help_text='Mejora las texturas vistas en ángulo. El controlador y la GPU pueden limitar el nivel efectivo. Automático heredado conserva la heurística de la base, aún sin validar para Snap; elige un nivel explícito para personalizarlo.')
        self._choice(advanced, 'Encaje en la ventana', 'aspect', {'Conservar proporciones': 'fit', 'Estirar a la ventana': 'stretch'},
                     help_text='Solo cambia la presentación: conservar proporciones puede dejar bandas; estirar llena la ventana y deforma la imagen. No amplía el campo de visión.')
        self._heading(advanced, 'Color de la imagen')
        self._choice(advanced, 'Perfil de color', 'color_preset', {'Original': 'default', 'Vívido': 'vivid', 'Claridad': 'clarity', 'Personalizado': 'custom'},
                     changed=self._select_color_preset,
                     help_text='Los perfiles aplican brillo, contraste, saturación y gamma reales. Los cambios de color también afectan al HUD del juego.')
        for label, key in (('Brillo · −30 a 30', 'color_brightness'), ('Contraste · 70 a 150', 'color_contrast'),
                           ('Saturación · 50 a 200', 'color_saturation'), ('Gamma · 0.8 a 1.2', 'color_gamma')):
            self._choice(advanced, label, key, None)
            self.variables[key].trace_add('write', self._custom_color)
        self._audio_options()
        self._game_options()
        self._control_options()

    def _settings_footer(self, frame, *, controls=False):
        footer = ttk.Frame(frame, padding=(0, 10, 0, 0))
        footer.pack(side='bottom', fill='x')
        button = ttk.Button(footer, text='Guardar ajustes', style='Accent.TButton', command=self.save_options)
        button.pack(side='left')
        self.save_buttons.append(button)
        if controls:
            ttk.Button(footer, text='Restaurar controles', command=self.reset_controls).pack(side='right')

    def _audio_options(self):
        ttk.Label(self.audio_tab, text='Escucha la expedición', style='Title.TLabel').pack(anchor='w')
        self._settings_footer(self.audio_tab)
        content = self._scrolling_options(self.audio_tab)
        self._help(content, 'Los cambios se aplican al próximo inicio. El runtime dispone de un volumen general para toda la mezcla del juego.')
        self._choice(content, 'Volumen general · 0 a 100', 'volume', None,
                     help_text='0 silencia la salida. No se ofrecen controles separados de música y efectos porque el runtime no los separa.')
        self._heading(content, 'Avanzado · Estabilidad del audio')
        self._choice(content, 'Cola inicial de audio · ms', 'audio_prefill_ms', None,
                     help_text='De 0 a 500 ms; valor inicial 20. El audio espera esta cantidad al iniciar o recuperarse de un corte, redondeada a bloques de 5 ms. Un valor mayor puede ayudar con cortes y también añade latencia.')

    def _game_options(self):
        ttk.Label(self.game_tab, text='Tu expedición', style='Title.TLabel').pack(anchor='w')
        self._settings_footer(self.game_tab)
        content = self._scrolling_options(self.game_tab)
        self._help(content, 'Los cambios se aplican al próximo inicio. Estos ajustes conservan tu perfil y sus guardados.')
        languages = {'Según el sistema': '', 'Español · España': 'es', 'Español · Latinoamérica': 'es-419',
                     'English · US': 'en-US', 'English · UK': 'en-GB', 'Français': 'fr', 'Français · Canada': 'fr-CA',
                     'Deutsch': 'de', 'Italiano': 'it', 'Português': 'pt', 'Português · Brasil': 'pt-BR',
                     '日本語': 'ja', '한국어': 'ko', 'Nederlands': 'nl', 'Русский': 'ru',
                     '中文 · 简体': 'zh-Hans', '中文 · 繁體': 'zh-Hant', '中文 · China': 'zh-CN', '中文 · Taiwan': 'zh-TW'}
        self._choice(content, 'Idioma solicitado al juego', 'lang', languages,
                     help_text='El juego utiliza las traducciones incluidas en sus datos. Si una variante no está disponible, su elección final depende del propio juego.')

    def _control_options(self):
        ttk.Label(self.controls_tab, text='Encuentra tu encuadre', style='Title.TLabel').pack(anchor='w', pady=(0, 8))
        self._settings_footer(self.controls_tab, controls=True)
        sections = ttk.Notebook(self.controls_tab)
        sections.pack(fill='both', expand=True)
        general_tab, bindings_tab = ttk.Frame(sections), ttk.Frame(sections)
        sections.add(general_tab, text='Ratón y mando')
        sections.add(bindings_tab, text='Asignaciones')
        general, bindings = self._scrolling_options(general_tab), self._scrolling_options(bindings_tab)
        self._help(general, 'Los cambios se aplican al próximo inicio. El ratón conserva la puntería libre de la cámara.')
        self._choice(general, 'Sensibilidad del ratón · 0 a 10', 'mouse_sens', None)
        self._choice(general, 'Distribución del mando', 'pad_layout', {'Automática': 'auto', 'Nintendo': 'nintendo', 'Xbox': 'xbox', 'PlayStation': 'playstation'},
                     help_text='Cambia cómo se interpretan los botones físicos. Los dibujos de botones del juego conservan su aspecto original.')
        ttk.Checkbutton(general, text='Activar controles de movimiento', variable=self.variables['motion'], onvalue='1', offvalue='0').pack(anchor='w', pady=10)
        self._help(general, 'Utiliza los sensores de movimiento si el mando, su conexión y el controlador los proporcionan.')
        self._heading(general, 'Zona muerta de los sticks')
        self._choice(general, 'Zona muerta común · 0 a 50 %', 'stick_deadzone', None)
        self._choice(general, 'Stick izquierdo · 0 a 50 %', 'lstick_deadzone', None)
        self._choice(general, 'Stick derecho · 0 a 50 %', 'rstick_deadzone', None,
                     help_text='Un campo de stick vacío hereda la zona muerta común. Aumenta el valor si el stick se mueve solo en reposo.')
        self._heading(general, 'Vibración')
        self._choice(general, 'Intensidad · 0 a 300 %', 'rumble_strength', None,
                     help_text='0 desactiva la vibración. La respuesta depende del mando y de los efectos enviados por el juego.')
        self._choice(general, 'Curva de vibración · 0.2 a 1.5', 'rumble_curve', None,
                     help_text='Ajusta cómo se amplifican los efectos débiles respecto de los fuertes. El valor inicial de la base es 0.6.')
        ttk.Checkbutton(general, text='Vibración en los gatillos compatibles', variable=self.variables['rumble_triggers'], onvalue='1', offvalue='0').pack(anchor='w', pady=10)
        self._help(bindings, 'Edita listas separadas por comas: key:mouse_l, key:e, pad:south. Las teclas y los nombres físicos del mando se distinguen con key: y pad:. La edición se valida al guardar; el texto previo se conserva hasta que lo cambies.')
        self._help(bindings, 'key:default y pad:default conservan las asignaciones originales de esa acción. Vacío restaura ambos; none por sí solo deja la acción sin entradas. Las direcciones de los sticks aceptan únicamente teclas.')
        ttk.Button(bindings, text='Ver teclas y botones admitidos', command=self.show_binding_names).pack(anchor='w', pady=(0, 12))
        for key in settings.BINDING_DEFAULTS:
            name = key.removeprefix('bind_').upper().replace('LSTICK_', 'Stick izq. · ').replace('RSTICK_', 'Stick der. · ')
            self._choice(bindings, 'A · Foto / confirmar' if key == 'bind_a' else name, key, None)

    def reset_controls(self):
        values = self._option_values()
        values.update(settings.CONTROL_DEFAULTS)
        self._set_option_values(values)
        self.status.set('Controles originales preparados · guarda los ajustes para aplicarlos al próximo inicio')

    def show_binding_names(self):
        messagebox.showinfo('Nombres para las asignaciones',
            'TECLADO Y RATÓN · key:<nombre>\n' + ', '.join(sorted(settings.BINDING_KEYS)) +
            '\n\nMANDO · pad:<nombre>\n' + ', '.join(sorted(settings.BINDING_PADS)) +
            '\n\nF1, F8, F10, F11 y Escape están reservadas por el runtime.', parent=self.root)

    def _scrolling_options(self, parent):
        canvas = tk.Canvas(parent, bg=CREAM, highlightthickness=0, borderwidth=0)
        scrollbar = ttk.Scrollbar(parent, orient='vertical', command=canvas.yview)
        scrollbar.pack(side='right', fill='y')
        canvas.pack(side='left', fill='both', expand=True)
        canvas.configure(yscrollcommand=scrollbar.set)
        content = ttk.Frame(canvas, padding=(5, 8, 15, 15))
        window = canvas.create_window(0, 0, window=content, anchor='nw')
        content.bind('<Configure>', lambda event: canvas.configure(scrollregion=canvas.bbox('all')))
        canvas.bind('<Configure>', lambda event: canvas.itemconfigure(window, width=event.width))
        def wheel(event):
            if canvas.winfo_ismapped() and str(event.widget).startswith(str(canvas)):
                canvas.yview_scroll(-1 if event.delta > 0 else 1, 'units')
                return 'break'
        self.root.bind_all('<MouseWheel>', wheel, add='+')
        return content

    def _help(self, frame, text):
        label = ttk.Label(frame, text=text, style='Muted.TLabel', wraplength=680, justify='left')
        label.pack(anchor='w', fill='x', pady=(0, 12))
        label.bind('<Configure>', lambda event: label.configure(wraplength=max(200, event.width)))

    def _heading(self, frame, title):
        ttk.Label(frame, text=title, font=('Segoe UI', 13, 'bold')).pack(anchor='w', pady=(8, 12))

    def _choice(self, frame, label, key, choices, *, editable=False, help_text=None, changed=None, choice_width=25):
        row = ttk.Frame(frame)
        row.pack(fill='x', pady=(7, 9))
        ttk.Label(row, text=label, width=29).pack(side='left')
        variable = self.variables[key]
        if isinstance(choices, dict):
            variable = tk.StringVar(value=next(label for label, value in choices.items() if value == variable.get()))
            self.labeled_choices[key] = variable, choices
        widget = (ttk.Combobox(row, textvariable=variable, values=tuple(choices), state='normal' if editable else 'readonly', width=choice_width)
                  if choices else ttk.Entry(row, textvariable=variable, width=28))
        widget.pack(side='left')
        if isinstance(choices, dict):
            def selected(event):
                self.variables[key].set(choices[variable.get()])
                if changed:
                    changed()
            widget.bind('<<ComboboxSelected>>', selected)
        if help_text:
            self._help(frame, help_text)

    def _select_color_preset(self):
        preset = self.variables['color_preset'].get()
        if preset in settings.COLOR_PRESETS:
            self.syncing_options = True
            try:
                for key, value in settings.COLOR_PRESETS[preset].items():
                    self.variables[key].set(value)
            finally:
                self.syncing_options = False

    def _custom_color(self, *args):
        if not self.syncing_options:
            self.variables['color_preset'].set('custom')
            self.labeled_choices['color_preset'][0].set('Personalizado')

    def save_options(self):
        if self.busy:
            return False
        try:
            settings.validate_runtime_data(self.project)
            current = settings.save_edited_settings(self.ini, self.baseline, self._option_values())
            self.baseline = dict(current)
            self._set_option_values(current)
            self.status.set('Ajustes guardados para el próximo inicio')
            return True
        except (OSError, ValueError) as error:
            messagebox.showerror('No se pudieron guardar los ajustes', str(error), parent=self.root)
            return False

    def _option_values(self):
        values = {key: value.get() for key, value in self.variables.items()}
        values['vk_present'] = PRESENTATION_LABELS[self.presentation.get()]
        return values

    def _set_option_values(self, values):
        self.syncing_options = True
        try:
            for key, variable in self.variables.items():
                variable.set(values[key])
            for key, (variable, choices) in self.labeled_choices.items():
                variable.set(next(label for label, value in choices.items() if value == values[key]))
            self.presentation.set(next(label for label, value in PRESENTATION_LABELS.items()
                                       if value == values['vk_present']))
        finally:
            self.syncing_options = False

    def reload_options(self):
        try:
            current = settings.load_settings(self.ini)
            merged = settings.merge_settings(self.baseline, self._option_values(), current)
            self.baseline = dict(current)
            self._set_option_values(merged)
        except (OSError, ValueError) as error:
            messagebox.showerror('No se pudieron actualizar los ajustes', str(error), parent=self.root)

    def choose_profile(self):
        folder = filedialog.askdirectory(parent=self.root, title='Elegir perfil local', initialdir=str(self.profile.parent))
        if folder:
            try:
                settings.save_profile(self.project, Path(folder))
            except OSError as error:
                messagebox.showerror('No se pudo recordar el perfil', str(error), parent=self.root)
                return
            self.profile = Path(folder)
            self.profile_text.set(str(self.profile))
            self.photos, self.page = [], 0
            if self.preview and self.preview.winfo_exists():
                self.preview.destroy()
            self.draw_page()
            self.refresh_album()

    def _set_busy(self, busy):
        self.busy = busy
        for widget in [self.play_button, self.profile_button, *self.save_buttons]:
            widget.configure(state='disabled' if busy else 'normal')

    def launch(self):
        if self.busy:
            return
        if not (runtime_dir(self.project) / 'newsnap.exe').is_file():
            messagebox.showerror('Faltan tus datos del juego', 'Copia tu carpeta GameData junto a NewSnapLauncher.exe antes de iniciar.', parent=self.root)
            return
        if not self.save_options():
            return
        profile = self.profile
        command = settings.preparation_command(self.project) if self.prepare.get() else None
        self._set_busy(True)
        self.status.set('Preparando gráficos…' if command else 'Iniciando expedición…')
        threading.Thread(target=self._run_game, args=(profile, command), daemon=True).start()

    def _run_game(self, profile, preparation):
        try:
            with settings.ProfileLock(profile):
                self._execute_game(profile, preparation)
            error = None
        except (OSError, RuntimeError) as failure:
            error = str(failure)
        finally:
            self.process = None
        self.events.put(('finished', error))

    def _execute_game(self, profile, preparation):
        logdir = runtime_dir(self.project) / 'logs'
        logdir.mkdir(parents=True, exist_ok=True)
        session = datetime.now().strftime('%Y%m%d-%H%M%S') + '-' + uuid.uuid4().hex[:8]
        env = settings.game_environment(root=self.project)
        hidden = subprocess.CREATE_NO_WINDOW if hasattr(subprocess, 'CREATE_NO_WINDOW') else 0
        if preparation:
            logfile = logdir / f'launcher-prepare-{session}.log'
            with logfile.open('x', encoding='utf-8') as log:
                self.process = subprocess.Popen(preparation, cwd=self.project, env=env, stdout=log, stderr=subprocess.STDOUT, creationflags=hidden)
                code = self.process.wait()
            if code:
                raise RuntimeError(f'La preparación no terminó correctamente. Revisa {logfile}.')
        logfile = None
        def run_attempt(attempt):
            nonlocal logfile
            self.events.put(('status', 'Reiniciando expedición…' if attempt > 1 else 'Expedición en curso · cierra el juego para volver'))
            logfile = logdir / f'launcher-game-{session}-{attempt:03d}.log'
            with logfile.open('x', encoding='utf-8') as log:
                self.process = subprocess.Popen(settings.game_command(self.project, profile), cwd=self.project, env=env, stdout=log, stderr=subprocess.STDOUT, creationflags=hidden)
                return self.process.wait()
        code = settings.supervise_game(run_attempt)
        if code:
            raise RuntimeError(settings.game_failure_message(code, logfile))

    def refresh_album(self):
        self.album_generation += 1
        generation, profile = self.album_generation, self.profile
        self.album_status.set('Buscando fotografías reales en el perfil…')
        self.refresh_button.configure(state='disabled')
        def scan():
            try:
                from .photos import scan_photos
                with settings.ProfileLock(profile):
                    photos = scan_photos(profile, runtime_dir(self.project) / 'launcher-cache/photos')
                self.events.put(('photos', generation, photos, None))
            except settings.ProfileInUseError:
                self.events.put(('album_locked', generation))
            except Exception as error:
                self.events.put(('photos', generation, [], str(error)))
        threading.Thread(target=scan, daemon=True).start()

    def change_page(self, direction):
        self.page = max(0, min(self.page + direction, max(0, (len(self.photos) - 1) // PAGE_SIZE)))
        self.draw_page()

    def draw_page(self):
        self.thumbnails.clear()
        for widget in self.grid.winfo_children():
            widget.destroy()
        total = max(1, (len(self.photos) + PAGE_SIZE - 1) // PAGE_SIZE)
        self.page_label.configure(text=f'{self.page + 1} / {total}' if self.photos else '')
        self.previous.configure(state='normal' if self.page > 0 else 'disabled')
        self.next.configure(state='normal' if self.page + 1 < total else 'disabled')
        generation, page = self.album_generation, self.page
        selected = self.photos[page * PAGE_SIZE:(page + 1) * PAGE_SIZE]
        if not selected:
            ttk.Label(self.grid, text='Aún no hay fotos para mostrar.\nLas capturas de diagnóstico no forman parte del álbum.', justify='center', style='Muted.TLabel').grid(row=0, column=0, columnspan=4, pady=65)
        for offset, photo in enumerate(selected):
            tile = ttk.Frame(self.grid, padding=4)
            tile.grid(row=offset // 4, column=offset % 4, sticky='nsew')
            index = page * PAGE_SIZE + offset
            button = ttk.Button(tile, text=f'Foto {index + 1}\nCargando…', command=lambda i=index: self.open_preview(i))
            button.pack(fill='both', expand=True)
            ttk.Label(tile, text=f'{photo.width} × {photo.height}', style='Muted.TLabel', anchor='center').pack(fill='x')
        def thumbnails():
            for offset, photo in enumerate(selected):
                try:
                    with self.Image.open(photo.path) as original:
                        original.thumbnail((170, 96))
                        image = original.convert('RGB').copy()
                    self.events.put(('thumb', generation, page, offset, image))
                except (OSError, ValueError):
                    self.events.put(('thumb', generation, page, offset, None))
        threading.Thread(target=thumbnails, daemon=True).start()

    def open_preview(self, index):
        if self.preview and self.preview.winfo_exists():
            self.preview.destroy()
        self.preview = tk.Toplevel(self.root)
        self.preview.title('Álbum · Vista de fotografía')
        self.preview.geometry('950x700')
        self.preview.configure(bg=GREEN)
        self.preview_image = tk.Label(self.preview, bg=GREEN, fg=CREAM)
        self.preview_image.pack(fill='both', expand=True, padx=14, pady=14)
        self.preview_caption = ttk.Label(self.preview, anchor='center', padding=10)
        self.preview_caption.pack(fill='x')
        bar = ttk.Frame(self.preview, padding=12)
        bar.pack(fill='x')
        self.preview_prev = ttk.Button(bar, text='← Anterior', command=lambda: self.show_preview(self.preview_index - 1))
        self.preview_prev.pack(side='left')
        ttk.Button(bar, text='Exportar fotografía…', command=self.export_photo).pack(side='right')
        self.preview_next = ttk.Button(bar, text='Siguiente →', command=lambda: self.show_preview(self.preview_index + 1))
        self.preview_next.pack(side='right', padx=12)
        self.preview.bind('<Left>', lambda event: self.show_preview(self.preview_index - 1))
        self.preview.bind('<Right>', lambda event: self.show_preview(self.preview_index + 1))
        self.show_preview(index)

    def show_preview(self, index):
        if not 0 <= index < len(self.photos):
            return
        self.preview_index = index
        photo = self.photos[index]
        self.preview_generation += 1
        generation = self.preview_generation
        self.preview_image.configure(image='', text='Abriendo fotografía…')
        self.preview_caption.configure(text=f'Foto {index + 1} de {len(self.photos)} · {photo.width} × {photo.height} · {photo.source}')
        self.preview_prev.configure(state='normal' if index else 'disabled')
        self.preview_next.configure(state='normal' if index + 1 < len(self.photos) else 'disabled')
        def decode():
            try:
                with self.Image.open(photo.path) as original:
                    original.thumbnail((900, 540))
                    image = original.convert('RGB').copy()
                self.events.put(('preview', generation, image))
            except (OSError, ValueError):
                self.events.put(('preview', generation, None))
        threading.Thread(target=decode, daemon=True).start()

    def export_photo(self):
        photo = self.photos[self.preview_index]
        target = filedialog.asksaveasfilename(parent=self.preview, title='Exportar fotografía', initialfile=f'foto-{self.preview_index + 1}{photo.path.suffix}', defaultextension=photo.path.suffix, filetypes=[('Imagen original', '*' + photo.path.suffix)])
        if target:
            try:
                if Path(target).resolve() != photo.path.resolve():
                    shutil.copyfile(photo.path, target)
                self.status.set('Fotografía exportada')
            except OSError as error:
                messagebox.showerror('No se pudo exportar', str(error), parent=self.preview)

    def _poll(self):
        try:
            while True:
                event = self.events.get_nowait()
                kind = event[0]
                if kind == 'status':
                    self.status.set(event[1])
                elif kind == 'finished':
                    self._set_busy(False)
                    self.reload_options()
                    self.status.set('Listo para explorar' if event[1] is None else 'La expedición se detuvo')
                    if event[1]:
                        messagebox.showerror('No se pudo completar el inicio', event[1], parent=self.root)
                    self.refresh_album()
                elif kind == 'album_locked' and event[1] == self.album_generation:
                    self.refresh_button.configure(state='normal')
                    self.album_status.set('Cierra la expedición para actualizar el álbum. Puedes seguir viendo las fotografías ya cargadas.')
                elif kind == 'photos' and event[1] == self.album_generation:
                    self.photos, error = event[2:]
                    self.page = 0
                    self.refresh_button.configure(state='normal')
                    self.album_status.set(f'No se pudo leer el álbum: {error}' if error else f'{len(self.photos)} fotografías · archivos locales, sin modificar guardados')
                    if self.preview and self.preview.winfo_exists():
                        self.preview.destroy()
                    self.draw_page()
                elif kind == 'thumb' and event[1:3] == (self.album_generation, self.page):
                    tile = self.grid.winfo_children()[event[3]]
                    button = tile.winfo_children()[0]
                    if event[4] is None:
                        button.configure(text='No se pudo abrir')
                    else:
                        image = self.ImageTk.PhotoImage(event[4], master=self.root)
                        self.thumbnails.append(image)
                        button.configure(image=image, text='')
                elif kind == 'preview' and event[1] == self.preview_generation and self.preview and self.preview.winfo_exists():
                    if event[2] is None:
                        self.preview_image.configure(text='No se pudo abrir esta fotografía.')
                    else:
                        self.full_image = self.ImageTk.PhotoImage(event[2], master=self.preview)
                        self.preview_image.configure(image=self.full_image, text='')
        except queue.Empty:
            pass
        self.root.after(100, self._poll)

    def close(self):
        if self.busy:
            messagebox.showinfo('Expedición en curso', 'Espera a que termine la preparación o cierra la ventana del juego antes de cerrar el launcher.', parent=self.root)
            return
        self.root.destroy()


def main():
    root = tk.Tk()
    try:
        Launcher(root)
    except ImportError:
        messagebox.showerror('Falta Pillow', 'Instala las dependencias con python -m pip install -r requirements.txt.', parent=root)
        root.destroy()
        return
    root.mainloop()


if __name__ == '__main__':
    main()
