import os
import pandas as pd
from tabulate import tabulate
path_folder_input = '/home/superuser/Dados/mapbiomas/toolkit_areas/src/dados'
name_file = 'table_areas_shps_prioritarios.csv'

def corregir_dados(row):
    nregion = row['region']
    nvetor = row['nomeVetor']
    if nregion == 'Assent_Br':
        row['region'] = 'Assent-Br'

    if nvetor == 'Assent':
        row['nomeVetor'] = 'Assent-Br'
    if nvetor == 'Semiarido-2024':
        row['nomeVetor'] = 'semiarido'

    return row
path_name = os.path.join(path_folder_input, name_file)
df = pd.read_csv(path_name)

print(tabulate(df.head(5), headers = 'keys', tablefmt = 'psql', floatfmt=".2f"))
print(list(df['region'].unique()))
print("Nome de Vectors ", list(df['nomeVetor'].unique()))

# df = df.apply(corregir_dados, axis= 1)
# df.to_csv(path_name, index= False)