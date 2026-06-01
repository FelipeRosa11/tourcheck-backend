# MEDIÇÕES DO SLA - TOURCHECK

**Data da medição:** 01/06/2026
**Responsável pelas medições:** Grupo TourCheck - PI2

---

## Serviço 1: Cadastro de Usuários (`POST /auth/cadastro`)

- **Tipo de operações:** Inserção (Escrita)
- **Arquivos envolvidos:**
  - [app/models/usuario.py](https://github.com/FelipeRosa11/tourcheck-backend/blob/main/app/models/usuario.py)
  - [app/routers/auth.py](https://github.com/FelipeRosa11/tourcheck-backend/blob/main/app/routers/auth.py)
- **Arquivos com o código fonte de medição do SLA:** [tests_carga/cadastro_stress.js](https://github.com/FelipeRosa11/tourcheck-backend/blob/main/tests_carga/cadastro_stress.js)
- **Data da medição:** 01/06/2026
- **Descrição das configurações:** Ambiente local Windows 11, rodando ambiente virtual Python (venv), servidor FastAPI via Uvicorn na porta 8000 e banco de dados MongoDB ativo localmente como serviço na porta 27017.

<img width="1497" height="564" alt="image" src="https://github.com/user-attachments/assets/4dbac263-f876-478c-a873-d7ddc379d329" />

### Testes de carga (SLA)

- **Concorrência máxima alcançada:** 50 usuários simultâneos (VUs).
- **Vazão média:** 10.65 requisições por segundo (Total de 543 requisições processadas).
- **Latência média (Tempo de resposta):** 1.27 segundos (1270ms), com pico máximo de 2.77 segundos.
- **Taxa de Sucesso HTTP:** 99.82% das requisições completadas com sucesso (Apenas 1 falha em 543).
- **Link da medição oficial:** https://feliperosamartins1111.grafana.net/a/k6-app/runs/7655028

### LEVANTAMENTO DE HIPÓTESES dos potenciais gargalos:

1. **Saturação de CPU por Criptografia Síncrona (Bcrypt):** O teste revelou que a taxa de erro HTTP é quase nula (0.18%), validando a estabilidade da rota. Contudo, 75% das requisições violaram o SLA de tempo de resposta esperado (< 500ms), elevando a latência média para 1.27s. A principal hipótese do gargalo é o alto custo computacional do algoritmo Bcrypt para encriptar as senhas recebidas. Por ser uma operação intensiva de CPU executada de forma concorrente por 50 VUs, o processador atinge o topo de consumo.
2. **Bloqueio do Event Loop do FastAPI:** Como o FastAPI gerencia requisições assíncronas em uma única thread principal, se a biblioteca de hash utilizada não delegar o cálculo pesado do Bcrypt para um pool de threads separado (ex: rodar em uma thread do `anyio`), ela bloqueia o Event Loop por milissegundos. Sob alta concorrência, esse microbloqueio acumula em cascata, gerando a rampa de crescimento observada na latência.

---

## Serviço 2: Listagem Pública de Pontos Turísticos (`GET /pontos`)

- **Tipo de operações:** Leitura
- **Arquivos envolvidos:**
  - [app/models/ponto.py](https://github.com/FelipeRosa11/tourcheck-backend/blob/main/app/models/ponto.py)
  - [app/routers/pontos.py](https://github.com/FelipeRosa11/tourcheck-backend/blob/main/app/routers/pontos.py)
- **Arquivos com o código fonte de medição do SLA:** [tests_carga/busca_pontos_stress.js](https://github.com/FelipeRosa11/tourcheck-backend/blob/main/tests_carga/busca_pontos_stress.js)
- **Data da medição:** 01/06/2026
- **Descrição das configurações:** Mesma infraestrutura local descrita no Serviço 1.

### Testes de carga (SLA)

- **Concorrência máxima alcançada:** 100 usuários simultâneos (VUs).
- **Vazão média:** 77.15 requisições por segundo (Totalizando 3886 requisições completas).
- **Latência média (Tempo de resposta):** 121.4 milissegundos, com pico máximo de 1.9 segundos sob estresse máximo de concorrência.
- **Taxa de Sucesso HTTP:** 100.00% de sucesso estável (0 falhas em 3886 requisições).
- **Link da medição oficial:** https://feliperosamartins1111.grafana.net/a/k6-app/runs/7655058

### LEVANTAMENTO DE HIPÓTESES dos potenciais gargalos:

1. **Volume de Transferência de Rede e Tamanho do Payload (I/O Bound):** O teste de leitura trafegou massivos 62 MB de dados em apenas 50 segundos. A latência média se manteve excelente (121.4ms), porém o pico máximo atingiu 1.9s. A principal hipótese de gargalo é o tamanho do payload JSON retornado pela coleção do MongoDB. À medida que o número de pontos turísticos cadastrados cresce (carregando listas de imagens, coordenadas e descrições), a serialização de grandes vetores de dados consome muita largura de banda de rede e processamento do framework.
2. **Ausência de Paginação de Dados:** Como a rota faz um dump bruto de leitura da coleção (`GET /pontos`), o banco de dados processa e entrega todo o conjunto de dados em cada requisição. Sob concorrência extrema de 100 usuários virtuais, isso gera gargalo de processamento na serialização do Pydantic/FastAPI, o que justifica a falha de 18% no SLA de tempo ideal de resposta (< 200ms).
