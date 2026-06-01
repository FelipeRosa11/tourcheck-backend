# 🌍 TourCheck - Backend

Implementação do backend do projeto **TourCheck**, um sistema completo para gestão e consulta de pontos turísticos.

## 👥 Integrantes do Grupo (PI2)
* Caio Miranda Moreira da Fonseca
* Felipe Rosa Martins
* Gabriel Nunes Amorim

---

## 📈 Testes de Performance e SLA (Fase E)
O relatório detalhado contendo os gráficos de evolução, análise de concorrência, vazão, latência e o levantamento de hipóteses de gargalos do sistema está disponível diretamente no link abaixo:
👉 **[Aceder ao Relatório de Medições de SLA (SLA_MEDICOES.md)](SLA_MEDICOES.md)**

---

## 🛠️ Como Executar o Projeto Localmente

### 1. Instalar as Dependências
Garanta que o seu ambiente virtual (`venv`) está ativo e instale os pacotes necessários:
```bash
pip install -r requirements.txt
2. Configuração do Banco de Dados
O banco de dados padrão ativo agora é o MongoDB. Configure as variáveis de ambiente necessárias:

Snippet de código
DB_BACKEND=mongodb
MONGODB_URL=mongodb://localhost:27017
MONGODB_DATABASE=tourcheck
Nota: O suporte ao SQLAlchemy continua disponível no sistema para PostgreSQL/SQLite. Caso queira alternar para PostgreSQL, utilize:

Snippet de código
DB_BACKEND=postgresql
DATABASE_URL=postgresql+psycopg://usuario:senha@localhost:5432/tourcheck
3. Iniciar o Servidor
Execute a API FastAPI utilizando o Uvicorn:

Bash
uvicorn app.main:app --reload
A API estará disponível para testes em http://127.0.0.1:8000 e a documentação interativa (Swagger) em http://127.0.0.1:8000/docs.
