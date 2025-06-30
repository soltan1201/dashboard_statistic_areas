# app/api/routes.py
import os
import pandas as pd
from tabulate import tabulate
import geopandas as gpd
from sqlalchemy import func
from flask import  Blueprint, request, jsonify
# Importe os modelos do banco de dados a partir da instância principal do db
from app import db
from app.models import TimeSeriesData, ClassInfo, LimitArea

# 1. Cria o Blueprint para a API
api_bp = Blueprint('api', __name__)

pathparent = str(os.getcwd())
print(" we set the path ==> ", os.getcwd())
# NOTA: Carregar os geojson pode ser lento. Para produção, considere cachear.
# Os caminhos devem ser ajustados para os seus arquivos.
GEOJSON_PATHS = {
    "areaQuil": os.path.join(pathparent, "dados/geojson/areas_Quilombolas.geojson"),  # areaQuil
    "Assent-Br": os.path.join(pathparent, "dados/geojson/Assentamento_Brasil.geojson"),  # Assent-Br
    "bacia-sao-francisco": os.path.join(pathparent, "dados/geojson/bacia_sao_francisco.geojson"),  # bacia-sao-francisco
    "br_estados_shp": os.path.join(pathparent, "dados/geojson/br_estados_shp.geojson"),
    "energias-renovaveis": os.path.join(pathparent, "dados/geojson/energiasE.geojson"),  # energias-renovaveis
    "macro-RH": os.path.join(pathparent, "dados/geojson/macro_RH.geojson"),  # macro-RH
    "matopiba": os.path.join(pathparent, "dados/geojson/matopiba.geojson"),  # matopiba
    "meso-RH": os.path.join(pathparent, "dados/geojson/meso_RH.geojson"),  # meso-RH
    "micro-RH": os.path.join(pathparent, "dados/geojson/micro_RH.geojson"),   # micro-RH
    "nucleos-desert": os.path.join(pathparent, "dados/geojson/nucleos_desertificacao.geojson"),    # nucleos-desert
    "prioridade-conservacao-V1": os.path.join(pathparent, "dados/geojson/prioridade-conservacao-V1.geojson"),  # prioridade-conservacao-V1
    "prioridade-conservacao-V2": os.path.join(pathparent, "dados/geojson/prioridade-conservacao-V2.geojson"),  # prioridade-conservacao-V2 
    "res-biosf": os.path.join(pathparent, "dados/geojson/reserva_biosfera.geojson"),   # res-biosf
    "semiarido": os.path.join(pathparent, "dados/geojson/semiarido2024.geojson"),  # semiarido
    "tis-port": os.path.join(pathparent, "dados/geojson/tis_poligonais_portarias.geojson"), # tis-port
    "vetor_biomas_250": os.path.join(pathparent, "dados/geojson/vetor_biomas_250.geojson"),
    "UnidCons-S": os.path.join(pathparent, "dados/geojson/UnidadesConservacao_S.geojson"),   # UnidCons-S 
}

# Pré-carregar os GeoDataFrames para melhor performance
gdfs = {}
for name, path in GEOJSON_PATHS.items():
    try:
        gdfs[name] = gpd.read_file(path)
        # print(f"Carregado: {name}")
    except Exception as e:
        print(f"Erro ao carregar {name}: {str(e)}")
        gdfs[name] = None

print(f" We have loaded {len(list(gdfs.keys()))} maps ")

# Adicione esta função auxiliar no routes.py
def calculate_gain_loss(df, classes, start_year, end_year, class_info_df):
    results = []

    # Criar um mapeamento de ID para nome da classe
    name_map = dict(zip(class_info_df['code_id'], class_info_df['class_name']))
    
    for classe in classes:
        # Filtrar dados para a classe específica
        class_data = df[df['classe'] == classe]

        # Obter o nome da classe
        class_name = name_map.get(classe, f"Classe {classe}")
        
        # Obter área no ano inicial
        start_area = class_data[class_data['year'] == start_year]['area'].sum()
        
        # Obter área no ano final
        end_area = class_data[class_data['year'] == end_year]['area'].sum()
        
        # Calcular diferença
        diff = end_area - start_area
        
        # Calcular porcentagem (evitar divisão por zero)
        if start_area != 0:
            percent = (diff / start_area) * 100
        else:
            percent = 0.0   #if diff == 0 else (float('inf') if diff > 0 else float('-inf'))
        
        results.append({
            'class_id': classe,
            'class_name': class_name,  # Adicionar o nome da classe
            'start_area': start_area,
            'end_area': end_area,
            'difference': diff,
            'percent': percent
        })
    
    return results



# 2. Define a rota /data dentro do Blueprint. A URL final será /api/data
@api_bp.route('/data')
def get_data():
    # 1. Obter parâmetros do request
    limit_shp = request.args.get('limit_shp', "CAATINGA", type=str)
    region = request.args.get('region', None, type=str)
    nomeVetor = request.args.get('nomeVetor', None, type=str)
    estado_name = request.args.get('estado_name', None, type=str)
    start_year = request.args.get('start_year', 1985, type=int)
    end_year = request.args.get('end_year', 2024, type=int)
    limit_shp = str(limit_shp).upper()
    print(f"""
            Parâmetros recebidos:
                * limit_shp = {limit_shp}
                * region = {region}
                * nomeVetor = {nomeVetor}
                * estado_name = {estado_name}
                * start_year = {start_year}
                * end_year = {end_year}
    """)
    

    # Se nomeVetor for 'None' (string), trata como None
    if nomeVetor == 'null':
        nomeVetor = None
    print("Valores únicos de nomeVetor no banco:", 
                    db.session.query(TimeSeriesData.nomeVetor).distinct().all())  

    # 2. Construir a query base com base nos filtros
    # TimeSeriesData é a tabela que tem todos os dados de área, classe
    # e as regiões de limit
    query = TimeSeriesData.query.filter(
        TimeSeriesData.limit_shp == limit_shp,
        TimeSeriesData.year.between(start_year, end_year)
    )

    # group_by_fields = []

    # Adicionar filtros e campos de agrupamento dinamicamente    
    if estado_name and estado_name != 'None':
        query = query.filter(func.lower(TimeSeriesData.estado_name) == func.lower(estado_name))
        # group_by_fields.append(TimeSeriesData.estado_name)

    if region and region != 'None':
        query = query.filter(func.lower(TimeSeriesData.region) == func.lower(region))
        # group_by_fields.append(TimeSeriesData.region)

    if nomeVetor and nomeVetor != 'None':
        query = query.filter(func.lower(TimeSeriesData.nomeVetor) == func.lower(nomeVetor))
        # group_by_fields.append(TimeSeriesData.nomeVetor)

    df = pd.read_sql(query.statement, db.engine)
    print(f"Registros encontrados: {df.shape}")
    
    if df.empty:
        # Retorna estrutura vazia se não houver dados
        return jsonify({
            'map_geojson': None,
            'chart_data': {},
            # 'sankey_data': {},
            # 'gain_loss_data': []
        })
    
    # 3. Agrupamento dos dados (sem alterações aqui)
    data_for_charts = df.groupby(['year', 'classe'])['area'].sum().reset_index()
    data_for_charts['classe'] = data_for_charts['classe'].astype(int)
    data_for_charts['year'] = data_for_charts['year'].astype(int)
    # print(tabulate(data_for_charts.head(5), headers = 'keys', tablefmt = 'psql', floatfmt=".2f"))

    # 4. Lógica de Geoprocessamento (Intersect)
    # Começa com o limite principal
    if limit_shp == 'CAATINGA':
        gdfsCaat = gdfs['vetor_biomas_250']
        map_gdf = gdfsCaat[gdfsCaat['CD_Bioma'].astype(int) == 2] 
    else:
        map_gdf = gdfs['semiarido']
    
    # A lógica de intersecção exata depende dos nomes das colunas nos seus GeoJSONs
    # Exemplo: se o GeoJSON de estados tem uma coluna 'NM_ESTADO'
    if estado_name and estado_name != 'None':
        # IMPORTANTE: Verifique se a coluna no seu GeoJSON se chama 'NM_ESTADO'
        gdf_todos_os_estados = gdfs['br_estados_shp']
        estado_filtrado_gdf = gdf_todos_os_estados[gdf_todos_os_estados['NM_ESTADO'].str.upper() == estado_name.upper()]
        if not estado_filtrado_gdf.empty:
            map_gdf = gpd.overlay(map_gdf, estado_filtrado_gdf, how='intersection')

    if region and region != 'None':
        # Supondo que o GDF de regiões tem uma coluna 'NM_REGIAO'
        if region in gdfs:
            region_gdf = gdfs[region]
            map_gdf = gpd.overlay(map_gdf, region_gdf, how='intersection')
    
    # ... Lógica similar para nomeVetor ...
    if not map_gdf.empty:
        map_geojson = map_gdf.__geo_interface__
    else:
        map_geojson = None
    # GeoJSON nativa

    # ==============================================================================
    # 5. PREPARAR DADOS PARA OS GRÁFICOS (LÓGICA REESCRITA E SIMPLIFICADA)
    # ==============================================================================

    # --- MUDANÇA 1: Carregar a legenda para um dicionário para consulta rápida ---
    class_info_df = pd.read_sql(db.session.query(ClassInfo).statement, db.engine)
    # Cria um mapa de ID -> Nome da Classe
    name_map = pd.Series(class_info_df.class_name.values, index=class_info_df.code_id).to_dict()
    name_map = dict(name_map)
    # print("ver a tabela de classes v1 ", name_map)
    # Cria um mapa de ID -> Cor Hexadecimal
    color_map = pd.Series(class_info_df.hex_color.values, index=class_info_df.code_id).to_dict()
    # print("ver a tabela de color_map v1 ", color_map)
    charts_data = {}
    years = sorted(data_for_charts['year'].unique().tolist())

    # #get values of name class
    # # 3. (Sugestão 2) Busca os nomes das classes para os títulos (ClassInfo)
    info_area_results = LimitArea.query.all()    
    dict_area_limits = {c.state_limit: c.area for c in info_area_results}
    # print("ver a tabela de LimitArea  ", dict_area_limits)

    dict_area_exp = {}
    dict_area_exp[limit_shp] = dict_area_limits[limit_shp]
    if str(estado_name).upper() != 'NONE':
        dict_area_exp[str(estado_name).upper()] = dict_area_limits[str(estado_name).upper()]
        area_estado = data_for_charts[data_for_charts['year'] == int(end_year)]['area'].sum()
        area_estado = round(float(area_estado), 2)
        dict_area_exp[str(estado_name).upper() + '_interna'] = area_estado

    # print("ver a tabela de LimitArea final ", dict_area_exp)

    for classe_id, group in data_for_charts.groupby('classe'):
        # --- MUDANÇA 2: Estrutura de dados simplificada ---
        if classe_id != 0 and classe_id != 27:
            # classe_id = 27
            class_name = name_map[classe_id]
            # print(f" classe Id == {classe_id}  <> {class_name}")     
            
            class_color = color_map.get(classe_id, '#cccccc') # Usa cinza como cor padrão

            series_data = group.set_index('year')['area'].reindex(years, fill_value=0)

            charts_data[classe_id] = {
                'years': years,
                'series_data': series_data.tolist(),
                'color': class_color,
                'class_name': class_name
            }


    # Aqui você adicionaria a lógica para a tabela de Ganho/Perda e o Sankey
    # A lógica do Sankey precisa de dados de 2 anos específicos.
    # A de Ganho/Perda precisa comparar o primeiro e último ano do intervalo.
    gain_loss_classes = [3,4,12,15,20,21,23,24,25,39,41,46,48,62]
    gain_loss_data = calculate_gain_loss(df, gain_loss_classes, start_year, end_year, class_info_df)
    print(gain_loss_data[:3])

    # 6. Retornar JSON para o front-end
    return jsonify({
        'map_geojson': map_geojson,
        'bar_chart_data': charts_data,
        'statistical_summary': dict_area_exp,
        # 'sankey_data': sankey_data,
        'gain_loss_data': gain_loss_data
    })