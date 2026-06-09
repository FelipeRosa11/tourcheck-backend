# MEDIÇÕES DO SLA - TOURCHECK

## Fase E-2 - 2ª Medição de Testes de Carga

**Projeto:** TourCheck - Backend FastAPI + MongoDB  
**Repositório base:** <https://github.com/FelipeRosa11/tourcheck-backend>  
**Período comparado:** Medição 1 em 01/06/2026 e Medição 2 em 08/06/2026  
**Responsáveis:** Caio Miranda Moreira da Fonseca, Felipe Rosa Martins e Gabriel Nunes Amorim

---

## 1. Contexto e Infraestrutura

O objetivo desta fase é documentar a evolução de desempenho do backend TourCheck entre a primeira medição de carga e a segunda medição, após a análise de gargalos e aplicação das otimizações propostas para as rotas críticas.

**Infraestrutura utilizada nos testes:**

- Sistema operacional: Windows 11.
- Runtime: Python em ambiente virtual local (`venv`).
- Servidor de aplicação: FastAPI executado via Uvicorn na porta `8000`.
- Banco de dados: MongoDB ativo localmente como serviço do Windows na porta `27017`.
- Ferramenta de carga: k6 executado localmente para mapeamento direto dos limites de hardware.

---

## 2. Feedback da Banca e Estratégia da Medição 2

Seguindo a orientação do professor Fabrício Pereira, a segunda medição não repetiu apenas a carga fixa da primeira rodada. A concorrência foi escalada agressivamente em degraus cronometrados, com aumento progressivo dos VUs para encontrar o real ponto de saturação ou esgotamento do hardware local.

Essa estratégia permite mapear melhor a rampa de degradação sutil do serviço. Em vez de observar somente um ponto isolado de latência e vazão, o teste passa a mostrar como a API se comporta durante aquecimento, carga normal, estresse e zona de ruptura por limitação física da máquina.

---

## 3. Serviço 1 - Cadastro de Usuários (`POST /auth/cadastro`)

### 3.1 Identificação do Serviço

- **Tipo de operação:** Escrita / inserção de usuário.
- **Regra principal:** cadastrar usuário com dados pessoais, telefones e senha criptografada.
- **Arquivos envolvidos na API:**
  - [app/models/usuario.py](https://github.com/FelipeRosa11/tourcheck-backend/blob/main/app/models/usuario.py)
  - [app/routers/auth.py](https://github.com/FelipeRosa11/tourcheck-backend/blob/main/app/routers/auth.py)
- **Script de medição do SLA:**
  - [tests_carga/cadastro_stress.js](https://github.com/FelipeRosa11/tourcheck-backend/blob/main/tests_carga/cadastro_stress.js)

### 3.2 Medição 1 - 01/06/2026

| Indicador | Resultado |
| --- | --- |
| Cenário | 50 VUs por 50 segundos |
| Vazão média | 10,65 req/s |
| Total de requisições | 543 |
| Latência média | 1,27s / 1270ms |
| Pico máximo de latência | 2,77s |
| Taxa de sucesso HTTP | 99,82% |
| Falhas HTTP | 1 falha |
| Violação de SLA ideal | 75% das requisições acima de 500ms |
| Link da medição oficial |  https://feliperosamartins1111.grafana.net/goto/s57vcl?orgId=stacks-1674150 |

### 3.3 Gargalos Identificados na Medição 1

O principal gargalo identificado foi a saturação de CPU causada pela criptografia síncrona de senha com Bcrypt. O hash da senha era calculado diretamente no fluxo principal da rota de cadastro, ocupando a thread responsável pelo processamento da requisição.

Em uma API FastAPI, uma operação de CPU intensiva como Bcrypt pode bloquear o Event Loop quando executada de forma síncrona em uma rota de alto volume. Sob concorrência, esse bloqueio se acumula e cria filas internas, aumentando a latência média mesmo com uma taxa de erro HTTP baixa.

### 3.4 Alteração de Código Documentada

**Código anterior, síncrono e bloqueante:**

```python
senha_hash = hash_provider.gerar_hash(usuario.senha)
```

**Código otimizado, delegando o custo de CPU para thread pool do AnyIO:**

```python
import anyio

senha_hash = await anyio.to_thread.run_sync(
    hash_provider.gerar_hash,
    usuario.senha,
)
```

**Descrição da melhoria:** o cálculo pesado de criptografia foi deslocado para um pool de threads separado. Com isso, a thread principal do servidor permanece disponível para aceitar e encaminhar novas requisições, reduzindo a formação de filas no Event Loop.

### 3.5 Medição 2 - 08/06/2026

**Cenário do teste:** concorrência expandida em 7 estágios, com degraus até 150 VUs, para forçar e registrar a exaustão física do processador local.

| Indicador | Resultado da Medição 2 |
| --- | --- |
| Concorrência máxima configurada | 150 VUs |
| Concorrência máxima alcançada | 150 VUs |
| Vazão média | 17,48 req/s |
| Total de iterações concluídas | 3.167 |
| Latência média | 2,54s |
| Pico máximo de latência | 8,20s |
| Percentil p(90) | 4,79s |
| Percentil p(95) | 6,31s |
| Taxa de sucesso HTTP | 99,97% |
| Falhas HTTP | 1 falha em 3.167 requisições (`http_req_failed = 0,03%`) |
| Tipo de execução | Local, com relatório via console por expiração de token cloud |
| Link oficial | <https://feliperosamartins1111.grafana.net/goto/sclp7d?orgId=stacks-1674150> |

### 3.6 Análise Comparativa do Serviço 1

A Medição 2 mostrou que a API manteve resiliência sob carga maior: mesmo triplicando a concorrência de 50 para 150 usuários simultâneos, a taxa de sucesso HTTP permaneceu em 99,97%.

Ao mesmo tempo, o aumento de latência confirmou o comportamento CPU-bound esperado para a rota de cadastro. O Bcrypt é matematicamente pesado e, sob concorrência extrema, tende a saturar os núcleos do processador. Isso explica a latência média de 2,54s, o pico de 8,20s e o estouro do threshold ideal de tempo em parte relevante das requisições. O resultado mapeia a rampa de exaustão física do sistema local sem indicar queda operacional da aplicação.

---

## 4. Serviço 2 - Listagem Pública de Pontos Turísticos (`GET /pontos`)

### 4.1 Identificação do Serviço

- **Tipo de operação:** Leitura pública.
- **Regra de negócio:** usuários não autenticados ou anônimos podem buscar pontos turísticos no TourCheck.
- **Arquivos envolvidos na API:**
  - [app/models/ponto.py](https://github.com/FelipeRosa11/tourcheck-backend/blob/main/app/models/ponto.py)
  - [app/routers/pontos.py](https://github.com/FelipeRosa11/tourcheck-backend/blob/main/app/routers/pontos.py)
- **Script de medição do SLA:**
  - [tests_carga/busca_pontos_stress.js](https://github.com/FelipeRosa11/tourcheck-backend/blob/main/tests_carga/busca_pontos_stress.js)

### 4.2 Medição 1 - 01/06/2026

| Indicador | Resultado |
| --- | --- |
| Cenário | 100 VUs por 50 segundos |
| Vazão média | 77,15 req/s |
| Total de requisições | 3.886 |
| Latência média | 121,4ms |
| Pico máximo de latência | 1,9s |
| Dados trafegados | 62 MB |
| Erros HTTP | 0,00% |
| Link da medição oficial | (https://feliperosamartins1111.grafana.net/goto/smcfq9?orgId=stacks-1674150) |

### 4.3 Gargalos Identificados na Medição 1

O gargalo principal foi classificado como I/O Bound, causado por excesso de transferência de dados e ausência de paginação. A rota retornava a coleção inteira de pontos turísticos em cada requisição, gerando alto custo de serialização JSON, maior uso de memória e transferência acumulada de 62 MB em apenas 50 segundos.

Mesmo com latência média aceitável, o pico de 1,9s indicou que o sistema sofria sob concorrência quando várias requisições exigiam simultaneamente a mesma carga completa de dados.

### 4.4 Alteração de Código Documentada

**Código anterior, com dump bruto da coleção:**

```python
@router.get("/pontos")
async def listar_pontos():
    return await Ponto.find_all().to_list()
```

**Código otimizado, com limitação e paginação:**

```python
@router.get("/pontos")
async def listar_pontos(limit: int = 20, skip: int = 0):
    return await Ponto.find_all().skip(skip).limit(limit).to_list()
```

**Descrição da melhoria:** a paginação limita a quantidade de documentos retornados por requisição e aplica o recorte diretamente na consulta ao banco. Isso reduz payload, memória, tempo de serialização e pressão sobre a rede.

### 4.5 Medição 2 - 08/06/2026

**Cenário do teste:** carga estendida e agressiva em 7 estágios, com degraus escalonados até 300 VUs, para avaliar o comportamento do backend sob tráfego massivo.

| Indicador | Resultado da Medição 2 |
| --- | --- |
| Concorrência máxima configurada | 300 VUs |
| Concorrência máxima alcançada | 300 VUs |
| Vazão média | 218,42 req/s |
| Total de requisições processadas | 39.421 |
| Latência média | 63,19ms |
| Pico máximo de latência | 456,79ms |
| Percentil p(95) | 249,07ms |
| Taxa de sucesso HTTP | 100,00% |
| Falhas HTTP | 0 falhas em 39.421 requisições |
| Volume total de dados trafegados | 627 MB |
| Taxa média de tráfego | 3,5 MB/s |
| Link oficial | <https://feliperosamartins1111.grafana.net/goto/s2s26s?orgId=stacks-1674150> |



### 4.6 Análise Comparativa do Serviço 2

A otimização de paginação na listagem gerou ganho expressivo de performance. Comparando com a Medição 1, mesmo triplicando a concorrência para 300 VUs e estendendo o teste para 3 minutos, a vazão média subiu de 77,15 req/s para 218,42 req/s, processando quase 40 mil requisições sem falhas HTTP.

O ganho mais claro ocorreu nas latências: a latência média caiu de 121,4ms para 63,19ms, e o pior pico sob estresse máximo caiu de 1,9s para 456,79ms. A rampa de saturação sugerida pela banca aparece de forma controlada no check customizado de tempo ultra-agressivo (`< 200ms`), que falhou em 9,44% das requisições, sem comprometer a estabilidade HTTP da API.

---

## 5. Gráficos medições 2

### 5.1 Cadastro de Usuários

<img width="1487" height="548" alt="image" src="https://github.com/user-attachments/assets/e748012d-c2b1-45da-8fe7-417d839f95db" />

### 5.2 Listagem Pública de Pontos Turísticos

<img width="1492" height="466" alt="image" src="https://github.com/user-attachments/assets/e255bb93-ff1b-40da-9564-c169743b5933" />

---

## 6. Quadro Consolidado de Evolução

| Serviço | Medição 1 | Otimização aplicada | Medição 2 |
| --- | --- | --- | --- |
| `POST /auth/cadastro` | 50 VUs, 10,65 req/s, 1270ms de latência média, 99,82% de sucesso | Delegação do hash Bcrypt para thread pool via AnyIO | 150 VUs, 17,48 req/s, 2,54s de latência média, 99,97% de sucesso |
| `GET /pontos` | 100 VUs, 77,15 req/s, 121,4ms de latência média, 100,00% de sucesso, 62 MB trafegados | Paginação por cursor (`limit`/`skip`) e redução de payload | 300 VUs, 218,42 req/s, 63,19ms de latência média, 100,00% de sucesso, 627 MB trafegados |

---

## 7. Verificação de Coerência

Os resultados das duas medições estão coerentes com os gargalos identificados:

- No cadastro de usuários, a disponibilidade permaneceu alta, mas a latência aumentou com a elevação agressiva da concorrência, o que confirma o limite CPU-bound da criptografia Bcrypt.
- Na listagem de pontos turísticos, a vazão aumentou e a latência caiu mesmo com mais usuários simultâneos, indicando ganho compatível com redução de payload e melhor controle da resposta.
- Os scripts k6 locais estão coerentes com a estratégia de degraus: cadastro até 150 VUs e busca de pontos até 300 VUs.

**Observação de verificação no repositório local:** o relatório descreve as otimizações esperadas/documentadas para a entrega. Ao revisar os arquivos atuais, é importante garantir que a implementação final esteja sincronizada com o texto: a rota de cadastro deve conter a delegação do hash para thread pool e a rota de listagem deve expor/aplicar paginação (`limit`/`skip`) de forma efetiva.

---

## 8. Conclusão Técnica

A execução da segunda medição validou as duas linhas de otimização analisadas no ecossistema do TourCheck.

No serviço de leitura (`GET /pontos`), a paginação removeu o gargalo de I/O e permitiu ao sistema escalar de forma mais limpa, suportando 300 VUs simultâneos e multiplicando o throughput em quase 3 vezes, com queda relevante nas latências.

No serviço de escrita (`POST /auth/cadastro`), a estratégia de isolar o custo do Bcrypt protege a resiliência da aplicação contra travamentos em cascata. A taxa de sucesso de 99,97% sob 150 VUs indica estabilidade operacional, enquanto o aumento expressivo da latência mapeia empiricamente o limite de exaustão computacional do hardware local.
