#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
update_layer.py — Atualiza apenas uma camada (layer_key) no banco sem recriar tudo.

Uso:
    cd src/
    python update_layer.py                          # atualiza spatial_Sieve
    python update_layer.py --layer spatial_Sieve
    python update_layer.py --layer gap_fill --version 2
    python update_layer.py --layer temporalN --janela 3
"""
import argparse, os, re
import pandas as pd
from pathlib import Path
from tqdm import tqdm

os.chdir(Path(__file__).parent)

from app import create_app, db
from app.models import AreaData, AccuracyData

# Reutiliza helpers e constantes do populate_db sem executar o main()
from populate_db import (
    AREA_DIR, ACC_DIR,
    REMAP_REF_10, REMAP_REF_7,
    parse_area_filename, parse_acc_filename,
    calc_metrics,
)


def delete_layer(layer_key: str, version: int | None, num_class: int | None, janela: int | None):
    q_area = db.session.query(AreaData).filter(AreaData.layer_key == layer_key)
    q_acc  = db.session.query(AccuracyData).filter(AccuracyData.layer_key == layer_key)

    if version is not None:
        q_area = q_area.filter(AreaData.version == version)
        q_acc  = q_acc.filter(AccuracyData.version == version)
    if num_class is not None:
        q_area = q_area.filter(AreaData.num_class == num_class)
        q_acc  = q_acc.filter(AccuracyData.num_class == num_class)
    if janela is not None:
        q_area = q_area.filter(AreaData.janela == janela)
        q_acc  = q_acc.filter(AccuracyData.janela == janela)

    n_area = q_area.delete(synchronize_session=False)
    n_acc  = q_acc.delete(synchronize_session=False)
    db.session.commit()
    print(f"  🗑  Removidos: {n_area} registros de area_data, {n_acc} de accuracy_data")


def insert_areas(layer_key: str, version: int | None, num_class: int | None, janela: int | None, engine):
    files = sorted(f for f in AREA_DIR.glob('*.csv') if not re.search(r'\(\d+\)', f.name))
    frames = []

    for csv_path in tqdm(files, desc='  Áreas'):
        meta = parse_area_filename(csv_path.name)
        if not meta or meta['layer_key'] != layer_key:
            continue
        if version   is not None and meta['version']   != version:
            continue
        if num_class is not None and meta['num_class'] != num_class:
            continue
        if janela    is not None and meta['janela']    != janela:
            continue

        try:
            df = pd.read_csv(csv_path)
        except Exception as e:
            print(f"\n    ⚠ {csv_path.name}: {e}")
            continue

        needed = {'area', 'classe', 'id_bacia', 'year'}
        if not needed.issubset(df.columns):
            print(f"\n    ⚠ Colunas ausentes em {csv_path.name}")
            continue

        df = df[['area', 'classe', 'id_bacia', 'year']].copy()
        df['id_bacia']  = df['id_bacia'].astype(str)
        df['layer_key'] = meta['layer_key']
        df['version']   = meta['version']
        df['num_class'] = meta['num_class']
        df['janela']    = meta['janela']
        frames.append(df)

        df_caat = df.groupby(['year', 'classe'])['area'].sum().reset_index()
        df_caat['id_bacia']  = 'Caatinga'
        df_caat['layer_key'] = meta['layer_key']
        df_caat['version']   = meta['version']
        df_caat['num_class'] = meta['num_class']
        df_caat['janela']    = meta['janela']
        frames.append(df_caat)

    if not frames:
        print("  ⚠  Nenhum CSV de área encontrado para os filtros especificados.")
        return

    df_all = pd.concat(frames, ignore_index=True)
    chunk = 50_000
    for start in range(0, len(df_all), chunk):
        df_all.iloc[start:start+chunk].to_sql('area_data', engine, if_exists='append', index=False)
    print(f"  ✔ area_data: {len(df_all):,} registros inseridos")


def insert_accuracy(layer_key: str, version: int | None, num_class: int | None, janela: int | None, engine):
    files = sorted(ACC_DIR.glob('*.csv'))
    all_rows = []

    for csv_path in tqdm(files, desc='  Acurácia'):
        meta = parse_acc_filename(csv_path.name)
        if not meta or meta['layer_key'] != layer_key:
            continue
        if version   is not None and meta['version']   != version:
            continue
        if num_class is not None and meta['num_class'] != num_class:
            continue
        if janela    is not None and meta['janela']    != janela:
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
            rc, pc = f'CLASS_{y}', f'classification_{y}'
            if rc in df.columns and pc in df.columns:
                years_avail.append(y)
                if df[rc].dtype == object:
                    df[rc] = df[rc].map(remap)

        if not years_avail:
            continue

        bacias_list = sorted(df['bacia'].astype(str).unique().tolist()) if 'bacia' in df.columns else []
        all_bacias  = ['Caatinga'] + bacias_list

        for bacia in all_bacias:
            df_sub = df if bacia == 'Caatinga' else df[df['bacia'].astype(str) == bacia]
            if df_sub.empty:
                continue

            all_ref_parts, all_pred_parts = [], []
            for yy in years_avail:
                rc, pc = f'CLASS_{yy}', f'classification_{yy}'
                res = calc_metrics(df_sub[rc], df_sub[pc], nc, only_all_cm=False)
                if res:
                    res.update({'id_bacia': bacia, 'year': str(yy),
                                'layer_key': meta['layer_key'], 'version': meta['version'],
                                'num_class': nc, 'janela': meta['janela']})
                    all_rows.append(res)
                all_ref_parts.append(df_sub[rc])
                all_pred_parts.append(df_sub[pc])

            ref_all  = pd.concat(all_ref_parts, ignore_index=True)
            pred_all = pd.concat(all_pred_parts, ignore_index=True)
            res_all  = calc_metrics(ref_all, pred_all, nc, only_all_cm=True)
            if res_all:
                res_all.update({'id_bacia': bacia, 'year': 'All',
                                'layer_key': meta['layer_key'], 'version': meta['version'],
                                'num_class': nc, 'janela': meta['janela']})
                all_rows.append(res_all)

    if not all_rows:
        print("  ⚠  Nenhum CSV de acurácia encontrado para os filtros especificados.")
        return

    df_out = pd.DataFrame(all_rows)
    for start in range(0, len(df_out), 10_000):
        df_out.iloc[start:start+10_000].to_sql('accuracy_data', engine, if_exists='append', index=False)
    print(f"  ✔ accuracy_data: {len(df_out):,} registros inseridos")


def main():
    parser = argparse.ArgumentParser(description='Atualiza uma camada no banco de dados')
    parser.add_argument('--layer',     default='spatial_Sieve', help='layer_key a atualizar (ex: spatial_Sieve)')
    parser.add_argument('--version',   type=int, default=None,  help='Filtrar por version (omita para todas)')
    parser.add_argument('--num-class', type=int, default=None,  help='Filtrar por num_class (omita para todas)')
    parser.add_argument('--janela',    type=int, default=None,  help='Filtrar por janela (para filtros temporais)')
    args = parser.parse_args()

    print("=" * 60)
    print(f"  ATUALIZAÇÃO PARCIAL — layer_key='{args.layer}'")
    if args.version:   print(f"  version={args.version}")
    if args.num_class: print(f"  num_class={args.num_class}")
    if args.janela:    print(f"  janela={args.janela}")
    print("=" * 60)

    app = create_app()
    with app.app_context():
        print("\n[1/3] Removendo registros antigos...")
        delete_layer(args.layer, args.version, args.num_class, args.janela)

        print("\n[2/3] Inserindo dados de área...")
        insert_areas(args.layer, args.version, args.num_class, args.janela, db.engine)

        print("\n[3/3] Inserindo dados de acurácia...")
        insert_accuracy(args.layer, args.version, args.num_class, args.janela, db.engine)

    print("\n" + "=" * 60)
    print(f"  ✅  Camada '{args.layer}' atualizada com sucesso!")
    print("=" * 60)


if __name__ == '__main__':
    main()
