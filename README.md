Implementacao do projeto TourCheck, seguindo a documentacao criada pelo grupo Caio Miranda Moreira da Fonseca, Felipe Rosa Martins e Gabriel Nunes Amorim.

Instale as dependencias do `requirements.txt` e rode:

```bash
uvicorn app.main:app --reload
```

O banco ativo padrao agora e MongoDB:

```env
DB_BACKEND=mongodb
MONGODB_URL=mongodb://localhost:27017
MONGODB_DATABASE=tourcheck
```

O suporte SQLAlchemy continua no sistema para PostgreSQL/SQLite. Para usar PostgreSQL, configure:

```env
DB_BACKEND=postgresql
DATABASE_URL=postgresql+psycopg://usuario:senha@localhost:5432/tourcheck
```
