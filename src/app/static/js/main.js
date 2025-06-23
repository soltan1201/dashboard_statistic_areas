// app/static/js/main.js (Versão Final e Corrigida)

document.addEventListener('DOMContentLoaded', function () {
    
    // --- SELETORES DE ELEMENTOS ---
    // Centraliza a busca por elementos do DOM para facilitar a manutenção.
    const mapContainer = L.map('map-container').setView([-10, -55], 4);
    const timeSlider = document.getElementById('time-slider');
    const startYearLabel = document.getElementById('start-year-label');
    const endYearLabel = document.getElementById('end-year-label');
    const chartsContainer = document.getElementById('charts-container');
    const allFilters = document.querySelectorAll('select, input[name="limit_shp_filter"]');
    
    let geojsonLayer = null; // Variável para armazenar a camada do mapa

    // --- INICIALIZAÇÃO DE COMPONENTES ---

    // Mapa de base da OpenStreetMap
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '&copy; OpenStreetMap contributors'
    }).addTo(mapContainer);

    // Slider de tempo com a biblioteca noUiSlider
    noUiSlider.create(timeSlider, {
        start: [1985, 2024],
        connect: true, // A barra entre as alças será colorida
        step: 1,
        range: {
            'min': 1985,
            'max': 2024
        },
        format: { // Garante que os valores sejam sempre números inteiros
            to: value => Math.round(value),
            from: value => Number(value)
        }
    });

    // Atualiza os labels do ano em tempo real conforme o slider se move
    timeSlider.noUiSlider.on('update', values => {
        startYearLabel.textContent = values[0];
        endYearLabel.textContent = values[1];
    });


    // --- FUNÇÃO PRINCIPAL DE ATUALIZAÇÃO ---

    /**
     * Coleta todos os filtros, busca os dados na API e dispara a atualização da tela.
     * Esta é a função central que orquestra toda a interatividade.
     */
    async function updateDashboard() {
        // Mostra um indicador de "Carregando" para o usuário saber que algo está acontecendo.
        chartsContainer.innerHTML = `<div class="d-flex justify-content-center align-items-center h-100"><div class="spinner-border" role="status"><span class="visually-hidden">Loading...</span></div></div>`;

        try {
            // 1. Coleta os valores atuais de todos os filtros da página
            const params = new URLSearchParams({
                limit_shp: document.querySelector('input[name="limit_shp_filter"]:checked').value,
                region: document.getElementById('region-filter').value,
                nomeVetor: document.getElementById('nomeVetor-filter').value,
                estado_name: document.getElementById('estado-filter').value,
                start_year: timeSlider.noUiSlider.get()[0],
                end_year: timeSlider.noUiSlider.get()[1]
            });
            
            // 2. Faz a requisição para a nossa API no back-end
            const response = await fetch(`/api/data?${params.toString()}`);
            if (!response.ok) {
                // Se a resposta da rede não for 'OK' (ex: erro 404, 500), lança um erro.
                throw new Error(`A requisição falhou: ${response.statusText}`);
            }
            
            const data = await response.json();
            // Se o back-end enviar um erro na sua resposta JSON, nós o capturamos aqui.
            if (data.error) {
                throw new Error(`Erro no servidor: ${data.error}`);
            }

            // 3. Se tudo deu certo, chama as funções para desenhar os componentes
            updateMap(data.map_geojson);
            updateChartsGrid(data.charts_data);

        } catch (error) {
            // Se qualquer etapa do 'try' falhar, este bloco é executado.
            console.error("Falha ao atualizar o dashboard:", error);
            // Mostra uma mensagem de erro clara na tela para o usuário.
            chartsContainer.innerHTML = `<div class="alert alert-danger mx-3">Erro ao carregar dados: ${error.message}</div>`;
        }
    }


    // --- FUNÇÕES DE ATUALIZAÇÃO DOS COMPONENTES VISUAIS ---

    /**
     * Limpa o mapa antigo e desenha a nova camada GeoJSON.
     * @param {object | null} geojson - Os dados geográficos para o mapa.
     */
    function updateMap(geojson) {
        if (geojsonLayer) {
            mapContainer.removeLayer(geojsonLayer);
        }
        if (geojson) {
            try {
                geojsonLayer = L.geoJSON(geojson, {
                    style: { color: "#3388ff", weight: 2 } // Estilo simples para a camada
                }).addTo(mapContainer);
                // Ajusta o zoom e a centralização do mapa para a nova camada
                mapContainer.fitBounds(geojsonLayer.getBounds());
            } catch (e) {
                console.error("Erro ao desenhar GeoJSON no mapa:", e);
            }
        }
    }

    /**
     * Limpa a área de gráficos e cria uma nova grade, com um gráfico para cada classe.
     * @param {object} chartsData - O objeto vindo do back-end com os dados de todos os gráficos.
     */
    function updateChartsGrid(chartsData) {
        chartsContainer.innerHTML = ''; // Limpa o "loader" ou gráficos antigos

        // Se o objeto de dados estiver vazio, mostra uma mensagem amigável.
        if (!chartsData || Object.keys(chartsData).length === 0) {
            chartsContainer.innerHTML = '<p class="text-muted text-center p-5">Nenhum dado para exibir com os filtros selecionados.</p>';
            return;
        }

        // Itera sobre cada classe de cobertura recebida do back-end.
        for (const className in chartsData) {
            const chartData = chartsData[className];
            const chartDiv = document.createElement('div');
            chartsContainer.appendChild(chartDiv);

            // Prepara os dados e o layout para a biblioteca Plotly.
            const plotData = [{
                x: chartData.years,
                y: chartData.series_data.map(area => area / 1000000), // Converte m² para km²
                type: 'bar',
                marker: { color: chartData.color } // Usa a cor enviada pelo back-end
            }];

            const layout = {
                title: { text: chartData.class_name, font: { size: 14 }},
                margin: { l: 60, r: 20, t: 40, b: 40 },
                xaxis: { title: 'Ano', titlefont: {size: 12} },
                yaxis: { title: 'Área (km²)', titlefont: {size: 12}},
                showlegend: false
            };
            
            // Cria o gráfico no div que acabamos de adicionar.
            Plotly.newPlot(chartDiv, plotData, layout, { responsive: true, displayModeBar: false });
        }
    }


    // --- EVENT LISTENERS (GATILHOS DE ATUALIZAÇÃO) ---

    // Adiciona um gatilho para cada filtro. Quando o valor de um deles muda,
    // a função updateDashboard é chamada.
    allFilters.forEach(el => el.addEventListener('change', updateDashboard));
    timeSlider.noUiSlider.on('change', updateDashboard);
    
    // --- CARGA INICIAL ---
    // Chama a função uma vez quando a página carrega para mostrar os dados iniciais.
    updateDashboard();
});