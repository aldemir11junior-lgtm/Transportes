from datetime import date, datetime

from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash

from extensions import db


class Usuario(db.Model, UserMixin):
    """Usuários que acessam o sistema (não há área pública)."""

    __tablename__ = "usuarios"

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    senha_hash = db.Column(db.String(255), nullable=False)
    # perfil: "operacional" (lança viagens) ou "gerente" (vê dashboard e tudo)
    perfil = db.Column(db.String(20), nullable=False, default="operacional")
    criado_em = db.Column(db.DateTime, default=datetime.utcnow)

    def set_senha(self, senha_plana):
        self.senha_hash = generate_password_hash(senha_plana)

    def checar_senha(self, senha_plana):
        return check_password_hash(self.senha_hash, senha_plana)

    def __repr__(self):
        return f"<Usuario {self.email} ({self.perfil})>"


class Motorista(db.Model):
    __tablename__ = "motoristas"

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(120), nullable=False)
    cnh = db.Column(db.String(20))
    telefone = db.Column(db.String(20))
    ativo = db.Column(db.Boolean, default=True)

    viagens = db.relationship("Viagem", backref="motorista", lazy=True)

    def __repr__(self):
        return f"<Motorista {self.nome}>"


class Veiculo(db.Model):
    __tablename__ = "veiculos"

    id = db.Column(db.Integer, primary_key=True)
    placa = db.Column(db.String(10), unique=True, nullable=False)
    modelo = db.Column(db.String(80))
    capacidade_kg = db.Column(db.Float)
    ativo = db.Column(db.Boolean, default=True)

    viagens = db.relationship("Viagem", backref="veiculo", lazy=True)

    def __repr__(self):
        return f"<Veiculo {self.placa}>"


class Viagem(db.Model):
    __tablename__ = "viagens"

    id = db.Column(db.Integer, primary_key=True)
    data = db.Column(db.Date, nullable=False, default=date.today)

    veiculo_id = db.Column(db.Integer, db.ForeignKey("veiculos.id"), nullable=False)
    motorista_id = db.Column(db.Integer, db.ForeignKey("motoristas.id"), nullable=False)

    origem = db.Column(db.String(120), nullable=False)
    destino = db.Column(db.String(120), nullable=False)

    distancia_km = db.Column(db.Float, default=0)
    volume_tons = db.Column(db.Float, default=0)

    faturamento = db.Column(db.Numeric(12, 2), default=0)
    custo_total = db.Column(db.Numeric(12, 2), default=0)

    # em_transito | concluida | atrasada | cancelada
    status = db.Column(db.String(20), nullable=False, default="em_transito")

    observacoes = db.Column(db.Text)

    criado_em = db.Column(db.DateTime, default=datetime.utcnow)
    criado_por_id = db.Column(db.Integer, db.ForeignKey("usuarios.id"))

    criado_por = db.relationship("Usuario")

    @property
    def custo_por_km(self):
        if self.distancia_km and self.distancia_km > 0:
            return float(self.custo_total) / self.distancia_km
        return 0

    def __repr__(self):
        return f"<Viagem {self.id} {self.origem} -> {self.destino}>"
