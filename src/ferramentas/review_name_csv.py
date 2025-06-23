import glob 
import os

path_folders_caatinga = '/home/superuser/Dados/mapbiomas/toolkit_areas/src/dados/AREA-CAATINGA-CORR'
path_folders_semiarido = '/home/superuser/Dados/mapbiomas/toolkit_areas/src/dados/AREA-SEMIARIDO-CORR'
lstColunas = ['area', 'classe', 'estado_codigo', 'estado_name', 'nomeVetor', 'region', 'year', 'limit_shp']

lst_folders_caat = glob.glob(path_folders_caatinga + '/*.csv')
lst_folders_semiar = glob.glob(path_folders_semiarido + '/*.csv')
# modificandoo folder de Caatinga
for cc, npath in enumerate(lst_folders_caat):
    name_csv = npath.replace(path_folders_caatinga + '/', '')
    print(f"#{cc} >>> {name_csv}")
    if "_bacia_sao_francisco_" in name_csv:
        new_name = name_csv.replace("_bacia_sao_francisco_", "_bacia-sao-francisco_")
        print(" =========== > ", new_name)
        current_file_name = npath
        new_file_name = os.path.join(path_folders_caatinga, new_name)
        os.rename(current_file_name, new_file_name)
    if "_micro_RH_" in name_csv:
        new_name = name_csv.replace("_micro_RH_", "_micro-RH_")
        print(" =========== > ", new_name)
        current_file_name = npath
        new_file_name = os.path.join(path_folders_caatinga, new_name)
        os.rename(current_file_name, new_file_name)

# modificando o folder de Semiarido
for cc, npath in enumerate(lst_folders_semiar):
    name_csv = npath.replace(path_folders_semiarido + '/', '')
    print(f"#{cc} >>> {name_csv}")
    if "_bacia_sao_francisco_" in name_csv:
        new_name = name_csv.replace("_bacia_sao_francisco_", "_bacia-sao-francisco_")
        print(" =========== > ", new_name)
        current_file_name = npath
        new_file_name = os.path.join(path_folders_semiarido, new_name)
        os.rename(current_file_name, new_file_name)

    if "_micro_RH_" in name_csv:
        new_name = name_csv.replace("_micro_RH_", "_micro-RH_")
        print(" =========== > ", new_name)
        current_file_name = npath
        new_file_name = os.path.join(path_folders_semiarido, new_name)
        os.rename(current_file_name, new_file_name)