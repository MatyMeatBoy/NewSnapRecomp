"""Static photographic cover; cached images do no work during gameplay."""
from tkinter import Canvas,ttk


class SnapCover(ttk.Frame):
    def __init__(self,parent,launcher):
        super().__init__(parent)
        self.images=[]
        canvas=Canvas(self,width=232,height=344,bg='#f5f1e5',highlightthickness=0)
        canvas.pack(anchor='n')
        assets=launcher.project/'assets/launcher'
        def photo(name,x,y,width,height):
            path=assets/name
            if not path.is_file():return False
            with launcher.Image.open(path) as original:
                image=original.convert('RGBA');image.thumbnail((width,height),launcher.Image.Resampling.LANCZOS)
            value=launcher.ImageTk.PhotoImage(image,master=launcher.root);self.images.append(value)
            canvas.create_image(x,y,image=value,anchor='nw');return True
        canvas.create_rectangle(12,7,225,293,fill='#d7d7c9',outline='')
        canvas.create_rectangle(7,2,220,287,fill='#fffdf6',outline='#d6d7c8')
        if not photo('lental-hero.jpg',13,8,201,265):
            canvas.create_text(112,110,text='LENTAL',fill='#163d32',font=('Segoe UI',22,'bold'))
        photo('snap-logo.png',20,170,188,110)
        canvas.create_rectangle(110,269,231,343,fill='#d7d7c9',outline='')
        canvas.create_rectangle(105,264,226,338,fill='#fffdf6',outline='#d6d7c8')
        photo('lental-explore.jpg',111,270,109,61)
        ttk.Label(self,text='LENTAL · CUADERNO DE CAMPO',font=('Segoe UI',8,'bold'),foreground='#597067').pack(anchor='w',pady=(12,4))
        ttk.Label(self,text='Encuadra tu próxima aventura.',style='Muted.TLabel',font=('Segoe UI',9),wraplength=225).pack(anchor='w')
