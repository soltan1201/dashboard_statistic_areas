# app/models.py
from . import db


class AreaData(db.Model):
    """Série temporal de área por bacia, ano, classe e camada."""
    __tablename__ = 'area_data'
    id         = db.Column(db.Integer, primary_key=True)
    id_bacia   = db.Column(db.String(20),  nullable=False, index=True)
    year       = db.Column(db.Integer,     nullable=False)
    classe     = db.Column(db.Integer,     nullable=False)
    area       = db.Column(db.Float,       nullable=False)   # hectares
    layer_key  = db.Column(db.String(30),  nullable=False, index=True)
    version    = db.Column(db.Integer,     default=1)
    num_class  = db.Column(db.Integer,     default=10)
    janela     = db.Column(db.Integer,     nullable=True)


class AccuracyData(db.Model):
    """Métricas de acurácia por bacia, ano/All e camada."""
    __tablename__ = 'accuracy_data'
    id                    = db.Column(db.Integer,  primary_key=True)
    id_bacia              = db.Column(db.String(20), nullable=False, index=True)
    year                  = db.Column(db.String(10), nullable=False)   # '1985' ou 'All'
    global_accuracy       = db.Column(db.Float)
    quantity_diss         = db.Column(db.Float)
    alloc_diss            = db.Column(db.Float)
    exchange              = db.Column(db.Float)
    shift                 = db.Column(db.Float)
    layer_key             = db.Column(db.String(30), nullable=False, index=True)
    version               = db.Column(db.Integer,   default=1)
    num_class             = db.Column(db.Integer,   default=10)
    janela                = db.Column(db.Integer,   nullable=True)
    confusion_matrix_json = db.Column(db.Text,      nullable=True)   # JSON, só para year='All'


class ClassInfo(db.Model):
    """Legenda de classes: nome e cor hex."""
    __tablename__ = 'class_info'
    id         = db.Column(db.Integer, primary_key=True)
    class_name = db.Column(db.String(200))
    code_id    = db.Column(db.Integer, unique=True, nullable=False)
    hex_color  = db.Column(db.String(7))


class LimitArea(db.Model):
    """Área total dos limites (Caatinga, Semiárido, estados)."""
    __tablename__ = 'limit_area'
    id          = db.Column(db.Integer, primary_key=True)
    limit_shp   = db.Column(db.String(50),  nullable=False)
    state_limit = db.Column(db.String(100))
    area        = db.Column(db.Float,       nullable=False)
