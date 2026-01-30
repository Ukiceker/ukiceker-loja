# -------------------------------------------------------------------------
# SISTEMA DE GESTÃO UKICEKER (Versão Desktop)
# Arquivo Principal: main.py
# -------------------------------------------------------------------------
import customtkinter as ctk
from tkinter import messagebox
import mysql.connector
import hashlib
import binascii
import os

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

class SistemaUkiceker(ctk.CTk):
    def __init__(self):
        super().__init__()

        # Configuração da Janela
        self.title("Ukiceker Manager - Sistema de Gestão de Afiliados")
        self.geometry("800x600")
        
        # --- TELA DE LOGIN (Simulação) ---
        self.frame_login = ctk.CTkFrame(self)
        self.frame_login.pack(pady=100, padx=100, fill="both", expand=True)

        self.label_titulo = ctk.CTkLabel(self.frame_login, text="Acesso ao Sistema", font=("Roboto", 24))
        self.label_titulo.pack(pady=20)

        self.entry_usuario = ctk.CTkEntry(self.frame_login, placeholder_text="Usuário")
        self.entry_usuario.pack(pady=10)

        self.entry_senha = ctk.CTkEntry(self.frame_login, placeholder_text="Senha", show="*")
        self.entry_senha.pack(pady=10)

        self.btn_entrar = ctk.CTkButton(self.frame_login, text="ENTRAR", command=self.fazer_login)
        self.btn_entrar.pack(pady=20)

        self.label_status = ctk.CTkLabel(self.frame_login, text="v1.0.0 - Versão Comercial", text_color="gray")
        self.label_status.pack(side="bottom", pady=10)

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

        self.btn_produtos = ctk.CTkButton(self.sidebar, text="Gerenciar Produtos")
        self.btn_produtos.pack(pady=10, padx=10)

        self.btn_plataformas = ctk.CTkButton(self.sidebar, text="Configurar Plataformas")
        self.btn_plataformas.pack(pady=10, padx=10)

        self.btn_relatorios = ctk.CTkButton(self.sidebar, text="Relatórios")
        self.btn_relatorios.pack(pady=10, padx=10)
        
        self.btn_sair = ctk.CTkButton(self.sidebar, text="Sair", fg_color="red", command=self.destroy)
        self.btn_sair.pack(side="bottom", pady=20, padx=10)

        # Área de Conteúdo
        self.conteudo = ctk.CTkLabel(self.frame_painel, text="Bem-vindo ao Ukiceker Manager", font=("Roboto", 20))
        self.conteudo.pack(side="top", pady=20)
        
        self.info = ctk.CTkLabel(self.frame_painel, text="Selecione uma opção no menu para começar.\nEste sistema controla sua vitrine e integrações.", font=("Roboto", 14))
        self.info.pack(pady=10)

if __name__ == "__main__":
    app = SistemaUkiceker()
    app.mainloop()