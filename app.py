"""
Sistema Operacional - Transportadora XYZ
=========================================
Aplicação interna (sem área pública) para:
  - Equipe operacional lançar viagens/custos
  - Gerência acompanhar um dashboard consolidado

Como rodar:
    pip install -r requirements.txt
    python app.py

Acesse: http://localhost:5000
Login de exemplo criado automaticamente na primeira execução:
    email: gerente@xyz.com   | senha: 123456   (perfil gerente)
    email: operacional@xyz.com | senha: 123456 (perfil operacional)
"""

from datetime import datetime, date
from decimal import Decimal, InvalidOperation

from flask import Flask, render_template, redirect, url_for, request, flash, jsonify
from flask_login import (
    login_user,
    logout_user,
    login_required,
    current_user,
)
from sqlalchemy import func, extract

from config import Config
from extensions import db, login_manager
from models import Usuario, Motorista, Veiculo, Viagem


def criar_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    login_manager.init_app(app)

    with app.app_context():
        db.create_all()
        seed_dados_iniciais()

    registrar_rotas(app)
    return app


@login_manager.user_loader
def carregar_usuario(user_id):
    return Usuario.query.get(int(user_id))


def seed_dados_iniciais():
    """Cria usuários e cadastros básicos de exemplo se o banco estiver vazio."""
    if Usuario.query.first():
        return  # já existe dado, não faz nada

    gerente = Usuario(nome="Gerente XYZ", email="gerente@xyz.com", perfil="gerente")
    gerente.set_senha("123456")

    operacional = Usuario(
        nome="Operacional XYZ", email="operacional@xyz.com", perfil="operacional"
    )
    operacional.set_senha("123456")

    db.session.add_all([gerente, operacional])

    v1 = Veiculo(placa="PN13-0005", modelo="Volvo FH 540", capacidade_kg=25000)
    v2 = Veiculo(placa="PNT3-0002", modelo="Scania R450", capacidade_kg=22000)
    m1 = Motorista(nome="João Motesso", cnh="12345678900")
    m2 = Motorista(nome="Mavia Silva", cnh="98765432100")

    db.session.add_all([v1, v2, m1, m2])
    db.session.commit()


def perfil_requerido(*perfis):
    """Decorator simples para restringir rota por perfil de usuário."""
    from functools import wraps

    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            if not current_user.is_authenticated:
                return login_manager.unauthorized()
            if current_user.perfil not in perfis:
                flash("Você não tem permissão para acessar esta página.", "danger")
                return redirect(url_for("dashboard"))
            return f(*args, **kwargs)

        return wrapper

    return decorator


def registrar_rotas(app):
    # ------------------------------------------------------------------
    # AUTENTICAÇÃO (não há área pública - tudo exige login)
    # ------------------------------------------------------------------
    @app.route("/login", methods=["GET", "POST"])
    def login():
        if current_user.is_authenticated:
            return redirect(url_for("dashboard"))

        if request.method == "POST":
            email = request.form.get("email", "").strip().lower()
            senha = request.form.get("senha", "")

            usuario = Usuario.query.filter_by(email=email).first()
            if usuario and usuario.checar_senha(senha):
                login_user(usuario)
                proxima = request.args.get("next")
                return redirect(proxima or url_for("dashboard"))

            flash("E-mail ou senha inválidos.", "danger")

        return render_template("login.html")

    @app.route("/logout")
    @login_required
    def logout():
        logout_user()
        return redirect(url_for("login"))

    # ------------------------------------------------------------------
    # DASHBOARD (gerente acompanha os indicadores)
    # ------------------------------------------------------------------
    @app.route("/")
    @login_required
    def dashboard():
        ultimas_viagens = (
            Viagem.query.order_by(Viagem.data.desc(), Viagem.id.desc()).limit(6).all()
        )
        return render_template("dashboard.html", ultimas_viagens=ultimas_viagens)

    @app.route("/api/dashboard-data")
    @login_required
    def api_dashboard_data():
        """Retorna os dados agregados que alimentam os gráficos do dashboard."""

        ano_atual = date.today().year

        # Faturamento x Custo total, agrupado por mês do ano atual
        linhas = (
            db.session.query(
                extract("month", Viagem.data).label("mes"),
                func.sum(Viagem.faturamento).label("faturamento"),
                func.sum(Viagem.custo_total).label("custo"),
            )
            .filter(extract("year", Viagem.data) == ano_atual)
            .group_by("mes")
            .order_by("mes")
            .all()
        )

        meses_pt = [
            "Jan", "Fev", "Mar", "Abr", "Mai", "Jun",
            "Jul", "Ago", "Set", "Out", "Nov", "Dez",
        ]
        faturamento_por_mes = {int(l.mes): float(l.faturamento or 0) for l in linhas}
        custo_por_mes = {int(l.mes): float(l.custo or 0) for l in linhas}

        labels = meses_pt
        faturamento_serie = [faturamento_por_mes.get(i, 0) for i in range(1, 13)]
        custo_serie = [custo_por_mes.get(i, 0) for i in range(1, 13)]

        # Volume de carga movimentada (toneladas) por mês
        volumes = (
            db.session.query(
                extract("month", Viagem.data).label("mes"),
                func.sum(Viagem.volume_tons).label("volume"),
            )
            .filter(extract("year", Viagem.data) == ano_atual)
            .group_by("mes")
            .all()
        )
        volume_por_mes = {int(v.mes): float(v.volume or 0) for v in volumes}
        volume_serie = [volume_por_mes.get(i, 0) for i in range(1, 13)]

        # Custo médio por KM (média geral)
        media_custo_km = db.session.query(
            func.avg(Viagem.custo_total / func.nullif(Viagem.distancia_km, 0))
        ).scalar()
        media_custo_km = round(float(media_custo_km), 2) if media_custo_km else 0

        # Contagem por status (para eventuais indicadores extras)
        status_contagem = dict(
            db.session.query(Viagem.status, func.count(Viagem.id))
            .group_by(Viagem.status)
            .all()
        )

        return jsonify(
            {
                "labels": labels,
                "faturamento": faturamento_serie,
                "custo_total": custo_serie,
                "volume_tons": volume_serie,
                "custo_medio_km": media_custo_km,
                "status_contagem": status_contagem,
            }
        )

    # ------------------------------------------------------------------
    # VIAGENS (lançamento operacional + listagem)
    # ------------------------------------------------------------------
    @app.route("/viagens")
    @login_required
    def listar_viagens():
        pagina = request.args.get("pagina", 1, type=int)
        paginacao = (
            Viagem.query.order_by(Viagem.data.desc(), Viagem.id.desc())
            .paginate(page=pagina, per_page=10, error_out=False)
        )
        return render_template("viagens_lista.html", paginacao=paginacao)

    @app.route("/viagens/nova", methods=["GET", "POST"])
    @login_required
    def nova_viagem():
        motoristas = Motorista.query.filter_by(ativo=True).all()
        veiculos = Veiculo.query.filter_by(ativo=True).all()

        if request.method == "POST":
            erro = _validar_e_salvar_viagem(request.form)
            if erro:
                flash(erro, "danger")
            else:
                flash("Viagem lançada com sucesso!", "success")
                return redirect(url_for("listar_viagens"))

        return render_template(
            "viagem_form.html", motoristas=motoristas, veiculos=veiculos, viagem=None
        )

    @app.route("/viagens/<int:viagem_id>/editar", methods=["GET", "POST"])
    @login_required
    def editar_viagem(viagem_id):
        viagem = Viagem.query.get_or_404(viagem_id)
        motoristas = Motorista.query.filter_by(ativo=True).all()
        veiculos = Veiculo.query.filter_by(ativo=True).all()

        if request.method == "POST":
            erro = _validar_e_salvar_viagem(request.form, viagem=viagem)
            if erro:
                flash(erro, "danger")
            else:
                flash("Viagem atualizada com sucesso!", "success")
                return redirect(url_for("listar_viagens"))

        return render_template(
            "viagem_form.html", motoristas=motoristas, veiculos=veiculos, viagem=viagem
        )

    @app.route("/viagens/<int:viagem_id>/excluir", methods=["POST"])
    @login_required
    @perfil_requerido("gerente")
    def excluir_viagem(viagem_id):
        viagem = Viagem.query.get_or_404(viagem_id)
        db.session.delete(viagem)
        db.session.commit()
        flash("Viagem excluída.", "success")
        return redirect(url_for("listar_viagens"))

    # ------------------------------------------------------------------
    # CADASTROS AUXILIARES (motoristas e veículos) - CRUD simples
    # ------------------------------------------------------------------
    @app.route("/motoristas", methods=["GET", "POST"])
    @login_required
    def motoristas():
        if request.method == "POST":
            nome = request.form.get("nome", "").strip()
            if not nome:
                flash("Informe o nome do motorista.", "danger")
            else:
                db.session.add(
                    Motorista(
                        nome=nome,
                        cnh=request.form.get("cnh", "").strip(),
                        telefone=request.form.get("telefone", "").strip(),
                    )
                )
                db.session.commit()
                flash("Motorista cadastrado.", "success")
            return redirect(url_for("motoristas"))

        lista = Motorista.query.order_by(Motorista.nome).all()
        return render_template("motoristas.html", motoristas=lista)

    @app.route("/veiculos", methods=["GET", "POST"])
    @login_required
    def veiculos():
        if request.method == "POST":
            placa = request.form.get("placa", "").strip().upper()
            if not placa:
                flash("Informe a placa do veículo.", "danger")
            else:
                db.session.add(
                    Veiculo(
                        placa=placa,
                        modelo=request.form.get("modelo", "").strip(),
                        capacidade_kg=_para_float(request.form.get("capacidade_kg")),
                    )
                )
                db.session.commit()
                flash("Veículo cadastrado.", "success")
            return redirect(url_for("veiculos"))

        lista = Veiculo.query.order_by(Veiculo.placa).all()
        return render_template("veiculos.html", veiculos=lista)


# ----------------------------------------------------------------------
# Funções auxiliares de validação (o "cérebro" que valida antes de salvar)
# ----------------------------------------------------------------------
def _para_float(valor, padrao=0.0):
    try:
        return float(str(valor).replace(",", ".")) if valor not in (None, "") else padrao
    except (ValueError, TypeError):
        return padrao


def _para_decimal(valor, padrao="0"):
    try:
        return Decimal(str(valor).replace(",", ".")) if valor not in (None, "") else Decimal(padrao)
    except (InvalidOperation, TypeError):
        return Decimal(padrao)


def _validar_e_salvar_viagem(form, viagem=None):
    """Valida os dados vindos do formulário e persiste no banco.

    Retorna uma mensagem de erro (string) se algo estiver inválido,
    ou None se salvou com sucesso.
    """
    data_str = form.get("data", "").strip()
    veiculo_id = form.get("veiculo_id")
    motorista_id = form.get("motorista_id")
    origem = form.get("origem", "").strip()
    destino = form.get("destino", "").strip()
    status = form.get("status", "em_transito")

    # --- validações obrigatórias ---
    if not data_str:
        return "Informe a data da viagem."
    if not veiculo_id:
        return "Selecione o veículo."
    if not motorista_id:
        return "Selecione o motorista."
    if not origem or not destino:
        return "Informe origem e destino."

    try:
        data_viagem = datetime.strptime(data_str, "%Y-%m-%d").date()
    except ValueError:
        return "Data inválida."

    distancia_km = _para_float(form.get("distancia_km"))
    volume_tons = _para_float(form.get("volume_tons"))
    faturamento = _para_decimal(form.get("faturamento"))
    custo_total = _para_decimal(form.get("custo_total"))

    if distancia_km < 0 or volume_tons < 0:
        return "Distância e volume não podem ser negativos."
    if faturamento < 0 or custo_total < 0:
        return "Faturamento e custo não podem ser negativos."

    if viagem is None:
        viagem = Viagem()
        viagem.criado_por_id = current_user.id if current_user.is_authenticated else None
        db.session.add(viagem)

    viagem.data = data_viagem
    viagem.veiculo_id = int(veiculo_id)
    viagem.motorista_id = int(motorista_id)
    viagem.origem = origem
    viagem.destino = destino
    viagem.distancia_km = distancia_km
    viagem.volume_tons = volume_tons
    viagem.faturamento = faturamento
    viagem.custo_total = custo_total
    viagem.status = status
    viagem.observacoes = form.get("observacoes", "").strip()

    db.session.commit()
    return None


app = criar_app()

if __name__ == "__main__":
    # debug=True facilita o desenvolvimento (recarrega sozinho e mostra erros).
    # Em produção, troque para debug=False e use um servidor como gunicorn/waitress.
    app.run(debug=True, port=5000)
