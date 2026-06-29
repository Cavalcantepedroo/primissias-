import os
import sqlite3
import pandas as pd

# Constantes de configuração
EXCEL_FILE = "Pedido Satine - Ordenado.xlsx"
DB_FILE = "sistema_vendas.db"

def ler_excel(caminho_arquivo: str) -> pd.DataFrame:
    """
    Lê o arquivo Excel especificado e retorna um DataFrame do Pandas.
    """
    if not os.path.exists(caminho_arquivo):
        raise FileNotFoundError(f"O arquivo '{caminho_arquivo}' não foi encontrado no diretório atual.")
    
    print(f"--> Lendo arquivo Excel: '{caminho_arquivo}'...")
    try:
        df = pd.read_excel(caminho_arquivo)
        print(f"[SUCESSO] Arquivo lido com sucesso. Total de registros: {len(df)}")
        return df
    except Exception as e:
        print(f"[ERRO] Falha ao ler o arquivo Excel '{caminho_arquivo}': {e}")
        raise

def conectar_banco(caminho_db: str) -> sqlite3.Connection:
    """
    Cria e/ou conecta ao banco de dados SQLite.
    """
    print(f"--> Conectando ao banco de dados SQLite: '{caminho_db}'...")
    try:
        conn = sqlite3.connect(caminho_db)
        print(f"[SUCESSO] Conexão com o banco de dados '{caminho_db}' estabelecida.")
        return conn
    except sqlite3.Error as e:
        print(f"[ERRO] Falha ao conectar ao banco de dados '{caminho_db}': {e}")
        raise

def salvar_planilha_base(df: pd.DataFrame, conn: sqlite3.Connection, nome_tabela: str = "planilha_base") -> None:
    """
    Salva os dados do DataFrame na tabela relacional 'planilha_base'.
    """
    print(f"--> Salvando dados na tabela '{nome_tabela}'...")
    try:
        # Salva o DataFrame na tabela SQLite (substitui caso já exista)
        df.to_sql(nome_tabela, conn, if_exists="replace", index=False)
        print(f"[SUCESSO] Dados salvos com sucesso na tabela '{nome_tabela}'.")
    except Exception as e:
        print(f"[ERRO] Falha ao salvar dados na tabela '{nome_tabela}': {e}")
        raise

def criar_tabela_vendas_log(conn: sqlite3.Connection) -> None:
    """
    Cria a tabela de histórico (append-only log) 'vendas_log' caso ela não exista.
    """
    print("--> Criando tabela de histórico 'vendas_log'...")
    query_criacao = """
    CREATE TABLE IF NOT EXISTS vendas_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        codigo_produto TEXT NOT NULL,
        quantidade INTEGER NOT NULL,
        data_venda TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """
    try:
        cursor = conn.cursor()
        cursor.execute(query_criacao)
        conn.commit()
        print("[SUCESSO] Tabela 'vendas_log' criada/verificada com sucesso.")
    except sqlite3.Error as e:
        print(f"[ERRO] Falha ao criar a tabela 'vendas_log': {e}")
        raise

def criar_tabela_entradas_log(conn: sqlite3.Connection) -> None:
    """
    Cria a tabela de histórico (append-only log) 'entradas_log' caso ela não exista.
    """
    print("--> Criando tabela de histórico 'entradas_log'...")
    query_criacao = """
    CREATE TABLE IF NOT EXISTS entradas_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        codigo_produto TEXT NOT NULL,
        quantidade INTEGER NOT NULL,
        data_entrada TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """
    try:
        cursor = conn.cursor()
        cursor.execute(query_criacao)
        conn.commit()
        print("[SUCESSO] Tabela 'entradas_log' criada/verificada com sucesso.")
    except sqlite3.Error as e:
        print(f"[ERRO] Falha ao criar a tabela 'entradas_log': {e}")
        raise

def main():
    print("==================================================")
    print("   INICIANDO CONFIGURAÇÃO DO BANCO DE DADOS       ")
    print("==================================================\n")
    
    conn = None
    try:
        # 1. Conectar ao Banco de Dados (ou criar se não existir)
        conn = conectar_banco(DB_FILE)
        
        # 2. Ler o arquivo Excel
        df = ler_excel(EXCEL_FILE)
        
        # 3. Salvar na tabela planilha_base
        salvar_planilha_base(df, conn)
        
        # 4. Criar as tabelas de logs
        criar_tabela_vendas_log(conn)
        criar_tabela_entradas_log(conn)
        
        print("\n==================================================")
        print("   PROCESSO CONCLUÍDO COM SUCESSO!                ")
        print("==================================================")
        
    except Exception as e:
        print("\n==================================================")
        print("   PROCESSO INTERROMPIDO DEVIDO A ERROS.          ")
        print("==================================================")
    finally:
        if conn:
            conn.close()
            print("--> Conexão com o banco de dados encerrada.")

if __name__ == "__main__":
    main()
