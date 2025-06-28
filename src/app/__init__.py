# app/__init__.py
import os
from flask import Flask
from config import Config
from flask_sqlalchemy import SQLAlchemy

# Inicializa a extensão do banco de dados
db = SQLAlchemy()

#  Relação de camadas para destaques:
#  Assentamento_Brasil - Asentamentos 
#  nucleos_desertificacao - Nucleos de desertificação,
#  UnidadesConservacao_S - Unidades de conservação  -> 'TipoUso' -> ["Proteção Integral", "Proteção integral",  "Uso Sustentável"]
#  unidade_gerenc_RH_SNIRH_2020- Unidade de gerenciamento de recursos Hidricos 
#  tis_poligonais_portarias -  Terras indígenas
#  prioridade-conservacao - Prioridade de conservação (usar apenas Extremamente alta)
#  florestaspublicas - Unidades de conservação
#  areas_Quilombolas - áreas quilombolas
#  macro_RH - Bacias hidrográficas 
#  reserva da biosfera - 'zona' ->  ["nucleo","transicao","amortecimento"]
#  Novo limite do semiarido 2024

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
    dict_nome_subregions =  {
        'Assent-Br': ['Assent-Br'],
        'res-biosf': ['nucleo', 'transicao', 'amortecimento'],
        'prioridade-conservacao-V2': [
            'prioridade-conservacao-V1', 'prioridade-conservacao-V2', 'ext-alta'
        ],
        'bacia-sao-francisco': [
            'Baixo-Sao-Francisco', 'Submedio-Sao-Francisco',
            'Medio-Sao-Francisco','Alto-Sao-Francisco'
        ],
        'meso-RH': [
            'AltoP', 'MedioP','BaixoP',
            'AtlaNO-Jag','AtlaNO-LC','AtlaNO-LRGNP','AtlaNO-PPA','AtlaNO-LPA',
            'MedioSF','SubmedSF','BaixoSF',
            'AtlaL-C','AtlaL-IP','AtlaL-JP','AtlaL-VB',
        ],
        'micro-RH': ['micro-RH'],
        'macro-RH': [
            "PARNAÍBA", "ATLÂNTICO NORDESTE ORIENTAL", 
            "SÃO FRANCISCO", "ATLÂNTICO LESTE"
        ],
        'UnidCons-S': ['UnidCons-S', 'prot-Int', 'Uso-sustt'],
        'tis-port': ['tis-port'],
        'areaQuil': ['areaQuil'],        
        'nucleos-desert': ['nucleos-desert'] ,        
        'energias-renovaveis': ['energias-renovaveis'],         
        'transposicao-cbhsf': ['transposicao-cbhsf'],    
        'matopiba': ['matopiba'],        
    }
    # lst_nome_subregions = [
    #     'Assent-Br','nucleo', 'transicao', 'amortecimento','prioridade-conservacao-V1', 
    #     'prioridade-conservacao-V2', 'ext-alta','Baixo-Sao-Francisco', 'Submedio-Sao-Francisco',
    #     'Medio-Sao-Francisco','Alto-Sao-Francisco','AltoP', 'MedioP','BaixoP',
    #     'AtlaNO-Jag','AtlaNO-LC','AtlaNO-LRGNP','AtlaNO-PPA','AtlaNO-LPA',
    #     'MedioSF','SubmedSF','BaixoSF','AtlaL-C','AtlaL-IP','AtlaL-JP','AtlaL-VB',
    #     'micro-RH',"PARNAÍBA", "ATLÂNTICO NORDESTE ORIENTAL","SÃO FRANCISCO", 
    #     "ATLÂNTICO LESTE",'UnidCons-S', 'prot-Int', 'Uso-sustt',
    #     'tis-port','areaQuil','nucleos-desert','energias-renovaveis','transposicao-cbhsf',
    #     'matopiba'
    # ]

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

        # Passamos as listas para o template no momento da renderização
        # Passa os mesmos dados para JS
        return render_template(
            'index.html', 
            estados=estados_options,
            regions=region_options,
            vetores=dict_nome_subregions,    
            vetores_data=dict_nome_subregions
        )

    return app