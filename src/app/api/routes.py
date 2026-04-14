# app/api/routes.py
import os, json
import pandas as pd
import geopandas as gpd
from flask import Blueprint, request, jsonify
from app import db
from app.models import AreaData, AccuracyData, ClassInfo, LimitArea

api_bp = Blueprint('api', __name__)

pathparent = str(os.getcwd())

# ─────────────────────────────────────────────────────────────────────────────
# GeoJSON pré-carregado
# ─────────────────────────────────────────────────────────────────────────────
GEOJSON_PATHS = {
    "areaQuil":                  os.path.join(pathparent, "dados/geojson/areas_Quilombolas.geojson"),
    "Assent-Br":                 os.path.join(pathparent, "dados/geojson/Assentamento_Brasil.geojson"),
    "bacia-sao-francisco":       os.path.join(pathparent, "dados/geojson/bacia_sao_francisco.geojson"),
    "br_estados_shp":            os.path.join(pathparent, "dados/geojson/br_estados_shp.geojson"),
    "energias-renovaveis":       os.path.join(pathparent, "dados/geojson/energiasE.geojson"),
    "macro-RH":                  os.path.join(pathparent, "dados/geojson/macro_RH.geojson"),
    "matopiba":                  os.path.join(pathparent, "dados/geojson/matopiba.geojson"),
    "meso-RH":                   os.path.join(pathparent, "dados/geojson/meso_RH.geojson"),
    "micro-RH":                  os.path.join(pathparent, "dados/geojson/micro_RH.geojson"),
    "nucleos-desert":            os.path.join(pathparent, "dados/geojson/nucleos_desertificacao.geojson"),
    "prioridade-conservacao-V1": os.path.join(pathparent, "dados/geojson/prioridade-conservacao-V1.geojson"),
    "prioridade-conservacao-V2": os.path.join(pathparent, "dados/geojson/prioridade-conservacao-V2.geojson"),
    "res-biosf":                 os.path.join(pathparent, "dados/geojson/reserva_biosfera.geojson"),
    "semiarido":                 os.path.join(pathparent, "dados/geojson/semiarido2024.geojson"),
    "tis-port":                  os.path.join(pathparent, "dados/geojson/tis_poligonais_portarias.geojson"),
    "vetor_biomas_250":          os.path.join(pathparent, "dados/geojson/vetor_biomas_250.geojson"),
    "UnidCons-S":                os.path.join(pathparent, "dados/geojson/UnidadesConservacao_S.geojson"),
}

gdfs = {}
for _name, _path in GEOJSON_PATHS.items():
    try:
        gdfs[_name] = gpd.read_file(_path)
    except Exception as _e:
        print(f"  ⚠ GeoJSON não carregado: {_name} — {_e}")
        gdfs[_name] = None

print(f"  ✔ {len([v for v in gdfs.values() if v is not None])} GeoJSONs carregados")

# Cores fixas por coleção (para overlay nos gráficos)
COLLECTION_COLORS = {
    'Map71':  '#8e44ad',   # roxo
    'Map80':  '#e67e22',   # laranja
    'Map90':  '#27ae60',   # verde
    'Map100': '#2980b9',   # azul
}
COLLECTION_LABELS = {
    'Map71': 'Col 7.1', 'Map80': 'Col 8', 'Map90': 'Col 9', 'Map100': 'Col 10'
}


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────
def _query_area(bacia, layer_key, version, num_class, janela, start_year, end_year):
    q = (AreaData.query
         .filter(AreaData.id_bacia  == bacia,
                 AreaData.layer_key == layer_key,
                 AreaData.version   == version,
                 AreaData.num_class == num_class,
                 AreaData.year.between(start_year, end_year)))
    if janela:
        q = q.filter(AreaData.janela == janela)
    else:
        q = q.filter(AreaData.janela.is_(None))
    return pd.read_sql(q.statement, db.engine)


def _query_accuracy(bacia, layer_key, version, num_class, janela):
    q = (AccuracyData.query
         .filter(AccuracyData.id_bacia  == bacia,
                 AccuracyData.layer_key == layer_key,
                 AccuracyData.version   == version,
                 AccuracyData.num_class == num_class))
    if janela:
        q = q.filter(AccuracyData.janela == janela)
    else:
        q = q.filter(AccuracyData.janela.is_(None))
    return pd.read_sql(q.statement, db.engine)


# ─────────────────────────────────────────────────────────────────────────────
# Endpoint principal
# ─────────────────────────────────────────────────────────────────────────────
@api_bp.route('/data')
def get_data():
    bacia      = request.args.get('bacia',      'Caatinga', type=str)
    layer_key  = request.args.get('layer_key',  'spatial_all', type=str)
    version    = request.args.get('version',    1,  type=int)
    num_class  = request.args.get('num_class',  10, type=int)
    janela     = request.args.get('janela',     None, type=int)
    start_year = request.args.get('start_year', 1985, type=int)
    end_year   = request.args.get('end_year',   2025, type=int)
    include_cm = request.args.get('include_cm', 'false').lower() == 'true'

    # ── Legenda de classes ────────────────────────────────────────────────
    df_cls   = pd.read_sql(ClassInfo.query.statement, db.engine)
    name_map  = dict(zip(df_cls['code_id'], df_cls['class_name']))
    color_map = dict(zip(df_cls['code_id'], df_cls['hex_color']))

    active = [3, 4, 12, 15, 19, 21, 25, 29, 33, 36] if num_class == 10 else [3, 4, 12, 21, 25, 33]

    # ── Área — camada selecionada ─────────────────────────────────────────
    df_area = _query_area(bacia, layer_key, version, num_class, janela, start_year, end_year)
    if df_area.empty:
        return jsonify({'error': f'Sem dados para layer_key={layer_key}, bacia={bacia}'}), 404

    df_area = df_area[df_area['classe'].isin(active)]
    years   = sorted(df_area['year'].unique().tolist())

    area_charts = {}
    for cls_id, grp in df_area.groupby('classe'):
        series = grp.set_index('year')['area'].reindex(years, fill_value=0)
        area_charts[int(cls_id)] = {
            'class_name': name_map.get(cls_id, f'Classe {cls_id}'),
            'hex_color':  color_map.get(cls_id, '#aaaaaa'),
            'years':      years,
            'areas':      [round(v, 2) for v in series.tolist()],
        }

    # ── Comparação com coleções anteriores ───────────────────────────────
    # As coleções anteriores usam version=10
    collections_compare = {}
    for col_key in ('Map71', 'Map80', 'Map90', 'Map100'):
        col_ver = 10   # versão fixa para coleções anteriores
        df_col  = _query_area(bacia, col_key, col_ver, num_class, None, start_year, end_year)
        if df_col.empty:
            continue
        df_col  = df_col[df_col['classe'].isin(active)]
        col_years = sorted(df_col['year'].unique().tolist())
        by_class  = {}
        for c_id, grp in df_col.groupby('classe'):
            s = grp.set_index('year')['area'].reindex(col_years, fill_value=0)
            by_class[int(c_id)] = [round(v, 2) for v in s.tolist()]
        collections_compare[col_key] = {
            'years':    col_years,
            'by_class': by_class,
            'color':    COLLECTION_COLORS[col_key],
            'label':    COLLECTION_LABELS[col_key],
        }

    # ── Pie charts: 1985 e ano final disponível ───────────────────────────
    def get_pie(year):
        df_y = df_area[df_area['year'] == year]
        if df_y.empty:
            df_y = df_area[df_area['year'] == df_area['year'].max()]
        return {
            int(r['classe']): float(r['area'])
            for _, r in df_y.iterrows()
            if int(r['classe']) in active
        }

    pie_1985 = get_pie(1985)
    end_actual = min(end_year, int(df_area['year'].max()))
    pie_end  = get_pie(end_actual)

    # ── Acurácia — camada selecionada ─────────────────────────────────────
    df_acc = _query_accuracy(bacia, layer_key, version, num_class, janela)

    acc_global, acc_by_year, cm_data = None, {}, None
    qty_diss = alloc_diss = exchange = shift = None

    if not df_acc.empty:
        row_all = df_acc[df_acc['year'] == 'All']
        if not row_all.empty:
            r = row_all.iloc[0]
            acc_global  = r.get('global_accuracy')
            qty_diss    = r.get('quantity_diss')
            alloc_diss  = r.get('alloc_diss')
            exchange    = r.get('exchange')
            shift       = r.get('shift')
            if include_cm and r.get('confusion_matrix_json'):
                try:
                    cm_data = json.loads(r['confusion_matrix_json'])
                except Exception:
                    pass

        for _, row in df_acc[df_acc['year'] != 'All'].iterrows():
            try:
                y = int(row['year'])
                if start_year <= y <= end_year:
                    acc_by_year[y] = float(row['global_accuracy'])
            except (ValueError, TypeError):
                pass

    # ── Acurácia col100 para comparação (global + por ano) ───────────────
    df_acc100_all = pd.read_sql(
        AccuracyData.query
        .filter(AccuracyData.id_bacia  == bacia,
                AccuracyData.layer_key == 'Map100',
                AccuracyData.num_class == num_class)
        .statement, db.engine)

    acc_col100 = None
    acc_col100_by_year = {}
    if not df_acc100_all.empty:
        row_all_100 = df_acc100_all[df_acc100_all['year'] == 'All']
        if not row_all_100.empty:
            acc_col100 = float(row_all_100.iloc[0]['global_accuracy'])
        for _, row in df_acc100_all[df_acc100_all['year'] != 'All'].iterrows():
            try:
                y = int(row['year'])
                if start_year <= y <= end_year:
                    acc_col100_by_year[y] = float(row['global_accuracy'])
            except (ValueError, TypeError):
                pass

    acc_comparison = None
    if acc_global is not None and acc_col100 is not None:
        diff = round(acc_global - acc_col100, 2)
        acc_comparison = {'diff': diff, 'direction': 'up' if diff >= 0 else 'down'}

    accuracy = {
        'selected': {
            'global':          acc_global,
            'quantity_diss':   qty_diss,
            'alloc_diss':      alloc_diss,
            'exchange':        exchange,
            'shift':           shift,
            'by_year':         acc_by_year,
        },
        'col100':     {'global': acc_col100, 'by_year': acc_col100_by_year},
        'comparison': acc_comparison,
    }

    # ── Ganho / Perda ─────────────────────────────────────────────────────
    gain_loss = []
    for cls_id, d in area_charts.items():
        if not d['areas']:
            continue
        sa = d['areas'][0]
        ea = d['areas'][-1]
        diff = ea - sa
        pct  = round(diff / sa * 100, 2) if sa > 0 else 0.0
        gain_loss.append({
            'class_id':   cls_id,
            'class_name': d['class_name'],
            'hex_color':  d['hex_color'],
            'start_area': round(sa, 2),
            'end_area':   round(ea, 2),
            'difference': round(diff, 2),
            'percent':    pct,
        })

    # ── Mapa GeoJSON ──────────────────────────────────────────────────────
    map_geojson = None
    if gdfs.get('vetor_biomas_250') is not None:
        gdf = gdfs['vetor_biomas_250']
        gdf = gdf[gdf['CD_Bioma'].astype(int) == 2]
        if not gdf.empty:
            map_geojson = gdf.__geo_interface__

    return jsonify({
        'area_charts':         area_charts,
        'collections_compare': collections_compare,
        'pie_1985':            pie_1985,
        'pie_end':             pie_end,
        'pie_end_year':        end_actual,
        'accuracy':            accuracy,
        'confusion_matrix':    cm_data,
        'map_geojson':         map_geojson,
        'gain_loss':           gain_loss,
    })


# ─────────────────────────────────────────────────────────────────────────────
# Endpoints auxiliares
# ─────────────────────────────────────────────────────────────────────────────
@api_bp.route('/bacias')
def get_bacias():
    rows = db.session.query(AreaData.id_bacia).distinct().all()
    lst  = sorted(r[0] for r in rows if r[0] != 'Caatinga')
    return jsonify(['Caatinga'] + lst)


@api_bp.route('/layers')
def get_layers():
    rows = db.session.query(
        AreaData.layer_key, AreaData.version, AreaData.num_class, AreaData.janela
    ).distinct().all()
    seen, result = set(), []
    for r in rows:
        key = (r[0], r[1], r[2], r[3])
        if key not in seen:
            seen.add(key)
            result.append({'layer_key': r[0], 'version': r[1],
                           'num_class': r[2], 'janela': r[3]})
    return jsonify(sorted(result, key=lambda x: x['layer_key']))
