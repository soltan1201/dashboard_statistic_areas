import os
import pandas as pd
from tabulate import tabulate
path_folder_input = '/home/superuser/Dados/mapbiomas/toolkit_areas/src/dados'
name_file = 'legenda.csv'

path_name = os.path.join(path_folder_input, name_file)
df = pd.read_csv(path_name)

print(tabulate(df, headers = 'keys', tablefmt = 'psql', floatfmt=".2f"))