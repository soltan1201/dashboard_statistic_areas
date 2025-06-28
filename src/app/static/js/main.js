// app/static/js/main.js (Versão Final e Corrigida)

// Função para processar vetores hierárquicos
function processVetorOptions(vetores) {
    console.log("Processando opções de vetor...");
    
    // 1. Encontra o elemento select
    const vetorSelect = document.getElementById('nomeVetor-filter');
    if (!vetorSelect) {
        console.error("Elemento 'nomeVetor-filter' não encontrado!");
        return;
    }
    
    // 2. Limpa opções existentes (mantém apenas 'Nenhum')
    while (vetorSelect.options.length > 1) {
        vetorSelect.remove(1);
    }
    
    // 3. Encontra o template Handlebars
    const templateElement = document.getElementById('vetor-options-template');
    if (!templateElement) {
        console.error("Elemento 'vetor-options-template' não encontrado!");
        return;
    }
    
    // 4. Compila e renderiza o template
    try {
        const template = Handlebars.compile(templateElement.innerHTML);
        const html = template({ vetores: vetores });
        vetorSelect.insertAdjacentHTML('beforeend', html);
        console.log(`Adicionadas ${Object.keys(vetores).length} categorias de vetores`);
    } catch (error) {
        console.error("Erro ao processar template Handlebars:", error);
    }
}

document.addEventListener('DOMContentLoaded', function () {
    
    // --- SELETORES DE ELEMENTOS ---
    // Centraliza a busca por elementos do DOM para facilitar a manutenção.
    const mapContainer = L.map('map-container').setView([-10, -55], 4);
    const timeSlider = document.getElementById('time-slider');
    const startYearLabel = document.getElementById('start-year-label');
    const endYearLabel = document.getElementById('end-year-label');
    const chartsContainer = document.getElementById('charts-container');
    const allFilters = document.querySelectorAll('select, input[name="limit_shp_filter"]');
    const template = document.getElementById('vetor-options-template');
    if (template) {
        console.log("Template encontrado:", template);
    } else {
        console.error("Template NÃO encontrado!");
        // Listar todos os scripts na página para diagnóstico
        console.log("Scripts na página:", document.querySelectorAll('script'));
    }
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

    // Processa os vetores hierárquicos
    try {
        // Os vetores estão disponíveis globalmente via template?
        if (typeof window.vetoresData !== 'undefined') {
            console.log("Dados de vetores disponíveis:", window.vetoresData);
            processVetorOptions(window.vetoresData);
        } else {
            console.warn("Dados de vetores não disponíveis (window.vetoresData)");
        }
    } catch (e) {
        console.error("Erro ao processar vetores:", e);
    }
    

    // --- FUNÇÃO PRINCIPAL DE ATUALIZAÇÃO ---

    /**
     * Coleta todos os filtros, busca os dados na API e dispara a atualização da tela.
     * Esta é a função central que orquestra toda a interatividade.
     */

    // Adicione esta função para atualizar os gráficos das classes
    function updateClassCharts(chartsData) {
        console.log("Dados recebidos para gráficos:", chartsData);
        if (!chartsData || Object.keys(chartsData).length === 0) {
            return;
        }
        
        // Ordenar as classes por nome
        const sortedClasses = Object.keys(chartsData).sort();
        
        sortedClasses.forEach((className, index) => {
            const chartId = `chart-class-${index + 1}`;
            const chartElement = document.getElementById(chartId);
            
            if (chartElement) {
                const chartData = chartsData[className];
                
                const plotData = [{
                    x: chartData.years,
                    y: chartData.series_data.map(area => area / 1000000),
                    type: 'bar',
                    marker: { color: chartData.color }
                }];
                
                const layout = {
                    title: { text: className, font: { size: 14 } },
                    margin: { t: 40, l: 50, r: 20, b: 40 },
                    xaxis: { title: 'Ano' },
                    yaxis: { title: 'Área (km²)' },
                    showlegend: false
                };
                
                Plotly.newPlot(chartElement, plotData, layout, { 
                    responsive: true, 
                    displayModeBar: false 
                });
            }
        });
    }


    // Atualize a função updateDashboard
    async function updateDashboard() {
        chartsContainer.innerHTML = `<div class="d-flex justify-content-center align-items-center h-100"><div class="spinner-border" role="status"></div></div>`;
        console.log("Atualizando dashboard...");
    
        // Mostrar loader
        document.getElementById('loader').classList.remove('d-none');
        document.getElementById('error-message').classList.add('d-none');
        try {
            const nomeVetorSelect = document.getElementById('nomeVetor-filter');
            let nomeVetorValue = nomeVetorSelect.value;
            
            // Se for um grupo, pega o valor selecionado
            if (nomeVetorValue === 'None') nomeVetorValue = null;
            // Corrija os nomes dos parâmetros para combinar com o routes.py
            const params = new URLSearchParams({
                limit_shp: document.querySelector('input[name="limit_shp_filter"]:checked').value,
                region: document.getElementById('region-filter').value,
                // nomeVetor: document.getElementById('nomeVetor-filter').value,
                nomeVetor: nomeVetorValue,
                estado_name: document.getElementById('estado-filter').value,
                start_year: timeSlider.noUiSlider.get()[0],
                end_year: timeSlider.noUiSlider.get()[1]
            });
            
            // Adicione logs para depuração
            console.log(`Solicitando dados da API: /api/data?${params.toString()}`);            
            const response = await fetch(`/api/data?${params.toString()}`);

            console.log("Status da resposta:", response.status);
            
            // Adicione verificação de erro mais detalhada
            if (!response.ok) {
                const errorText = await response.text();
                throw new Error(`API response error: ${response.status} - ${errorText}`);
            }
            
            const data = await response.json();
            console.log("Dados recebidos da API:", data);

            updateMap(data.map_geojson);            
            // Corrija o nome da propriedade (bar_chart_data em vez de charts_data)
            updateChartsGrid(data.bar_chart_data);

            // Esconder loader
            document.getElementById('loader').classList.add('d-none');

        } catch (error) {
            console.error("Falha ao atualizar o dashboard:", error);
            document.getElementById('loader').classList.add('d-none');
            const errorMessage = document.getElementById('error-message');
            errorMessage.textContent = `Erro: ${error.message}`;
            errorMessage.classList.remove('d-none');
        }
    }


    // --- FUNÇÕES DE ATUALIZAÇÃO DOS COMPONENTES VISUAIS ---

    /**
     * Limpa o mapa antigo e desenha a nova camada GeoJSON.
     * @param {object | null} geojson - Os dados geográficos para o mapa.
     */
    function updateMap(geojson) {
        console.log("Atualizando mapa...");
        console.log("Recebido GeoJSON:", geojson ? "Válido" : "Nulo");

        if (geojsonLayer) {
            mapContainer.removeLayer(geojsonLayer);
        }

        if (geojson) {
            try {
                geojsonLayer = L.geoJSON(geojson, {
                                        style: { color: "#3388ff", weight: 2} // Estilo simples para a camada
                                    }).addTo(mapContainer);
                // Ajusta o zoom e a centralização do mapa para a nova camada
                mapContainer.fitBounds(geojsonLayer.getBounds());
                console.log("Mapa atualizado com sucesso");
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
        console.log("Atualizando gráficos de classe...");

        // Se o objeto de dados estiver vazio, mostra uma mensagem amigável.
        if (!chartsData || typeof chartsData !== 'object' || Object.keys(chartsData).length === 0) {
            chartsContainer.innerHTML = '<p class="text-muted text-center p-5">Nenhum dado para exibir com os filtros selecionados.</p>';
            console.warn("Nenhum dado de gráfico recebido");
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