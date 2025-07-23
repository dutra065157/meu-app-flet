import flet as ft
import os
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime

# Se for local, carregar variáveis do .env
if os.environ.get("RENDER") != "true":
    from dotenv import load_dotenv
    load_dotenv()

# ===============================
# Conexão com o PostgreSQL
# ===============================
def get_connection():
    DATABASE_URL = os.environ['DATABASE_URL']
    if DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)
    return psycopg2.connect(DATABASE_URL, sslmode="require", cursor_factory=RealDictCursor)

def criar_tabela():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute('''
        CREATE TABLE IF NOT EXISTS galeria (
            id SERIAL PRIMARY KEY,
            nome TEXT,
            descricao TEXT,
            imagem_url TEXT,
            data_cadastro TIMESTAMP DEFAULT NOW()
        )
    ''')
    conn.commit()
    cur.close()
    conn.close()

# ===============================
# Operações no banco
# ===============================
def salvar_item(nome, descricao, imagem_url):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO galeria (nome, descricao, imagem_url) VALUES (%s, %s, %s)",
        (nome, descricao, imagem_url)
    )
    conn.commit()
    cur.close()
    conn.close()

def listar_itens():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM galeria ORDER BY data_cadastro DESC")
    dados = cur.fetchall()
    cur.close()
    conn.close()
    return dados

# ===============================
# Interface com Flet
# ===============================
def main(page: ft.Page):
    page.title = "Galeria"
    page.scroll = True
    page.window_width = 600
    page.theme_mode = ft.ThemeMode.LIGHT

    criar_tabela()

    nome = ft.TextField(label="Nome", width=400)
    descricao = ft.TextField(label="Descrição", multiline=True, width=400)
    imagem = ft.FilePicker()
    imagem_url = ft.TextField(visible=False)

    lista = ft.Column()

    def exibir_lista():
        lista.controls.clear()
        for item in listar_itens():
            lista.controls.append(
                ft.Card(
                    content=ft.Column([
                        ft.Text(f"📌 {item['nome']}", weight="bold"),
                        ft.Text(item['descricao']),
                        ft.Image(src=item['imagem_url'], width=200, height=200),
                        ft.Divider()
                    ])
                )
            )
        page.update()

    def enviar(e):
        if not nome.value or not descricao.value or not imagem_url.value:
            page.snack_bar = ft.SnackBar(ft.Text("Todos os campos são obrigatórios!"), bgcolor=ft.colors.RED)
            page.snack_bar.open = True
            page.update()
            return
        salvar_item(nome.value, descricao.value, imagem_url.value)
        nome.value = descricao.value = imagem_url.value = ""
        exibir_lista()

    def on_upload(e: ft.FilePickerResultEvent):
        if e.files:
            file = e.files[0]
            uploaded_path = f"/tmp/{file.name}"
            with open(uploaded_path, "wb") as f:
                f.write(file.read_bytes())
            imagem_url.value = f"https://render.com/imagens/{file.name}"  # Substituir com CDN se desejar

    imagem.on_result = on_upload

    page.overlay.append(imagem)

    page.add(
        ft.Column([
            ft.Text("📷 Cadastro de Imagens", size=30, weight="bold"),
            nome,
            descricao,
            ft.Row([
                ft.ElevatedButton("Selecionar Imagem", on_click=lambda _: imagem.pick_files()),
                ft.Text("Imagem selecionada:"),
                imagem_url
            ]),
            ft.ElevatedButton("Salvar", on_click=enviar),
            ft.Divider(),
            ft.Text("🖼 Itens cadastrados", size=20, weight="bold"),
            lista
        ])
    )

    exibir_lista()

ft.app(target=main)
