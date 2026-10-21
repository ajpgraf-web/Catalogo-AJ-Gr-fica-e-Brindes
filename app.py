import streamlit as st
import pandas as pd
import urllib.parse
import os
import unicodedata

# 1. Configuração da página (DEVE SER A PRIMEIRA CHAMADA DO STREAMLIT)
st.set_page_config(
    page_title="A.J. Gráfica & Brindes | Catálogo",
    page_icon="🛍️",
    layout="wide"
)

# 2. Ocultar menu, cabeçalho, rodapé e estilização de fundo
hide_streamlit_style = """
            <style>
            #MainMenu {visibility: hidden;}
            header {visibility: hidden;}
            footer {visibility: hidden;}
            [data-testid="stHeader"] {visibility: hidden;}
            [data-testid="stToolbar"] {visibility: hidden;}
            .stApp {
                background-color: #f8f9fa;
            }
            </style>
            """
st.markdown(hide_streamlit_style, unsafe_allow_html=True)

SEU_WHATSAPP = "5591987140119"
IMAGEM_PADRAO = "https://via.placeholder.com/400x300?text=Sem+Foto"


# Carrega os produtos SEM cache para garantir atualizações instantâneas
def carregar_produtos():
    if os.path.exists("produtos.xlsx"):
        df = pd.read_excel("produtos.xlsx")
    elif os.path.exists("produtos.xls"):
        df = pd.read_excel("produtos.xls")
    else:
        for arq in os.listdir("."):
            if "produto" in arq.lower() and arq.endswith(".csv"):
                for sep in [",", ";"]:
                    for enc in ["latin1", "cp1252", "iso-8859-1", "utf-8"]:
                        try:
                            df = pd.read_csv(arq, sep=sep, encoding=enc)
                            if 'categoria' in df.columns or 'nome' in df.columns:
                                return df
                        except:
                            continue
        raise FileNotFoundError("Arquivo de produtos não encontrado.")
    return df


# Função blindada para encontrar a imagem correta
def encontrar_imagem(row):
    if not os.path.exists("imagens"):
        return IMAGEM_PADRAO

    val_col = str(row.get('imagem', '')).strip()
    if val_col and val_col.lower() != 'nan':
        nome_limpo = val_col.replace('\\', '/').split('/')[-1].split('?')[0].strip()
        if nome_limpo.endswith('.'):
            nome_limpo = nome_limpo[:-1]
        caminho = os.path.join("imagens", nome_limpo)
        if os.path.exists(caminho):
            return caminho

    # Busca por aproximação usando o nome do produto
    nome_prod = str(row.get('nome', '')).strip().lower()
    norm_nome = unicodedata.normalize('NFD', nome_prod).encode('ascii', 'ignore').decode('utf-8')
    palavras = [p for p in norm_nome.replace('(', '').replace(')', '').replace('-', ' ').split() if len(p) > 2]

    arquivos_pasta = os.listdir("imagens")
    melhor_match = None
    max_pontos = 0

    for arq in arquivos_pasta:
        arq_norm = unicodedata.normalize('NFD', arq.lower()).encode('ascii', 'ignore').decode('utf-8')
        pontos = sum(1 for p in palavras if p in arq_norm)
        if pontos > max_pontos:
            max_pontos = pontos
            melhor_match = arq

    if melhor_match and max_pontos > 0:
        return os.path.join("imagens", melhor_match)

    return IMAGEM_PADRAO


# Exibe a logo oficial centralizada ou no topo (com largura ajustada para 250 pixels)
if os.path.exists("imagens/logo.png"):
    st.image("imagens/logo.png", width=250)
elif os.path.exists("imagens/logo.jpg"):
    st.image("imagens/logo.jpg", width=250)
else:
    st.title("✨ A.J. Gráfica & Brindes")

st.write("Escolha seus produtos, monte seu pedido e envie direto para nosso WhatsApp!")

try:
    df_produtos = carregar_produtos()
    df_produtos.columns = [c.strip().lower() for c in df_produtos.columns]

    # Remove linhas totalmente vazias ou sem nome (evita o erro do 'nan')
    df_produtos = df_produtos.dropna(subset=['nome'])
    df_produtos = df_produtos[df_produtos['nome'].astype(str).str.strip().str.lower() != 'nan']

    # Filtro de Categoria
    categorias = ["Todas"] + list(df_produtos["categoria"].dropna().unique())
    categoria_selecionada = st.selectbox("📂 Filtrar por Categoria:", categorias)

    if categoria_selecionada != "Todas":
        df_exibicao = df_produtos[df_produtos["categoria"] == categoria_selecionada]
    else:
        df_exibicao = df_produtos

    st.markdown(f"*Mostrando {len(df_exibicao)} de {len(df_produtos)} produtos cadastrados.*")
    st.markdown("---")

    carrinho = []
    total_geral = 0.0

    # Exibição dos produtos em formato de cartão responsivo (perfeito para telemóvel e PC)
    for idx, row in df_exibicao.reset_index(drop=True).iterrows():

        with st.container():
            col_img, col_info = st.columns([1, 2])

            with col_img:
                caminho_img = encontrar_imagem(row)
                st.image(caminho_img, use_container_width=True)

            with col_info:
                st.subheader(row['nome'])
                st.caption(row.get('descricao', ''))
                st.markdown(f"### **R$ {float(row['preco_un']):.2f}**")

                # Seletor de Quantidade
                qtd = st.number_input(
                    "Quantidade:",
                    min_value=0,
                    value=0,
                    step=1,
                    key=f"prod_{idx}_{row.get('id', idx)}"
                )

                if qtd > 0:
                    subtotal = qtd * float(row['preco_un'])
                    carrinho.append({
                        "nome": row['nome'],
                        "qtd": qtd,
                        "preco_un": float(row['preco_un']),
                        "subtotal": subtotal
                    })
                    total_geral += subtotal

            st.markdown("---")

    # Sidebar / Carrinho
    st.sidebar.header("🛒 Seu Pedido")
    nome_cliente = st.sidebar.text_input("Seu Nome:")
    obs_cliente = st.sidebar.text_area("Observações / Detalhes da Arte:")

    if carrinho:
        st.sidebar.markdown("---")
        for item in carrinho:
            st.sidebar.write(f"• **{item['qtd']}x** {item['nome']}")
            st.sidebar.caption(f"Subtotal: R$ {item['subtotal']:.2f}")

        st.sidebar.markdown(f"### **Total: R$ {total_geral:.2f}**")

        if st.sidebar.button("📲 Finalizar no WhatsApp", type="primary"):
            if not nome_cliente:
                st.sidebar.error("Por favor, digite seu nome antes de enviar!")
            else:
                mensagem = f"🛒 *NOVO PEDIDO DO CATÁLOGO*\n"
                mensagem += f"👤 *Cliente:* {nome_cliente}\n"
                if obs_cliente:
                    mensagem += f"📝 *Obs:* {obs_cliente}\n"
                mensagem += f"\n📌 *Itens Selecionados:*\n"

                for item in carrinho:
                    mensagem += f"• {item['qtd']}x {item['nome']} - R$ {item['subtotal']:.2f}\n"

                mensagem += f"\n💰 *Total Estimado:* R$ {total_geral:.2f}\n"
                mensagem += "💬 *Aguardando confirmação!*"

                mensagem_url = urllib.parse.quote(mensagem)
                link_whatsapp = f"https://wa.me/{SEU_WHATSAPP}?text={mensagem_url}"

                st.sidebar.link_button("👉 Abrir conversa no WhatsApp", link_whatsapp)
    else:
        st.sidebar.info("Seu carrinho está vazio. Selecione a quantidade de algum produto para começar!")

except Exception as e:
    st.error(f"Erro ao carregar os produtos: {e}")