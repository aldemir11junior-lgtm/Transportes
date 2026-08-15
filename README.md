# Painel Operacional — Transportadora XYZ

Esqueleto funcional de sistema interno (sem área pública) para:
- **Operacional**: lançar viagens (origem, destino, veículo, motorista, faturamento, custo, status).
- **Gerente**: acompanhar o dashboard consolidado (faturamento x custo, volume de carga, custo médio por KM).

## Arquitetura

```
Transportes/
├── app.py              # Back-end: rotas, validação, API do dashboard (o "cérebro")
├── models.py            # Banco de dados: tabelas Usuario, Motorista, Veiculo, Viagem
├── extensions.py        # Instâncias do SQLAlchemy e do Flask-Login
├── config.py             # Configurações (lê variáveis de ambiente)
├── requirements.txt
├── .env.example          # copie para .env e ajuste
├── templates/            # Front-end (HTML + Jinja2)
│   ├── base.html
│   ├── login.html
│   ├── dashboard.html
│   ├── viagens_lista.html
│   ├── viagem_form.html      <- tela onde o operacional digita os dados
│   ├── motoristas.html
│   └── veiculos.html
└── static/
    ├── css/style.css     # visual escuro (baseado no print enviado)
    └── js/dashboard.js   # consome /api/dashboard-data e desenha os gráficos (Chart.js)
```

**Front-end**: HTML + CSS + JavaScript puro (sem framework), com Chart.js via CDN só para os gráficos.
**Back-end**: Flask (Python) — recebe os formulários, valida os dados (`_validar_e_salvar_viagem` em `app.py`) e grava no banco via SQLAlchemy.
**Banco de dados**: SQLAlchemy ORM. Por padrão usa **SQLite** (arquivo `transportes.db`, zero configuração) — mas já está pronto para apontar para **PostgreSQL** ou **MySQL** só trocando uma variável de ambiente (veja abaixo).

## Como rodar (Windows/VSCode)

1. Abra a pasta `Transportes` no VSCode.
2. Abra o terminal integrado (Ctrl+`) e crie o ambiente virtual:
   ```
   python -m venv venv
   venv\Scripts\activate        # Windows
   # source venv/bin/activate   # Mac/Linux
   ```
3. Instale as dependências:
   ```
   pip install -r requirements.txt
   ```
4. (Opcional) copie `.env.example` para `.env` e ajuste `SECRET_KEY`.
5. Rode a aplicação:
   ```
   python app.py
   ```
6. Acesse no navegador: **http://localhost:5000**

Na primeira execução o sistema cria automaticamente o banco (`transportes.db`) e dois usuários de teste:

| Perfil       | E-mail                | Senha  |
|--------------|------------------------|--------|
| Gerente      | gerente@xyz.com        | 123456 |
| Operacional  | operacional@xyz.com    | 123456 |

> ⚠️ Troque essas senhas antes de usar em produção — isso é só para você testar o sistema imediatamente.

## Migrando de SQLite para PostgreSQL

1. Instale o PostgreSQL e crie um banco, ex: `transportes`.
2. No `requirements.txt`, descomente a linha `psycopg2-binary`.
3. Rode `pip install -r requirements.txt` novamente.
4. No `.env`, defina:
   ```
   DATABASE_URL=postgresql+psycopg2://usuario:senha@localhost:5432/transportes
   ```
5. Rode `python app.py` normalmente — as tabelas são criadas automaticamente (`db.create_all()`).

Para MySQL o processo é o mesmo, usando `PyMySQL` e a URL `mysql+pymysql://...`.

## O que já está pronto (esqueleto funcional)

- ✅ Login/logout (sem área pública — tudo exige autenticação)
- ✅ Dois perfis: `operacional` e `gerente` (gerente pode excluir viagens)
- ✅ CRUD de Viagens (criar, listar com paginação, editar, excluir)
- ✅ Cadastro simples de Motoristas e Veículos
- ✅ Validação de dados no back-end antes de salvar (`app.py`)
- ✅ Dashboard com gráficos dinâmicos (Faturamento x Custo, Volume por mês, Custo médio/KM)
- ✅ API JSON (`/api/dashboard-data`) que alimenta os gráficos — pode ser reaproveitada por outros front-ends

## Próximos passos sugeridos

- Trocar o mapa "estático" por um mapa real (ex: Google Maps API / Leaflet) se quiser reproduzir o card "Mapa de Viagens Ativas" do print.
- Adicionar exportação (CSV/Excel/PDF) na listagem de viagens.
- Adicionar filtros por período/status/motorista no dashboard.
- Trocar `debug=True` por um servidor de produção (gunicorn, waitress) e usar HTTPS.
- Adicionar testes automatizados (pytest) para as validações do back-end.
