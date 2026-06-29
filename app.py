import io
import streamlit as st
import pandas as pd
from motor_vendas import registrar_venda, registrar_entrada, gerar_relatorio_atualizado

db_url = st.secrets.get("DB_URL")
# No topo do seu app.py:
senha_correta = st.secrets["SENHA_ACESSO"]

def check_password():
    """Retorna True se o usuário digitou a senha correta."""
    def password_entered():
        if st.session_state["password"] == senha_correta:
            st.session_state["password_correct"] = True
            del st.session_state["password"]
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        st.text_input("Digite a senha para acessar:", type="password", on_change=password_entered, key="password")
        return False
    elif not st.session_state["password_correct"]:
        st.text_input("Senha incorreta. Tente novamente:", type="password", on_change=password_entered, key="password")
        return False
    else:
        return True

if not check_password():
    st.stop() # Para a execução do código se a senha não estiver correta

# Configuração da página Streamlit
st.set_page_config(
    page_title="Sistema PDV - Satine",
    page_icon="🛒",
    layout="centered"
)

# Estilização CSS personalizada para um design moderno e responsivo
st.markdown("""
    <style>
        .main-header {
            text-align: center;
            margin-bottom: 0.5rem;
            color: #0F172A;
            font-weight: 700;
        }
        .sub-header {
            text-align: center;
            color: #64748B;
            margin-bottom: 1.5rem;
        }
        .stButton>button {
            border-radius: 8px;
            font-weight: 600;
        }
    </style>
""", unsafe_allow_html=True)

# Título e cabeçalho do sistema
st.markdown("<h1 class='main-header'>🛒 Sistema PDV Satine</h1>", unsafe_allow_html=True)
st.markdown("<p class='sub-header'>Ponto de Venda rápido com controle dinâmico de estoque</p>", unsafe_allow_html=True)

# Divisão da tela principal em duas abas usando st.tabs
tab_venda, tab_estoque = st.tabs(["🛒 Registrar Venda", "📦 Adicionar Estoque"])

# ABA 1: Registrar Venda
with tab_venda:
    st.subheader("Registrar Venda")
    with st.form("form_venda", clear_on_submit=True):
        col_cod, col_qtd = st.columns([3, 1])
        with col_cod:
            codigo_venda = st.text_input(
                "Código do Produto", 
                placeholder="Digite ou bipe o código de barras...",
                key="input_venda_codigo"
            )
        with col_qtd:
            qtd_venda = st.number_input("Quantidade", min_value=1, value=1, step=1, key="input_venda_qtd")
            
        btn_venda = st.form_submit_button("🛒 Confirmar Venda", type="primary", use_container_width=True)

    if btn_venda:
        cod_limpo = codigo_venda.strip() if codigo_venda else ""
        if not cod_limpo:
            st.warning("⚠️ Por favor, insira ou bipe um código de produto válido.")
        else:
            sucesso = registrar_venda(cod_limpo, int(qtd_venda))
            if sucesso:
                st.success(f"✅ Venda registrada com sucesso! Produto: **{cod_limpo}** | Quantidade: **{qtd_venda}**")
            else:
                st.error(f"❌ O produto **'{cod_limpo}'** não existe no cadastro da planilha base.")

# ABA 2: Adicionar Estoque
with tab_estoque:
    st.subheader("Adicionar Estoque")
    with st.form("form_estoque", clear_on_submit=True):
        col_cod_e, col_qtd_e = st.columns([3, 1])
        with col_cod_e:
            codigo_estoque = st.text_input(
                "Código do Produto", 
                placeholder="Digite ou bipe o código para reposição...",
                key="input_estoque_codigo"
            )
        with col_qtd_e:
            qtd_estoque = st.number_input("Quantidade", min_value=1, value=1, step=1, key="input_estoque_qtd")
            
        btn_estoque = st.form_submit_button("📦 Confirmar Entrada", type="primary", use_container_width=True)

    if btn_estoque:
        cod_e_limpo = codigo_estoque.strip() if codigo_estoque else ""
        if not cod_e_limpo:
            st.warning("⚠️ Por favor, insira ou bipe um código de produto válido.")
        else:
            sucesso_e = registrar_entrada(cod_e_limpo, int(qtd_estoque))
            if sucesso_e:
                st.success(f"✅ Entrada de estoque registrada com sucesso! Produto: **{cod_e_limpo}** | Quantidade: **{qtd_estoque}**")
            else:
                st.error(f"❌ O produto **'{cod_e_limpo}'** não existe no cadastro da planilha base.")

# Separador visual fora das abas
st.divider()

# SEÇÃO INFERIOR: Fechamento do Dia (mantido fora das abas)
st.subheader("📊 Fechamento do Dia")
st.write("Consolide todas as entradas e vendas registradas no banco de dados e gere o relatório atualizado com o estoque final.")

if st.button("📈 Gerar Fechamento do Dia", use_container_width=True):
    with st.spinner("Processando dados e gerando o relatório..."):
        try:
            df_fechamento = gerar_relatorio_atualizado()
            st.success("🎉 Relatório de Fechamento atualizado com sucesso!")
            
            buffer = io.BytesIO()
            with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                df_fechamento.to_excel(writer, index=False)
            buffer.seek(0)
            
            st.download_button(
                label="📥 Baixar Fechamento_Atualizado.xlsx",
                data=buffer,
                file_name="Fechamento_Atualizado.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                type="primary",
                use_container_width=True
            )
            
            with st.expander("👀 Visualizar prévia dos dados consolidados", expanded=True):
                st.dataframe(df_fechamento, use_container_width=True)
                
        except Exception as e:
            st.error(f"❌ Ocorreu um erro ao gerar o relatório: {e}")
