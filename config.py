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
    # Para usar PostgreSQL/MySQL, defina DATABASE_URL no .env.
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL", f"sqlite:///{os.path.join(BASE_DIR, 'transportes.db')}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
