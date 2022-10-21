from tkinter import messagebox
import traceback
try:
    from utils import *
    from logutils import *

    import tkinter as tk
    from tkinter import ttk, filedialog as fd
    import webbrowser
    from sys import platform

    def callback(event):
        webbrowser.open_new(f'https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/edit')

    root = tk.Tk()
    style = ttk.Style(root)
    root.title('GUI')
    if platform == "win32":
        root.geometry('380x580')
    else:
        style.theme_use('default')
        root.geometry('380x510')
    root.resizable(False, False)
    root.configure(background='#EBECEC')

    # configure the grid
    root.columnconfigure(0, weight=2)
    root.columnconfigure(1, weight=3)

    style.configure('.', font=('Helvetica', 16), background="#EBECEC")
    style.configure('TLabel', font=('Helvetica', 18),
            borderwidth=1, focusthickness=3, focuscolor='none')
    style.configure('Heading.TLabel', font=('Helvetica', 20))
    style.configure('FP.TLabel', font=('Consolas', 11))
    style.configure('E.TButton', font=('Helvetica', 18), padding=[50,30])
    style.configure('TEntry', font=('Helvetica', 18))

    # heading
    heading = ttk.Label(root, text='清大天文台 Autologger', style='Heading.TLabel')
    heading.grid(column=0, row=0, columnspan=2, pady=(20, 10), sticky=tk.N)

    items = ['light', 'dark', 'flat', 'bias']

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

        tk.messagebox.showinfo("showinfo", f'Done! {len(seq)} entries added. Please check the spreadsheet.')

    observer = tk.StringVar()
    ttk.Label(root, text=f'Observer ：', style='TLabel').grid(
            column=0, row=1+i*2+2, sticky=tk.W, padx=(50, 0), pady=(20, 10))
    ttk.Entry(root, textvariable=observer, style='TEntry').grid(
            column=1, row=1+i*2+2, pady=(20, 10), padx=(0,50))

    ttk.Button(root, text='自動填入', style='E.TButton',
            command=execute).grid(columnspan=2, row=1+i*2+3, pady=15)
    link = tk.Label(root, text=f'Observation Log', fg="blue", cursor="hand2")
    link.grid(columnspan=2, row=1+i*2+4, pady=5)
    link.bind("<Button-1>", callback)

    root.mainloop()
except Exception as e:
    messagebox.showerror(title="Exception raised", message = "".join(traceback.format_exception_only(type(e), e)).strip())
