import tkinter as tk
from tkinter.constants import *
from mp import *
import queue
import datetime

class Application(tk.Frame):
    def createWidgets(self):
        self.top = tk.Frame(self,bd=1,relief=GROOVE,bg="yellow")
        self.top.pack(side=TOP)

        self.bottom = tk.Frame(self,bd=1,relief=GROOVE,bg="blue")
        self.bottom.pack(side=BOTTOM,fill=BOTH,expand=YES)

        self.right = tk.Frame(self,bd=1,relief=GROOVE,bg="green")
        self.right.pack(side=RIGHT,fill=BOTH,expand=YES)

        self.left = tk.Frame(self,bd=1,relief=GROOVE,bg="red")
        self.left.pack(side=LEFT)

        self.vgrid = tk.Frame(self.left)
        self.vgrid.grid()

        self.message = tk.Message(self.bottom,width=500)
        self.message.pack(fill=BOTH,expand=YES)

        tk.Button(self.top,text="Add",fg="red", 
                    command=self.add_symbol).pack(side=LEFT)

        today = datetime.date.today()
        self.symbols = tk.StringVar(value="")
        self.mm = tk.IntVar(value=today.month)
        self.yyyy = tk.IntVar(value=today.year)

        tk.Label(self.top,text="Symbols:").pack(side=LEFT)
        tk.Entry(self.top,textvariable=self.symbols,width=10).pack(side=LEFT)
        tk.Label(self.top,text="MM:").pack(side=LEFT)
        tk.Entry(self.top,textvariable=self.mm,width=2).pack(side=LEFT)
        tk.Label(self.top,text="Year:").pack(side=LEFT)
        tk.Entry(self.top,textvariable=self.yyyy,width=4).pack(side=LEFT)

        self.graph = tk.Canvas(self.right)
        self.graph.pack(fill=BOTH,expand=YES)

    def __init__(self, master=None):
        tk.Frame.__init__(self, master)
        self.root = master
        self.pack()
        self.createWidgets()
        self.queue = queue.Queue()
        self.running = True
        master.protocol('WM_DELETE_WINDOW', self.close)
        self.process_queue()

    def close(self):
        self.running = False

    def process_queue(self):
        while True:
            try:
                mp = self.queue.get_nowait()
            except queue.Empty:
                break
            if mp != None:
                print(mp)
                self.draw_grid(mp)
                self.draw_graph(mp)
                self.draw_text(mp)
            self.update_idletasks()
        if self.running:
            self.after(200,self.process_queue)
        else:
            self.root.destroy()

    def draw_grid(self,mp):
        for o in self.vgrid.grid_slaves():
            o.destroy()

        headers = ['prices','puts','calls','totals']
        bg="#dddddd"
        fg="#000000"
        hdrfont = ("Arial",8,"bold")
        font = ("Arial",8)
        for i,v in enumerate(headers):
            lbl = tk.Label(self.vgrid,text=v,font=hdrfont,bg=bg,fg=fg,
                    relief="ridge",justify="center",width=12)
            lbl.grid(column=i,row=0)
        val = mp['value']
        for i in range(len(val['prices'])):
            for j,v in enumerate(headers): 
                lbl = tk.Label(self.vgrid,text=val[v][i],font=font,
                        bg=bg,fg=fg,relief='ridge',justify='right',width=12)
                lbl.grid(column=j,row=i+1)

    def draw_text(self,mp):
        puts = sum(mp['puts']['open int'])
        calls = sum(mp['calls']['open int'])
        s = "Open Interest P/C Ratio: {0:5.2f}\t ({1} / {2})\n".format( 
                float(puts)/calls, puts, calls)
        s += "Minimum (MP): ${0:5.2f}\n".format(mp['max pain'])
        self.message['text'] = s

    def draw_graph(self,mp):
        self.right.pack(side=RIGHT,fill=BOTH,expand=YES)
        self.graph.pack(fill=BOTH,expand=YES)
        ctx = self.graph
        width = ctx.winfo_width() 
        height = ctx.winfo_height() 
        AXIS = 20
        self.graph.delete(ALL) 
        val = mp['value']
        x1 = val['prices'][0]
        x2 = val['prices'][-1]
        y1 = 0
        y2 = val['totals'][-1]
        
        to_x = lambda x: int(AXIS+(width-AXIS)*(x-x1)/(x2-x1))
        to_y = lambda y: int((height-AXIS)*(1-(y-y1)/(y2-y1)))

        def draw_line(x,y,**kwargs): 
            for i in range(1,len(x)):
               ctx.create_line(to_x(x[i-1]),to_y(y[i-1]),
                               to_x(x[i]),to_y(y[i]),kwargs)

        draw_line(val['prices'],val['calls'],fill="green")
        draw_line(val['prices'],val['puts'],fill="red")
        draw_line(val['prices'],val['totals'])

        ctx.create_line(AXIS,0,AXIS,height-AXIS)
        ctx.create_line(AXIS,height-AXIS,width,height-AXIS)

        ctx.create_line(to_x(mp['max pain']),0,to_x(mp['max pain']),height,
                        fill="blue",dash=(4,4))
 


       
    def add_symbol(self):
        def _get_max_pain_thread(symbol, mm, yyyy,queue):
            out = YahooOptions().get(symbol,mm,yyyy)
            queue.put(out)
        sym = self.symbols.get().strip()
        if len(sym) == 0:
            self.message['text'] = "Enter a symbol"
            return
        arg = (sym,self.mm.get(),self.yyyy.get(),self.queue)
        print(arg)
        t = threading.Thread(target=_get_max_pain_thread, args=arg)
        t.start()        


def run():
    root = tk.Tk()
    app = Application(master=root)
    app.mainloop()

run()

