# init_db.py
import pandas as pd
from app import create_app, db
from app.models import TimeSeriesData, LimitArea, ClassInfo

# Caminhos para os arquivos CSV na pasta 'dados'
DATA_SERIES_CSV = 'dados/table_areas_shps_prioritarios.csv'
LIMIT_AREA_CSV = 'dados/areas_biomas_semiarido.csv'
CLASS_INFO_CSV = 'dados/legenda.csv'

def populate_database():
    """Lê os CSVs e popula o banco de dados SQLite."""
    app = create_app()
    with app.app_context():
        print("Apagando banco de dados antigo (se existir)...")
        db.drop_all()
        print("Criando novas tabelas...")
        db.create_all()

        # Popular tabela de séries temporais
        print(f"Lendo {DATA_SERIES_CSV}...")
        df_series = pd.read_csv(DATA_SERIES_CSV)
        # Renomeia colunas para bater com o modelo se necessário
        # df_series.rename(columns={'old_name': 'new_name'}, inplace=True)
        df_series.to_sql(TimeSeriesData.__tablename__, db.engine, if_exists='append', index=False)
        print("Tabela 'time_series_data' populada.")

        # Popular tabela de áreas limite
        print(f"Lendo {LIMIT_AREA_CSV}...")
        df_limits = pd.read_csv(LIMIT_AREA_CSV)
        df_limits.to_sql(LimitArea.__tablename__, db.engine, if_exists='append', index=False)
        print("Tabela 'limit_area' populada.")

        # Popular tabela de informações de classe
        print(f"Lendo {CLASS_INFO_CSV}...")
        df_classes = pd.read_csv(CLASS_INFO_CSV)
        # Limpa e renomeia colunas para bater com o modelo
        # df_classes.rename(columns={
        #     'COLEÇÃO 9 - CLASSES': 'class_name',
        #     'Code ID': 'code_id',  # Ajuste os nomes exatos das colunas do seu CSV
        #     'Hexacode Number': 'hex_color'
        # }, inplace=True)
        # Remove as aspas dos valores se houver
        for col in df_classes.columns:
            if df_classes[col].dtype == 'object':
                 df_classes[col] = df_classes[col].str.strip().str.replace('"', '')

        df_classes['code_id'] = pd.to_numeric(df_classes['code_id'])
        df_classes.to_sql(ClassInfo.__tablename__, db.engine, if_exists='append', index=False)
        print("Tabela 'class_info' populada.")

        print("\n Banco de dados criado e populado com sucesso!")

if __name__ == '__main__':
    populate_database()