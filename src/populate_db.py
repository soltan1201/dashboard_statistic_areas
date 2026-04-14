#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
populate_db.py — Script de populamento do banco de dados MapBiomas Dashboard
Lê os CSVs de AREA-EXPORT-COL10 e ptosAccCol11, calcula métricas de acurácia
e popula o banco de dados SQLite com os novos modelos.

Uso:
    cd src/
    python populate_db.py
"""
import os, re, json
import pandas as pd
import numpy as np
from pathlib import Path
from sklearn.metrics import accuracy_score, confusion_matrix
from tqdm import tqdm

os.chdir(Path(__file__).parent)          # garante que o cwd seja src/

from app import create_app, db
from app.models import AreaData, AccuracyData, ClassInfo, LimitArea

# ─────────────────────────────────────────────────────────────────────────────
# Caminhos
# ─────────────────────────────────────────────────────────────────────────────
BASE_DIR    = Path(__file__).parent
AREA_DIR    = BASE_DIR / 'dados' / 'AREA-EXPORT-COL10'
ACC_DIR     = BASE_DIR / 'dados' / 'ptosAccCol11'
LEGENDA_CSV = BASE_DIR / 'dados' / 'legenda.csv'
LIMIT_CSV   = BASE_DIR / 'dados' / 'areas_biomas_semiarido.csv'

# ─────────────────────────────────────────────────────────────────────────────
# Classes e remapeamento para acurácia
# ─────────────────────────────────────────────────────────────────────────────
# Remap texto → código numérico para colunas CLASS_YYYY dos pontos de referência.
# Schema nc10: mantém Pastagem(15), Lav.Temp(19), Lav.Perene(36) e Afloramento(29) distintos.
REMAP_REF_10 = {
    # Floresta (3)
    "FORMAÇÃO FLORESTAL":              3,
    "MANGUE":                          3,
    "RESTINGA ARBÓREA":                3,
    "FLORESTA INUNDÁVEL":              3,
    # Savana (4)
    "FORMAÇÃO SAVÂNICA":               4,
    # Campestre (12)
    "FORMAÇÃO CAMPESTRE":              12,
    "CAMPO ALAGADO E ÁREA PANTANOSA":  12,
    "APICUM":                          12,
    "RESTINGA HERBÁCEA":               12,
    "OUTRA FORMAÇÃO NÃO FLORESTAL":    12,
    # Pastagem (15) — nc10 separado
    "PASTAGEM":                        15,
    # Lavoura Temporária (19) — nc10 separado
    "LAVOURA TEMPORÁRIA":              19,
    "CANA":                            19,
    "SOJA":                            19,
    "OUTRAS LAVOURAS TEMPORÁRIAS":     19,
    "ALGODÃO (BETA)":                  19,
    # Mosaico de Usos (21)
    "MOSAICO DE USOS":                 21,
    "FLORESTA PLANTADA":               21,
    "SILVICULTURA":                    21,
    # Urb./Solo Exposto (25)
    "INFRAESTRUTURA URBANA":           25,
    "ÁREA URBANIZADA":                 25,
    "MINERAÇÃO":                       25,
    "PRAIA E DUNA":                    25,
    "OUTRA ÁREA NÃO VEGETADA":         25,
    "VEGETAÇÃO URBANA":                25,
    # Afloramento (29) — nc10 distinto
    "AFLORAMENTO ROCHOSO":             29,
    # Água (33)
    "RIO, LAGO E OCEANO":              33,
    "AQUICULTURA":                     33,
    "CORPO D'ÁGUA":                    33,
    # Lavoura Perene (36) — nc10 separado
    "LAVOURA PERENE":                  36,
    "CAFÉ":                            36,
    "CITRUS":                          36,
    "CAJU":                            36,
    "OUTRAS LAVOURAS PERENES":         36,
    # Não observado (27)
    "NÃO OBSERVADO":                   27,
}

# nc7: colapsa as 3 classes agrícolas para Mosaico(21) e afloramento para Solo Exp.(25)
REMAP_REF_7 = {
    **REMAP_REF_10,
    "PASTAGEM":        21,
    "LAVOURA TEMPORÁRIA": 21, "CANA": 21, "SOJA": 21,
    "OUTRAS LAVOURAS TEMPORÁRIAS": 21, "ALGODÃO (BETA)": 21,
    "LAVOURA PERENE":  21, "CAFÉ": 21, "CITRUS": 21,
    "CAJU": 21, "OUTRAS LAVOURAS PERENES": 21,
    "AFLORAMENTO ROCHOSO": 25,
}

# nc10: 10 classes ativas (excluindo 27=não observado)
CLASSES_10 = [3, 4, 12, 15, 19, 21, 25, 29, 33, 36]
# nc7: 6 classes ativas (pastagem/lavoura→21, afloramento→25)
CLASSES_7  = [3, 4, 12, 21, 25, 33]

# Cores padrão MapBiomas
DEFAULT_CLASSES = [
    {'code_id': 3,  'class_name': 'Floresta',         'hex_color': '#1f8d49'},
    {'code_id': 4,  'class_name': 'Savana',           'hex_color': '#7dc975'},
    {'code_id': 12, 'class_name': 'Campestre',        'hex_color': '#d6bc74'},
    {'code_id': 15, 'class_name': 'Pastagem',         'hex_color': '#edde8e'},
    {'code_id': 19, 'class_name': 'Lav. Temporária',  'hex_color': '#C27BA0'},
    {'code_id': 21, 'class_name': 'Mosaico de Usos',  'hex_color': '#ffefc3'},
    {'code_id': 25, 'class_name': 'Urb./Solo Exp.',   'hex_color': '#d4271e'},
    {'code_id': 27, 'class_name': 'Não Observado',    'hex_color': '#D5D5E8'},
    {'code_id': 29, 'class_name': 'Afloramento',      'hex_color': '#e975ad'},
    {'code_id': 33, 'class_name': 'Água',             'hex_color': '#2532e4'},
    {'code_id': 36, 'class_name': 'Lav. Perene',      'hex_color': '#d082de'}
]


# ─────────────────────────────────────────────────────────────────────────────
# Helpers de parsing de nomes de arquivo
# ─────────────────────────────────────────────────────────────────────────────
def parse_area_filename(fname: str) -> dict | None:
    """
    Extrai metadados do nome do CSV de área.
    Ex.: areaXclasse_CAATINGA_Col11.0_spatial_all_nc10_vers_1.csv
    Retorna dict com layer_key, version, num_class, janela ou None se inválido.
    """
    # Pula duplicatas como (1), (2)...
    if re.search(r'\(\d+\)', fname):
        return None

    name = fname
    for prefix in ('areaXclasse_CAATINGA_Col11.0_', 'areaXclasse_CAATINGA_Col11_'):
        name = name.replace(prefix, '')
    name = name.replace('.csv', '')

    vm  = re.search(r'_vers_(\d+)', name)
    version = int(vm.group(1)) if vm else 1
    name = re.sub(r'_vers_\d+', '', name)

    ncm = re.search(r'_nc(\d+)', name)
    num_class = int(ncm.group(1)) if ncm else 10
    name = re.sub(r'_nc\d+', '', name)

    name = name.replace('_remap', '').strip('_')

    janela = None
    jm = re.search(r'_J(\d+)', name)
    if jm:
        janela = int(jm.group(1))
        name = re.sub(r'_J\d+', '', name).strip('_')

    return {'layer_key': name, 'version': version, 'num_class': num_class, 'janela': janela}


def parse_acc_filename(fname: str) -> dict | None:
    """
    Extrai metadados do nome do CSV de acurácia.
    Ex.: acc_col11_spatial_all_nc10_vers_1.csv
    """
    name = fname.replace('acc_col11_', '').replace('.csv', '')

    vm  = re.search(r'_vers_(\d+)', name)
    version = int(vm.group(1)) if vm else 1
    name = re.sub(r'_vers_\d+', '', name)

    ncm = re.search(r'_nc(\d+)', name)
    num_class = int(ncm.group(1)) if ncm else 10
    name = re.sub(r'_nc\d+', '', name).strip('_')

    janela = None
    jm = re.search(r'_J(\d+)', name)
    if jm:
        janela = int(jm.group(1))
        name = re.sub(r'_J\d+', '', name).strip('_')

    return {'layer_key': name, 'version': version, 'num_class': num_class, 'janela': janela}


# ─────────────────────────────────────────────────────────────────────────────
# Cálculo de métricas
# ─────────────────────────────────────────────────────────────────────────────
def calc_metrics(y_true_s: pd.Series, y_pred_s: pd.Series,
                 num_class: int, only_all_cm=False) -> dict | None:
    """
    Calcula global_accuracy + erros de dissimilaridade + matriz de confusão.
    only_all_cm: se True, calcula a CM (apenas para year='All').
    """
    classes = CLASSES_10 if num_class == 10 else CLASSES_7

    # Remove não-observados e NaN
    mask = (
        y_true_s.notna() & y_pred_s.notna() &
        (y_true_s != 27)  & (y_pred_s != 27)
    )
    y_true = y_true_s[mask].values.astype(np.int32)
    y_pred = y_pred_s[mask].values.astype(np.int32)

    if len(y_true) < 5:
        return None

    try:
        acc   = round(float(accuracy_score(y_true, y_pred)) * 100, 2)
        total = len(y_true)

        cm = confusion_matrix(y_true, y_pred, labels=classes)
        dim = len(classes)

        # Acrescenta totais às margens
        cm_ext = np.zeros((dim + 1, dim + 1), dtype=np.int64)
        cm_ext[:dim, :dim] = cm
        for i in range(dim):
            cm_ext[i, dim]   = cm_ext[i, :dim].sum()
            cm_ext[dim, i]   = cm_ext[:dim, i].sum()
        cm_ext[dim, dim] = cm_ext[:dim, :dim].sum()

        quant_list, alloc_list, exch_list = [], [], []
        for i in range(dim):
            row_s = int(cm_ext[i, dim])
            col_s = int(cm_ext[dim, i])
            diag  = int(cm_ext[i, i])
            quant_list.append(abs(row_s - col_s) / total * 100)
            min_val = 2 * min(row_s - diag, col_s - diag)
            alloc_list.append(max(min_val, 0) / total * 100)
            suma = sum(min(int(cm_ext[i, j]), int(cm_ext[j, i])) for j in range(dim) if j != i)
            exch_list.append(suma * 2 / total * 100)

        quant_v = round(sum(quant_list) / 2, 2)
        alloc_v = round((100 - acc) - quant_v, 2)
        exch_v  = round(sum(exch_list) / 2, 2)
        shift_v = round((100 - acc) - quant_v - alloc_v, 2)

        cm_json = None
        if only_all_cm:
            cm_json = json.dumps({
                'classes': classes,
                'matrix':  cm.tolist(),
                'labels':  [str(c) for c in classes]
            })

        return {
            'global_accuracy': acc,
            'quantity_diss':   quant_v,
            'alloc_diss':      alloc_v,
            'exchange':        exch_v,
            'shift':           shift_v,
            'confusion_matrix_json': cm_json,
        }
    except Exception as e:
        print(f"    ⚠ calc_metrics erro: {e}")
        return None


# ─────────────────────────────────────────────────────────────────────────────
# Populamento
# ─────────────────────────────────────────────────────────────────────────────
def populate_class_info(engine):
    df_leg = pd.read_csv(LEGENDA_CSV) if LEGENDA_CSV.exists() else pd.DataFrame(DEFAULT_CLASSES)
    if LEGENDA_CSV.exists():
        for col in df_leg.select_dtypes('object').columns:
            df_leg[col] = df_leg[col].str.strip().str.replace('"', '', regex=False)
        df_leg['code_id'] = pd.to_numeric(df_leg['code_id'], errors='coerce')
        df_leg = df_leg.dropna(subset=['code_id'])
        df_leg['code_id'] = df_leg['code_id'].astype(int)
    df_leg.to_sql('class_info', engine, if_exists='append', index=False)
    print(f"  ✔ class_info: {len(df_leg)} registros")


def populate_limit_area(engine):
    if not LIMIT_CSV.exists():
        print("  ⚠ CSV de limites não encontrado")
        return
    df = pd.read_csv(LIMIT_CSV)
    df.to_sql('limit_area', engine, if_exists='append', index=False)
    print(f"  ✔ limit_area: {len(df)} registros")


def populate_areas(engine):
    files = sorted(f for f in AREA_DIR.glob('*.csv') if not re.search(r'\(\d+\)', f.name))
    print(f"\n  Processando {len(files)} CSVs de área...")
    all_frames = []

    for csv_path in tqdm(files, desc='  Áreas'):
        meta = parse_area_filename(csv_path.name)
        if not meta:
            continue
        try:
            df = pd.read_csv(csv_path)
        except Exception as e:
            print(f"\n    ⚠ {csv_path.name}: {e}")
            continue

        needed = {'area', 'classe', 'id_bacia', 'year'}
        if not needed.issubset(df.columns):
            print(f"\n    ⚠ Colunas ausentes em {csv_path.name}: {needed - set(df.columns)}")
            continue

        df = df[['area', 'classe', 'id_bacia', 'year']].copy()
        df['id_bacia']  = df['id_bacia'].astype(str)
        df['layer_key'] = meta['layer_key']
        df['version']   = meta['version']
        df['num_class'] = meta['num_class']
        df['janela']    = meta['janela']
        all_frames.append(df)

        # Agregação para Caatinga inteira
        df_caat = df.groupby(['year', 'classe'])['area'].sum().reset_index()
        df_caat['id_bacia']  = 'Caatinga'
        df_caat['layer_key'] = meta['layer_key']
        df_caat['version']   = meta['version']
        df_caat['num_class'] = meta['num_class']
        df_caat['janela']    = meta['janela']
        all_frames.append(df_caat)

    if all_frames:
        df_all = pd.concat(all_frames, ignore_index=True)
        # Inserção em lotes para não travar memória
        chunk = 50_000
        for start in range(0, len(df_all), chunk):
            df_all.iloc[start:start+chunk].to_sql(
                'area_data', engine, if_exists='append', index=False)
        print(f"  ✔ area_data: {len(df_all):,} registros")


def populate_accuracy(engine):
    files = sorted(ACC_DIR.glob('*.csv'))
    print(f"\n  Processando {len(files)} CSVs de acurácia...")
    all_rows = []

    for csv_path in tqdm(files, desc='  Acurácia'):
        meta = parse_acc_filename(csv_path.name)
        if not meta:
            continue
        try:
            df = pd.read_csv(csv_path, low_memory=False)
        except Exception as e:
            print(f"\n    ⚠ {csv_path.name}: {e}")
            continue

        nc    = meta['num_class']
        remap = REMAP_REF_10 if nc == 10 else REMAP_REF_7

        years_avail = []
        for y in range(1985, 2026):
            rc = f'CLASS_{y}'
            pc = f'classification_{y}'
            if rc in df.columns and pc in df.columns:
                years_avail.append(y)
                if df[rc].dtype == object:
                    df[rc] = df[rc].map(remap)

        if not years_avail:
            continue

        if 'bacia' in df.columns:
            df['bacia'] = df['bacia'].astype(str)
            bacias_list = sorted(df['bacia'].unique().tolist())
        else:
            bacias_list = []

        all_bacias = ['Caatinga'] + bacias_list

        for bacia in all_bacias:
            df_sub = df if bacia == 'Caatinga' else df[df['bacia'] == bacia]
            if df_sub.empty:
                continue

            all_ref_parts, all_pred_parts = [], []

            for yy in years_avail:
                rc = f'CLASS_{yy}'
                pc = f'classification_{yy}'
                res = calc_metrics(df_sub[rc], df_sub[pc], nc, only_all_cm=False)
                if res:
                    res.update({
                        'id_bacia':  bacia,
                        'year':      str(yy),
                        'layer_key': meta['layer_key'],
                        'version':   meta['version'],
                        'num_class': nc,
                        'janela':    meta['janela'],
                    })
                    all_rows.append(res)
                all_ref_parts.append(df_sub[rc])
                all_pred_parts.append(df_sub[pc])

            # Acurácia "All" (todos os anos)
            ref_all  = pd.concat(all_ref_parts,  ignore_index=True)
            pred_all = pd.concat(all_pred_parts, ignore_index=True)
            res_all  = calc_metrics(ref_all, pred_all, nc, only_all_cm=True)
            if res_all:
                res_all.update({
                    'id_bacia':  bacia,
                    'year':      'All',
                    'layer_key': meta['layer_key'],
                    'version':   meta['version'],
                    'num_class': nc,
                    'janela':    meta['janela'],
                })
                all_rows.append(res_all)

    if all_rows:
        df_out = pd.DataFrame(all_rows)
        chunk = 10_000
        for start in range(0, len(df_out), chunk):
            df_out.iloc[start:start+chunk].to_sql(
                'accuracy_data', engine, if_exists='append', index=False)
        print(f"  ✔ accuracy_data: {len(df_out):,} registros")


# ─────────────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────────────
def main():
    print("=" * 60)
    print("  POPULAMENTO DO BANCO — MapBiomas Dashboard v2")
    print("=" * 60)

    app = create_app()
    with app.app_context():
        print("\n[1/2] Recriando tabelas...")
        db.drop_all()
        db.create_all()

        print("[2/6] Populando class_info...")
        populate_class_info(db.engine)

        print("[3/6] Populando limit_area...")
        populate_limit_area(db.engine)

        print("[4/6] Populando area_data...")
        populate_areas(db.engine)

        print("[5/6] Populando accuracy_data (pode demorar alguns minutos)...")
        populate_accuracy(db.engine)

    print("\n" + "=" * 60)
    print("  ✅  Banco de dados populado com sucesso!")
    print("=" * 60)


if __name__ == '__main__':
    main()
