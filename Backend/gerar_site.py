# -------------------------------------------------------------------------
# ARQUIVO: gerar_site.py
# FUNÇÃO: Gerador de Site Estático (Static Site Generator)
# DESCRIÇÃO: Conecta no banco, pega os produtos e preenche o template HTML.
# -------------------------------------------------------------------------

import mysql.connector
import os
from jinja2 import Environment, FileSystemLoader

def gerar_site_estatico():
    print("Iniciando geração do site...")
    
    try:
        # --- PASSO 1: Conectar ao Banco de Dados ---
        conexao = mysql.connector.connect(
            host='127.0.0.1',
            user='ukiceker_app',
            password='Ukiceker@123',
            database='ukiceker_db',
            use_pure=True
        )
        cursor = conexao.cursor()
        
        # --- PASSO 2: Buscar Produtos (Dinâmico e Escalável) ---
        # Buscamos todos os produtos, exceto Amazon (conforme solicitado), ordenados pela plataforma
        sql = "SELECT nome, preco, imagem, link, plataforma FROM produtos WHERE plataforma != 'Amazon' ORDER BY plataforma"
        cursor.execute(sql)
        
        # Dicionário para agrupar produtos por plataforma
        # Ex: {'Shopee': {'id': 'shopee', 'produtos': [...]}, ...}
        plataformas_dict = {}

        for (nome, preco, imagem, link, nome_plataforma) in cursor:
            if nome_plataforma not in plataformas_dict:
                # Cria o ID seguro para HTML (Ex: "Mercado Livre" vira "mercado-livre")
                id_safe = nome_plataforma.lower().replace(' ', '-')
                plataformas_dict[nome_plataforma] = {
                    'nome': nome_plataforma,
                    'id': id_safe,
                    'produtos': []
                }
            
            plataformas_dict[nome_plataforma]['produtos'].append({
                'nome': nome,
                'preco': str(preco).replace('.', ','), # Formata preço (ponto para vírgula)
                'imagem': imagem,
                'link': link
            })
        
        # Converte para lista para o Jinja2 processar
        lista_plataformas = list(plataformas_dict.values())
        print(f"Plataformas processadas: {list(plataformas_dict.keys())}")

        # --- PASSO 3: Configurar o Template (Jinja2) ---
        env = Environment(loader=FileSystemLoader('/app/templates'))
        template = env.get_template('index_template.html') # Usando o novo nome do template
        
        # --- PASSO 4: Renderizar (Preencher o molde com dados) ---
        # Agora passamos apenas uma lista inteligente, não mais listas separadas
        html_final = template.render(plataformas=lista_plataformas)
        
        # --- PASSO 5: Salvar o arquivo final na pasta pública ---
        with open('/app/frontend_output/index.html', 'w', encoding='utf-8') as arquivo:
            arquivo.write(html_final)
            
        print("SUCESSO: Site atualizado em 'frontend/index.html'!")
        
    except Exception as e:
        print(f"ERRO: {e}")

if __name__ == "__main__":
    gerar_site_estatico()