# Dashboard de Estatísticas de Áreas — MapBiomas Caatinga

Dashboard interativo para análise e avaliação de cobertura e uso da terra na Caatinga e no Semiárido. Permite visualizar séries temporais de área por classe, métricas de acurácia, comparações entre coleções MapBiomas e análises por bacia hidrográfica.

---

## Pré-requisitos

- Python 3.10 ou superior
- Git

---

## 1. Clonar o repositório

```bash
git clone <url-do-repositorio>
cd dashboard_statistic_areas
```

---

## 2. Criar e ativar o ambiente virtual

```bash
# Criar o venv na raiz do projeto
python3 -m venv .venv

# Ativar (Linux / macOS)
source .venv/bin/activate

# Ativar (Windows)
.venv\Scripts\activate
```

> Para reativar em sessões futuras, sempre execute `source .venv/bin/activate` antes de rodar o projeto.

---

## 3. Instalar as dependências

```bash
pip install --upgrade pip
pip install -r src/requirements.txt
pip install scikit-learn tqdm tabulate
```

---

## 4. Configurar o arquivo `.env`

O arquivo `src/.env` já está incluído no repositório com valores padrão para desenvolvimento:

```dotenv
SECRET_KEY='7e86e14ec0f80183e76419acc8dd66082d76eaa2454fad58'
FLASK_APP=run.py
FLASK_DEBUG=1
```

> Em produção, gere uma chave nova:
> ```bash
> python3 -c "import secrets; print(secrets.token_hex(24))"
> ```

---

## 5. Preparar os dados

Os dados de área e acurácia devem estar nas pastas:

```
src/dados/AREA-EXPORT-COL10/    ← CSVs de área por bacia (calculoAreaV3.py)
src/dados/ptosAccCol11/         ← CSVs de pontos de acurácia (getCSVsPointstoAccGlobarlBacia_2col.py)
src/dados/legenda.csv           ← Legenda de classes e cores
src/dados/areas_biomas_semiarido.csv  ← Áreas totais dos limites
src/dados/geojson/              ← Camadas GeoJSON para o mapa
```

---

## 6. Popular o banco de dados

Este passo lê todos os CSVs, calcula as métricas de acurácia e preenche o banco SQLite. **Só precisa ser executado uma vez** (ou quando os dados forem atualizados).

```bash
cd src/
python populate_db.py
```

> Pode levar entre 5 e 15 minutos dependendo da quantidade de bacias e filtros disponíveis.

---

## 7. Iniciar o dashboard

```bash
cd src/
python run.py
```

Abra o navegador em **http://localhost:5000**

---

## Estrutura do projeto

```
dashboard_statistic_areas/
├── .venv/                      # Ambiente virtual (não versionado)
├── src/
│   ├── app/
│   │   ├── __init__.py         # Factory da aplicação Flask
│   │   ├── models.py           # Modelos SQLAlchemy (AreaData, AccuracyData, ...)
│   │   ├── api/
│   │   │   └── routes.py       # API REST (/api/data, /api/bacias, /api/layers)
│   │   ├── templates/
│   │   │   └── index.html      # Template principal
│   │   └── static/
│   │       ├── js/main.js      # Lógica do frontend
│   │       └── css/style.css   # Estilos
│   ├── ferramentas/
│   │   ├── calculoAreaV3.py            # Cálculo de área via GEE
│   │   ├── getCSVsPointstoAccGlobarlBacia_2col.py  # Coleta de pontos de acurácia
│   │   ├── newsMetrics_AccuracySamples.py          # Métricas de acurácia
│   │   ├── joinAlltables_PointsAcc_Basin.py
│   │   └── joinMatrixConfutionbyBasin.py
│   ├── dados/                  # CSVs e GeoJSONs
│   ├── instance/
│   │   └── database.sqlite     # Banco de dados (gerado pelo populate_db.py)
│   ├── populate_db.py          # Script de populamento do banco
│   ├── run.py                  # Ponto de entrada da aplicação
│   ├── config.py               # Configurações Flask
│   └── requirements.txt        # Dependências Python
└── README.md
```

---

## Fluxo completo de atualização dos dados

Quando novos mapas são gerados no Google Earth Engine:

```
1. calculoAreaV3.py          → gera CSVs em AREA-EXPORT-COL10/
2. getCSVsPointstoAccGlobarlBacia_2col.py → gera CSVs em ptosAccCol11/
3. python populate_db.py     → recalcula tudo e atualiza o banco
4. python run.py             → dashboard atualizado
```

---

## Tecnologias

| Camada | Tecnologia |
|---|---|
| Backend | Flask 3.1, SQLAlchemy 2.0, pandas, geopandas |
| Banco de dados | SQLite |
| Frontend | Bootstrap 5, Plotly.js, Leaflet.js, noUiSlider |
| Dados GEE | Earth Engine Python API |
| Acurácia | scikit-learn (confusion_matrix, accuracy_score) |
