# app/api/routes.py
import pandas as pd
import geopandas as gpd
from flask import Blueprint, request, jsonify
from app.models import TimeSeriesData, ClassInfo, db

api_bp = Blueprint('api', __name__)

# NOTA: Carregar os geojson pode ser lento. Para produção, considere cachear.
# Os caminhos devem ser ajustados para os seus arquivos.
GEOJSON_PATHS = {
    "areaQuil": "dados/geojson/areas_Quilombolas.geojson",  # areaQuil
    "Assent-Br": "dados/geojson/Assentamento_Brasil.geojson",  # Assent-Br
    "bacia-sao-francisco": "dados/geojson/bacia_sao_francisco.geojson",  # bacia-sao-francisco
    "br_estados_shp": "dados/geojson/br_estados_shp.geojson",
    "energias-renovaveis": "dados/geojson/energiasE.geojson",  # energias-renovaveis
    "macro-RH": "dados/geojson/macro_RH.geojson",  # macro-RH
    "matopiba": "dados/geojson/matopiba.geojson",  # matopiba
    "meso-RH": "dados/geojson/meso_RH.geojson",  # meso-RH
    "micro-RH": "dados/geojson/micro_RH.geojson",   # micro-RH
    "nucleos-desert": "dados/geojson/nucleos_desertificacao.geojson",    # nucleos-desert
    "prioridade-conservacao-V1": "dados/geojson/prioridade-conservacao-V1.geojson",  # prioridade-conservacao-V1
    "prioridade-conservacao-V2": "dados/geojson/prioridade-conservacao-V2.geojson",  # prioridade-conservacao-V2 
    "res-biosf": "dados/geojson/reserva_biosfera.geojson",   # res-biosf
    "semiarido": "dados/geojson/semiarido2024.geojson",  # semiarido
    "tis-port": "dados/geojson/tis_poligonais_portarias.geojson", # tis-port
    "vetor_biomas_250": "dados/geojson/vetor_biomas_250.geojson",
    "UnidCons-S": "dados/geojson/UnidadesConservacao_S.geojson",   # UnidCons-S 
}

# Pré-carregar os GeoDataFrames para melhor performance
gdfs = {name: gpd.read_file(path) for name, path in GEOJSON_PATHS.items()}

@api_bp.route('/data')
def get_data():
    # 1. Obter parâmetros do request
    limit_shp = request.args.get('limit_shp', "CAATINGA", type=str)
    region = request.args.get('region', None, type=str)
    nomeVetor = request.args.get('nomeVetor', None, type=str)
    estado_name = request.args.get('estado_name', None, type=str)
    start_year = request.args.get('start_year', 1985, type=int)
    end_year = request.args.get('end_year', 2024, type=int)

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
        query = query.filter(TimeSeriesData.estado_name == estado_name)
        # group_by_fields.append(TimeSeriesData.estado_name)

    if region and region != 'None':
        query = query.filter(TimeSeriesData.region == region)
        # group_by_fields.append(TimeSeriesData.region)

    if nomeVetor and nomeVetor != 'None':
        query = query.filter(TimeSeriesData.nomeVetor == nomeVetor)
        # group_by_fields.append(TimeSeriesData.nomeVetor)


    df = pd.read_sql(query.statement, db.engine)
    
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
    map_geojson = map_gdf.to_json() if not map_gdf.empty else None

    # ==============================================================================
    # 5. PREPARAR DADOS PARA OS GRÁFICOS (LÓGICA REESCRITA E SIMPLIFICADA)
    # ==============================================================================

    # --- MUDANÇA 1: Carregar a legenda para um dicionário para consulta rápida ---
    class_info_df = pd.read_sql(db.session.query(ClassInfo).statement, db.engine)
    # Cria um mapa de ID -> Nome da Classe
    name_map = pd.Series(class_info_df.class_name.values, index=class_info_df.code_id).to_dict()
    # Cria um mapa de ID -> Cor Hexadecimal
    color_map = pd.Series(class_info_df.hex_color.values, index=class_info_df.code_id).to_dict()
    
    charts_data = {}
    years = sorted(data_for_charts['year'].unique().tolist())

    for classe_id, group in data_for_charts.groupby('classe'):
        # --- MUDANÇA 2: Estrutura de dados simplificada ---
        class_name = name_map.get(classe_id, f'Classe {classe_id}')
        class_color = color_map.get(classe_id, '#cccccc') # Usa cinza como cor padrão

        series_data = group.set_index('year')['area'].reindex(years, fill_value=0)

        charts_data[class_name] = {
            'years': years,
            'series_data': series_data.tolist(),
            'color': class_color,
            'class_name': class_name
        }

    # Aqui você adicionaria a lógica para a tabela de Ganho/Perda e o Sankey
    # A lógica do Sankey precisa de dados de 2 anos específicos.
    # A de Ganho/Perda precisa comparar o primeiro e último ano do intervalo.

    # 6. Retornar JSON para o front-end
    return jsonify({
        'map_geojson': map_geojson,
        'bar_chart_data': charts_data,
        # 'sankey_data': sankey_data,
        # 'gain_loss_data': gain_loss_data
    })