# app/__init__.py
import os
from flask import Flask
from config import Config
from flask_sqlalchemy import SQLAlchemy

# Inicializa a extensão do banco de dados
db = SQLAlchemy()

def create_app(config_class=Config):
    """Cria e configura uma instância da aplicação Flask."""
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object(config_class)

    # Garante que a pasta 'instance' exista
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    # Inicializa o app com o banco de dados
    db.init_app(app)

    # Registra os blueprints (nossas rotas)
    from .api import routes as api_routes
    app.register_blueprint(api_routes.api_bp, url_prefix='/api')

    # Rota principal para servir o index.html
    @app.route('/')
    def index():
        from flask import render_template
        # --- ADIÇÃO: Definimos as listas de opções para os filtros ---
        # Usamos set() para remover duplicatas e sorted() para ordenar alfabeticamente
        
        estados_options = sorted([
            'MARANHÃO', 'PIAUÍ', 'CEARÁ', 'RIO GRANDE DO NORTE', 'PARAÍBA', 
            'PERNAMBUCO', 'ALAGOAS', 'SERGIPE', 'BAHIA', 'MINAS GERAIS', 'ESPÍRITO SANTO'
        ])

        region_options = sorted(list(set([
            'Assent-Br', 'res-biosf', 'prioridade-conservacao-V2', 'bacia-sao-francisco', 
            'prioridade-conservacao-V1', 'meso-RH', 'transposicao-cbhsf', 'macro-RH', 
            'UnidCons-S', 'tis-port', 'micro-RH', 'semiarido', 'areaQuil', 
            'nucleos-desert', 'energias-renovaveis', 'matopiba', 'micro-RH'
        ])))

        nome_vetor_options = sorted(list(set([
            'Assent-Br', 'res-biosf', 'prioridade-conservacao-V2', 'Alto-Sao-Francisco', 
            'ext-alta', 'AtlaNO-PPA', 'MedioSF', 'Caatinga', 'AtlaNO-Jag', 'BaixoSF', 
            'meso-RH', 'Medio-Sao-Francisco', 'macro-RH', 'UnidCons-S', 'tis-port', 
            'micro-RH', 'AltoP', 'AtlaL-C', 'Baixo-Sao-Francisco', 'transposicao-cbhsf', 
            'BaixoP', 'SA', 'MedioP', 'areaQuil', 'AtlaNO-LRGNP', 'amortecimento', 
            'AtlaL-VB', 'energias-renovaveis', 'AtlaL-JP', 'SubmedSF', 
            'prioridade-conservacao-V1', 'bacia-sao-francisco', 'semiarido',
            'Submedio-Sao-Francisco', 'AtlaNO-LC', 'matopiba', 'Uso-sustt', 
            'nucleos-desert', 'AtlaNO-LPA', 'AtlaL-IP', 'prot-Int', 'nucleo', 'transicao'
        ])))

        # Passamos as listas para o template no momento da renderização
        return render_template(
            'index.html', 
            estados=estados_options,
            regions=region_options,
            vetores=nome_vetor_options
        )

    return app