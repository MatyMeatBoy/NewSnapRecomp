"""Local desktop launcher. Run with ``python -m newsnap.launcher``."""
from pathlib import Path
from datetime import datetime
import queue
import shutil
import subprocess
import threading
import time
import tkinter as tk
import uuid
from tkinter import filedialog, messagebox, ttk

from . import launcher_settings as settings
from .paths import runtime_dir
from .upstream import ROOT
from .version import VERSION

GREEN, CREAM, AMBER, INK = '#163d32', '#f5f1e5', '#dfa648', '#203c34'
PAGE_SIZE = 12
PRESENTATION_LABELS = {'VSync · FIFO': 'fifo', 'Mailbox': 'mailbox', 'Sin VSync · Immediate': 'immediate',
                       'VSync adaptable · FIFO Relaxed': 'fifo_relaxed'}
PRESENTATION_HELP = ('FIFO: presenta la cola en orden durante el refresco vertical; evita tearing y puede añadir latencia. '
                     'Mailbox: sincroniza con el refresco y reemplaza el fotograma pendiente por el más reciente. '
                     'Immediate: presenta sin esperar al refresco; puede producir tearing. '
                     'FIFO Relaxed: permite tearing si el fotograma llega tarde. '
                     'Si el modo solicitado no está disponible, Vulkan usa FIFO. '
                     'Ningún modo garantiza por sí solo que FreeSync/G-SYNC esté activo.')


class Launcher:
    def __init__(self, root, project=ROOT, check_updates=True):
        from PIL import Image, ImageTk
        self.Image, self.ImageTk = Image, ImageTk
        self.root, self.project = root, Path(project)
        self.ini = runtime_dir(self.project) / 'newsnap.ini'
        self.profile = settings.load_profile(self.project)
        self.profile_text = tk.StringVar(master=root, value=str(self.profile))
        self.events = queue.Queue()
        self.busy = False
        self.diagnostics_running = False
        self._album_loaded = False
        self.controller_test = None
        self.process = None
        self.photos, self.thumbnails = [], []
        self.page, self.album_generation, self.preview_generation = 0, 0, 0
        self.preview = None
        self.root.title(f'NewSnap · {VERSION}')
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
        header = tk.Frame(root, bg=GREEN, padx=24, pady=10)
        header.pack(fill='x')
        tk.Label(header, text='NewSnap', font=('Segoe UI', 24, 'bold'), fg=CREAM, bg=GREEN).pack(anchor='w')
        tk.Label(header, text='NEW POKÉMON SNAP · PORT NATIVO', font=('Segoe UI', 10), fg=AMBER, bg=GREEN).pack(anchor='w')
        self.status = tk.StringVar(value='Carga o verifica los datos del juego para comenzar.')
        ttk.Label(root, textvariable=self.status, style='Status.TLabel', padding=(25, 9)).pack(side='bottom', fill='x')
        self.tabs = ttk.Notebook(root)
        self.tabs.pack(fill='both', expand=True, padx=22, pady=(12, 8))
        self.play_tab, self.album_tab, self.options_tab, self.controls_tab = [ttk.Frame(self.tabs, padding=16) for _ in range(4)]
        for frame, title in zip((self.play_tab, self.album_tab, self.options_tab, self.controls_tab), ('Inicio', 'Álbum', 'Opciones', 'Controles')):
            self.tabs.add(frame, text=title)
        option_pages=ttk.Notebook(self.options_tab);option_pages.pack(fill='both',expand=True)
        self.video_tab,self.audio_tab,self.game_tab=[ttk.Frame(option_pages,padding=8) for _ in range(3)]
        for frame,title in ((self.video_tab,'Vídeo'),(self.audio_tab,'Audio'),(self.game_tab,'Juego')):option_pages.add(frame,text=title)
        self.update_tab = ttk.Frame(self.tabs, padding=16)
        self.tabs.add(self.update_tab, text='Actualizaciones')
        from .home_ui import HomePanel
        self.home=HomePanel(self,self.play_tab)
        self._album()
        self._options()
        from .update_ui import UpdatePanel
        self.updates = UpdatePanel(self, self._scrolling_options(self.update_tab), automatic=check_updates)
        self.tabs.bind('<<NotebookTabChanged>>',self._tab_changed)
        self.root.after(100, self._poll)
        self.album_status.set('Abre el álbum para cargar las fotografías del perfil.')

    def _style(self):
        style = ttk.Style(self.root)
        style.theme_use('clam')
        style.configure('.', font=('Segoe UI', 11), background=CREAM, foreground=INK)
        style.configure('TFrame', background=CREAM)
        style.configure('TNotebook', background=CREAM, borderwidth=0, tabmargins=(0, 0, 0, 0))
        style.configure('TNotebook.Tab', padding=(18, 10), background='#e5e5d9', expand=(0, 0, 0, 0))
        style.map('TNotebook.Tab', background=[('selected', GREEN)], foreground=[('selected', CREAM)],
                  padding=[('selected', (18, 10)), ('!selected', (18, 10))],
                  expand=[('selected', (0, 0, 0, 0)), ('!selected', (0, 0, 0, 0))])
        style.configure('TButton', padding=(15, 9), background='#e5e5d9')
        style.configure('Accent.TButton', background=GREEN, foreground=CREAM, font=('Segoe UI', 13, 'bold'), padding=(25, 14))
        style.map('Accent.TButton', background=[('active', '#245846'), ('disabled', '#84978c')])
        style.configure('Accent.TButton',focuscolor=AMBER,focusthickness=2)
        style.configure('Snap.Horizontal.TProgressbar',background=GREEN,troughcolor='#dedfce',borderwidth=0,thickness=9)
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
        ttk.Button(frame, text='Créditos y licencias gráficas', command=self.show_credits).pack(anchor='w', pady=(20, 4))
        ttk.Label(frame, text='AMD FidelityFX Super Resolution · NVIDIA DLSS',
                  style='Muted.TLabel').pack(anchor='w')

    def show_credits(self):
        window=tk.Toplevel(self.root)
        window.title('NewSnap · Créditos y licencias')
        window.geometry('760x560')
        text=tk.Text(window,wrap='word',padx=16,pady=16)
        bar=ttk.Scrollbar(window,command=text.yview)
        text.configure(yscrollcommand=bar.set)
        bar.pack(side='right',fill='y');text.pack(fill='both',expand=True)
        text.insert('end','NewSnapRecomp · MatyMeatBoy y colaboradores\n\n'
            'Infraestructura y contribuciones bajo MIT; atribuciones completas en las licencias incluidas.\n'
            'AMD FidelityFX Super Resolution, utilizado conforme a las licencias incluidas.\n'
            'NVIDIA DLSS, utilizado bajo la licencia NVIDIA RTX SDKs. NVIDIA y DLSS son marcas de NVIDIA Corporation.\n\n')
        for label,path in (('Licencia NVIDIA DLSS',runtime_dir(self.project)/'licenses/NVIDIA-DLSS.txt'),
                           ('Licencias AMD FSR',runtime_dir(self.project)/'upscalers/license.md')):
            text.insert('end',label+'\n\n')
            if path.is_file():
                with path.open('r',encoding='utf-8',errors='replace') as stream:
                    text.insert('end',stream.read(1<<20)+'\n\n')
            else:
                text.insert('end','Se incluye con el proveedor gráfico correspondiente.\n\n')
        text.configure(state='disabled')

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
        ttk.Label(self.video_tab, text='Vídeo y presentación', style='Title.TLabel').pack(anchor='w', pady=(0, 5))
        ttk.Label(self.video_tab, text='Todos los cambios se aplican al próximo inicio del juego.', style='Muted.TLabel').pack(anchor='w', pady=(0, 10))
        self.save_buttons = []
        actions = ttk.Frame(self.video_tab, padding=(0, 10, 0, 0))
        actions.pack(side='bottom', fill='x')
        save = ttk.Button(actions, text='Guardar ajustes', style='Accent.TButton', command=self.save_options)
        save.pack(side='left')
        self.save_buttons.append(save)
        video = self._scrolling_options(self.video_tab)
        from .graphics_presets import PRESETS, DESCRIPTION, matching_preset
        from .tooltip import Tooltip
        self.quality_preset = tk.StringVar(value=matching_preset(values))
        preset_row = ttk.Frame(video); preset_row.pack(fill='x', pady=9)
        preset_label = ttk.Label(preset_row, text='Preset de calidad gráfica', width=29)
        preset_label.pack(side='left')
        preset = ttk.Combobox(preset_row, textvariable=self.quality_preset,
                             values=(*PRESETS, 'Personalizado'), state='readonly', width=31)
        preset.pack(side='left')
        preset.bind('<<ComboboxSelected>>', self._apply_quality_preset)
        Tooltip(preset_label, DESCRIPTION); Tooltip(preset, DESCRIPTION)
        self._help(video, 'Original · Bajo · Medio · Alto · Ultra. Pasa el ratón para ver los ajustes exactos.')
        self._heading(video, 'Pantalla y presentación')
        fullscreen = ttk.Checkbutton(video, text='Pantalla completa', variable=self.variables['fullscreen'], onvalue='1', offvalue='0')
        fullscreen.pack(anchor='w', pady=(5, 10))
        Tooltip(fullscreen, 'Solicita pantalla completa al runtime. No cambia la resolución interna ni garantiza VRR o modo exclusivo del controlador.')
        self._choice(video, 'Tamaño de ventana', 'window_size', ('1280x720', '1600x900', '1920x1080', '2560x1440', '3440x1440', '3840x2160'), editable=True,
                     help_text='Admite un tamaño propio como 2560x1080. Cambia la ventana, no la resolución interna ni la salida nativa.')
        self._choice(video, 'Salida nativa del juego', 'operation_mode', {'TV · 1920 × 1080': 'docked', 'Portátil · 1280 × 720': 'handheld'},
                     help_text='El modo TV produce una salida de 1080p; el modo portátil, 720p. Una ventana 4K no convierte la salida nativa en 4K.')
        self._choice(video, 'Límite de FPS · Frame cap', 'fps', {'30 FPS': '30', '60 FPS': '60'},
                     help_text='30 y 60 FPS son los límites disponibles. Más de 60 FPS sigue en investigación.')
        self.presentation = tk.StringVar(value=next(label for label, value in PRESENTATION_LABELS.items() if value == values['vk_present']))
        row = ttk.Frame(video)
        row.pack(fill='x', pady=9)
        present_label = ttk.Label(row, text='Modo de presentación Vulkan', width=29)
        present_label.pack(side='left')
        present_choice = ttk.Combobox(row, textvariable=self.presentation, values=tuple(PRESENTATION_LABELS), state='readonly', width=31)
        present_choice.pack(side='left')
        Tooltip(present_label, PRESENTATION_HELP); Tooltip(present_choice, PRESENTATION_HELP)
        self._help(video, 'FIFO / Mailbox / Immediate / FIFO Relaxed. El modo efectivo y VRR se comprueban durante el juego.')
        self._help(video, 'La frecuencia variable depende de la pantalla y el controlador. Su presentación se comprueba durante la expedición.')
        from .display_ui import DisplayPanel
        self.display=DisplayPanel(self,video)
        self._choice(video, 'Overlay de rendimiento', 'perf_overlay', {'Oculta': 'off', 'Solo FPS': 'fps', 'Completa': 'full'},
                     help_text='Muestra datos del runtime. La vista completa incluye tiempos de CPU/GPU y actividad de compilación cuando están disponibles.')
        self._heading(video, 'Resolución y reconstrucción')
        self._choice(video, 'Reconstrucción temporal · FSR/DLSS', 'upscaling', {
            'Original': 'off', 'Automática': 'auto', 'AMD FSR 3.1': 'fsr3',
            'AMD FSR 4 · GPU compatible': 'fsr4', 'NVIDIA DLSS · RTX': 'dlss'},
            help_text='Reconstruye la escena antes del HUD. La disponibilidad depende del proveedor y del controlador; una opción no disponible conserva una alternativa compatible. FSR 4 selecciona automáticamente el modelo compatible, incluido INT8 en RX 6000/7000.')
        self._choice(video, 'Preset de reconstrucción', 'upscaling_quality', {
            'Nativo · antialiasing': 'native', 'Calidad · escena 70 %': 'quality',
            'Equilibrado · escena 60 %': 'balanced', 'Rendimiento · escena 50 %': 'performance'},
            help_text='Cada proveedor usa su propio algoritmo con el preset elegido. Las escalas corresponden a los niveles reales del motor de Snap; requieren reiniciar la expedición.')
        self._choice(video, 'Escala interna de la escena', 'render_scale', {'Según el juego': 'game', **{f'{n} %': str(n) for n in (50, 60, 70, 80, 90, 100)},
                     '1,25× (125 %) · experimental': '125', '1,5× (150 %) · experimental': '150', '2× (200 %) · experimental': '200'},
                     choice_width=31,
                     help_text='Hasta el 100 %, una escala menor favorece el rendimiento y pierde detalle; el HUD conserva su resolución de salida. 125 %, 150 % y 200 % son supersampling experimental exclusivo del modo TV: aumentan el detalle y el coste de GPU. Para modo portátil elige 100 % o menos; guardar una combinación incompatible muestra un error sin cambiar tu elección.')
        self._choice(video, 'Filtrado anisotrópico · AF', 'aniso', {'Según el juego': 'game', **{f'{n}×': str(n) for n in (2, 4, 8, 16)}, 'Automático heredado': 'auto'},
                     help_text='Mejora las texturas vistas en ángulo. El controlador y la GPU pueden limitar el nivel efectivo. Automático heredado conserva la heurística de la base, aún sin validar para Snap; elige un nivel explícito para personalizarlo.')
        self._choice(video, 'Relación de aspecto · Aspect ratio', 'aspect', {'Conservar proporciones': 'fit', 'Estirar a la ventana': 'stretch'},
                     help_text='Solo cambia la presentación: conservar proporciones puede dejar bandas; estirar llena la ventana y deforma la imagen. No amplía el campo de visión.')
        self._heading(video, 'Color original del juego')
        self._help(video, 'Salida neutra: conserva los colores y el posprocesado propios de Snap. '
                   'Sin perfiles de contraste, saturación, gamma, HDR añadido ni nitidez adicional del port.')
        self._audio_options()
        self._game_options()
        self._control_options()
        for key in ('render_scale', 'aniso', 'upscaling'):
            self.variables[key].trace_add('write', self._quality_preset_changed)

    def _apply_quality_preset(self, event=None):
        from .graphics_presets import PRESETS, apply_preset
        name = self.quality_preset.get()
        if name in PRESETS:
            self._set_option_values(apply_preset(self._option_values(), name))

    def _quality_preset_changed(self, *args):
        if not self.syncing_options:
            from .graphics_presets import matching_preset
            self.quality_preset.set(matching_preset({key: value.get() for key, value in self.variables.items()}))

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
        self._choice(content, 'Prebuffer de audio · ms', 'audio_prefill_ms', None,
                     help_text='De 0 a 500 ms; valor inicial 20. El audio espera esta cantidad al iniciar o recuperarse de un corte, redondeada a bloques de 5 ms. Un valor mayor puede ayudar con cortes y también añade latencia.')

    def _game_options(self):
        ttk.Label(self.game_tab, text='Tu expedición', style='Title.TLabel').pack(anchor='w')
        self._settings_footer(self.game_tab)
        content = self._scrolling_options(self.game_tab)
        profile = ttk.LabelFrame(content, text='Perfil y guardados', padding=12)
        profile.pack(fill='x', pady=(0, 12))
        self.profile_label = ttk.Label(profile, textvariable=self.profile_text,
                                      wraplength=700, style='Muted.TLabel')
        self.profile_label.pack(anchor='w', pady=4)
        self.profile_button = ttk.Button(profile, text='Elegir perfil…', command=self.choose_profile)
        self.profile_button.pack(anchor='w', pady=4)
        from .tooltip import Tooltip
        self.diagnostics_button = ttk.Button(content, text='Exportar diagnóstico…', command=self.export_diagnostics)
        self.diagnostics_button.pack(anchor='w', pady=(0, 12))
        Tooltip(self.diagnostics_button, 'Crea un ZIP local con identidad del launcher/runtime, ajustes conocidos, logs recientes y observaciones de pantalla. No incluye fotos, partidas, claves ni archivos del juego; no envía nada por Internet.')
        self.trace_present=tk.BooleanVar(master=self.root,value=False)
        self.trace_present_button=ttk.Checkbutton(content,text='Traza de presentación Vulkan · diagnóstico',
            variable=self.trace_present)
        self.trace_present_button.pack(anchor='w',pady=(0,12))
        Tooltip(self.trace_present_button,'Añade tiempos separados de adquisición de imagen, espera de fence, presentación y recreación del swapchain al próximo inicio. No cambia VSync, VRR ni el límite de FPS. Se desactiva al cerrar el launcher; el registro puede afectar a las mediciones. Inclúyelo con Exportar diagnóstico.')
        self._help(content, 'Los cambios se aplican al próximo inicio. Estos ajustes conservan tu perfil y sus guardados.')
        languages = {'Según el sistema': '', 'Español · España': 'es', 'Español · Latinoamérica': 'es-419',
                     'English · US': 'en-US', 'English · UK': 'en-GB', 'Français': 'fr', 'Français · Canada': 'fr-CA',
                     'Deutsch': 'de', 'Italiano': 'it', 'Português': 'pt', 'Português · Brasil': 'pt-BR',
                     '日本語': 'ja', '한국어': 'ko', 'Nederlands': 'nl', 'Русский': 'ru',
                     '中文 · 简体': 'zh-Hans', '中文 · 繁體': 'zh-Hant', '中文 · China': 'zh-CN', '中文 · Taiwan': 'zh-TW'}
        languages = {label: code for label, code in languages.items() if code in settings.LANGUAGES}
        self._choice(content, 'Idioma solicitado al juego', 'lang', languages,
                     help_text='Ofrece los idiomas declarados por Snap. El juego conserva su propia elección de texto y voces; si un perfil sigue en otro idioma, cámbialo también en sus ajustes de idioma.')

    def _control_options(self):
        self.controller_test_button=ttk.Button(self.controls_tab,text='Probar mando conectado…',command=self.show_controller_test)
        self.controller_test_button.pack(anchor='w',pady=(0,10))
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
        motion = ttk.Checkbutton(general, text='Giroscopio · controles de movimiento', variable=self.variables['motion'], onvalue='1', offvalue='0')
        motion.pack(anchor='w', pady=10)
        from .tooltip import Tooltip
        Tooltip(motion, 'Habilita la entrada de movimiento/giroscopio cuando el mando y su controlador la proporcionan. Desactívalo si prefieres apuntar solo con ratón o sticks.')
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
        triggers = ttk.Checkbutton(general, text='Vibración de gatillos · Trigger Rumble', variable=self.variables['rumble_triggers'], onvalue='1', offvalue='0')
        triggers.pack(anchor='w', pady=10)
        Tooltip(triggers, self._control_tooltip('rumble_triggers'))
        self._help(bindings, 'Edita listas separadas por comas: key:mouse_l, key:e, pad:south. Las teclas y los nombres físicos del mando se distinguen con key: y pad:. La edición se valida al guardar; el texto previo se conserva hasta que lo cambies.')
        self._help(bindings, 'key:default y pad:default conservan las asignaciones originales de esa acción. Vacío restaura ambos; none por sí solo deja la acción sin entradas. Las direcciones de los sticks aceptan únicamente teclas.')
        ttk.Button(bindings, text='Ver teclas y botones admitidos', command=self.show_binding_names).pack(anchor='w', pady=(0, 12))
        for key in settings.BINDING_DEFAULTS:
            name = key.removeprefix('bind_').upper().replace('LSTICK_', 'Stick izq. · ').replace('RSTICK_', 'Stick der. · ')
            self._choice(bindings, 'A · Foto / confirmar' if key == 'bind_a' else name, key, None)

    def export_diagnostics(self):
        if self.diagnostics_running:
            return
        destination = filedialog.asksaveasfilename(parent=self.root, title='Exportar diagnóstico de NewSnap',
            defaultextension='.zip', filetypes=[('Diagnóstico ZIP', '*.zip')],
            initialfile=f'NewSnap-diagnostico-{datetime.now():%Y%m%d-%H%M%S}-{uuid.uuid4().hex[:6]}.zip')
        if not destination:
            return
        self.diagnostics_running = True
        self.diagnostics_button.configure(state='disabled')
        self.status.set('Recopilando diagnóstico local…')
        def work():
            try:
                from .diagnostics import export_diagnostics
                output = export_diagnostics(self.project, destination)
                self.events.put(('diagnostics_done', str(output), None))
            except Exception as error:
                self.events.put(('diagnostics_done', None, str(error)))
        threading.Thread(target=work, daemon=True).start()

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
        caption = ttk.Label(row, text=label, width=29, wraplength=250)
        caption.pack(side='left')
        variable = self.variables[key]
        if isinstance(choices, dict):
            variable = tk.StringVar(value=next(label for label, value in choices.items() if value == variable.get()))
            self.labeled_choices[key] = variable, choices
        widget = (ttk.Combobox(row, textvariable=variable, values=tuple(choices), state='normal' if editable else 'readonly', width=choice_width)
                  if choices else ttk.Entry(row, textvariable=variable, width=28))
        widget.pack(side='left')
        from .tooltip import Tooltip
        tooltip = help_text or self._control_tooltip(key)
        Tooltip(caption, tooltip); Tooltip(widget, tooltip)
        if isinstance(choices, dict):
            def selected(event):
                self.variables[key].set(choices[variable.get()])
                if changed:
                    changed()
            widget.bind('<<ComboboxSelected>>', selected)
        if help_text:
            self._help(frame, help_text)

    @staticmethod
    def _control_tooltip(key):
        if key in settings.BINDING_DEFAULTS:
            if key.startswith(('bind_lstick_', 'bind_rstick_')):
                return ('Asigna una tecla a esta dirección del stick de Switch: key:<tecla>. '
                        'key:default conserva la asignación original; none la desactiva. '
                        'Estas direcciones solo aceptan teclas, no pad:<botón>.')
            return ('Asigna la entrada a este botón/eje de Switch. Usa key:<tecla> o pad:<botón>, separados por comas. '
                    'pad:default conserva el mando original; none desactiva la asignación. Vacío restaura los valores originales.')
        return {
            'mouse_sens': 'Multiplicador de sensibilidad de la cámara con ratón, de 0 a 10; 1 conserva la sensibilidad base.',
            'stick_deadzone': 'Porcentaje de recorrido ignorado alrededor del centro de ambos sticks. 0–50 %. Un valor mayor reduce drift y pierde respuesta cerca del centro.',
            'lstick_deadzone': 'Zona muerta del stick izquierdo, 0–50 %. Vacío hereda la zona muerta común.',
            'rstick_deadzone': 'Zona muerta del stick derecho, 0–50 %. Vacío hereda la zona muerta común.',
            'rumble_strength': 'Ganancia de vibración del mando, 0–300 %. 0 la desactiva. La intensidad efectiva depende del dispositivo.',
            'rumble_curve': 'Exponente de respuesta de vibración, de 0,2 a 1,5. Cambia la relación entre intensidades débiles y fuertes.',
            'rumble_triggers': 'Permite vibración de gatillos si el dispositivo y el controlador la soportan.',
        }.get(key, 'Se aplica al próximo inicio del juego; guarda los ajustes para conservar el cambio.')

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
        values.update(settings.NEUTRAL_SETTINGS)
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
        if hasattr(self, 'quality_preset'):
            self._quality_preset_changed()

    def reload_options(self):
        try:
            current = settings.load_settings(self.ini)
            merged = settings.merge_settings(self.baseline, self._option_values(), current)
            self.baseline = dict(current)
            self._set_option_values(merged)
        except (OSError, ValueError) as error:
            messagebox.showerror('No se pudieron actualizar los ajustes', str(error), parent=self.root)

    def choose_profile(self):
        if self.busy:return
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
            self._album_loaded=False

    def _tab_changed(self,event=None):
        if self.tabs.select()==str(self.album_tab) and not self.busy and not self._album_loaded:self.refresh_album()

    def notify_update(self,release):
        self.home.notify_update(release)

    def show_controller_test(self):
        if self.busy:return
        from .controller_ui import ControllerTest
        try:settings.validate_runtime_data(self.project)
        except (OSError,ValueError) as error:
            self.status.set(str(error));return
        self.controller_test=ControllerTest(self)

    def _set_busy(self, busy):
        self.busy = busy
        for widget in [self.play_button, self.profile_button, *self.save_buttons]:
            widget.configure(state='disabled' if busy else 'normal')
        if hasattr(self,'home'):self.home.set_busy(busy)
        if hasattr(self,'controller_test_button'):self.controller_test_button.configure(state='disabled' if busy else 'normal')
        if hasattr(self,'trace_present_button'):self.trace_present_button.configure(state='disabled' if busy else 'normal')

    def launch(self):
        if self.busy:
            return
        data=self.home.refresh()
        if not data['loaded']:
            self.home.choose_data();return
        if not data['verified']:
            self.home.verify(resume_game=True);return
        try:
            options=self._option_values()
            settings.validate_settings(options);settings.validate_video_combination(options)
        except ValueError as error:
            self.status.set(str(error));return
        profile = self.profile
        self._session_diagnostic_env=({'AC_SNAP_PRESENT_TRACE':'1'} if self.trace_present.get() else {})
        required = settings.shader_preparation_required(self.project)
        command = settings.preparation_command(self.project) if self.prepare.get() or required else None
        self._set_busy(True)
        self.status.set('Comprobando el runtime antes de la expedición…')
        threading.Thread(target=self._run_game, args=(profile, command, options), daemon=True).start()

    def _run_game(self, profile, preparation, options=None):
        deferred=False
        try:
            with settings.ProfileLock(profile):
                from .maintenance import assess_runtime
                if settings.is_release_layout(self.project) and assess_runtime(self.project)['needs_rebuild']:
                    deferred=True
                    self.events.put(('maintenance_needed',None));return
                if settings.shader_preparation_required(self.project) and preparation is None:
                    # A rebuilt/first-run installation need not have recordings
                    # yet. Live shader compilation is a valid native boot path;
                    # retain the pending marker instead of inventing a receipt.
                    self.events.put(('preparation_fallback',
                        'Primer inicio sin registros: los shaders se compilarán durante el juego.'))
                if options is not None:
                    saved=settings.save_edited_settings(self.ini,self.baseline,options)
                    self.events.put(('settings_saved',saved))
                self._execute_game(profile, preparation)
            error = None
        except (OSError, RuntimeError,ValueError) as failure:
            error = str(failure)
        finally:
            self.process = None
        if not deferred:self.events.put(('finished', error))

    def _execute_game(self, profile, preparation):
        logdir = runtime_dir(self.project) / 'logs'
        logdir.mkdir(parents=True, exist_ok=True)
        session = datetime.now().strftime('%Y%m%d-%H%M%S') + '-' + uuid.uuid4().hex[:8]
        env = settings.game_environment(root=self.project)
        env.pop('AC_SNAP_PRESENT_TRACE',None)
        env.update(getattr(self,'_session_diagnostic_env',{}))
        hidden = subprocess.CREATE_NO_WINDOW if hasattr(subprocess, 'CREATE_NO_WINDOW') else 0
        if preparation:
            self.events.put(('progress','Preparando shaders y pipelines para esta GPU…'))
            logfile = logdir / f'launcher-prepare-{session}.log'
            with logfile.open('x', encoding='utf-8') as log:
                self.process = subprocess.Popen(preparation, cwd=self.project, env=env, stdout=log, stderr=subprocess.STDOUT, creationflags=hidden)
                code = self.process.wait()
            if code:
                raise RuntimeError(f'La preparación no terminó correctamente. Revisa {logfile}.')
            settings.clear_shader_preparation_required(self.project)
        logfile = None
        def run_attempt(attempt):
            nonlocal logfile
            logfile = logdir / f'launcher-game-{session}-{attempt:03d}.log'
            display_file=logdir/f'launcher-display-{session}-{attempt:03d}.json'
            env['NEWSNAP_DISPLAY_STATUS']=str(display_file.resolve())
            command=settings.game_command(self.project, profile)
            from .session_log import runtime_identity, write_record
            with logfile.open('x', encoding='utf-8') as log:
                write_record(log,'start',attempt=attempt,runtime=runtime_identity(command[0]),
                             requested_present_mode=env.get('AC_VK_PRESENT','runtime-default'))
                started_at=time.time()
                self.process = subprocess.Popen(command, cwd=self.project, env=env, stdout=log, stderr=subprocess.STDOUT, creationflags=hidden)
                self.events.put(('status', 'Reiniciando expedición…' if attempt > 1 else 'Expedición en curso · cierra el juego para volver'))
                self.events.put(('game_started',None))
                self.events.put(('display_file',display_file,self.process.pid,started_at))
                code=self.process.wait()
                write_record(log,'exit',exit_code=code)
                return code
        code = settings.supervise_game(run_attempt)
        if code:
            raise RuntimeError(settings.game_failure_message(code, logfile))

    def refresh_album(self):
        self._album_loaded=True
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
                elif kind == 'progress':
                    self.home.progress.report(event[1])
                elif kind == 'game_started':
                    self.home.progress.finish('Juego iniciado')
                elif kind == 'preparation_fallback':
                    self.status.set(event[1])
                    if hasattr(self.home,'show_preparation_note'):
                        self.home.show_preparation_note(event[1])
                elif kind == 'diagnostics_done':
                    self.diagnostics_running = False
                    self.diagnostics_button.configure(state='normal')
                    self.status.set('Diagnóstico exportado: '+event[1] if event[1] else 'No se pudo exportar el diagnóstico: '+event[2])
                elif kind == 'settings_saved':
                    self.baseline=dict(event[1]);self._set_option_values(event[1])
                elif kind == 'maintenance_needed':
                    self._set_busy(False)
                    self.updates.maintenance.start(resume_game=True)
                elif kind == 'display_file':
                    self.display.observe(*event[1:])
                elif kind == 'finished':
                    self._set_busy(False)
                    self.reload_options()
                    self.status.set('Listo para explorar' if event[1] is None else 'La expedición se detuvo')
                    if event[1]:
                        self.home.progress.finish('No se pudo iniciar o continuar el juego',error=True)
                        messagebox.showerror('No se pudo completar el inicio', event[1], parent=self.root)
                    else:
                        self.home.progress.finish('Juego cerrado · listo para iniciar otra expedición')
                    self._album_loaded=False
                    self.display.stop();self.home.refresh();self._tab_changed()
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
        if self.diagnostics_running:
            messagebox.showinfo('Diagnóstico en curso', 'Espera a que termine la exportación del diagnóstico.', parent=self.root)
            return
        if self.busy:
            messagebox.showinfo('Operación en curso', 'Espera a que termine la preparación o actualización, o cierra la ventana del juego antes de cerrar el launcher.', parent=self.root)
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
