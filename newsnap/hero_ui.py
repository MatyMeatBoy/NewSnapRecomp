"""Home's cover: two photo prints on the page, with soft shadows, held by a strip of paper tape.

The prints show the owner-approved promotional images in assets/launcher when they are present (they are shown as
they are, only scaled). The frames, shadows, tape and — when those images are not there — the landscape inside the
print are drawn here by code (original artwork). Built once at start; no work during gameplay."""
from tkinter import Canvas, ttk

from . import artwork, fonts
from .theme import CREAM, MUTED, WHITE

WIDTH, HEIGHT = 248, 372


def landscape(size, Image, ImageDraw):
    """An original scene for the print when no image is available: sky, sun, layered hills and a path."""
    w, h = size
    picture = artwork.vertical_gradient(size, '#f6e7bd', '#e9f0d2')
    d = ImageDraw.Draw(picture)
    d.ellipse((w * 0.60, h * 0.13, w * 0.60 + w * 0.22, h * 0.13 + w * 0.22), fill='#f7cf73')
    for base, amplitude, phase, colour in ((0.50, 0.060, 0.4, '#b7d3a8'), (0.62, 0.075, 2.1, '#86b78a'),
                                            (0.76, 0.060, 3.7, '#4f956c'), (0.90, 0.045, 5.2, '#2f6f55')):
        import math
        points = [(0, h)]
        for x in range(0, w + 8, 8):
            points.append((x, h * (base + amplitude * math.sin(phase + x / w * 5.2) + amplitude * 0.4 * math.sin(phase * 2 + x / w * 11))))
        points.append((w, h))
        d.polygon(points, fill=colour)
    d.polygon([(w * 0.40, h), (w * 0.56, h), (w * 0.47, h * 0.80), (w * 0.44, h * 0.80)], fill='#efe3c0')
    return artwork.add_grain(picture, 9)


def print_frame(photo, border, Image, ImageDraw, ImageFilter):
    """A photo as a paper print: white border and a soft shadow around it (12 px of room on every side)."""
    w, h = photo.width + 2 * border, photo.height + 2 * border + border // 2
    out = Image.new('RGBA', (w + 24, h + 24), (52, 44, 24, 0))
    shade = Image.new('L', out.size, 0)
    ImageDraw.Draw(shade).rounded_rectangle((12, 15, 12 + w, 15 + h), 5, fill=96)
    out.putalpha(shade.filter(ImageFilter.GaussianBlur(5)))
    paper = Image.new('RGBA', (w, h), WHITE)
    ImageDraw.Draw(paper).rectangle((0, 0, w - 1, h - 1), outline='#e2decd')
    paper.paste(photo.convert('RGB'), (border, border))
    ImageDraw.Draw(paper).rectangle((border - 1, border - 1, border + photo.width, border + photo.height), outline='#d9d5c3')
    out.alpha_composite(paper, (12, 12))
    return out


class SnapCover(ttk.Frame):
    def __init__(self, parent, launcher):
        super().__init__(parent)
        from PIL import ImageDraw, ImageFilter
        Image = launcher.Image
        self.images = []
        canvas = Canvas(self, width=WIDTH, height=HEIGHT, bg=CREAM, highlightthickness=0)
        canvas.pack(anchor='n')
        assets = launcher.project / 'assets/launcher'

        def load(name, size):
            try:
                with Image.open(assets / name) as original:
                    image = original.convert('RGBA')
                    image.thumbnail(size, Image.Resampling.LANCZOS)
                    return image
            except (OSError, ValueError):
                return None

        scene = Image.new('RGBA', (WIDTH, HEIGHT), artwork.rgb(CREAM) + (255,))
        main = load('lental-hero.jpg', (206, 272))
        original_art = main is None
        if original_art:
            main = landscape((206, 272), Image, ImageDraw)
        logo = load('snap-logo.png', (188, 110))
        if logo is not None:
            main = main.convert('RGBA')
            main.alpha_composite(logo, ((main.width - logo.width) // 2, main.height - logo.height - 6))
        scene.alpha_composite(print_frame(main, 8, Image, ImageDraw, ImageFilter), (-4, -6))
        small = load('lental-explore.jpg', (112, 64))
        if small is None:
            small = landscape((112, 64), Image, ImageDraw)
        scene.alpha_composite(print_frame(small, 6, Image, ImageDraw, ImageFilter).rotate(-5, resample=Image.BICUBIC, expand=True),
                              (WIDTH - 152, HEIGHT - 124))
        tape = Image.new('RGBA', (74, 22), artwork.rgb('#e9c376') + (205,))
        ImageDraw.Draw(tape).line((0, 11, 74, 11), fill=(255, 255, 255, 40), width=6)
        scene.alpha_composite(tape.rotate(-8, resample=Image.BICUBIC, expand=True), (72, -6))
        value = launcher.ImageTk.PhotoImage(scene.convert('RGB'), master=launcher.root)
        self.images.append(value)
        canvas.create_image(0, 0, image=value, anchor='nw')
        ttk.Label(self, text='LENTAL · CUADERNO DE CAMPO', font=fonts.ui(9, 'bold'), foreground=MUTED).pack(anchor='w', pady=(8, 2))
        ttk.Label(self, text='Encuadra tu próxima aventura.', style='Caption.TLabel', wraplength=240).pack(anchor='w')
