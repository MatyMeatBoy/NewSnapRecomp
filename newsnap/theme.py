"""The launcher's rounded («bubble») theme: ttk elements drawn from antialiased rounded images made at start.

Tk has no rounded widgets; ttk can draw any element from images, stretched with fixed borders (nine-slice). This
makes those images with Pillow (drawn 4x and reduced, so the curves are smooth) and replaces the elements of
buttons, combo boxes, entries, cards (label frames), notebook tabs and progress bars. Every page of the launcher
uses ttk widgets, so all of them get the rounded look without being rewritten.
"""
from PIL import Image, ImageDraw, ImageTk

GREEN, GREEN_HI, CREAM, AMBER, INK = '#163d32', '#245846', '#f5f1e5', '#dfa648', '#203c34'
SOFT, LINE, WHITE, MUTED = '#e7e6d8', '#d3d4c4', '#fffdf6', '#597067'
RADIUS = 14
SCALE = 4


def rounded(size, radius, fill, outline=None, width=1, shadow=False):
    """A rounded rectangle on a transparent background, size in pixels."""
    w, h = size
    big = Image.new('RGBA', (w * SCALE, h * SCALE), (0, 0, 0, 0))
    d = ImageDraw.Draw(big)
    r = radius * SCALE
    if shadow:
        d.rounded_rectangle((0, 2 * SCALE, w * SCALE - 1, h * SCALE - 1), r, fill=(0, 0, 0, 28))
        box = (0, 0, w * SCALE - 1, (h - 2) * SCALE - 1)
    else:
        box = (0, 0, w * SCALE - 1, h * SCALE - 1)
    d.rounded_rectangle(box, r, fill=fill, outline=outline, width=width * SCALE if outline else 0)
    return big.resize((w, h), Image.LANCZOS)


def pill(size, fill):
    return rounded(size, size[1] // 2, fill)


class Bubble:
    """Keeps the PhotoImages alive for as long as the style uses them."""

    def __init__(self, root):
        self.root, self.images = root, []

    def img(self, picture):
        photo = ImageTk.PhotoImage(picture, master=self.root)
        self.images.append(photo)
        return photo

    def apply(self, style):
        b = RADIUS + 2
        size = (2 * b + 8, 2 * b + 8)
        button = {state: self.img(rounded(size, RADIUS, fill, LINE if outline else None, shadow=True))
                  for state, fill, outline in (('normal', SOFT, True), ('active', '#efeee2', True),
                                               ('pressed', '#dcdbcb', True), ('disabled', '#ecebe3', True))}
        style.element_create('Bubble.button', 'image', button['normal'], ('disabled', button['disabled']),
                             ('pressed', button['pressed']), ('active', button['active']), border=b, sticky='nsew')
        style.layout('TButton', [('Bubble.button', {'sticky': 'nsew', 'children': [
            ('Button.padding', {'sticky': 'nsew', 'children': [('Button.label', {'sticky': 'nsew'})]})]})])
        style.configure('TButton', padding=(16, 9), background=CREAM, foreground=INK, anchor='center')
        style.map('TButton', foreground=[('disabled', '#9aa59f')], background=[('active', CREAM)])

        accent = {state: self.img(rounded(size, RADIUS, fill, shadow=True))
                  for state, fill in (('normal', GREEN), ('active', GREEN_HI), ('pressed', '#0f2e25'),
                                      ('disabled', '#84978c'))}
        style.element_create('Accent.button', 'image', accent['normal'], ('disabled', accent['disabled']),
                             ('pressed', accent['pressed']), ('active', accent['active']), border=b, sticky='nsew')
        style.layout('Accent.TButton', [('Accent.button', {'sticky': 'nsew', 'children': [
            ('Button.padding', {'sticky': 'nsew', 'children': [('Button.label', {'sticky': 'nsew'})]})]})])
        style.configure('Accent.TButton', foreground=CREAM, background=CREAM, font=('Segoe UI', 13, 'bold'),
                        padding=(26, 13))
        style.map('Accent.TButton', foreground=[('disabled', '#dfe5df')], background=[('active', CREAM)])

        field = {state: self.img(rounded(size, RADIUS - 2, fill, outline))
                 for state, fill, outline in (('normal', WHITE, LINE), ('focus', WHITE, GREEN),
                                              ('disabled', '#efeee6', LINE))}
        for name in ('Combobox', 'Entry', 'Spinbox'):
            style.element_create(f'Bubble.{name}.field', 'image', field['normal'], ('disabled', field['disabled']),
                                 ('focus', field['focus']), border=b - 4, sticky='nsew')
        style.layout('TCombobox', [('Bubble.Combobox.field', {'sticky': 'nsew', 'children': [
            ('Combobox.downarrow', {'side': 'right', 'sticky': 'ns'}),
            ('Combobox.padding', {'expand': '1', 'sticky': 'nsew', 'children': [
                ('Combobox.textarea', {'sticky': 'nsew'})]})]})])
        style.configure('TCombobox', padding=(10, 6), arrowsize=14, background=CREAM, fieldbackground=WHITE,
                        foreground=INK, arrowcolor=GREEN, bordercolor=WHITE, lightcolor=WHITE, darkcolor=WHITE)
        style.map('TCombobox', fieldbackground=[('readonly', WHITE)], background=[('active', CREAM)],
                  selectbackground=[('readonly', WHITE)], selectforeground=[('readonly', INK)])
        style.layout('TEntry', [('Bubble.Entry.field', {'sticky': 'nsew', 'children': [
            ('Entry.padding', {'sticky': 'nsew', 'children': [('Entry.textarea', {'sticky': 'nsew'})]})]})])
        style.configure('TEntry', padding=(10, 6), fieldbackground=WHITE, foreground=INK)
        self.root.option_add('*TCombobox*Listbox.background', WHITE)
        self.root.option_add('*TCombobox*Listbox.selectBackground', GREEN)
        self.root.option_add('*TCombobox*Listbox.font', ('Segoe UI', 10))

        # the card is the page's colour with a soft border and shadow: labels inside keep a matching background
        card = self.img(rounded((64, 64), RADIUS + 4, CREAM, LINE, shadow=True))
        style.element_create('Bubble.card', 'image', card, border=RADIUS + 6, sticky='nsew')
        style.layout('TLabelframe', [('Bubble.card', {'sticky': 'nsew'})])
        style.configure('TLabelframe', background=CREAM, padding=14)
        style.configure('TLabelframe.Label', background=CREAM, foreground=MUTED, font=('Segoe UI', 10, 'bold'))

        tab = {state: self.img(pill((60, 34), fill)) for state, fill in
               (('normal', SOFT), ('active', '#efeee2'), ('selected', GREEN))}
        style.element_create('Bubble.tab', 'image', tab['normal'], ('selected', tab['selected']),
                             ('active', tab['active']), border=17, sticky='nsew')
        style.layout('TNotebook.Tab', [('Bubble.tab', {'sticky': 'nsew', 'children': [
            ('Notebook.padding', {'side': 'top', 'sticky': 'nsew', 'children': [
                ('Notebook.label', {'side': 'top', 'sticky': ''})]})]})])
        style.configure('TNotebook', background=CREAM, borderwidth=0, tabmargins=(0, 0, 0, 10))
        style.configure('TNotebook.Tab', padding=(20, 7), background=CREAM, foreground=INK, borderwidth=0)
        style.map('TNotebook.Tab', foreground=[('selected', CREAM)], background=[('selected', CREAM)],
                  expand=[('selected', (0, 0, 0, 0))])
        style.layout('Pages.TNotebook.Tab', [])   # the sidebar chooses the launcher's pages
        style.configure('Pages.TNotebook', background=CREAM, borderwidth=0, tabmargins=(0, 0, 0, 0))

        trough = self.img(pill((40, 12), '#e1e0d0'))
        bar = self.img(pill((40, 12), GREEN))
        style.element_create('Bubble.trough', 'image', trough, border=6, sticky='nsew')
        style.element_create('Bubble.pbar', 'image', bar, border=6, sticky='nsew')
        style.layout('Snap.Horizontal.TProgressbar', [('Bubble.trough', {'sticky': 'nsew', 'children': [
            ('Bubble.pbar', {'side': 'left', 'sticky': 'ns'})]})])
        style.configure('Snap.Horizontal.TProgressbar', thickness=12, background=CREAM)
