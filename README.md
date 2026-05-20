tourcheck-backend/
│
├── app/
│   ├── __init__.py
│   ├── main.py            # Inicializa o FastAPI e inclui as rotas (routers)
│   ├── database.py        # Configuração da conexão com o MySQL (SQLAlchemy)
│   │
│   ├── models/            # Classes que espelham as tabelas do banco de dados
│   │   ├── __init__.py
│   │   ├── usuario.py     # Modelo da tabela 'usuario' [cite: 376]
│   │   └── ponto.py       # Modelo da tabela 'ponto_turistico' [cite: 395]
│   │
│   ├── schemas/           # Validações de dados de entrada/saída (Pydantic)
│   │   ├── __init__.py
│   │   ├── usuario.py     # Regras de cadastro/login (ex: e-mail válido) [cite: 380]
│   │   └── ponto.py       # Regras para novos pontos
│   │
│   └── routers/           # Os endpoints da API divididos por contexto
│       ├── __init__.py
│       ├── auth.py        # Rotas de Cadastro e Login (UC001, UC002) [cite: 218, 219]
│       └── pontos.py      # Rotas de Busca e Cadastro de Pontos (UC003, UC008) [cite: 220, 234]
│
├── .gitignore             # Para não enviar o 'venv' e ficheiros temporários para o GitHub
├── README.md              # Descrição do projeto e instruções de como rodar
└── requirements.txt       # Lista de dependências (fastapi, sqlalchemy, etc.)


Com o MongoDB e o FastAPI definidos no backend, o desenvolvimento fica extremamente ágil. 
Como a modelagem NoSQL que vocês estruturaram permite salvar dados complexos (como endereços e telefones embebidos no mesmo documento), o trabalho dos dois desenvolvedores de backend vai render muito mais.  
Para uma equipa de 3 pessoas trabalhando em 3 Sprints, a divisão ideal de tarefas separa os contextos de forma a evitar que um dependa do outro o tempo todo.

Aqui está a linha de desenvolvimento distribuída por papel:

Sprint 1: 
Fundação, Acesso e AutenticaçãoO objetivo desta sprint é colocar o sistema no ar e garantir que um utilizador consiga se registar e logar, seguindo o Diagrama de Atividades de Autenticação que vocês desenharam.  
💻 Backend 1 (Infraestrutura e Cadastro):Configurar a conexão com o MongoDB usando o Beanie/Motor no arquivo app/database.py.
Criar o modelo de dados Usuario com a lista de telefones embebida, exatamente como na coleção definida no documento.  
Criar o endpoint POST /usuarios/cadastro (RF001 / UC001). Aplicar criptografia de senha com bcrypt.  
💻 Backend 2 (Autenticação e Carga Inicial):Criar o endpoint de login POST /usuarios/login (RF002 / UC002) gerando tokens JWT seguros para a sessão.  
Criar um script Python rápido de Seed para injetar a carga inicial de dados no MongoDB (inserir o utilizador Admin, o Cristo Redentor, Pão de Açúcar, as imagens e categorias oficiais).  
🎨 Frontend:Criar a estrutura base do site com HTML5 e Tailwind CSS.Desenvolver a interface da Tela de Cadastro e da Tela de Login, criando os formulários que vão enviar os dados para as rotas criadas pelos desenvolvedores de backend.  

Sprint 2: 
Core do Sistema (Catálogo, Busca e Filtros)Nesta etapa, o utilizador já logado conseguirá interagir com os pontos turísticos do Rio de Janeiro.  
💻 Backend 1 (Consultas e Filtros):Criar o endpoint GET /pontos-turisticos que permite listar todos os locais.Implementar os parâmetros de busca e filtros nessa rota: busca por Nome (RF003 / UC003) e filtro por Categoria (RF004 / UC004). 
No MongoDB, utilize os índices de texto criados na coleção para tornar a busca ultra rápida, cumprindo o requisito de tempo de resposta inferior a 3 segundos.  
💻 Backend 2 (Detalhes e Inclusão de Pontos):Criar o endpoint GET /pontos-turisticos/{id} para trazer os detalhes completos de um local específico, incluindo as imagens oficiais associadas (RF005 / UC006).  
Criar a rota POST /pontos-turisticos para que utilizadores cadastrados possam sugerir novos locais (RF009 / UC008). O ponto deve ser salvo com o status inicial "pendente".  
🎨 Frontend:Desenvolver a Tela Principal/Dashboard, que exibe a barra de pesquisa e os cards dos pontos turísticos retornados pela API.  
Desenvolver a Tela de Detalhes do Ponto Turístico, exibindo as fotos, descrição do local e o endereço detalhado.  Criar o formulário da Tela de Sugestão/Cadastro de Novo Ponto.  

Sprint 3: 
Interações, Painel de Moderação e Testes de CargaFoco nas regras de engajamento social, controle do administrador e validação de performance do sistema para a vossa apresentação de 15 minutos.
💻 Backend 1 (Avaliações e Favoritos):Criar a rota POST /pontos-turisticos/{id}/avaliar (RF007, RF008 / UC011). 
Regra Crítica: Bloquear a rota caso a nota não esteja entre 1 e 5 (RN002) ou se o utilizador já tiver avaliado aquele ponto específico (RN003, utilizando o índice único que vocês planearam).  
Criar as rotas de favoritar e desfavoritar locais (RF010 / UC007).  
💻 Backend 2 (Moderação Administrativa e Testes):Criar rotas protegidas (apenas para o tipo "admin") para aprovar/rejeitar novos pontos turísticos sugeridos (UC012) e apagar comentários ofensivos (RF011 / UC014).  
Escrever o script de testes de estresse usando o Locust em Python. 
Rodar os testes simulando mais de 100 e 200 utilizadores simultâneos para recolher as métricas e preencher as tabelas de resultados que faltam no relatório do projeto.  
🎨 Frontend:Implementar a secção de comentários e o botão de "Estrela/Favorito" dentro da tela de detalhes do ponto turístico.  
Desenvolver a Tela da Área Administrativa (restrita para utilizadores Admin), exibindo a lista de pontos turísticos "pendentes" para o administrador clicar em "Aprovar" ou "Rejeitar", além de permitir a remoção de comentários.  


Dica de ouro para a integração do grupo:Assim que os desenvolvedores de Backend terminarem de criar uma rota, eles não precisam de esperar o Frontend ficar pronto para testar. 
Eles podem testar tudo diretamente pela página do Swagger (http://127.0.0.1:8000/docs).
O desenvolvedor de Frontend pode usar ferramentas como o Fetch API do JavaScript para disparar as requisições para o endereço local do FastAPI assim que as rotas forem validadas no Swagger.
