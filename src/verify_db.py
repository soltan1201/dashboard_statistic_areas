# verify_db.py
import pandas as pd
from app import create_app, db
from app.models import TimeSeriesData, LimitArea, ClassInfo

# Caminhos para os arquivos CSV originais para comparação
DATA_SERIES_CSV = 'dados/table_areas_shps_prioritarios.csv'
LIMIT_AREA_CSV = 'dados/areas_biomas_semiarido.csv'
CLASS_INFO_CSV = 'dados/legenda.csv'

def run_verification():
    """Roda uma série de verificações no banco de dados e imprime um relatório."""
    
    app = create_app()
    with app.app_context():
        print("--- INICIANDO VERIFICAÇÃO DO BANCO DE DADOS ---")

        # === VERIFICAÇÃO 1: CONTAGEM DE LINHAS ===
        print("\n[VERIFICAÇÃO 1: Contagem de Linhas vs CSV original]")
        
        try:
            # Tabela TimeSeriesData
            csv_rows = len(pd.read_csv(DATA_SERIES_CSV))
            db_rows = db.session.query(TimeSeriesData).count()
            print(f"  - Tabela 'time_series_data': {'OK' if csv_rows == db_rows else 'ERRO'}")
            print(f"    > CSV: {csv_rows} linhas | Banco de Dados: {db_rows} linhas")

            # Tabela LimitArea
            csv_rows = len(pd.read_csv(LIMIT_AREA_CSV))
            db_rows = db.session.query(LimitArea).count()
            print(f"  - Tabela 'limit_area': {'OK' if csv_rows == db_rows else 'ERRO'}")
            print(f"    > CSV: {csv_rows} linhas | Banco de Dados: {db_rows} linhas")
            
            # Tabela ClassInfo
            csv_rows = len(pd.read_csv(CLASS_INFO_CSV))
            db_rows = db.session.query(ClassInfo).count()
            print(f"  - Tabela 'class_info': {'OK' if csv_rows == db_rows else 'ERRO'}")
            print(f"    > CSV: {csv_rows} linhas | Banco de Dados: {db_rows} linhas")

        except FileNotFoundError as e:
            print(f"  ERRO: Arquivo CSV não encontrado: {e.filename}")


        # === VERIFICAÇÃO 2: AMOSTRA DE DADOS ===
        print("\n[VERIFICAÇÃO 2: Amostra de Dados (primeiro registro)]")
        first_record = db.session.query(TimeSeriesData).first()
        if first_record:
            print(f"  - Primeira linha de 'time_series_data':")
            print(f"    > Ano: {first_record.year}, Classe: {first_record.classe}, Area: {first_record.area}, Bioma: {first_record.limit_shp}")
        else:
            print("  - Tabela 'time_series_data' está vazia.")


        # === VERIFICAÇÃO 3: INTEGRIDADE DE CHAVES (MUITO IMPORTANTE) ===
        print("\n[VERIFICAÇÃO 3: Integridade de Chaves Estrangeiras (Classe ID)]")
        
        # Pega todos os IDs de classe únicos da tabela de dados principal
        ids_na_tabela_de_dados = {row.classe for row in db.session.query(TimeSeriesData.classe).distinct()}
        
        # Pega todos os IDs de classe únicos da tabela de legendas
        ids_na_tabela_de_legenda = {row.code_id for row in db.session.query(ClassInfo.code_id).distinct()}
        
        # Verifica se todos os IDs da tabela principal existem na tabela de legenda
        if ids_na_tabela_de_dados.issubset(ids_na_tabela_de_legenda):
            print("  - 'classe' <-> 'code_id': OK")
            print("    > Todos os IDs de classe presentes nos dados têm uma correspondência na legenda.")
        else:
            print("  - 'classe' <-> 'code_id': ERRO DE INTEGRIDADE")
            missing_ids = ids_na_tabela_de_dados - ids_na_tabela_de_legenda
            print(f"    > Os seguintes IDs de classe estão nos dados mas NÃO na legenda: {sorted(list(missing_ids))}")
            print("    > Isso pode causar erros ao tentar buscar nomes ou cores das classes.")

        print("\n--- VERIFICAÇÃO CONCLUÍDA ---")


if __name__ == '__main__':
    run_verification()