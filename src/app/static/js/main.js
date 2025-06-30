document.addEventListener('DOMContentLoaded', function () {
    // --- SELETORES DE ELEMENTOS ---
    // Mapa
    const mapContainer = document.getElementById('map-container');
    let map = null;
    let geojsonLayer = null;
    let currentBounds = null;
    
    // Slider de tempo
    const timeSlider = document.getElementById('time-slider');
    const startYearLabel = document.getElementById('start-year-label');
    const endYearLabel = document.getElementById('end-year-label');
    
    // Filtros
    const allFilters = document.querySelectorAll('select, input[name="limit_shp_filter"]');
    const classSearch = document.getElementById('class-search');
    
    // Elementos para mensagens
    const loader = document.getElementById('loader');
    const errorMessage = document.getElementById('error-message');
    const noDataMessage = document.getElementById('no-data-message');
    
    // Áreas de conteúdo
    const chartsArea = document.getElementById('charts-area');
    const classCount = document.getElementById('class-count');
    
    // Template para cards
    const chartCardTemplate = document.getElementById('chart-card-template').innerHTML;
    const compiledTemplate = Handlebars.compile(chartCardTemplate);
    
    // --- INICIALIZAÇÃO DE COMPONENTES ---
    
    // 1. Inicialização do Mapa
    if (mapContainer) {
        map = L.map('map-container').setView([-10, -55], 4);
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            attribution: '&copy; OpenStreetMap contributors'
        }).addTo(map);
        
        // Controles do mapa
        document.getElementById('map-zoom-in').addEventListener('click', () => map.zoomIn());
        document.getElementById('map-zoom-out').addEventListener('click', () => map.zoomOut());
        document.getElementById('map-reset').addEventListener('click', () => {
            if (currentBounds) {
                map.fitBounds(currentBounds);
            } else {
                map.setView([-10, -55], 4);
            }
        });
    }
    
    // 2. Inicialização do Slider de Tempo
    if (timeSlider) {
        noUiSlider.create(timeSlider, {
            start: [1985, 2024],
            connect: true,
            step: 1,
            range: {
                'min': 1985,
                'max': 2024
            },
            format: {
                to: value => Math.round(value),
                from: value => Number(value)
            }
        });
        
        timeSlider.noUiSlider.on('update', values => {
            if (startYearLabel) startYearLabel.textContent = values[0];
            if (endYearLabel) endYearLabel.textContent = values[1];
        });
    }
    
    // 3. Processar vetores hierárquicos
    try {
        if (typeof window.vetoresData !== 'undefined') {
            processVetorOptions(window.vetoresData);
        } else {
            console.warn("Dados de vetores não disponíveis (window.vetoresData)");
        }
    } catch (e) {
        console.error("Erro ao processar vetores:", e);
    }
    
    // 4. Renderizar tabela de ganho/perda
    renderGainLossTable();
    
    // 5. Ocultar loader inicialmente
    if (loader) loader.classList.add('d-none');
    
    // --- FUNÇÕES AUXILIARES ---
    
    // Função para processar vetores hierárquicos
    function processVetorOptions(vetores) {
        const vetorSelect = document.getElementById('nomeVetor-filter');
        if (!vetorSelect) return;
        
        // Limpa opções existentes (exceto a primeira)
        while (vetorSelect.options.length > 1) {
            vetorSelect.remove(1);
        }
        
        const templateElement = document.getElementById('vetor-options-template');
        if (!templateElement) return;
        
        try {
            const template = Handlebars.compile(templateElement.innerHTML);
            const html = template({ vetores: vetores });
            vetorSelect.insertAdjacentHTML('beforeend', html);
        } catch (error) {
            console.error("Erro ao processar template Handlebars:", error);
        }
    }
    
    // Função para atualizar o mapa com novo GeoJSON
    function updateMap(geojson) {
        if (!map) return;
        
        // Remove camada anterior
        if (geojsonLayer) {
            map.removeLayer(geojsonLayer);
        }
        
        // Adiciona nova camada
        if (geojson) {
            geojsonLayer = L.geoJSON(geojson, {
                style: { 
                    color: "#3498db", 
                    weight: 2,
                    fillOpacity: 0.1
                }
            }).addTo(map);
            
            currentBounds = geojsonLayer.getBounds();
            map.fitBounds(currentBounds);
        }
    }
    
    // Função para atualizar os gráficos das classes
    function updateClassCharts(chartsData) {
        if (!chartsData || Object.keys(chartsData).length === 0) {
            chartsArea.innerHTML = `
                <div class="no-data-message animate-fade-in">
                    <i class="fas fa-chart-bar fa-3x mb-3"></i>
                    <h5>Nenhum dado disponível</h5>
                    <p class="text-muted">Não foram encontrados dados para as classes selecionadas.</p>
                </div>
            `;
            classCount.textContent = "0";
            return;
        }
        // 1. Compilar o template Handlebars
        const chartCardTemplate = document.getElementById('chart-card-template').innerHTML;
        const compiledTemplate = Handlebars.compile(chartCardTemplate);
        
        // Preparar dados para o template
        const classesForTemplate = [];
        for (const [classId, chartData] of Object.entries(chartsData)) {
            classesForTemplate.push({
                id: classId,
                name: chartData.class_name
            });
        }
        
        // Renderizar cards usando Handlebars
        chartsArea.innerHTML = compiledTemplate({ classes: classesForTemplate });
        classCount.textContent = classesForTemplate.length;
        
        // Para cada classe nos dados
        for (const [classId, chartData] of Object.entries(chartsData)) {
            const containerId = `chart-class-${classId}`;
            const container = document.getElementById(containerId);
            
            if (!container) {
                console.warn(`Contêiner não encontrado para classe ${classId} (${containerId})`);
                continue;
            }
            
            // Converter m² para km² (1 km² = 1,000,000 m²)
            const areasha2 = chartData.series_data.map(area => area / 1000000);
            
            // Criar novo gráfico
            const plotData = [{
                x: chartData.years,
                y: areasha2,
                type: 'bar',
                marker: { 
                    color: chartData.color,
                    line: {
                        color: 'rgba(0,0,0,0.2)',
                        width: 1
                    }
                },
                hovertemplate: '<b>%{x}</b><br>%{y:.2f} km²<extra></extra>'
            }];
            
            const layout = {
                margin: { t: 10, l: 50, r: 20, b: 40 },
                height: 300,
                showlegend: false,
                xaxis: {
                    title: 'Ano',
                    tickmode: 'linear',
                    dtick: 5
                },
                yaxis: {
                    title: 'Área (M ha)',
                    tickformat: ',.2f'
                },
                hoverlabel: {
                    bgcolor: 'rgba(255,255,255,0.9)',
                    bordercolor: '#ddd',
                    font: {
                        color: '#333'
                    }
                }
            };
            
            try {
                Plotly.newPlot(container, plotData, layout, { 
                    responsive: true,
                    displayModeBar: false
                });
                
                // Adicionar evento de download
                const downloadBtn = container.closest('.chart-card').querySelector('.download-chart');
                if (downloadBtn) {
                    downloadBtn.addEventListener('click', () => {
                        downloadChart(classId, chartData);
                    });
                }
            } catch (error) {
                console.error(`Erro ao renderizar gráfico para classe ${classId}:`, error);
            }
        }
    }
    
    // Função para baixar dados do gráfico
    function downloadChart(classId, chartData) {
        // Criar CSV
        let csv = "Ano,Área (km²)\n";
        chartData.years.forEach((year, index) => {
            const areaKm2 = chartData.series_data[index] / 1000000;
            csv += `${year},${areaKm2.toFixed(2)}\n`;
        });
        
        // Criar blob e link de download
        const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
        const url = URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.setAttribute('href', url);
        link.setAttribute('download', `dados_classe_${classId}.csv`);
        link.style.visibility = 'hidden';
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    }
    
    // Função para atualizar o resumo estatístico
    function updateStatisticalSummary(summaryData) {
        const container = document.getElementById('statistical-summary-container');
        if (!container) return;
        
        if (!summaryData || Object.keys(summaryData).length === 0) {
            container.innerHTML = '<p class="text-muted text-center py-4">Nenhum dado estatístico disponível</p>';
            return;
        }
        
        let html = '<div class="row">';
        
        for (const [key, value] of Object.entries(summaryData)) {
            html += `
                <div class="col-md-6 mb-2">
                    <div class="card stat-card bg-light">
                        <div class="card-body p-2">
                            <strong>${key}:</strong> ${value.toLocaleString()} km²
                        </div>
                    </div>
                </div>
            `;
        }
        
        html += '</div>';
        container.innerHTML = html;
    }
    
    // Função para renderizar a tabela de ganho/perda
    function renderGainLossTable(gainLossData, startYear, endYear) {
        const container = document.getElementById('gain-loss-container');
        if (!container) return;
        
        // Se não houver dados, mostra uma mensagem
        if (!gainLossData || gainLossData.length === 0) {
            container.innerHTML = '<p class="text-muted text-center p-4">Nenhum dado disponível para a tabela de ganho/perda</p>';
            return;
        }
        
        let html = `
            <div class="table-responsive">
                <table class="gain-loss-table">
                    <thead>
                        <tr>
                            <th>Classe</th>
                            <th>Área ${startYear} (milhões ha)</th>
                            <th>Área ${endYear} (milhões ha)</th>
                            <th>Diferença (milhões ha)</th>
                            <th>% Ganho/Perda</th>
                        </tr>
                    </thead>
                    <tbody>
        `;
        
        gainLossData.forEach(item => {
            // Converter áreas de m² para km²
            const startKm2 = (item.start_area / 1000000).toFixed(2);
            const endKm2 = (item.end_area / 1000000).toFixed(2);
            const diffKm2 = (item.difference / 1000000).toFixed(2);
            const percent = item.percent.toFixed(2);
            
            // Determinar a classe CSS com base no sinal da mudança percentual
            const changeClass = item.percent > 0 ? 'positive' : 'negative';
            
            html += `
                <tr>
                    <td>${item.class_name}</td>
                    <td>${startKm2}</td>
                    <td>${endKm2}</td>
                    <td>${diffKm2}</td>
                    <td class="${changeClass}">${percent}%</td>
                </tr>
            `;
        });
        
        html += `
                    </tbody>
                </table>
            </div>
        `;
        
        container.innerHTML = html;
    }
    
    // --- FUNÇÃO PRINCIPAL DE ATUALIZAÇÃO ---
    
    async function updateDashboard() {
        // Mostrar loader e ocultar mensagens de erro
        if (loader) loader.classList.remove('d-none');
        if (errorMessage) errorMessage.classList.add('d-none');
        if (noDataMessage) noDataMessage.classList.add('d-none');
        
        try {
            // Coletar parâmetros dos filtros
            const nomeVetorSelect = document.getElementById('nomeVetor-filter');
            let nomeVetorValue = nomeVetorSelect.value;
            if (nomeVetorValue === 'None') nomeVetorValue = null;
            
            const params = new URLSearchParams({
                limit_shp: document.querySelector('input[name="limit_shp_filter"]:checked').value,
                region: document.getElementById('region-filter').value,
                nomeVetor: nomeVetorValue,
                estado_name: document.getElementById('estado-filter').value,
                start_year: timeSlider.noUiSlider.get()[0],
                end_year: timeSlider.noUiSlider.get()[1]
            });
            
            // Fazer requisição para a API
            const response = await fetch(`/api/data?${params.toString()}`);
            
            // Verificar erros na resposta
            if (!response.ok) {
                const errorText = await response.text();
                throw new Error(`API response error: ${response.status} - ${errorText}`);
            }
            
            const data = await response.json();
            console.log("Dados recebidos da API:", data);
            
            // Obter anos do slider
            const startYear = timeSlider.noUiSlider.get()[0];
            const endYear = timeSlider.noUiSlider.get()[1];
            
            // Verificar se há dados
            if (!data.bar_chart_data || Object.keys(data.bar_chart_data).length === 0) {
                if (noDataMessage) noDataMessage.classList.remove('d-none');
            } else {
                if (noDataMessage) noDataMessage.classList.add('d-none');
            }
            
            // Atualizar componentes visuais
            if (data.map_geojson) updateMap(data.map_geojson);
            if (data.bar_chart_data) updateClassCharts(data.bar_chart_data);
            if (data.statistical_summary) updateStatisticalSummary(data.statistical_summary);

            // Atualizar tabela de ganho/perda com os novos dados
            if (data.gain_loss_data) {
                renderGainLossTable(data.gain_loss_data, startYear, endYear);
            }
            
        } catch (error) {
            console.error("Falha ao atualizar o dashboard:", error);
            if (errorMessage) {
                errorMessage.textContent = `Erro: ${error.message}`;
                errorMessage.classList.remove('d-none');
            }
        } finally {
            // Esconder loader
            if (loader) loader.classList.add('d-none');
        }
    }
    
    // --- EVENT LISTENERS ---
    
    // Adicionar listeners para todos os filtros
    allFilters.forEach(el => el.addEventListener('change', updateDashboard));
    
    // Adicionar listener para o slider
    if (timeSlider && timeSlider.noUiSlider) {
        timeSlider.noUiSlider.on('change', updateDashboard);
    }
    
    // Pesquisa de classes
    if (classSearch) {
        classSearch.addEventListener('input', function() {
            const searchTerm = this.value.toLowerCase();
            const cards = chartsArea.querySelectorAll('.chart-card');
            
            let visibleCount = 0;
            
            cards.forEach(card => {
                const header = card.querySelector('.card-header').textContent.toLowerCase();
                if (header.includes(searchTerm)) {
                    card.style.display = 'block';
                    visibleCount++;
                } else {
                    card.style.display = 'none';
                }
            });
            
            classCount.textContent = visibleCount;
        });
    }
    
    // Botão de exportar
    document.getElementById('export-btn').addEventListener('click', function() {
        // Implementar exportação completa dos dados
        alert('Exportação de dados será implementada em breve!');
    });
    
    // --- INICIALIZAÇÃO DO DASHBOARD ---
    updateDashboard();
});