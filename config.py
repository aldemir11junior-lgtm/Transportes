import os
from dotenv import load_dotenv

# Carrega variáveis do arquivo .env (se existir)
load_dotenv()

BASE_DIR = os.path.abspath(os.path.dirname(__file__))


class Config:
    """Configurações centrais da aplicação.

    Toda credencial/segredo fica em variáveis de ambiente (.env),
    nunca direto no código.
    """

    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-key-nao-use-em-producao")

    # Por padrão usa um arquivo SQLite local (transportes.db).
    # Para usar PostgreSQL/MySQL, defina DATABASE_URL no .env (ou nas
    # variáveis de ambiente da hospedagem, como o Render).
    _url = os.environ.get(
        "DATABASE_URL", f"sqlite:///{os.path.join(BASE_DIR, 'transportes.db')}"
    )
    # O Render (e outros provedores) às vezes fornecem a URL no formato antigo
    # "postgres://", mas o SQLAlchemy exige "postgresql://". Corrigimos aqui.
    if _url.startswith("postgres://"):
        _url = _url.replace("postgres://", "postgresql://", 1)
    SQLALCHEMY_DATABASE_URI = _url
    SQLALCHEMY_TRACK_MODIFICATIONS = False
