# app/models.py
from . import db

class TimeSeriesData(db.Model):
    __tablename__ = 'time_series_data'
    id = db.Column(db.Integer, primary_key=True)
    area = db.Column(db.Float, nullable=False)
    classe = db.Column(db.Integer, nullable=False)
    estado_codigo = db.Column(db.Integer)
    estado_name = db.Column(db.String(100))
    nomeVetor = db.Column(db.String(100))
    region = db.Column(db.String(100))
    year = db.Column(db.Integer, nullable=False)
    limit_shp = db.Column(db.String(50), nullable=False)

class LimitArea(db.Model):
    __tablename__ = 'limit_area'
    id = db.Column(db.Integer, primary_key=True)
    limit_shp = db.Column(db.String(50), nullable=False)
    state_limit = db.Column(db.String(100))
    area = db.Column(db.Float, nullable=False)

class ClassInfo(db.Model):
    __tablename__ = 'class_info'
    id = db.Column(db.Integer, primary_key=True)
    class_name = db.Column(db.String(200))
    code_id = db.Column(db.Integer, unique=True, nullable=False)
    hex_color = db.Column(db.String(7))