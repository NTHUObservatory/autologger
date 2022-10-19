from utils import *
from logutils import *

import tkinter as tk
from tkinter import ttk, filedialog as fd

root = tk.Tk()
root.title('GUI')
root.geometry('380x480')
root.resizable(False, False)
root.configure(background='#EBECEC')

# configure the grid
root.columnconfigure(0, weight=2)
root.columnconfigure(1, weight=3)

style = ttk.Style(root)
style.configure('.', font=('Helvetica', 16), background="#EBECEC")
style.configure('TLabel', font=('Helvetica', 18),
                borderwidth=1, focusthickness=3, focuscolor='none')
style.configure('Heading.TLabel', font=('Helvetica', 20))
style.configure('FP.TLabel', font=('Consolas', 12))
style.configure('E.TButton', font=('Consolas', 18), padding=[50,30])
style.configure('TEntry', font=('Helvetica', 18))

# heading
heading = ttk.Label(root, text='清大天文台 Autologger', style='Heading.TLabel')
heading.grid(column=0, row=0, columnspan=2, pady=(20, 10), sticky=tk.N)

items = ['light', 'dark', 'bias']

directory_var = {}
def select_dir(item):
    global directory

    directory_var[item].set(fd.askdirectory(
        title='選擇目錄',
        initialdir='E:/astro_images/nina'))

def gen_button(item, i):
    ttk.Label(root, text=f'本日 {item} ：', style='TLabel').grid(
        column=0, row=1+i*2, sticky=tk.W, padx=(65, 0), pady=4)
    ttk.Button(root, text='選擇目錄', command=lambda: select_dir(item)).grid(
        column=1, row=1+i*2, sticky=tk.W, padx=(0, 100), pady=4)

    ttk.Label(root, textvariable=directory_var[item], style='FP.TLabel').grid(
        column=0, row=1+i*2+1, columnspan=2, sticky=tk.W, padx=(65, 0), pady=4)

for i, item in enumerate(items):
    directory_var[item] = tk.StringVar()
    gen_button(item, i)

def execute():
    directory = {x:y.get() for x, y in directory_var.items() if y.get()}
    seq = Sequence(sum((walk(root) for root in directory.values()), []), observer = observer.get())
    for obs in seq:
        newObs(obs.entry)

observer = tk.StringVar()
ttk.Label(root, text=f'Observer ：', style='TLabel').grid(
    column=0, row=1+i*2+2, sticky=tk.W, padx=(50, 0), pady=(20, 10))
ttk.Entry(root, textvariable=observer, style='TEntry').grid(
    column=1, row=1+i*2+2, pady=(20, 10), padx=(0,50))

ttk.Button(root, text='填入 Observation Log', style='E.TButton',
           command=execute).grid(columnspan=2, row=1+i*2+3, pady=15)

root.mainloop()
