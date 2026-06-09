# TourCheck - Backend

Backend do projeto **TourCheck**, desenvolvido com FastAPI e MongoDB para cadastro, consulta, avaliacao e gestao de pontos turisticos.

## Integrantes

- Caio Miranda Moreira da Fonseca
- Felipe Rosa Martins
- Gabriel Nunes Amorim

## Relatorio de Performance e SLA

A documentacao tecnica da Fase E-2, com a comparacao entre a Medicao 1 de 01/06/2026 e a Medicao 2 de 08/06/2026, esta em:

**[SLA_MEDICOES.md](SLA_MEDICOES.md)**

O relatorio inclui os servicos medidos, gargalos encontrados, alteracoes de codigo, estrategia de carga em degraus, graficos comparativos e campos para preenchimento dos resultados finais do k6/Grafana Cloud.

## Execucao Local

### 1. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 2. Configurar MongoDB

```env
DB_BACKEND=mongodb
MONGODB_URL=mongodb://localhost:27017
MONGODB_DATABASE=tourcheck
```

### 3. Iniciar a API

```bash
uvicorn app.main:app --reload
```

A API ficara disponivel em `http://127.0.0.1:8000` e a documentacao interativa em `http://127.0.0.1:8000/docs`.

## Testes de Carga

Os scripts k6 usados nas medicoes estao em:

- `tests_carga/cadastro_stress.js`
- `tests_carga/busca_pontos_stress.js`

Depois de executar os testes finais da Medicao 2, atualize os campos `PENDENTE` em `SLA_MEDICOES.md` com os valores exibidos pelo k6 e os links oficiais do Grafana Cloud.
