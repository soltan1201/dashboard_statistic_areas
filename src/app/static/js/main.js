/* main.js — MapBiomas Caatinga Dashboard v2 */
'use strict';

document.addEventListener('DOMContentLoaded', () => {

    // ─────────────────────────────────────────────────────────────────────
    // 1. ESTADO GLOBAL
    // ─────────────────────────────────────────────────────────────────────
    let map        = null;
    let geojsonLyr = null;
    let overlayLyr = null;
    let lastData   = null;

    // ─────────────────────────────────────────────────────────────────────
    // 2. MAPA LEAFLET
    // ─────────────────────────────────────────────────────────────────────
    const mapEl = document.getElementById('map-container');
    if (mapEl) {
        map = L.map('map-container', { zoomControl: true }).setView([-9.5, -40], 5);
        L.tileLayer('https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png', {
            attribution: '&copy; <a href="https://carto.com/">CartoDB</a>',
            maxZoom: 18
        }).addTo(map);
        document.getElementById('map-reset').addEventListener('click', () => {
            if (geojsonLyr) map.fitBounds(geojsonLyr.getBounds(), { padding: [10, 10] });
            else map.setView([-9.5, -40], 5);
        });
    }

    // ─────────────────────────────────────────────────────────────────────
    // 3. SLIDER TEMPORAL
    // ─────────────────────────────────────────────────────────────────────
    const sliderEl = document.getElementById('time-slider');
    if (sliderEl) {
        noUiSlider.create(sliderEl, {
            start: [1985, 2025], connect: true, step: 1,
            range: { min: 1985, max: 2025 },
            format: { to: v => Math.round(v), from: v => +v }
        });
        sliderEl.noUiSlider.on('update', ([s, e]) => {
            document.getElementById('start-year-label').textContent = s;
            document.getElementById('end-year-label').textContent   = e;
        });
    }

    // ─────────────────────────────────────────────────────────────────────
    // 4. VISIBILIDADE JANELA / VERSÃO CONFORME CAMADA
    // ─────────────────────────────────────────────────────────────────────
    const layerSel   = document.getElementById('layer-filter');
    const groupJan   = document.getElementById('group-janela');
    const groupVers  = document.getElementById('group-version');
    const versInput  = document.getElementById('version-filter');
    const COLL_KEYS  = ['Map71', 'Map80', 'Map90', 'Map100'];

    function updateLayerControls() {
        const opt = layerSel.selectedOptions[0];
        const needsJanela = opt && opt.dataset.needsJanela === '1';
        const isCollection = COLL_KEYS.includes(layerSel.value);

        groupJan.classList.toggle('d-none', !needsJanela);
        // Para coleções a versão é fixa (10) — oculta input
        groupVers.classList.toggle('d-none', isCollection);
        if (isCollection) {
            versInput.value = opt.dataset.version || '10';
        }
    }
    layerSel.addEventListener('change', updateLayerControls);
    updateLayerControls();

    // ─────────────────────────────────────────────────────────────────────
    // 5. CARREGAR LISTA DE BACIAS
    // ─────────────────────────────────────────────────────────────────────
    async function loadBacias() {
        try {
            const res = await fetch('/api/bacias');
            const lst = await res.json();
            const sel = document.getElementById('bacia-filter');
            sel.innerHTML = '';   // limpa a opção estática para evitar duplicatas
            lst.forEach(b => {
                const opt = document.createElement('option');
                opt.value = b;
                opt.textContent = b === 'Caatinga' ? 'Bacias (all)' : b;
                if (b === 'Caatinga') opt.selected = true;
                sel.appendChild(opt);
            });
        } catch (e) {
            console.warn('Não carregou bacias:', e);
        }
    }
    loadBacias();

    // ─────────────────────────────────────────────────────────────────────
    // 6. PARÂMETROS ATUAIS
    // ─────────────────────────────────────────────────────────────────────
    function getParams() {
        const [sy, ey] = sliderEl ? sliderEl.noUiSlider.get() : [1985, 2025];
        const numClass = document.querySelector('input[name="num_class"]:checked')?.value || '10';
        const janElem  = document.querySelector('input[name="janela"]:checked');
        const lk       = layerSel.value;
        const needsJ   = layerSel.selectedOptions[0]?.dataset.needsJanela === '1';
        return {
            bacia:      document.getElementById('bacia-filter').value,
            limit_shp:  document.querySelector('input[name="limit_shp_filter"]:checked')?.value || 'CAATINGA',
            layer_key:  lk,
            version:    versInput.value,
            num_class:  numClass,
            janela:     (needsJ && janElem) ? janElem.value : '',
            start_year: sy,
            end_year:   ey,
            include_cm: document.getElementById('toggle-cm').checked ? 'true' : 'false',
        };
    }

    // ─────────────────────────────────────────────────────────────────────
    // 7. RENDERIZADORES
    // ─────────────────────────────────────────────────────────────────────

    /* 7a. Mapa */
    function renderMap(geojson, overlay) {
        if (!map) return;
        if (geojsonLyr) { map.removeLayer(geojsonLyr); geojsonLyr = null; }
        if (overlayLyr) { map.removeLayer(overlayLyr); overlayLyr = null; }

        // Overlay: todas as bacias em cinza claro (contexto)
        if (overlay) {
            overlayLyr = L.geoJSON(overlay, {
                style: { color: '#666', weight: 0.7, fillColor: '#aaa', fillOpacity: 0.05 }
            }).addTo(map);
        }

        if (!geojson) return;
        geojsonLyr = L.geoJSON(geojson, {
            style: { color: '#1f8d49', weight: 2, fillOpacity: 0.12 }
        }).addTo(map);
        map.fitBounds(geojsonLyr.getBounds(), { padding: [10, 10] });
    }

    /* 7b. Painel de Acurácia */
    function renderAccuracy(acc, layerKey) {
        const el = document.getElementById('accuracy-panel');
        if (!el) return;
        const badge = document.getElementById('acc-layer-badge');
        if (badge) badge.textContent = layerKey;

        if (!acc || acc.selected?.global == null) {
            el.innerHTML = '<p class="text-muted text-center py-4 small">Sem dados de acurácia</p>';
            return;
        }

        const sel     = acc.selected;
        const comp    = acc.comparison;
        const col100  = acc.col100?.global;
        const globPct = sel.global != null ? sel.global.toFixed(1) : '—';

        let trendHtml = '';
        if (comp) {
            const dir  = comp.direction === 'up';
            const cls  = dir ? 'trend-up' : 'trend-down';
            const icon = dir ? 'fa-arrow-up' : 'fa-arrow-down';
            trendHtml = `<span class="trend-badge ${cls}">
                <i class="fas ${icon} me-1"></i>${Math.abs(comp.diff).toFixed(2)}% vs Col 10
            </span>`;
        }

        const col100Html = col100 != null
            ? `<div class="acc-compare-row"><span>Col 10 (ref)</span><strong>${col100.toFixed(1)}%</strong></div>`
            : '';

        el.innerHTML = `
            <div class="acc-global-value">${globPct}<span class="acc-unit">%</span></div>
            <div class="text-center mb-2">${trendHtml}</div>
            ${col100Html}
            <hr class="my-2">
            <div class="acc-metrics-grid">
                <div class="acc-metric"><span>Qtd. Diss.</span><strong>${sel.quantity_diss?.toFixed(2) ?? '—'}%</strong></div>
                <div class="acc-metric"><span>Aloc. Diss.</span><strong>${sel.alloc_diss?.toFixed(2) ?? '—'}%</strong></div>
                <div class="acc-metric"><span>Exchange</span><strong>${sel.exchange?.toFixed(2) ?? '—'}%</strong></div>
                <div class="acc-metric"><span>Shift</span><strong>${sel.shift?.toFixed(2) ?? '—'}%</strong></div>
            </div>
        `;
    }

    /* 7c. Gráfico de acurácia por ano — camada selecionada vs Col 10 */
    function renderAccTimeseries(byYearSelected, byYearCol100, layerKey) {
        const el = document.getElementById('acc-timeseries');
        if (!el) return;

        const traces = [];

        // Col 10 (referência fixa) — linha cinza pontilhada
        if (byYearCol100 && Object.keys(byYearCol100).length > 0) {
            const yrs = Object.keys(byYearCol100).map(Number).sort((a, b) => a - b);
            traces.push({
                x: yrs, y: yrs.map(y => byYearCol100[y]),
                type: 'scatter', mode: 'lines',
                name: 'Col 10',
                line: { color: '#2980b9', width: 1.5, dash: 'dot' },
                hovertemplate: '<b>Col 10</b> %{x}: %{y:.1f}%<extra></extra>',
            });
        }

        // Camada selecionada — linha verde sólida
        if (byYearSelected && Object.keys(byYearSelected).length > 0) {
            const yrs = Object.keys(byYearSelected).map(Number).sort((a, b) => a - b);
            traces.push({
                x: yrs, y: yrs.map(y => byYearSelected[y]),
                type: 'scatter', mode: 'lines+markers',
                name: layerKey || 'Selecionada',
                line: { color: '#1f8d49', width: 2 },
                marker: { color: '#1f8d49', size: 5 },
                hovertemplate: `<b>${layerKey || 'Sel.'}</b> %{x}: %{y:.1f}%<extra></extra>`,
            });
        }

        if (traces.length === 0) {
            el.innerHTML = '<p class="text-muted text-center p-3 small">Sem dados por ano</p>';
            return;
        }

        Plotly.react(el, traces, {
            margin: { t: 5, l: 45, r: 10, b: 30 },
            height: 170,
            yaxis: { title: 'Acurácia (%)', range: [0, 100], ticksuffix: '%' },
            xaxis: { dtick: 5 },
            legend: { orientation: 'h', x: 0, y: 1.15, font: { size: 10 } },
            plot_bgcolor: 'transparent', paper_bgcolor: 'transparent',
        }, { responsive: true, displayModeBar: false });
    }

    /* 7d. Gráficos de área por classe */
    function renderAreaCharts(areaCharts, collectionsCompare, layerKey) {
        const container = document.getElementById('charts-area');
        const countEl   = document.getElementById('class-count');
        if (!container) return;

        if (!areaCharts || Object.keys(areaCharts).length === 0) {
            container.innerHTML = '<div class="col-12 text-center text-muted py-4">Sem dados de área</div>';
            if (countEl) countEl.textContent = '0';
            return;
        }

        // Cor da camada selecionada
        const selColor = window.LAYER_COLORS?.[layerKey] || '#c0392b';
        const dotEl    = document.getElementById('legend-selected-dot');
        const lblEl    = document.getElementById('legend-selected-label');
        if (dotEl) dotEl.style.background = selColor;
        if (lblEl) lblEl.textContent = layerKey;

        const classIds = Object.keys(areaCharts).map(Number).sort((a, b) => a - b);
        if (countEl) countEl.textContent = classIds.length;

        container.innerHTML = '';
        classIds.forEach(clsId => {
            const d    = areaCharts[clsId];
            const colId = `chart-cls-${clsId}`;
            const col   = document.createElement('div');
            col.className = 'col-xl-6 col-md-6';
            col.innerHTML = `
                <div class="dash-card area-chart-card">
                    <div class="dash-card-header dash-card-header--class" style="border-left:4px solid ${d.hex_color}">
                        <span class="cls-dot" style="background:${d.hex_color}"></span>
                        <span class="text-truncate">${d.class_name}</span>
                    </div>
                    <div class="dash-card-body p-1">
                        <div id="${colId}" style="height:220px;"></div>
                    </div>
                </div>`;
            container.appendChild(col);

            // Traces: uma trace por coleção + trace camada selecionada
            const traces = [];

            // Coleções anteriores
            ['Map71', 'Map80', 'Map90', 'Map100'].forEach(colKey => {
                const colData = collectionsCompare?.[colKey];
                if (!colData || !colData.by_class[clsId]) return;
                traces.push({
                    x: colData.years,
                    y: colData.by_class[clsId].map(v => +(v / 1e6).toFixed(4)),
                    type: 'scatter', mode: 'lines',
                    name: colData.label,
                    line: { color: colData.color, width: 1.5, dash: 'dot' },
                    hovertemplate: `<b>${colData.label}</b> %{x}: %{y:.3f} Mha<extra></extra>`,
                    opacity: 0.75,
                });
            });

            // Camada selecionada (barras na cor da própria classe)
            traces.push({
                x: d.years,
                y: d.areas.map(v => +(v / 1e6).toFixed(4)),
                type: 'bar',
                name: layerKey,
                marker: { color: d.hex_color, opacity: 0.88,
                          line: { color: 'rgba(0,0,0,0.15)', width: 0.5 } },
                hovertemplate: `<b>${layerKey}</b> %{x}: %{y:.3f} Mha<extra></extra>`,
            });

            Plotly.react(
                document.getElementById(colId),
                traces,
                {
                    margin: { t: 5, l: 45, r: 5, b: 25 },
                    height: 215,
                    barmode: 'overlay',
                    showlegend: false,
                    xaxis: { dtick: 10, tickfont: { size: 9 } },
                    yaxis: { title: 'Mha', tickfont: { size: 9 }, tickformat: ',.3f' },
                    plot_bgcolor: 'transparent', paper_bgcolor: 'transparent',
                },
                { responsive: true, displayModeBar: false }
            );
        });
    }

    /* 7e. Pie charts */
    function renderPie(elId, pieData, classNames) {
        const el = document.getElementById(elId);
        if (!el || !pieData) return;
        const ids    = Object.keys(pieData).map(Number);
        const values = ids.map(id => +(pieData[id] / 1e6).toFixed(4));
        const labels = ids.map(id => classNames?.[id] || `Cls ${id}`);
        const colors = ids.map(id => {
            const palette = {
                3:  '#1f8d49',  // Floresta
                4:  '#7dc975',  // Savana
                12: '#d6bc74',  // Campestre
                15: '#edde8e',  // Pastagem
                19: '#ffffb2',  // Lav. Temporária
                21: '#ffefc3',  // Mosaico de Uso
                25: '#d4271e',  // Outras n. Veg.
                29: '#e975ad',  // Afloramento
                33: '#2532e4',  // Água
                36: '#c1db8a',  // Lav. Perene
            };
            return palette[id] || '#aaa';
        });
        Plotly.react(el, [{
            values, labels, type: 'pie',
            marker: { colors },
            textinfo: 'none',
            hovertemplate: '<b>%{label}</b><br>%{value:.3f} Mha (%{percent})<extra></extra>',
            hole: 0.35,
        }], {
            margin: { t: 5, l: 0, r: 0, b: 5 },
            height: 270,
            showlegend: false,
            plot_bgcolor: 'transparent', paper_bgcolor: 'transparent',
        }, { responsive: true, displayModeBar: false });
    }

    /* 7f. Tabela Ganho/Perda */
    function renderGainLoss(data, sy, ey) {
        const el = document.getElementById('gain-loss-container');
        if (!el) return;
        if (!data || data.length === 0) {
            el.innerHTML = '<p class="text-muted text-center p-4 small">Sem dados</p>';
            return;
        }
        let rows = data.map(item => {
            const sa   = (item.start_area / 1e6).toFixed(3);
            const ea   = (item.end_area   / 1e6).toFixed(3);
            const diff = (item.difference / 1e6).toFixed(3);
            const pct  = item.percent.toFixed(2);
            const cls  = item.percent > 0 ? 'gain' : (item.percent < 0 ? 'loss' : '');
            const ico  = item.percent > 0 ? '▲' : (item.percent < 0 ? '▼' : '■');
            return `<tr>
                <td><span class="cls-dot-sm" style="background:${item.hex_color}"></span>${item.class_name}</td>
                <td class="text-end">${sa}</td>
                <td class="text-end">${ea}</td>
                <td class="text-end">${diff}</td>
                <td class="text-end ${cls}">${ico} ${pct}%</td>
            </tr>`;
        }).join('');
        el.innerHTML = `
            <table class="gain-loss-table">
                <thead><tr>
                    <th>Classe</th>
                    <th class="text-end">Área ${sy} (Mha)</th>
                    <th class="text-end">Área ${ey} (Mha)</th>
                    <th class="text-end">Dif. (Mha)</th>
                    <th class="text-end">%</th>
                </tr></thead>
                <tbody>${rows}</tbody>
            </table>`;
    }

    /* 7h. Ranking de acurácia por bacia vs Col 10 */
    async function loadAccuracyRanking(params) {
        const el    = document.getElementById('acc-ranking-container');
        const badge = document.getElementById('acc-ranking-badge');
        if (!el) return;

        try {
            const qs  = new URLSearchParams({
                layer_key: params.layer_key,
                version:   params.version,
                num_class: params.num_class,
                janela:    params.janela || '',
            }).toString();
            const res  = await fetch(`/api/accuracy_ranking?${qs}`);
            const data = await res.json();

            if (!data.length) {
                el.innerHTML = '<p class="text-muted text-center p-4 small">Sem dados de acurácia</p>';
                if (badge) badge.textContent = '—';
                return;
            }

            const worseCount = data.filter(r => r.worse).length;
            if (badge) badge.textContent = `${worseCount} de ${data.length} bacias abaixo da Col 10`;

            const rows = data.map(r => {
                const accSel   = r.acc_sel   != null ? r.acc_sel.toFixed(1)   + '%' : '—';
                const accCol10 = r.acc_col10 != null ? r.acc_col10.toFixed(1) + '%' : '—';
                const diff     = r.diff      != null ? r.diff.toFixed(2)      + '%' : '—';
                const icon     = r.worse ? '▼' : (r.diff > 0 ? '▲' : '■');
                const cls      = r.worse ? 'loss' : (r.diff > 0 ? 'gain' : '');
                const rowCls   = r.worse ? 'row-worse' : '';
                const isAggreg = r.id_bacia === 'Caatinga' ? 'font-weight:600;' : '';
                return `<tr class="${rowCls}" style="${isAggreg}">
                    <td>${r.id_bacia}</td>
                    <td class="text-end">${accSel}</td>
                    <td class="text-end">${accCol10}</td>
                    <td class="text-end ${cls}">${icon} ${diff}</td>
                </tr>`;
            }).join('');

            el.innerHTML = `
                <table class="gain-loss-table">
                    <thead><tr>
                        <th>Bacia</th>
                        <th class="text-end">Acurácia</th>
                        <th class="text-end">Col 10</th>
                        <th class="text-end">Diferença</th>
                    </tr></thead>
                    <tbody>${rows}</tbody>
                </table>`;
        } catch (e) {
            console.warn('Ranking acurácia:', e);
            if (el) el.innerHTML = '<p class="text-muted text-center p-4 small">Erro ao carregar ranking</p>';
        }
    }

    /* helper: cor hex de uma classe pelo id */
    function getClassHex(clsId) {
        return lastData?.area_charts?.[clsId]?.hex_color || '#aaaaaa';
    }

    /* 7g-extra. Comissão e Omissão — dois gráficos lado a lado */
    function renderCmErrorCharts(cm) {
        const commPan = document.getElementById('cm-commission-panel');
        const omitPan = document.getElementById('cm-omission-panel');

        function hidePanels() {
            if (commPan) commPan.style.display = 'none';
            if (omitPan) omitPan.style.display = 'none';
        }

        if (!cm) { hidePanels(); return; }

        const elComm = document.getElementById('cm-commission-chart');
        const elOmit = document.getElementById('cm-omission-chart');
        if (!elComm || !elOmit) { hidePanels(); return; }

        const classes = cm.classes;
        const matrix  = cm.matrix;
        const n       = classes.length;

        const clsNames = document.querySelector('input[name="num_class"]:checked')?.value === '7'
            ? window.CLASS_NAMES_7 : window.CLASS_NAMES_10;

        const rowSums = matrix.map(row => row.reduce((a, b) => a + b, 0));
        const colSums = classes.map((_, j) => matrix.reduce((s, row) => s + (row[j] || 0), 0));

        const yLabels = classes.map(c => clsNames[c] || `Cl.${c}`);
        const h = Math.max(220, n * 26 + 60);

        // Tick labels: eixo simétrico mostrando valores absolutos (como na referência)
        const tickVals = [-1,-0.9,-0.8,-0.7,-0.6,-0.5,-0.4,-0.3,-0.2,-0.1,0,0.1,0.2,0.3,0.4,0.5,0.6,0.7,0.8,0.9,1];
        const tickText = tickVals.map(v => Math.abs(v) === 0 ? '0' : String(Math.abs(v)));

        const sharedLayout = {
            barmode: 'relative',
            height: h,
            margin: { t: 10, l: 180, r: 15, b: 40 },
            xaxis: {
                title: 'Valor',
                range: [-1.05, 1.05],
                tickvals: tickVals,
                ticktext: tickText,
                zeroline: true, zerolinecolor: '#333', zerolinewidth: 2,
                tickfont: { size: 9 },
            },
            yaxis: { automargin: true, tickfont: { size: 10 } },
            showlegend: false,
            plot_bgcolor: 'transparent',
            paper_bgcolor: 'transparent',
        };

        // ── COMISSÃO (colunas): Classes Mapeadas ──────────────────────────
        // Positivo = diagonal (Acurácia do Usuário)
        // Negativo = erros de comissão por classe confusora
        const commTraces = [];

        // Diagonal
        commTraces.push({
            x: classes.map((_, i) => colSums[i] > 0 ? matrix[i][i] / colSums[i] : 0),
            y: yLabels,
            type: 'bar', orientation: 'h',
            name: 'Correto',
            marker: { color: classes.map(c => getClassHex(c)), opacity: 0.85 },
            hovertemplate: '<b>Correto</b> %{y}: %{x:.1%}<extra></extra>',
        });

        // Erros de comissão: classe j mapeada como classe i → negativo no eixo da classe i
        classes.forEach((cls_j, j) => {
            const xVals = classes.map((_, i) => {
                if (i === j || colSums[i] === 0) return 0;
                return -(matrix[j][i] / colSums[i]);
            });
            if (xVals.every(v => v === 0)) return;
            const nameJ = clsNames[cls_j] || `Cl.${cls_j}`;
            commTraces.push({
                x: xVals, y: yLabels,
                type: 'bar', orientation: 'h',
                name: nameJ,
                marker: { color: getClassHex(cls_j), opacity: 0.82 },
                hovertemplate: `<b>${nameJ}</b> em %{y}: %{customdata:.1%}<extra></extra>`,
                customdata: xVals.map(v => Math.abs(v)),
            });
        });

        // ── OMISSÃO (filas): Classes Reais ────────────────────────────────
        // Positivo = diagonal (Acurácia do Produtor)
        // Negativo = erros de omissão por classe de destino
        const omitTraces = [];

        // Diagonal
        omitTraces.push({
            x: classes.map((_, i) => rowSums[i] > 0 ? matrix[i][i] / rowSums[i] : 0),
            y: yLabels,
            type: 'bar', orientation: 'h',
            name: 'Correto',
            marker: { color: classes.map(c => getClassHex(c)), opacity: 0.85 },
            hovertemplate: '<b>Correto</b> %{y}: %{x:.1%}<extra></extra>',
        });

        // Erros de omissão: classe i mapeada como classe j → negativo no eixo da classe i
        classes.forEach((cls_j, j) => {
            const xVals = classes.map((_, i) => {
                if (i === j || rowSums[i] === 0) return 0;
                return -(matrix[i][j] / rowSums[i]);
            });
            if (xVals.every(v => v === 0)) return;
            const nameJ = clsNames[cls_j] || `Cl.${cls_j}`;
            omitTraces.push({
                x: xVals, y: yLabels,
                type: 'bar', orientation: 'h',
                name: nameJ,
                marker: { color: getClassHex(cls_j), opacity: 0.82 },
                hovertemplate: `<b>${nameJ}</b> em %{y}: %{customdata:.1%}<extra></extra>`,
                customdata: xVals.map(v => Math.abs(v)),
            });
        });

        if (commPan) commPan.style.display = '';
        if (omitPan) omitPan.style.display = '';

        Plotly.react(elComm, commTraces, sharedLayout, { responsive: true, displayModeBar: false });
        Plotly.react(elOmit, omitTraces, sharedLayout, { responsive: true, displayModeBar: false });
    }

    /* 7g. Matriz de confusão */
    function renderConfusionMatrix(cm) {
        const el  = document.getElementById('confusion-matrix-container');
        const pan = document.getElementById('cm-panel');
        if (!el) return;

        const showCM = document.getElementById('toggle-cm').checked;
        if (!showCM || !cm) {
            if (pan) pan.style.display = 'none';
            renderCmErrorCharts(null);
            return;
        }
        if (pan) pan.style.display = '';

        const classes = cm.classes;
        const matrix  = cm.matrix;
        const total   = matrix.flat().reduce((a, b) => a + b, 0);

        // Calcular acurácia global do usuário
        const diag = classes.reduce((s, _, i) => s + (matrix[i]?.[i] || 0), 0);
        const acc  = total > 0 ? (diag / total * 100).toFixed(1) : '—';
        const badge = document.getElementById('cm-acc-badge');
        if (badge) badge.textContent = `Acc = ${acc}%`;

        // Rótulos de classes
        const clsNames = (document.querySelector('input[name="num_class"]:checked')?.value === '7')
            ? window.CLASS_NAMES_7
            : window.CLASS_NAMES_10;

        const header = `<tr><th class="cm-corner">Ref ↓ / Pred →</th>` +
            classes.map(c => `<th>${clsNames[c] || c}</th>`).join('') + `<th>Total</th></tr>`;

        const bodyRows = matrix.map((row, i) => {
            const rowTotal = row.reduce((a, b) => a + b, 0);
            const cells    = row.map((v, j) => {
                const pct  = rowTotal > 0 ? (v / rowTotal * 100) : 0;
                const isDiag = i === j;
                const style  = isDiag
                    ? `background:rgba(31,141,73,${(pct/100).toFixed(2)});color:${pct>50?'#fff':'#222'}`
                    : `background:rgba(231,76,60,${(pct/200).toFixed(3)})`;
                return `<td style="${style}" title="${v} (${pct.toFixed(1)}%)">${v}</td>`;
            }).join('');
            return `<tr><th>${clsNames[classes[i]] || classes[i]}</th>${cells}<td class="cm-total">${rowTotal}</td></tr>`;
        }).join('');

        const colTotals = classes.map((_, j) => matrix.reduce((s, r) => s + (r[j] || 0), 0));
        const totalRow  = `<tr class="cm-total-row"><th>Total</th>` +
            colTotals.map(v => `<td>${v}</td>`).join('') +
            `<td><strong>${total}</strong></td></tr>`;

        el.innerHTML = `<table class="cm-table">${header}${bodyRows}${totalRow}</table>`;

        renderCmErrorCharts(cm);
    }

    // ─────────────────────────────────────────────────────────────────────
    // 8. ATUALIZAÇÃO PRINCIPAL
    // ─────────────────────────────────────────────────────────────────────
    async function updateDashboard() {
        const statusBar = document.getElementById('status-bar');
        const errorBar  = document.getElementById('error-bar');
        if (statusBar) statusBar.classList.remove('d-none');
        if (errorBar)  errorBar.classList.add('d-none');

        try {
            const p   = getParams();
            const qs  = new URLSearchParams(p).toString();
            const res = await fetch(`/api/data?${qs}`);

            if (!res.ok) {
                const msg = await res.text();
                throw new Error(`API ${res.status}: ${msg}`);
            }

            const data = await res.json();
            lastData = data;

            const numClass = +p.num_class;
            const clsNames = numClass === 7 ? window.CLASS_NAMES_7 : window.CLASS_NAMES_10;

            renderMap(data.map_geojson, data.map_overlay);
            renderAccuracy(data.accuracy, p.layer_key);
            renderAccTimeseries(
                data.accuracy?.selected?.by_year,
                data.accuracy?.col100?.by_year,
                p.layer_key
            );
            renderAreaCharts(data.area_charts, data.collections_compare, p.layer_key);
            renderPie('pie-1985', data.pie_1985, clsNames);
            renderPie('pie-end',  data.pie_end,  clsNames);

            const pieEndLbl = document.getElementById('pie-end-label');
            if (pieEndLbl) pieEndLbl.textContent = data.pie_end_year || p.end_year;

            renderGainLoss(data.gain_loss, p.start_year, p.end_year);
            renderConfusionMatrix(data.confusion_matrix);
            loadAccuracyRanking(p);

        } catch (err) {
            console.error('Erro ao atualizar dashboard:', err);
            if (errorBar) {
                errorBar.textContent = `Erro: ${err.message}`;
                errorBar.classList.remove('d-none');
            }
        } finally {
            if (statusBar) statusBar.classList.add('d-none');
        }
    }

    // ─────────────────────────────────────────────────────────────────────
    // 9. CHECKBOX MATRIZ DE CONFUSÃO
    // ─────────────────────────────────────────────────────────────────────
    document.getElementById('toggle-cm').addEventListener('change', function () {
        if (this.checked && lastData?.confusion_matrix) {
            renderConfusionMatrix(lastData.confusion_matrix);
        } else if (!this.checked) {
            const pan = document.getElementById('cm-panel');
            if (pan) pan.style.display = 'none';
        } else {
            // precisa chamar API com include_cm=true
            updateDashboard();
        }
    });

    // ─────────────────────────────────────────────────────────────────────
    // 10. EVENT LISTENERS
    // ─────────────────────────────────────────────────────────────────────
    document.getElementById('btn-update').addEventListener('click', updateDashboard);

    // Mudança de qualquer filtro (exceto toggle-cm que tem handler próprio)
    ['bacia-filter', 'layer-filter', 'version-filter'].forEach(id => {
        document.getElementById(id)?.addEventListener('change', updateDashboard);
    });
    document.querySelectorAll('input[name="num_class"]').forEach(
        el => el.addEventListener('change', updateDashboard)
    );
    document.querySelectorAll('input[name="janela"]').forEach(
        el => el.addEventListener('change', updateDashboard)
    );
    document.querySelectorAll('input[name="limit_shp_filter"]').forEach(
        el => el.addEventListener('change', updateDashboard)
    );
    if (sliderEl) {
        sliderEl.noUiSlider.on('change', updateDashboard);
    }

    // ─────────────────────────────────────────────────────────────────────
    // 11. INICIALIZAÇÃO
    // ─────────────────────────────────────────────────────────────────────
    updateDashboard();
});
