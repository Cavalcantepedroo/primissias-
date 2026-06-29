import pandas as pd
from sqlalchemy import create_engine


def migrar_dados():

    # URL do Supabase (Pooler)

    db_url = "postgresql://postgres.bgypyuvazepwrvafsxdc:qqppwwooeeii@aws-1-us-west-2.pooler.supabase.com:5432/postgres?options=-c%20search_path=public"

    engine = create_engine(db_url)


    print("A carregar Excel...")
    df = pd.read_excel('Pedido Satine - Ordenado.xlsx')

    # 1. Limpeza
    df['Código'] = df['Código'].astype(str).str.strip().str.upper()

    # 2. Definição automática de colunas
    colunas_numericas = ['Qtde.', 'Unidade', 'Vl. Total', 'Venda', 'Estoque']
    colunas_texto = ['Referência / Descrição', 'Unid.', 'Embal.', 'Vl. Unit.']

    agg_dict = {col: 'sum' for col in colunas_numericas}
    agg_dict.update({col: 'first' for col in colunas_texto})

    # 3. Agrupamento
    df_agrupado = df.groupby('Código').agg(agg_dict).reset_index()

    # 4. Ordem das colunas
    ordem_final = [
        'Código', 'Referência / Descrição', 'Unid.', 'Embal.', 
        'Qtde.', 'Vl. Unit.', 'Unidade', 'Vl. Total', 'Venda', 'Estoque'
    ]
    df_agrupado = df_agrupado[ordem_final]

    # 5. Envio
    print("A enviar dados consolidados e somados...")
    df_agrupado.to_sql('planilha_base', engine, if_exists='replace', index=False)
    print("✅ Sucesso!")

if __name__ == '__main__':
    migrar_dados()