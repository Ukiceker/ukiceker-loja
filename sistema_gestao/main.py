# -------------------------------------------------------------------------
# SISTEMA DE GESTÃO UKICEKER (Versão Desktop)
# Arquivo Principal: main.py
# -------------------------------------------------------------------------
import customtkinter as ctk
from tkinter import messagebox
from tkinter import ttk, filedialog
import mysql.connector
import hashlib
import binascii
import os
import subprocess
import sys
import shutil
import requests
from bs4 import BeautifulSoup
import json
import unicodedata
import re
import datetime

# Configuração Visual (Modo Escuro e Cor Azul)
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

# Configuração Centralizada do Banco de Dados
DB_CONFIG = {
    "host": "127.0.0.1",    # Força TCP/IP (evita problemas de resolução de nome/socket)
    "port": 3306,
    "user": "ukiceker_app",         # Usuário dedicado da aplicação
    "password": "Ukiceker@123",     # Senha definida para acesso TCP/IP
    "database": "ukiceker_db",
    "use_pure": True,       # Força implementação Python pura (evita erro DLL/GSSAPI)
    "connection_timeout": 5 # Timeout de segurança
}

# Definição de Caminhos Absolutos (Para evitar erros de "arquivo não encontrado")
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__)) # Pasta onde está o main.py
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)              # Pasta raiz do projeto (Ukiceker)

TEMP_FILE = os.path.join(SCRIPT_DIR, "temp_products.json")
LOG_FILE = os.path.join(PROJECT_ROOT, "debug_extracao.log")
CHROME_PROFILE_PATH = os.path.join(PROJECT_ROOT, "chrome_profile") # Perfil Dedicado do Robô
EDGE_PROFILE_PATH = os.path.join(PROJECT_ROOT, "edge_profile")     # Perfil Dedicado do Edge

class SistemaUkiceker(ctk.CTk):
    def __init__(self):
        super().__init__()

        # Configuração da Janela
        self.title("Ukiceker Manager - Sistema de Gestão de Afiliados")
        self.geometry("800x600")
        
        # Inicializa a fila de produtos (Lê do arquivo temporário se existir)
        self.fila_produtos = self.carregar_fila_temporaria()
        
        # Verifica e atualiza a estrutura do banco (Migração)
        self.verificar_estrutura_banco()
        
        # --- TELA DE LOGIN (Simulação) ---
        self.frame_login = ctk.CTkFrame(self)
        self.frame_login.pack(pady=100, padx=100, fill="both", expand=True)

        self.label_titulo = ctk.CTkLabel(self.frame_login, text="Acesso ao Sistema", font=("Roboto", 24))
        self.label_titulo.pack(pady=20)

        self.entry_usuario = ctk.CTkEntry(self.frame_login, placeholder_text="Usuário")
        self.entry_usuario.pack(pady=10)

        self.entry_senha = ctk.CTkEntry(self.frame_login, placeholder_text="Senha", show="*")
        self.entry_senha.pack(pady=10)

        # Navegação com Enter
        self.entry_usuario.bind("<Return>", lambda e: self.entry_senha.focus())
        self.entry_senha.bind("<Return>", lambda e: self.fazer_login())

        self.btn_entrar = ctk.CTkButton(self.frame_login, text="ENTRAR", command=self.fazer_login)
        self.btn_entrar.pack(pady=20)

        self.label_status = ctk.CTkLabel(self.frame_login, text="v1.0.0 - Versão Comercial", text_color="gray")
        self.label_status.pack(side="bottom", pady=10)

        # Define o foco inicial no campo de usuário
        self.after(200, lambda: self.entry_usuario.focus())

    def verificar_estrutura_banco(self):
        """Verifica se a coluna 'status' existe, se não, cria."""
        print("--- Verificando integridade do Banco de Dados ---")
        try:
            conexao = mysql.connector.connect(**DB_CONFIG)
            cursor = conexao.cursor()
            
            # 1. Tabela de Plataformas (Dinâmica)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS plataformas (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    nome VARCHAR(50) NOT NULL UNIQUE
                )
            """)
            
            # Popula com padrões se estiver vazia
            cursor.execute("SELECT count(*) FROM plataformas")
            count = cursor.fetchone()[0]
            if count == 0:
                print("-> Populando tabela 'plataformas' com padrões...")
                padroes = [("Shopee",), ("Amazon",), ("AliExpress",), ("Mercado Livre",)]
                cursor.executemany("INSERT INTO plataformas (nome) VALUES (%s)", padroes)
                conexao.commit()
            else:
                print(f"-> Tabela 'plataformas' já contém {count} registros. Mantendo dados.")

            # 2. Colunas na Tabela Produtos
            # Tenta adicionar a coluna. Se já existir, o MySQL ignora ou dá erro controlado.
            # Verifica e adiciona colunas faltantes manualmente para evitar erros de sintaxe SQL
            colunas_necessarias = [
                ("status", "VARCHAR(20) DEFAULT 'A Publicar'"),
                ("descricao", "TEXT")
            ]
            
            cursor.execute("SHOW COLUMNS FROM produtos")
            colunas_existentes = [row[0] for row in cursor.fetchall()]
            
            alteracoes = False
            for col_nome, col_def in colunas_necessarias:
                if col_nome not in colunas_existentes:
                    print(f"-> Adicionando coluna '{col_nome}' à tabela 'produtos'...")
                    cursor.execute(f"ALTER TABLE produtos ADD COLUMN {col_nome} {col_def}")
                    alteracoes = True
            
            if alteracoes:
                conexao.commit()
                print("-> Estrutura da tabela 'produtos' atualizada com sucesso.")
            else:
                print("-> Estrutura da tabela 'produtos' já está atualizada.")

            cursor.close()
            conexao.close()
            print("--- Verificação concluída ---\n")
        except Exception as e:
            print(f"ERRO CRÍTICO NA VERIFICAÇÃO DO BANCO: {e}")

    def hash_password(self, password):
        """Cria um hash seguro da senha para salvar no banco."""
        salt = hashlib.sha256(os.urandom(60)).hexdigest().encode('ascii')
        pwdhash = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), 
                                    salt, 100000)
        pwdhash = binascii.hexlify(pwdhash)
        return (salt + pwdhash).decode('ascii')

    def verify_password(self, stored_password, provided_password):
        """Verifica se a senha fornecida bate com o hash salvo no banco."""
        try:
            # O salt são os primeiros 64 caracteres
            salt = stored_password[:64]
            stored_hash = stored_password[64:]
            
            # Recalcula o hash com a senha fornecida e o salt extraído
            pwdhash = hashlib.pbkdf2_hmac('sha256', 
                                        provided_password.encode('utf-8'), 
                                        salt.encode('ascii'), 
                                        100000)
            pwdhash = binascii.hexlify(pwdhash).decode('ascii')
            
            return pwdhash == stored_hash
        except Exception as e:
            print(f"Erro na verificação de hash: {e}")
            return False

    def fazer_login(self):
        usuario = self.entry_usuario.get()
        senha = self.entry_senha.get()

        try:
            # Conecta ao MySQL Local (Windows)
            conexao = mysql.connector.connect(**DB_CONFIG)
            cursor = conexao.cursor()
            
            # Busca o hash da senha no banco
            query = "SELECT id, senha_hash, nivel_acesso, trocar_senha FROM usuarios WHERE usuario = %s"
            cursor.execute(query, (usuario,))
            resultado = cursor.fetchone()
            cursor.close() # Boa prática: liberar recursos do cursor
            conexao.close()

            # resultado[0]=id, [1]=hash, [2]=nivel, [3]=trocar_senha
            if resultado and self.verify_password(resultado[1], senha):
                if resultado[3] == 1:
                    self.abrir_primeiro_acesso(resultado[0])
                else:
                    self.abrir_painel_principal()
            else:
                messagebox.showerror("Erro", "Usuário ou senha incorretos.")
                
        except mysql.connector.Error as err:
            print(f"ERRO DETALHADO MYSQL: {err}") # Mostra o erro real no terminal
            messagebox.showerror("Erro de Conexão", f"Falha ao conectar no Banco de Dados Local.\nVerifique se o MySQL está rodando.\n\nErro: {err}")
        except Exception as e:
            messagebox.showerror("Erro Crítico", f"Erro inesperado no login:\n{e}\n\nContate o suporte técnico.")

    def abrir_primeiro_acesso(self, user_id):
        self.frame_login.pack_forget()
        self.user_id_troca = user_id

        self.frame_troca = ctk.CTkFrame(self)
        self.frame_troca.pack(pady=50, padx=50, fill="both", expand=True)

        ctk.CTkLabel(self.frame_troca, text="Primeiro Acesso - Configuração", font=("Roboto", 24)).pack(pady=20)
        ctk.CTkLabel(self.frame_troca, text="Por segurança, defina seu usuário e senha definitivos.", text_color="yellow").pack(pady=5)

        self.entry_novo_user = ctk.CTkEntry(self.frame_troca, placeholder_text="Novo Nome de Usuário")
        self.entry_novo_user.pack(pady=10)

        self.entry_nova_senha = ctk.CTkEntry(self.frame_troca, placeholder_text="Nova Senha", show="*")
        self.entry_nova_senha.pack(pady=10)

        self.entry_confirma_senha = ctk.CTkEntry(self.frame_troca, placeholder_text="Confirmar Nova Senha", show="*")
        self.entry_confirma_senha.pack(pady=10)

        # Navegação com Enter
        self.entry_novo_user.bind("<Return>", lambda e: self.entry_nova_senha.focus())
        self.entry_nova_senha.bind("<Return>", lambda e: self.entry_confirma_senha.focus())
        self.entry_confirma_senha.bind("<Return>", lambda e: self.salvar_primeiro_acesso())

        ctk.CTkButton(self.frame_troca, text="SALVAR E ACESSAR", command=self.salvar_primeiro_acesso).pack(pady=20)

    def salvar_primeiro_acesso(self):
        novo_user = self.entry_novo_user.get()
        nova_senha = self.entry_nova_senha.get()
        confirma = self.entry_confirma_senha.get()

        if not novo_user or not nova_senha:
            messagebox.showwarning("Atenção", "Preencha todos os campos.")
            return
        
        if nova_senha != confirma:
            messagebox.showerror("Erro", "As senhas não coincidem.")
            return

        try:
            conexao = mysql.connector.connect(**DB_CONFIG)
            cursor = conexao.cursor()
            
            # Atualiza usuário, senha e remove a flag de troca
            senha_hash = self.hash_password(nova_senha)
            sql = "UPDATE usuarios SET usuario = %s, senha_hash = %s, trocar_senha = 0 WHERE id = %s"
            cursor.execute(sql, (novo_user, senha_hash, self.user_id_troca))
            conexao.commit()
            cursor.close()
            conexao.close()

            messagebox.showinfo("Sucesso", "Dados atualizados com sucesso!")
            self.frame_troca.pack_forget()
            self.abrir_painel_principal()

        except Exception as e:
            messagebox.showerror("Erro", f"Falha ao atualizar dados: {e}")

    def abrir_painel_principal(self):
        # Remove a tela de login
        self.frame_login.pack_forget()
        
        # Cria o Painel Principal
        self.frame_painel = ctk.CTkFrame(self)
        self.frame_painel.pack(fill="both", expand=True, padx=20, pady=20)

        # Menu Lateral
        self.sidebar = ctk.CTkFrame(self.frame_painel, width=200)
        self.sidebar.pack(side="left", fill="y", padx=10, pady=10)

        self.btn_produtos = ctk.CTkButton(self.sidebar, text="Gerenciar Produtos", command=self.exibir_tela_produtos)
        self.btn_produtos.pack(pady=10, padx=10)

        self.btn_plataformas = ctk.CTkButton(self.sidebar, text="Configurar Plataformas", command=self.abrir_gestao_plataformas)
        self.btn_plataformas.pack(pady=10, padx=10)
        
        # --- TEMPO 2: PUBLICAÇÃO (Isolado no Menu) ---
        # Separador visual para indicar mudança de contexto
        ctk.CTkFrame(self.sidebar, height=2, fg_color="#404040").pack(fill="x", padx=15, pady=15)
        
        self.btn_publicar = ctk.CTkButton(self.sidebar, text="🚀 PUBLICAR VITRINE", fg_color="#10b981", hover_color="#059669", height=40, font=("Roboto", 12, "bold"), command=self.executar_gerador_site)
        self.btn_publicar.pack(pady=5, padx=10)
        
        self.btn_sair = ctk.CTkButton(self.sidebar, text="Sair", fg_color="red", command=self.destroy)
        self.btn_sair.pack(side="bottom", pady=20, padx=10)

        # Área de Conteúdo
        self.frame_conteudo = ctk.CTkFrame(self.frame_painel)
        self.frame_conteudo.pack(side="right", fill="both", expand=True, padx=10, pady=10)
        
        # Tela Inicial
        self.exibir_dashboard()

    def limpar_conteudo(self):
        for widget in self.frame_conteudo.winfo_children():
            widget.destroy()

    def exibir_dashboard(self):
        self.limpar_conteudo()
        ctk.CTkLabel(self.frame_conteudo, text="Bem-vindo ao Ukiceker Manager", font=("Roboto", 24)).pack(pady=20)
        ctk.CTkLabel(self.frame_conteudo, text="Selecione uma opção no menu lateral.", font=("Roboto", 14)).pack(pady=10)

    # --- MÓDULO DE PRODUTOS ---
    def exibir_tela_produtos(self):
        self.limpar_conteudo()

        # Cabeçalho
        header = ctk.CTkFrame(self.frame_conteudo, fg_color="transparent")
        header.pack(fill="x", pady=10, padx=10)
        
        ctk.CTkLabel(header, text="Gestão de Produtos", font=("Roboto", 20, "bold")).pack(side="left")

        # Botões de Ação (Foco no Tempo 1: Garimpo e Banco)
        btn_exportar = ctk.CTkButton(header, text="💾 Exportar Fila", fg_color="#3b82f6", hover_color="#2563eb", width=120, command=self.processar_exportacao)
        btn_exportar.pack(side="right", padx=5)
        
        btn_novo = ctk.CTkButton(header, text="+ Novo Produto", command=self.abrir_form_produto)
        btn_novo.pack(side="right", padx=5)

        # Tabela (Treeview)
        # Estilo Customizado para Dark Mode
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Treeview", background="#2b2b2b", foreground="white", fieldbackground="#2b2b2b", borderwidth=0)
        style.map("Treeview", background=[("selected", "#1f538d")])
        
        columns = ("id", "status", "nome", "plataforma", "preco")
        self.tree = ttk.Treeview(self.frame_conteudo, columns=columns, show="headings", selectmode="browse")
        
        self.tree.heading("id", text="ID")
        self.tree.heading("status", text="Status")
        self.tree.heading("nome", text="Produto")
        self.tree.heading("plataforma", text="Plataforma")
        self.tree.heading("preco", text="Preço (R$)")
        
        self.tree.column("id", width=50, anchor="center")
        self.tree.column("status", width=100, anchor="center")
        self.tree.column("nome", width=250)
        self.tree.column("plataforma", width=100, anchor="center")
        self.tree.column("preco", width=100, anchor="e")
        
        self.tree.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Botão de Excluir (Abaixo da tabela)
        ctk.CTkButton(self.frame_conteudo, text="Excluir Selecionado", fg_color="#550000", hover_color="#880000", command=self.excluir_produto).pack(pady=10, anchor="e", padx=10)

        self.atualizar_grid()

    def atualizar_grid(self):
        # Limpa tabela atual
        for item in self.tree.get_children():
            self.tree.delete(item)
            
        # 1. Carrega itens da FILA (Temporários)
        for i, prod in enumerate(self.fila_produtos):
            # ID fictício para visualização
            display_id = f"NOVO-{i+1}"
            self.tree.insert("", "end", values=(display_id, "Fila", prod['nome'], prod['plataforma'], prod['preco']), tags=('novo',))
            
        try:
            conexao = mysql.connector.connect(**DB_CONFIG)
            cursor = conexao.cursor()
            # Busca também o status. Se for NULL (antigos), trata como 'A Publicar'
            cursor.execute("SELECT id, COALESCE(status, 'A Publicar'), nome, plataforma, preco FROM produtos ORDER BY id DESC")
            for row in cursor:
                # row = (id, status, nome, plataforma, preco)
                tag_status = 'publicado' if row[1] == 'Publicado' else 'pendente'
                self.tree.insert("", "end", values=row, tags=(tag_status,))
                
            cursor.close()
            conexao.close()
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao carregar produtos: {e}")

        # --- CORES DAS LINHAS ---
        self.tree.tag_configure('novo', foreground='#60a5fa')      # Azul Claro (Fila)
        self.tree.tag_configure('pendente', foreground='#fbbf24')  # Laranja (No Banco, mas não no Site)
        self.tree.tag_configure('publicado', foreground='#4ade80') # Verde (No Site)

    # --- GESTÃO DE PLATAFORMAS (NOVO) ---
    def abrir_gestao_plataformas(self):
        top = ctk.CTkToplevel(self)
        top.title("Plataformas")
        top.geometry("400x400")
        top.attributes("-topmost", True)
        
        ctk.CTkLabel(top, text="Plataformas Cadastradas", font=("Roboto", 16, "bold")).pack(pady=10)
        
        listbox = ctk.CTkTextbox(top, height=200)
        listbox.pack(pady=10, padx=20, fill="x")
        
        def carregar_lista():
            listbox.delete("0.0", "end")
            try:
                conexao = mysql.connector.connect(**DB_CONFIG)
                cursor = conexao.cursor()
                cursor.execute("SELECT nome FROM plataformas ORDER BY nome")
                for (nome,) in cursor:
                    listbox.insert("end", f"- {nome}\n")
                conexao.close()
            except: pass
            
        carregar_lista()
        
        entry_nova = ctk.CTkEntry(top, placeholder_text="Nova Plataforma")
        entry_nova.pack(pady=5, padx=20, fill="x")
        
        def adicionar():
            nome = entry_nova.get().strip()
            if nome:
                try:
                    conexao = mysql.connector.connect(**DB_CONFIG)
                    cursor = conexao.cursor()
                    cursor.execute("INSERT INTO plataformas (nome) VALUES (%s)", (nome,))
                    conexao.commit()
                    conexao.close()
                    carregar_lista()
                    entry_nova.delete(0, "end")
                except Exception as e:
                    messagebox.showerror("Erro", f"Erro ao adicionar: {e}")
                    
        ctk.CTkButton(top, text="Adicionar", command=adicionar).pack(pady=10)
        entry_nova.bind("<Return>", lambda e: adicionar())

    def _iniciar_driver(self):
        """Inicializa o Selenium Driver (Chrome ou Edge) com perfil dedicado."""
        try:
            from selenium import webdriver
            from selenium.webdriver.chrome.service import Service
            from selenium.webdriver.chrome.options import Options
            from webdriver_manager.chrome import ChromeDriverManager
            from webdriver_manager.microsoft import EdgeChromiumDriverManager
            from selenium.common.exceptions import WebDriverException
        except ImportError:
            messagebox.showerror("Erro de Dependência", "Selenium não instalado.\nExecute: pip install selenium webdriver-manager")
            return None

        driver = None
        # TENTATIVA 1: GOOGLE CHROME
        try:
            options = Options()
            options.add_argument(f"--user-data-dir={CHROME_PROFILE_PATH}")
            options.add_argument("--disable-blink-features=AutomationControlled") 
            options.add_argument("--start-maximized")
            
            # --- MELHORIA ANTI-DETECÇÃO (STEALTH) ---
            # Remove avisos de automação e define User-Agent de usuário real
            options.add_experimental_option("excludeSwitches", ["enable-automation"])
            options.add_experimental_option('useAutomationExtension', False)
            # REMOVIDO: User-Agent fixo causava conflito de versão. Deixamos o navegador decidir.
            
            service = Service(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=options)
            
            # Injeta JavaScript para esconder que é um robô
            driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
                "source": "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
            })
            
            print("-> Usando Google Chrome")
        except Exception as e_chrome:
            print(f"Chrome erro: {e_chrome}")
            # TENTATIVA 2: MICROSOFT EDGE
            try:
                from selenium.webdriver.edge.service import Service as EdgeService
                from selenium.webdriver.edge.options import Options as EdgeOptions
                
                edge_options = EdgeOptions()
                edge_options.add_argument(f"--user-data-dir={EDGE_PROFILE_PATH}")
                edge_options.add_argument("--disable-blink-features=AutomationControlled")
                edge_options.add_argument("--start-maximized")
                
                # Stealth para Edge
                edge_options.add_experimental_option("excludeSwitches", ["enable-automation"])
                edge_options.add_experimental_option('useAutomationExtension', False)
                
                service = EdgeService(EdgeChromiumDriverManager().install())
                driver = webdriver.Edge(service=service, options=edge_options)
                
                # Injeta JavaScript Stealth no Edge
                driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
                    "source": "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
                })
                
                print("-> Usando Microsoft Edge")
            except Exception as e_edge:
                messagebox.showerror("Erro de Navegador", f"Falha ao abrir navegador.\nChrome: {e_chrome}\nEdge: {e_edge}")
                return None
        
        return driver

    def realizar_login_manual(self, url_inicial):
        """Abre o navegador e espera o usuário fazer login."""
        if not url_inicial:
            url_inicial = "https://shopee.com.br" # Link padrão se estiver vazio
        
        messagebox.showinfo("Verificar Acesso", "O navegador será aberto.\n\nComo usamos um perfil persistente, se você já logou antes, sua sessão deve estar ativa.\n\n1. Verifique se está logado.\n2. Se não, faça o login.\n3. Clique em OK aqui para continuar.")
        
        driver = None
        try:
            driver = self._iniciar_driver()
            if not driver: return

            driver.get(url_inicial)
            
            # O sistema fica PAUSADO aqui até você clicar em OK
            messagebox.showinfo("Aguardando", "Navegador aberto.\n\nVerifique o login no site.\nQuando estiver pronto, clique em OK AQUI para salvar e fechar.")
            
        except Exception as e:
            messagebox.showerror("Erro", f"Erro no navegador: {e}")
        finally:
            if driver:
                try:
                    driver.quit()
                except:
                    pass # Evita erro se o usuário já fechou a janela

    def verificar_duplicidade(self, link):
        """Verifica se o link já existe no Banco ou na Fila."""
        if not link: return False
        
        # 1. Verifica na Fila em memória
        for prod in self.fila_produtos:
            if prod.get('link') == link:
                return True

        # 2. Verifica no Banco de Dados
        try:
            conexao = mysql.connector.connect(**DB_CONFIG)
            cursor = conexao.cursor()
            cursor.execute("SELECT count(*) FROM produtos WHERE link = %s", (link,))
            count = cursor.fetchone()[0]
            conexao.close()
            return count > 0
        except: return False

    def _processar_dados_extraidos(self, dados, e_nome, e_desc, e_preco, e_img, e_link, e_plat):
        """
        Lógica Centralizada: Recebe o JSON bruto (do Selenium ou Clipboard) 
        e preenche os campos do formulário.
        """
        try:
            # --- LÓGICA CIRÚRGICA DE EXTRAÇÃO ---
            produto_encontrado = None
            
            # 1. Tenta achar no JSON-LD (Padrão Ouro)
            if 'json_ld' in dados and isinstance(dados['json_ld'], list):
                for item in dados['json_ld']:
                    if isinstance(item, dict) and item.get('@type') == 'Product':
                        produto_encontrado = item
                        break

            if produto_encontrado:
                # Extrai os dados do objeto 'Product'
                nome = produto_encontrado.get('name', '')
                descricao = produto_encontrado.get('description', '')
                imagem = produto_encontrado.get('image', '')
                link = dados.get('url', '')
                
                # Validação de Duplicidade
                if self.verificar_duplicidade(link):
                    if not messagebox.askyesno("Duplicidade Detectada", "Este produto já está cadastrado (Banco ou Fila).\n\nDeseja importar os dados mesmo assim?"):
                        return False
                
                preco = ''
                offers = produto_encontrado.get('offers')
                if isinstance(offers, dict):
                    preco = str(offers.get('price', ''))

                # Preenche os campos do formulário
                if nome: e_nome.delete(0, "end"); e_nome.insert(0, nome)
                if descricao: e_desc.delete("0.0", "end"); e_desc.insert("0.0", descricao)
                if preco: e_preco.delete(0, "end"); e_preco.insert(0, preco)
                if link: e_link.delete(0, "end"); e_link.insert(0, link)
                if imagem: e_img.delete(0, "end"); e_img.insert(0, imagem)
                
                # Tenta identificar a Plataforma pela URL
                plataformas_db = self.obter_plataformas_db()
                for plat in plataformas_db:
                    if plat.lower().replace(" ", "") in link.lower().replace(" ", ""):
                        e_plat.set(plat)
                        break
                return True
            return False
        except Exception as e:
            print(f"Erro ao processar dados: {e}")
            return False

    def extrair_dados_url(self, url, entry_nome, entry_preco, entry_imagem, entry_plataforma, textbox_desc):
        """
        Abre o navegador, carrega o site e injeta o script de extração automaticamente.
        """
        if not url:
            messagebox.showwarning("Atenção", "Cole o link primeiro.")
            return

        import time

        try:
            # Usa a função centralizada para iniciar o driver
            driver = self._iniciar_driver()
            if not driver:
                return
            
            try:
                driver.get(url)
                
                # --- MONITORAMENTO INTELIGENTE DE CARREGAMENTO ---
                # Espera até que o JSON-LD apareça ou timeout de 15s
                print("Aguardando carregamento dos dados estruturados...")
                dados_carregados = False
                for _ in range(15): # Tenta por 15 segundos
                    time.sleep(1)
                    # Verifica se a página carregou completamente E se existe JSON-LD
                    ready = driver.execute_script("return document.readyState === 'complete' && document.querySelectorAll('script[type=\"application/ld+json\"]').length > 0")
                    if ready:
                        dados_carregados = True
                        break
                
                if not dados_carregados:
                    print("Aviso: JSON-LD não detectado rapidamente. Tentando extração mesmo assim...")

                # --- INJEÇÃO DO SCRIPT (O MESMO DO BOOKMARKLET) ---
                # A diferença é que aqui retornamos o JSON string direto para o Python
                js_script = """
                var d = document;
                var dump = {ukiceker_raw: true, url: window.location.href, title: d.title, meta: {}, json_ld: [], inputs: {}};
                
                var metas = d.getElementsByTagName('meta');
                for(var i=0; i<metas.length; i++){
                    var k = metas[i].getAttribute('name') || metas[i].getAttribute('property');
                    var v = metas[i].getAttribute('content');
                    if(!k) k = 'meta_sem_nome_' + i;
                    if(dump.meta[k]) k = k + '_' + i;
                    dump.meta[k] = v;
                }
                
                var scripts = d.querySelectorAll('script[type="application/ld+json"]');
                for(var i=0; i<scripts.length; i++){
                    try {
                        dump.json_ld.push(JSON.parse(scripts[i].innerText));
                    } catch(e){
                        dump.json_ld.push({error: "json_invalido", content: scripts[i].innerText.substring(0,100)});
                    }
                }
                
                return JSON.stringify(dump);
                """
                
                json_resultado = driver.execute_script(js_script)
                dados = json.loads(json_resultado)
                
                # Processa os dados usando a lógica centralizada
                sucesso = self._processar_dados_extraidos(dados, entry_nome, textbox_desc, entry_preco, entry_imagem, entry_plataforma.get(), entry_plataforma)
                
                if sucesso:
                    messagebox.showinfo("Sucesso", "Dados extraídos automaticamente via Script Injetado!")
                else:
                    # Se falhar, salva o dump para análise (fallback)
                    nome_arquivo = "dump_automacao_falha.json"
                    caminho_dump = os.path.join(PROJECT_ROOT, nome_arquivo)
                    with open(caminho_dump, "w", encoding="utf-8") as f:
                        json.dump(dados, f, indent=4, ensure_ascii=False)
                    messagebox.showwarning("Atenção", f"O script rodou, mas não encontrou o Produto no JSON.\nDump salvo em: {nome_arquivo}")

            finally:
                if driver:
                    try:
                        driver.quit()
                    except: pass

        except Exception as e:
            messagebox.showerror("Erro na Extração", f"Não foi possível ler o site.\nMotivo: {e}\n\nPreencha manualmente.")

    def selecionar_imagem_local(self, entry_widget):
        """
        Apenas seleciona o caminho do arquivo.
        A cópia e exclusão real acontecem apenas no 'Exportar'.
        """
        
        # Define caminhos baseados na raiz do projeto
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        path_material = os.path.join(base_dir, "material de apoio", "imagens")
        path_site_img = os.path.join(base_dir, "frontend_output", "images")
        
        # Garante que as pastas existam
        os.makedirs(path_material, exist_ok=True)
        os.makedirs(path_site_img, exist_ok=True)
        
        filename = filedialog.askopenfilename(
            title="Selecione a Imagem do Produto",
            initialdir=path_material,
            filetypes=[("Imagens", "*.jpg *.jpeg *.png *.webp")]
        )
        
        if filename:
            try:
                # Apenas preenche o campo com o caminho completo por enquanto
                entry_widget.delete(0, "end")
                entry_widget.insert(0, filename)
            except Exception as e:
                messagebox.showerror("Erro", f"Falha ao processar imagem: {e}")

    def obter_plataformas_db(self):
        try:
            conexao = mysql.connector.connect(**DB_CONFIG)
            cursor = conexao.cursor()
            cursor.execute("SELECT nome FROM plataformas")
            lista = [row[0] for row in cursor.fetchall()]
            conexao.close()
            return lista if lista else ["Geral"]
        except: return ["Erro DB"]
        
    # --- MÓDULO DE ESCUTA (RIP DE DADOS) ---
    def mostrar_instrucoes_extensao(self):
        """Exibe o código JavaScript para criar o Bookmarklet (Extensão Manual)."""
        top = ctk.CTkToplevel(self)
        top.title("Modo Diagnóstico - Varredura Completa")
        top.geometry("700x500")
        top.attributes("-topmost", True)
        
        ctk.CTkLabel(top, text="Script de Varredura (Coleta Bruta)", font=("Roboto", 18, "bold")).pack(pady=10)
        
        instrucoes = (
            "Este script não tenta adivinhar nada. Ele varre TODAS as tags da página.\n"
            "O objetivo é gerar um arquivo de análise para identificarmos as variáveis corretas.\n\n"
            "1. Atualize seu favorito 'Rip Ukiceker' com o código abaixo.\n"
            "2. Use na página do produto.\n"
            "3. O App vai gerar um arquivo 'dump_analise.json' com tudo que encontrou."
        )
        ctk.CTkLabel(top, text=instrucoes, justify="left", padx=20).pack(pady=5)
        
        # Código JavaScript: VARREDURA TOTAL (Loop Auto-Incremental)
        # IMPORTANTE: Sem comentários de linha (//) para não quebrar na minificação
        js_code_raw = """
        javascript:(function(){
            try {
                var d = document;
                var dump = {ukiceker_raw: true, url: window.location.href, title: d.title, meta: {}, json_ld: [], inputs: {}};
                
                var metas = d.getElementsByTagName('meta');
                for(var i=0; i<metas.length; i++){
                    var k = metas[i].getAttribute('name') || metas[i].getAttribute('property');
                    var v = metas[i].getAttribute('content');
                    if(!k) k = 'meta_sem_nome_' + i;
                    if(dump.meta[k]) k = k + '_' + i;
                    dump.meta[k] = v;
                }
                
                var scripts = d.querySelectorAll('script[type="application/ld+json"]');
                for(var i=0; i<scripts.length; i++){
                    try {
                        dump.json_ld.push(JSON.parse(scripts[i].innerText));
                    } catch(e){
                        dump.json_ld.push({error: "json_invalido", content: scripts[i].innerText.substring(0,100)});
                    }
                }
                
                var inputs = d.getElementsByTagName('input');
                for(var i=0; i<inputs.length; i++){
                    var k = inputs[i].name || inputs[i].id || 'input_'+i;
                    dump.inputs[k] = inputs[i].value;
                }
                
                var finalJson = JSON.stringify(dump, null, 2);
                navigator.clipboard.writeText(finalJson)
                    .then(() => alert("VARREDURA COMPLETA!\\nDados copiados. Volte ao App para salvar o arquivo."))
                    .catch(e => {
                        window.prompt("Cópia automática falhou. Copie manualmente (Ctrl+C):", finalJson);
                    });
            } catch(err) { alert("Erro Geral: " + err); }
        })();
        """
        
        # Minifica removendo quebras de linha e espaços extras
        js_code_min = " ".join(js_code_raw.split())
        
        textbox = ctk.CTkTextbox(top, height=150)
        textbox.pack(pady=10, padx=20, fill="x")
        textbox.insert("0.0", js_code_min)
        
        def copiar_js():
            self.clipboard_clear()
            self.clipboard_append(js_code_min)
            messagebox.showinfo("Copiado", "Código copiado! Crie o favorito no navegador agora.")
            
        ctk.CTkButton(top, text="Copiar Código JS", command=copiar_js).pack(pady=10)

    def monitorar_clipboard(self, window, e_nome, e_desc, e_preco, e_img, e_link, e_plat):
        """Verifica periodicamente se há dados do Ukiceker na área de transferência."""
        if not window.winfo_exists(): return
        
        if getattr(self, "modo_escuta_ativo", False):
            try:
                conteudo = window.clipboard_get()
                
                # MODO VARREDURA / DIAGNÓSTICO
                if conteudo.startswith("{") and "ukiceker_raw" in conteudo:
                    # Evita processar o mesmo dado repetidamente
                    if getattr(self, "ultimo_clipboard", "") != conteudo:
                        self.ultimo_clipboard = conteudo
                        
                        try:
                            dados = json.loads(conteudo)
                            sucesso = self._processar_dados_extraidos(dados, e_nome, e_desc, e_preco, e_img, e_link, e_plat)
                            
                            if sucesso:
                                messagebox.showinfo("Sucesso", "Dados do produto preenchidos automaticamente!")
                                window.attributes("-topmost", True); window.attributes("-topmost", False)
                            else:
                                nome_arquivo = "dump_analise.json"
                                caminho_dump = os.path.join(PROJECT_ROOT, nome_arquivo)
                                with open(caminho_dump, "w", encoding="utf-8") as f:
                                    json.dump(dados, f, indent=4, ensure_ascii=False)
                                messagebox.showwarning("Análise Necessária", f"Não foi encontrado um JSON-LD de 'Produto'.\n\nUm arquivo de análise foi salvo em:\n{caminho_dump}")

                        except Exception as e:
                            messagebox.showerror("Erro de Processamento", f"Falha ao processar os dados da área de transferência:\n{e}")
            except: pass
        
        # Loop a cada 1 segundo
        window.after(1000, lambda: self.monitorar_clipboard(window, e_nome, e_desc, e_preco, e_img, e_link, e_plat))

    def abrir_form_produto(self):
        # --- LIMPEZA PREVENTIVA ---
        # Limpa o clipboard se contiver dados de captura antiga para evitar disparo acidental
        try:
            clip = self.clipboard_get()
            if clip.startswith("{") and "ukiceker_raw" in clip:
                self.clipboard_clear()
                self.ultimo_clipboard = "" # Reseta o estado do monitor
        except: pass

        toplevel = ctk.CTkToplevel(self)
        toplevel.title("Novo Produto")
        toplevel.geometry("500x700") # Aumentei para caber a descrição
        toplevel.attributes("-topmost", True) # Mantém na frente

        ctk.CTkLabel(toplevel, text="Cadastrar Produto", font=("Roboto", 18)).pack(pady=10)
        
        # --- FORMULÁRIO ---
        ctk.CTkLabel(toplevel, text="Link do Afiliado:", text_color="gray", font=("Roboto", 12)).pack(anchor="w", padx=20, pady=(10,0))
        entry_link = ctk.CTkEntry(toplevel, placeholder_text="https://shopee.com.br/...")
        entry_link.pack(pady=5, padx=20, fill="x")

        ctk.CTkLabel(toplevel, text="Dados do Produto:", text_color="gray", font=("Roboto", 12)).pack(anchor="w", padx=20)

        entry_nome = ctk.CTkEntry(toplevel, placeholder_text="Nome do Produto")
        entry_nome.pack(pady=5, padx=20, fill="x")

        # Campo Descrição (Novo)
        ctk.CTkLabel(toplevel, text="Descrição:", font=("Roboto", 12)).pack(anchor="w", padx=20)
        entry_desc = ctk.CTkTextbox(toplevel, height=100)
        entry_desc.pack(pady=5, padx=20, fill="x")

        entry_preco = ctk.CTkEntry(toplevel, placeholder_text="Preço (ex: 29.90)")
        entry_preco.pack(pady=5, padx=20, fill="x")

        # Carrega plataformas do banco
        lista_plats = self.obter_plataformas_db()
        entry_plataforma = ctk.CTkComboBox(toplevel, values=lista_plats)
        if lista_plats: entry_plataforma.set(lista_plats[0])
        entry_plataforma.pack(pady=5, padx=20, fill="x")

        # Campo de Imagem com Botão de Upload
        entry_imagem = ctk.CTkEntry(toplevel, placeholder_text="URL ou Caminho da Imagem")
        entry_imagem.pack(pady=5, padx=20, fill="x")
        
        # Botão de Automação (Script Encapsulado)
        btn_auto = ctk.CTkButton(toplevel, text="⚡ Preencher Automático", fg_color="#4B0082", hover_color="#38006b",
                                 command=lambda: self.extrair_dados_url(entry_link.get(), entry_nome, entry_preco, entry_imagem, entry_plataforma, entry_desc))
        btn_auto.pack(pady=10, padx=20)

        btn_upload = ctk.CTkButton(toplevel, text="📂 Buscar em Material de Apoio", fg_color="#D97706", hover_color="#B45309", 
                                   command=lambda: self.selecionar_imagem_local(entry_imagem))
        btn_upload.pack(pady=5, padx=20)

        def adicionar_a_fila():
            # Cria objeto do produto
            produto = {
                "nome": entry_nome.get(),
                "descricao": entry_desc.get("0.0", "end").strip(),
                "preco": entry_preco.get(),
                "plataforma": entry_plataforma.get(),
                "link": entry_link.get(),
                "imagem": entry_imagem.get()
            }
            
            # Validação básica
            if not produto["nome"] or not produto["preco"]:
                messagebox.showwarning("Atenção", "Nome e Preço são obrigatórios.")
                return
            
            # Validação Rígida de Plataforma
            if produto["plataforma"] not in lista_plats:
                messagebox.showerror("Erro de Classificação", f"A plataforma '{produto['plataforma']}' não é válida.\nSelecione uma das opções da lista.")
                return
            
            # Validação de Duplicidade ao Adicionar
            if self.verificar_duplicidade(produto["link"]):
                if not messagebox.askyesno("Duplicidade", "Este link já existe no sistema.\nDeseja adicionar novamente?"):
                    return

            # Adiciona à lista em memória e salva no JSON
            self.fila_produtos.append(produto)
            self.salvar_fila_temporaria()
            
            messagebox.showinfo("Fila", "Produto adicionado à fila de exportação!")
            toplevel.destroy()
            self.atualizar_grid()

        ctk.CTkButton(toplevel, text="ADICIONAR À FILA", command=adicionar_a_fila).pack(pady=20)

        # Configuração de Navegação com Enter (Fluxo Rápido)
        entry_link.bind("<Return>", lambda e: entry_nome.focus())
        entry_nome.bind("<Return>", lambda e: entry_desc.focus())
        # entry_desc é Textbox (Enter = Nova Linha), então não vinculamos navegação aqui
        entry_preco.bind("<Return>", lambda e: entry_plataforma.focus())
        entry_imagem.bind("<Return>", lambda e: adicionar_a_fila())
        
        # Inicia o monitoramento
        self.monitorar_clipboard(toplevel, entry_nome, entry_desc, entry_preco, entry_imagem, entry_link, entry_plataforma)

    # --- LÓGICA DE FILA E EXPORTAÇÃO ---
    
    def carregar_fila_temporaria(self):
        if os.path.exists(TEMP_FILE):
            try:
                with open(TEMP_FILE, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return []
        return []

    def salvar_fila_temporaria(self):
        with open(TEMP_FILE, 'w', encoding='utf-8') as f:
            json.dump(self.fila_produtos, f, ensure_ascii=False, indent=4)

    def tratar_texto(self, texto):
        """Remove caracteres especiais, emojis e espaços extras."""
        if not texto: return ""
        # Normaliza para remover acentos se desejar, ou apenas limpa sujeira
        # Aqui vamos manter acentos (pt-BR) mas remover emojis e símbolos estranhos
        texto_limpo = texto.strip()
        # Remove emojis (range básico)
        texto_limpo = re.sub(r'[^\w\s\-\.,!?:/áàâãéêíóôõúçÁÀÂÃÉÊÍÓÔÕÚÇ]', '', texto_limpo)
        return texto_limpo

    def processar_exportacao(self):
        if not self.fila_produtos:
            messagebox.showinfo("Vazio", "A fila de exportação está vazia.")
            return
            
        if not messagebox.askyesno("Exportar", f"Deseja processar {len(self.fila_produtos)} produtos para o Banco de Dados?"):
            return

        try:
            conexao = mysql.connector.connect(**DB_CONFIG)
            cursor = conexao.cursor()
            
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            path_site_img = os.path.join(base_dir, "frontend_output", "images")
            os.makedirs(path_site_img, exist_ok=True)

            sql = "INSERT INTO produtos (nome, descricao, preco, plataforma, link, imagem, status) VALUES (%s, %s, %s, %s, %s, %s, %s)"
            
            for prod in self.fila_produtos:
                # 1. Tratamento de Dados
                nome_tratado = self.tratar_texto(prod['nome'])
                preco_tratado = prod['preco'].replace(',', '.') # Garante formato decimal
                
                # 2. Inserção Inicial (Para pegar o ID)
                # Inserimos primeiro para gerar o ID, depois atualizamos a imagem com o nome correto
                cursor.execute(sql, (nome_tratado, prod.get('descricao', ''), preco_tratado, prod['plataforma'], prod['link'], "temp", "A Publicar"))
                novo_id = cursor.lastrowid
                
                # 3. Tratamento de Imagem (Renomear com ID do Produto)
                img_final = prod['imagem']
                
                # Se for caminho local (não começa com http), move o arquivo
                if not img_final.startswith("http") and os.path.exists(img_final):
                    ext = os.path.splitext(img_final)[1]
                    # Nome padronizado: produto_ID.ext
                    novo_nome_img = f"produto_{novo_id}{ext}"
                    destino = os.path.join(path_site_img, novo_nome_img)
                    
                    # Copia para pasta do site
                    shutil.copy2(img_final, destino)
                    
                    # Deleta o original do material de apoio (Limpeza)
                    try:
                        os.remove(img_final)
                    except:
                        pass # Se não der pra apagar, segue o jogo
                        
                    img_final = f"images/{novo_nome_img}"
                
                # Atualiza o registro com o caminho final da imagem
                cursor.execute("UPDATE produtos SET imagem = %s WHERE id = %s", (img_final, novo_id))

            
            conexao.commit()
            cursor.close()
            conexao.close()
            
            # Limpa fila e arquivo temporário
            self.fila_produtos = []
            if os.path.exists(TEMP_FILE):
                os.remove(TEMP_FILE)
                
            messagebox.showinfo("Sucesso", "Exportação concluída com sucesso!")
            self.atualizar_grid()
            
        except Exception as e:
            messagebox.showerror("Erro Crítico", f"Falha na exportação: {e}")

    def excluir_produto(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Atenção", "Selecione um produto para excluir.")
            return
        
        item = self.tree.item(selected[0])
        prod_id = item['values'][0]
        
        # Se for item da fila (ID começa com NOVO-)
        if str(prod_id).startswith("NOVO-"):
            idx = int(prod_id.split("-")[1]) - 1
            del self.fila_produtos[idx]
            self.salvar_fila_temporaria()
            self.atualizar_grid()
            return

        if messagebox.askyesno("Confirmar", f"Deseja excluir o produto ID {prod_id}?"):
            try:
                conexao = mysql.connector.connect(**DB_CONFIG)
                cursor = conexao.cursor()
                
                # --- LIMPEZA DE ARQUIVO (Hospedagem) ---
                # Antes de apagar do banco, verificamos se tem imagem física para deletar
                cursor.execute("SELECT imagem FROM produtos WHERE id = %s", (prod_id,))
                row = cursor.fetchone()
                if row and row[0]:
                    img_path = row[0]
                    # Se não for link externo (http...), é arquivo local
                    if not img_path.startswith("http"):
                        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                        # Monta o caminho: .../frontend_output/images/foto.jpg
                        # O caminho no banco já vem como 'images/arquivo.jpg', então o join funciona bem
                        file_path = os.path.join(base_dir, "frontend_output", img_path)
                        
                        if os.path.exists(file_path):
                            try:
                                os.remove(file_path)
                            except Exception as e:
                                print(f"Aviso: Não foi possível deletar a imagem física: {e}")

                cursor.execute("DELETE FROM produtos WHERE id = %s", (prod_id,))
                conexao.commit()
                cursor.close()
                conexao.close()
                self.atualizar_grid()
            except Exception as e:
                messagebox.showerror("Erro", f"Falha ao excluir: {e}")

    def executar_gerador_site(self):
        # Caminho relativo para o script no Backend
        script_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "Backend", "gerar_site.py")
        
        try:
            # Executa o script Python externamente e captura a saída
            result = subprocess.run([sys.executable, script_path], capture_output=True, text=True)
            if result.returncode == 0:
                messagebox.showinfo("Sucesso", f"Site Atualizado!\n\n{result.stdout}")
                self.atualizar_grid() # Atualiza a tabela para ficar tudo verde (Publicado)
            else:
                messagebox.showerror("Erro no Gerador", f"Ocorreu um erro:\n{result.stderr}")
        except Exception as e:
            messagebox.showerror("Erro Crítico", f"Não foi possível executar o script:\n{e}")

if __name__ == "__main__":
    app = SistemaUkiceker()
    app.mainloop()