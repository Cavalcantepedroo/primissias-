import os
import pandas as pd
import streamlit as st
from sqlalchemy import create_engine, text, inspect

# Constantes de configuração
EXCEL_SAIDA = "Fechamento_Atualizado.xlsx"

def obter_engine():
    """
    Obtém a URL do banco de dados a partir de st.secrets["DATABASE_URL"] 
    e retorna uma nova engine do SQLAlchemy configurada para PostgreSQL.
    """
    try:
        db_url = st.secrets["DATABASE_URL"]
    except Exception:
        # Fallback para variável de ambiente caso executado fora do contexto puro do Streamlit
        db_url = os.getenv("DATABASE_URL")
        if not db_url:
            raise KeyError("A chave 'DATABASE_URL' não foi encontrada em st.secrets nem nas variáveis de ambiente.")
            
    # Ajuste para compatibilidade com o SQLAlchemy 1.4+ (postgres:// -> postgresql://)
    if db_url.startswith("postgres://"):
        db_url = db_url.replace("postgres://", "postgresql://", 1)
        
    return create_engine(db_url)

def inicializar_banco_nuvem(engine=None) -> None:
    """
    Cria as tabelas 'vendas_log' e 'entradas_log' no PostgreSQL caso elas não existam.
    Garante sintaxe nativa e compatível com PostgreSQL (SERIAL PRIMARY KEY).
    """
    if engine is None:
        engine = obter_engine()
        
    query_vendas = """
    CREATE TABLE IF NOT EXISTS vendas_log (
        id SERIAL PRIMARY KEY,
        codigo_produto VARCHAR(255) NOT NULL,
        quantidade INTEGER NOT NULL,
        data_venda TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """
    
    query_entradas = """
    CREATE TABLE IF NOT EXISTS entradas_log (
        id SERIAL PRIMARY KEY,
        codigo_produto VARCHAR(255) NOT NULL,
        quantidade INTEGER NOT NULL,
        data_entrada TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """
    
    try:
        with engine.begin() as conn:
            conn.execute(text(query_vendas))
            conn.execute(text(query_entradas))
        print("[SUCESSO] Tabelas 'vendas_log' e 'entradas_log' verificadas/criadas com sucesso no PostgreSQL.")
    except Exception as e:
        print(f"[ERRO] Falha ao inicializar o banco de dados na nuvem: {e}")
        raise

def validar_produto_existente(engine, codigo_produto: str) -> bool:
    """
    Realiza um SELECT 1 na tabela 'planilha_base' no PostgreSQL para verificar se o produto existe.
    Utiliza TRIM() e UPPER() tanto na coluna do banco quanto no parâmetro passado para prevenir falhas
    causadas por espaços invisíveis ou diferenças de caixa alta/baixa (case sensitivity).
    
    Retorna:
        bool: True se o produto existir na planilha_base, False caso contrário.
    """
    try:
        inspector = inspect(engine)
        colunas_info = inspector.get_columns("planilha_base")
        colunas_base = [col["name"] for col in colunas_info]
        
        if not colunas_base:
            print("[ERRO] Tabela 'planilha_base' não encontrada no banco de dados PostgreSQL.")
            return False
            
        # Busca a coluna exata 'Código' ou variações
        col_codigo = next(
            (c for c in colunas_base if c in ['Código', 'codigo', 'codigo_produto', 'código', 'cod_produto']), 
            colunas_base[0]
        )
        
        # Query com TRIM(UPPER("Código")) = TRIM(UPPER(:codigo))
        query = text(f'SELECT 1 FROM planilha_base WHERE TRIM(UPPER("{col_codigo}")) = TRIM(UPPER(:codigo)) LIMIT 1;')
        
        with engine.connect() as conn:
            result = conn.execute(query, {"codigo": str(codigo_produto)})
            return result.fetchone() is not None
    except Exception as e:
        print(f"[ERRO] Falha ao consultar a tabela 'planilha_base' no PostgreSQL: {e}")
        return False

def registrar_venda(codigo_produto: str, quantidade: int) -> bool:
    """
    Registra uma nova venda na tabela 'vendas_log' no PostgreSQL via SQLAlchemy,
    validando previamente se o produto existe na 'planilha_base' (com validação insensível a caixa e espaços).
    
    Parâmetros:
        codigo_produto (str): Código identificador do produto vendido.
        quantidade (int): Quantidade de itens vendidos.
        
    Retorna:
        bool: True se a venda for registrada com sucesso, False caso contrário.
    """
    if not codigo_produto or quantidade <= 0:
        print("[ERRO] Parâmetros inválidos: o código do produto não pode ser vazio e a quantidade deve ser maior que zero.")
        return False
        
    try:
        engine = obter_engine()
        inicializar_banco_nuvem(engine)
        
        # Regra de Validação Crucial à prova de balas
        if not validar_produto_existente(engine, codigo_produto):
            print(f"[RECUSADO] Produto com código '{codigo_produto}' NÃO existe na planilha base. Venda não registrada.")
            return False
            
        print(f"--> Registrando venda no PostgreSQL: Produto '{codigo_produto}', Quantidade: {quantidade}...")
        query = text("INSERT INTO vendas_log (codigo_produto, quantidade) VALUES (:codigo, :qtd);")
        
        with engine.begin() as conn:
            conn.execute(query, {"codigo": str(codigo_produto).strip(), "qtd": int(quantidade)})
            
        print(f"[SUCESSO] Venda do produto '{codigo_produto}' (Quantidade: {quantidade}) registrada no PostgreSQL.")
        return True
    except Exception as e:
        print(f"[ERRO] Falha ao registrar venda no banco de dados PostgreSQL: {e}")
        return False

def registrar_entrada(codigo_produto: str, quantidade: int) -> bool:
    """
    Registra uma nova entrada de estoque na tabela 'entradas_log' no PostgreSQL via SQLAlchemy,
    validando previamente se o produto existe na 'planilha_base' (com validação insensível a caixa e espaços).
    
    Parâmetros:
        codigo_produto (str): Código identificador do produto recebido.
        quantidade (int): Quantidade de itens recebidos.
        
    Retorna:
        bool: True se a entrada for registrada com sucesso, False caso contrário.
    """
    if not codigo_produto or quantidade <= 0:
        print("[ERRO] Parâmetros inválidos: o código do produto não pode ser vazio e a quantidade deve ser maior que zero.")
        return False
        
    try:
        engine = obter_engine()
        inicializar_banco_nuvem(engine)
        
        # Regra de Validação Crucial à prova de balas
        if not validar_produto_existente(engine, codigo_produto):
            print(f"[RECUSADO] Produto com código '{codigo_produto}' NÃO existe na planilha base. Entrada não registrada.")
            return False
            
        print(f"--> Registrando entrada no PostgreSQL: Produto '{codigo_produto}', Quantidade: {quantidade}...")
        query = text("INSERT INTO entradas_log (codigo_produto, quantidade) VALUES (:codigo, :qtd);")
        
        with engine.begin() as conn:
            conn.execute(query, {"codigo": str(codigo_produto).strip(), "qtd": int(quantidade)})
            
        print(f"[SUCESSO] Entrada do produto '{codigo_produto}' (Quantidade: {quantidade}) registrada no PostgreSQL.")
        return True
    except Exception as e:
        print(f"[ERRO] Falha ao registrar entrada no banco de dados PostgreSQL: {e}")
        return False

def gerar_relatorio_atualizado(caminho_saida: str = EXCEL_SAIDA) -> pd.DataFrame:
    """
    Executa uma consulta SQL avançada no PostgreSQL via SQLAlchemy unindo a 'planilha_base'
    com as tabelas 'entradas_log' e 'vendas_log' via LEFT JOIN.
    
    Calcula o estoque dinâmico atualizado:
    Estoque Final = Estoque Inicial + Total Entradas - Total Vendas
    
    Trata valores nulos como 0 via COALESCE e compara códigos aplicando TRIM(UPPER(...)) para máxima precisão.
    """
    print("--> Gerando relatório de fechamento atualizado no PostgreSQL...")
    try:
        engine = obter_engine()
        inicializar_banco_nuvem(engine)
        
        inspector = inspect(engine)
        colunas_info = inspector.get_columns("planilha_base")
        colunas_base = [col["name"] for col in colunas_info]
        
        if not colunas_base:
            raise ValueError("A tabela 'planilha_base' não foi encontrada ou está vazia no banco de dados PostgreSQL.")
            
        col_codigo = next(
            (c for c in colunas_base if c in ['Código', 'codigo', 'codigo_produto', 'código', 'cod_produto']), 
            colunas_base[0]
        )
        col_estoque = next(
            (c for c in colunas_base if c.lower() in ['estoque_inicial', 'estoque', 'qtd_inicial', 'quantidade_inicial', 'quantidade', 'saldo_inicial']), 
            colunas_base[1] if len(colunas_base) > 1 else colunas_base[0]
        )
        
        # Consulta SQL em PostgreSQL unindo entradas e vendas com tratamento de TRIM e UPPER nas junções
        query_sql = f"""
        SELECT 
            pb.*,
            COALESCE(e.total_entradas, 0) AS total_entradas,
            COALESCE(v.total_vendido, 0) AS total_vendido,
            (pb."{col_estoque}" + COALESCE(e.total_entradas, 0) - COALESCE(v.total_vendido, 0)) AS estoque_final
        FROM planilha_base pb
        LEFT JOIN (
            SELECT 
                TRIM(UPPER(codigo_produto)) AS codigo_produto_norm, 
                SUM(quantidade) AS total_entradas
            FROM entradas_log
            GROUP BY TRIM(UPPER(codigo_produto))
        ) e ON TRIM(UPPER(pb."{col_codigo}")) = e.codigo_produto_norm
        LEFT JOIN (
            SELECT 
                TRIM(UPPER(codigo_produto)) AS codigo_produto_norm, 
                SUM(quantidade) AS total_vendido
            FROM vendas_log
            GROUP BY TRIM(UPPER(codigo_produto))
        ) v ON TRIM(UPPER(pb."{col_codigo}")) = v.codigo_produto_norm;
        """
        
        with engine.connect() as conn:
            df_relatorio = pd.read_sql_query(text(query_sql), conn)
            
        df_relatorio.to_excel(caminho_saida, index=False)
        print(f"[SUCESSO] Relatório gerado e exportado com sucesso para '{caminho_saida}'. (Total de itens: {len(df_relatorio)})")
        return df_relatorio
        
    except Exception as e:
        print(f"[ERRO] Falha ao gerar o relatório atualizado no PostgreSQL: {e}")
        raise

if __name__ == "__main__":
    print("==================================================")
    print("  MOTOR DE VENDAS (VALIDAÇÃO DE CÓDIGO À PROVA DE BALAS)  ")
    print("==================================================")
