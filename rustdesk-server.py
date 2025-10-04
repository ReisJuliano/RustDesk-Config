import tkinter as tk
from tkinter import ttk, messagebox
import subprocess
import json
import os
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import parse_qs
import threading
import time

class APIHandler(BaseHTTPRequestHandler):
    manager = None
    
    def do_POST(self):
        if self.path == '/add_store':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length).decode('utf-8')
            params = parse_qs(post_data)
            
            nickname = params.get('nickname', [''])[0].strip()
            store_id = params.get('id', [''])[0].strip()
            
            if store_id:
                store_id_clean = store_id.replace(" ", "")
                
                store_data = {
                    "nickname": nickname if nickname else "",
                    "id": store_id_clean,
                    "id_display": store_id
                }
                
                self.manager.stores.append(store_data)
                self.manager.save_stores()
                self.manager.root.after(0, self.manager.render_stores)
                
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                response = json.dumps({
                    "status": "success",
                    "message": f"Loja adicionada com sucesso!"
                })
                self.wfile.write(response.encode())
                print(f"Loja adicionada via API: {nickname or store_id_clean} ({store_id_clean})")
            else:
                self.send_response(400)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                response = json.dumps({
                    "status": "error",
                    "message": "O ID é obrigatório"
                })
                self.wfile.write(response.encode())
        else:
            self.send_response(404)
            self.end_headers()
    
    def log_message(self, format, *args):
        pass

class RustDeskManager:
    def __init__(self, root):
        self.root = root
        self.root.title("Gerenciador RustDesk - Público")
        self.root.geometry("1000x700")
        self.root.configure(bg='#f0f0f0')
        
        self.password = ""
        self.rustdesk_path = r"C:\Program Files\RustDesk\rustdesk.exe"
        self.config_file = "rustdesk_stores.json"
        self.stores = []
        self.editing_index = -1
        self.filter_text = ""
        self.server_port = 8765
        self.ngrok_url = None
        self.ngrok_process = None
        
        self.load_stores()
        self.start_server()
        self.start_ngrok()
        self.create_ui()
        
    def start_server(self):
        APIHandler.manager = self
        self.server = HTTPServer(('0.0.0.0', self.server_port), APIHandler)
        self.server_thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.server_thread.start()
        
        import socket
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            local_ip = s.getsockname()[0]
            s.close()
        except:
            local_ip = "???"
        
        print(f"Servidor rodando na porta {self.server_port}")
        print(f"IP Local: {local_ip}")
    
    def start_ngrok(self):
        try:
            self.ngrok_process = subprocess.Popen(
                ['ngrok', 'http', str(self.server_port)],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            time.sleep(3)
            import requests
            try:
                response = requests.get('http://localhost:4040/api/tunnels')
                data = response.json()
                self.ngrok_url = data['tunnels'][0]['public_url']
                print(f"URL Pública ngrok: {self.ngrok_url}/add_store")
            except:
                self.ngrok_url = "Verifique em http://localhost:4040"
                print("Não foi possível obter URL do ngrok automaticamente")
        except FileNotFoundError:
            print("ngrok não encontrado!")
            print("Instale com: winget install ngrok (Windows)")
            self.ngrok_url = None
        except Exception as e:
            print(f"❌ Erro ao iniciar ngrok: {e}")
            self.ngrok_url = None
        
    def create_ui(self):
        controls = tk.Frame(self.root, bg='#D9D9D9', pady=20, padx=20)
        controls.pack(fill='x')
        
        server_frame = tk.Frame(controls, bg='#10b981', pady=8, padx=15)
        server_frame.pack(fill='x', pady=(0, 10))
        
        import socket
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            local_ip = s.getsockname()[0]
            s.close()
        except:
            local_ip = "???"
        
        server_label = tk.Label(server_frame, 
                               text=f"Rede Local: http://{local_ip}:{self.server_port}/add_store",
                               font=('Segoe UI', 9, 'bold'),
                               bg='#10b981', fg='white')
        server_label.pack()
        
        if self.ngrok_url:
            ngrok_frame = tk.Frame(controls, bg='#6366f1', pady=8, padx=15)
            ngrok_frame.pack(fill='x', pady=(0, 15))
            
            ngrok_label = tk.Label(ngrok_frame, 
                                   text=f"🌍 Internet (Público): {self.ngrok_url}/add_store",
                                   font=('Segoe UI', 10, 'bold'),
                                   bg='#6366f1', fg='white')
            ngrok_label.pack()
            
            copy_btn = tk.Button(ngrok_frame, text="Copiar URL",
                                command=lambda: self.copy_to_clipboard(f"{self.ngrok_url}/add_store"),
                                font=('Segoe UI', 9),
                                bg='#4f46e5', fg='white',
                                relief='flat', cursor='hand2',
                                padx=15, pady=5)
            copy_btn.pack(pady=(5, 0))
        else:
            warning_frame = tk.Frame(controls, bg='#f59e0b', pady=8, padx=15)
            warning_frame.pack(fill='x', pady=(0, 15))
            
            warning_label = tk.Label(warning_frame, 
                                    text="ngrok não está rodando - apenas acesso local disponível",
                                    font=('Segoe UI', 9, 'bold'),
                                    bg='#f59e0b', fg='white')
            warning_label.pack()
        
        search_frame = tk.Frame(controls, bg='#D9D9D9')
        search_frame.pack(fill='x', pady=(0, 15))
        
        tk.Label(search_frame, text="🔍 Buscar:", 
                font=('Segoe UI', 11, 'bold'), bg='#ffffff').pack(side='left', padx=(0, 10))
        
        self.search_entry = tk.Entry(search_frame, font=('Segoe UI', 11), width=40)
        self.search_entry.pack(side='left', fill='x', expand=True)
        self.search_entry.bind('<KeyRelease>', self.on_search)
        
        clear_btn = tk.Button(search_frame, text="✖ Limpar",
                            command=self.clear_search,
                            font=('Segoe UI', 9),
                            bg='#6b7280', fg='white',
                            relief='flat', cursor='hand2',
                            padx=15, pady=5)
        clear_btn.pack(side='left', padx=(10, 0))
        
        form_frame = tk.Frame(controls, bg='#D9D9D9')
        form_frame.pack(fill='x')
        
        tk.Label(form_frame, text="Apelido:", 
                font=('Segoe UI', 10), bg='#ffffff').grid(row=0, column=0, sticky='w', padx=5)
        self.nickname_entry = tk.Entry(form_frame, font=('Segoe UI', 11), width=20)
        self.nickname_entry.grid(row=0, column=1, padx=5, pady=5)
        
        tk.Label(form_frame, text="ID RustDesk:", 
                font=('Segoe UI', 10), bg='#ffffff').grid(row=0, column=2, sticky='w', padx=5)
        self.id_entry = tk.Entry(form_frame, font=('Segoe UI', 11), width=20)
        self.id_entry.grid(row=0, column=3, padx=5, pady=5)
        
        self.add_button = tk.Button(form_frame, text="➕ Adicionar", 
                                    command=self.add_store,
                                    font=('Segoe UI', 10, 'bold'),
                                    bg='#10b981', fg='white',
                                    relief='flat', padx=20, pady=8,
                                    cursor='hand2')
        self.add_button.grid(row=0, column=4, padx=10)
        
        self.id_entry.bind('<Return>', lambda e: self.add_store())
        
        list_frame = tk.Frame(self.root, bg='#f0f0f0')
        list_frame.pack(fill='both', expand=True, padx=20, pady=20)
        
        canvas = tk.Canvas(list_frame, bg='#f0f0f0', highlightthickness=0)
        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=canvas.yview)
        self.scrollable_frame = tk.Frame(canvas, bg='#f0f0f0')
        
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        self.render_stores()
    
    def copy_to_clipboard(self, text):
        self.root.clipboard_clear()
        self.root.clipboard_append(text)
        messagebox.showinfo("Copiado!", f"URL copiada para a área de transferência:\n\n{text}")
        
    def load_stores(self):
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    self.stores = json.load(f)
            except:
                self.stores = []
    
    def save_stores(self):
        with open(self.config_file, 'w', encoding='utf-8') as f:
            json.dump(self.stores, f, ensure_ascii=False, indent=2)
    
    def on_search(self, event=None):
        self.filter_text = self.search_entry.get().strip().lower()
        self.render_stores()
    
    def clear_search(self):
        self.search_entry.delete(0, tk.END)
        self.filter_text = ""
        self.render_stores()
    
    def filter_stores(self):
        if not self.filter_text:
            return self.stores
        
        filtered = []
        for store in self.stores:
            nickname = store.get('nickname', '').lower()
            store_id = store['id'].lower()
            
            if (self.filter_text in nickname or 
                self.filter_text in store_id):
                filtered.append(store)
        
        return filtered
    
    def add_store(self):
        nickname = self.nickname_entry.get().strip()
        store_id_input = self.id_entry.get().strip()

        if not store_id_input:
            messagebox.showwarning("Atenção", "Por favor, preencha o ID!")
            return

        store_id_clean = store_id_input.replace(" ", "")

        store_data = {
            "nickname": nickname if nickname else "",
            "id": store_id_clean,
            "id_display": store_id_input
        }

        if self.editing_index >= 0:
            self.stores[self.editing_index] = store_data
            self.editing_index = -1
            self.add_button.config(text="➕ Adicionar")
        else:
            self.stores.append(store_data)
        
        self.nickname_entry.delete(0, tk.END)
        self.id_entry.delete(0, tk.END)
        
        self.save_stores()
        self.render_stores()
        
    def connect_store(self, store_id):
        try:
            cmd = [self.rustdesk_path, "--connect", store_id, "--password", self.password]
            subprocess.Popen(cmd, shell=True)
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao executar comando:\n{str(e)}")
    
    def edit_store(self, index):
        filtered = self.filter_stores()
        store = filtered[index]
        real_index = self.stores.index(store)
        
        self.editing_index = real_index
        
        self.nickname_entry.delete(0, tk.END)
        self.nickname_entry.insert(0, store.get("nickname", ""))
        
        self.id_entry.delete(0, tk.END)
        self.id_entry.insert(0, store["id"])
        
        self.add_button.config(text="Salvar Alterações")
        
    def delete_store(self, index):
        filtered = self.filter_stores()
        store = filtered[index]
        real_index = self.stores.index(store)
        
        display_name = store.get('nickname') or store['id']
        if messagebox.askyesno("Confirmar", f"Tem certeza que deseja remover \"{display_name}\"?"):
            self.stores.pop(real_index)
            self.save_stores()
            self.render_stores()
    
    def render_stores(self):
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()
        
        filtered_stores = self.filter_stores()
        
        if not filtered_stores:
            empty_text = f"Nenhuma loja encontrada para: \"{self.filter_text}\"" if self.filter_text else "Nenhuma loja cadastrada"
            empty = tk.Label(self.scrollable_frame, text=empty_text, font=('Segoe UI', 12), bg='#f0f0f0', fg='#9ca3af', pady=50)
            empty.pack()
            return
        
        for i, store in enumerate(filtered_stores):
            row = i // 3
            col = i % 3
            
            card = tk.Frame(self.scrollable_frame, bg='#ffffff', relief='solid', bd=1, padx=15, pady=15)
            card.grid(row=row, column=col, padx=10, pady=10, sticky='nsew')
            
            # Exibir apelido ou ID como título
            display_title = store.get('nickname') or store['id']
            name_label = tk.Label(card, text=display_title, font=('Segoe UI', 14, 'bold'), bg='#ffffff', fg='#1f2937')
            name_label.pack(anchor='w')
            
            # Se houver apelido, não repetir; mas se não houver, já está no título
            # Mostrar o ID sempre
            id_frame = tk.Frame(card, bg='#f3f4f6', pady=5, padx=8)
            id_frame.pack(fill='x', pady=(8, 12))
            
            id_label = tk.Label(id_frame, text=f"ID: {store['id']}", font=('Courier New', 9), bg='#f3f4f6', fg='#6b7280')
            id_label.pack()
            
            buttons_frame = tk.Frame(card, bg='#ffffff')
            buttons_frame.pack(fill='x')
            
            connect_btn = tk.Button(buttons_frame, text="Conectar", command=lambda sid=store['id']: self.connect_store(sid), font=('Segoe UI', 9, 'bold'), bg='#667eea', fg='white', relief='flat', cursor='hand2', padx=10, pady=5)
            connect_btn.pack(side='left', padx=(0, 5))
            
            edit_btn = tk.Button(buttons_frame, text="✏️", command=lambda idx=i: self.edit_store(idx), font=('Segoe UI', 9), bg='#f59e0b', fg='white', relief='flat', cursor='hand2', padx=8, pady=5)
            edit_btn.pack(side='left', padx=2)
            
            delete_btn = tk.Button(buttons_frame, text="🗑️", command=lambda idx=i: self.delete_store(idx), font=('Segoe UI', 9), bg='#ef4444', fg='white', relief='flat', cursor='hand2', padx=8, pady=5)
            delete_btn.pack(side='left', padx=2)
        
        for i in range(3):
            self.scrollable_frame.columnconfigure(i, weight=1, uniform='col')

if __name__ == "__main__":
    root = tk.Tk()
    app = RustDeskManager(root)
    root.mainloop()
