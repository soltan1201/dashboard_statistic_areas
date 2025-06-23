import glob 
import os
import pandas as pd
from tabulate import tabulate

def load_make_csv(mpath, isCaatinga):
    if isCaatinga:
        name_csv = mpath.replace(path_folders_caatinga + '/', '')
    else:
        name_csv = mpath.replace(path_folders_semiarido + '/', '')
    print(f"#{cc} >>> {name_csv}")
    partes = name_csv.split("_")
    print('partes == ', partes)
    try:
        dftmp = pd.read_csv(mpath)
        dftmp = dftmp.drop(['system:index', ".geo"], axis=1)
        if isCaatinga:
            dftmp['limit_shp'] = ['CAATINGA'] * dftmp.shape[0]
            dftmp['nomeVetor'] = [partes[3]] * dftmp.shape[0]
            dftmp['nomeVetor'] = [partes[2]] * dftmp.shape[0]
        else:
            dftmp['limit_shp'] = ['SEMIARIDO'] * dftmp.shape[0]
            dftmp['nomeVetor'] = [partes[4]] * dftmp.shape[0]
            dftmp['nomeVetor'] = [partes[3]] * dftmp.shape[0]
        dftmp = dftmp[lstColunas]
        if cc > 300:
            print(tabulate(dftmp.head(10), headers = 'keys', tablefmt = 'psql'))
            print("=================================================")
            print(list(dftmp.columns))
    except:        
        lst_table_null.append(name_csv)  
        if isCaatinga:
            nomeVet = partes[3]  
            nomeReg = partes[2]
        else:
            nomeVet = partes[4]  
            nomeReg = partes[3]
        # 40 anos 
        dictCol = {
            'area': [0] * 40, 
            'classe': [27]  * 40, 
            'estado_codigo': [partes[-2]]  * 40, 
            'estado_name': [dictEst[partes[-2]]]  * 40, 
            'nomeVetor': [nomeVet]  * 40, 
            'region': [nomeReg]  * 40, 
            'year': lst_year, 
            'limit_shp': ['CAATINGA'] * 40
        }
        dftmp = pd.DataFrame.from_dict(dictCol)
        print(tabulate(dftmp.head(10), headers = 'keys', tablefmt = 'psql'))

    return dftmp

def corregir_campo_region(row):
    region = row['region']
    if region == 'bacia_sao_francisco':
        row['region'] = 'bacia-sao-francisco'
    if region == 'Semiarido-2024':
        row['region'] = 'semiarido'
    return row

dictEst = {
    '21': 'MARANHÃO',
    '22': 'PIAUÍ',
    '23': 'CEARÁ',
    '24': 'RIO GRANDE DO NORTE',
    '25': 'PARAÍBA',
    '26': 'PERNAMBUCO',
    '27': 'ALAGOAS',
    '28': 'SERGIPE',
    '29': 'BAHIA',
    '31': 'MINAS GERAIS',
    '32': 'ESPÍRITO SANTO'
}

path_folders_caatinga = '/home/superuser/Dados/mapbiomas/toolkit_areas/src/dados/AREA-CAATINGA-CORR'
path_folders_semiarido = '/home/superuser/Dados/mapbiomas/toolkit_areas/src/dados/AREA-SEMIARIDO-CORR'
path_folder_output = '/home/superuser/Dados/mapbiomas/toolkit_areas/src/dados'

lstColunas = ['area', 'classe', 'estado_codigo', 'estado_name', 'nomeVetor', 'region', 'year', 'limit_shp']

lst_folders_caat = glob.glob(path_folders_caatinga + '/*.csv')
lst_table_null = []
lst_year = [yy for yy in range(1985, 2025)]
lst_df = []
for cc, npath in enumerate(lst_folders_caat):
    df_tmp = load_make_csv(npath, True)   
    lst_df.append(df_tmp)

# for cc, path_fail in enumerate(lst_table_null):
#     print(f'#{cc} >> {path_fail}')

dfcomp = pd.concat(lst_df, axis=0)
print("size of primeiro corte Caatinga ", dfcomp.shape)  # 91813
print(tabulate(dfcomp.head(20), headers = 'keys', tablefmt = 'psql'))
lst_estados = list(dfcomp['estado_name'].unique())
print(" === lista de estados === ")
for cc, state in enumerate(lst_estados):
    print(f" >>> # {cc} ", state)
lst_regiones = list(dfcomp['region'].unique())
print(" --------- lista de regiões ------------------")
for cc, region in enumerate(lst_regiones):
    print(f" >>> # {cc} ", region)


lst_folders_semiarido = glob.glob(path_folders_semiarido + '/*.csv')
for cc, npath in enumerate(lst_folders_semiarido):
    df_tmp = load_make_csv(npath, False)   
    lst_df.append(df_tmp)

dfcomp = pd.concat(lst_df, axis=0)
print("size of primeiro corte Caatinga ", dfcomp.shape)  # 91813
dfcomp = dfcomp.apply(corregir_campo_region, axis= 1)
print(tabulate(dfcomp.tail(20), headers = 'keys', tablefmt = 'psql'))
lst_estados = list(dfcomp['estado_name'].unique())
print(" === lista de estados === ")
for cc, state in enumerate(lst_estados):
    print(f" >>> # {cc} ", state)
lst_regiones = list(dfcomp['region'].unique())
print(" --------- lista de regiões ------------------")
for cc, region in enumerate(lst_regiones):
    print(f" >>> # {cc} ", region)

print("limit shp ", dfcomp['limit_shp'].unique())
print("size for Caatinga ", dfcomp[dfcomp['limit_shp'] == 'CAATINGA'].shape)
print("size for Semiarido ", dfcomp[dfcomp['limit_shp'] == 'SEMIARIDO'].shape)
path_name_output = os.path.join(path_folder_output, "table_areas_shps_prioritarios.csv")
dfcomp.to_csv(path_name_output, index= False)