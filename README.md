# SGPD — Sistema de Gestão de Processos Digitais (MVP)

Aplicação web monolítica em **Django 5.1** para abertura, acompanhamento, tramitação e avaliação de processos digitais, com suporte a **PostgreSQL 16** (ou SQLite em desenvolvimento local), validações no servidor (RNF02), controles de segurança OWASP e testes automatizados com **Pytest**.

## Requisitos Funcionais Cobertos

- **RF01 / RF02 (`inicio.html`)**: Abertura de solicitação com geração automática de protocolo (`SGPD-AAAA-XXXXXX`) e consulta rápida por protocolo.
- **RF03 (`painel.html`)**: Painel de acompanhamento com indicadores e filtros por status, categoria, prioridade e busca textual.
- **RF02 / RF04 (`protocolo_detalhe.html`)**: Detalhamento do processo, histórico cronológico de tramitação, movimentação de status e avaliação de conclusão (1 a 5).

## Como Executar Localmente

1. **Crie e ative o ambiente virtual:**
   ```bash
   python -m venv .venv
   # Linux/macOS:
   source .venv/bin/activate
   # Windows (PowerShell):
   .venv\Scripts\Activate.ps1
   ```

2. **Instale as dependências:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure as variáveis de ambiente:**
   ```bash
   cp .env.example .env
   ```
   Para rodar rapidamente sem PostgreSQL instalado, defina `DB_ENGINE=sqlite3` no `.env` (ou mantenha `DB_ENGINE=postgresql` com as credenciais do PostgreSQL 16).

4. **Gere as migrações e inicialize o banco de dados:**
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   python manage.py createsuperuser
   ```

5. **Inicie o servidor:**
   ```bash
   python manage.py runserver
   ```

## Testes Automatizados

Execute a suíte de testes unitários e de integração com:
```bash
pytest
```
