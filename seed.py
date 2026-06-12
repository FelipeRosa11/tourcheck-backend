# seed.py - roda uma vez para popular o banco com dados iniciais
import os
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database import SessionLocal, using_mongodb
from app.mongo_database import mongo_db
from app.models.avaliacao import Avaliacao
from app.models.ponto import PontoTuristico, StatusPonto
from app.models.usuario import TipoUsuario, Usuario
from app.security import gerar_hash_senha


PONTOS_DATA = [
    {
        "nome": "Cristo Redentor",
        "descricao": "Estatua iconica no topo do Corcovado, com vista panoramica do Rio de Janeiro.",
        "categoria": "Monumento",
        "cidade": "Rio de Janeiro",
        "bairro": "Santa Teresa",
        "endereco": "Parque Nacional da Tijuca - Alto da Boa Vista",
        "latitude": -22.9519,
        "longitude": -43.2105,
        "imagem_url": "https://upload.wikimedia.org/wikipedia/commons/4/4f/Christ_the_Redeemer_-_Cristo_Redentor.jpg",
    },
    {
        "nome": "Pao de Acucar",
        "descricao": "Morro com vista panoramica da Baia de Guanabara, acessivel por bondinho.",
        "categoria": "Natureza",
        "cidade": "Rio de Janeiro",
        "bairro": "Urca",
        "endereco": "Praca General Tiburcio, 68 - Urca",
        "latitude": -22.9489,
        "longitude": -43.1546,
        "imagem_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/f/fc/Vista_do_Morro_Dona_Marta.jpg/3840px-Vista_do_Morro_Dona_Marta.jpg",
    },
    {
        "nome": "Jardim Botanico",
        "descricao": "Area verde historica com palmeiras imperiais, estufas, lagos e colecoes botanicas.",
        "categoria": "Parque",
        "cidade": "Rio de Janeiro",
        "bairro": "Jardim Botanico",
        "endereco": "Rua Jardim Botanico, 1008",
        "latitude": -22.9676,
        "longitude": -43.2230,
        "imagem_url": "https://upload.wikimedia.org/wikipedia/commons/2/2b/Corcovado%2C_veduta_02_giardin_botanico.JPG",
    },
    {
        "nome": "Parque Lage",
        "descricao": "Parque publico aos pes do Corcovado, com casarão historico, trilhas e jardins.",
        "categoria": "Parque",
        "cidade": "Rio de Janeiro",
        "bairro": "Jardim Botanico",
        "endereco": "Rua Jardim Botanico, 414",
        "latitude": -22.9604,
        "longitude": -43.2116,
        "imagem_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/0/01/Parque_Lage%2C_Rio_de_Janeiro_Project_2345_01.jpg/3840px-Parque_Lage%2C_Rio_de_Janeiro_Project_2345_01.jpg",
    },
    {
        "nome": "Escadaria Selaron",
        "descricao": "Escadaria colorida revestida por azulejos de diversos paises, um marco da Lapa.",
        "categoria": "Arte urbana",
        "cidade": "Rio de Janeiro",
        "bairro": "Lapa",
        "endereco": "Rua Manuel Carneiro",
        "latitude": -22.9153,
        "longitude": -43.1796,
        "imagem_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/f/fc/Escadaria_Selar%C3%B3n_-_Rio_de_Janeiro_-_20240417062601.jpg/3840px-Escadaria_Selar%C3%B3n_-_Rio_de_Janeiro_-_20240417062601.jpg",
    },
    {
        "nome": "Arcos da Lapa",
        "descricao": "Aqueduto historico do seculo XVIII e um dos simbolos arquitetonicos do centro carioca.",
        "categoria": "Historico",
        "cidade": "Rio de Janeiro",
        "bairro": "Lapa",
        "endereco": "Praca Cardeal Camara",
        "latitude": -22.9122,
        "longitude": -43.1796,
        "imagem_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/a/a3/2018_Rio_de_Janeiro_-_Aqueduto_da_Carioca.jpg/3840px-2018_Rio_de_Janeiro_-_Aqueduto_da_Carioca.jpg",
    },
    {
        "nome": "Museu do Amanha",
        "descricao": "Museu de ciencias aplicadas com exposicoes sobre sustentabilidade e futuros possiveis.",
        "categoria": "Museu",
        "cidade": "Rio de Janeiro",
        "bairro": "Centro",
        "endereco": "Praca Maua, 1",
        "latitude": -22.8948,
        "longitude": -43.1790,
        "imagem_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/6/63/Museu_do_Amanh%C3%A3_rio.jpg/3840px-Museu_do_Amanh%C3%A3_rio.jpg",
    },
    {
        "nome": "AquaRio",
        "descricao": "Aquario marinho na zona portuaria, com tuneis de observacao e especies variadas.",
        "categoria": "Aquario",
        "cidade": "Rio de Janeiro",
        "bairro": "Gamboa",
        "endereco": "Praca Muhammad Ali",
        "latitude": -22.8952,
        "longitude": -43.1903,
        "imagem_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/8/8d/Pra%C3%A7a_Muhammad_Ali.jpg/3840px-Pra%C3%A7a_Muhammad_Ali.jpg",
    },
    {
        "nome": "Maracana",
        "descricao": "Estadio historico do futebol brasileiro, palco de grandes partidas e eventos.",
        "categoria": "Esporte",
        "cidade": "Rio de Janeiro",
        "bairro": "Maracana",
        "endereco": "Avenida Presidente Castelo Branco",
        "latitude": -22.9122,
        "longitude": -43.2302,
        "imagem_url": "https://commons.wikimedia.org/wiki/Special:FilePath/Rio_de_Janeiro_Maracan%C3%A3_Stadium_1.jpg?width=1200",
    },
    {
        "nome": "Praia de Copacabana",
        "descricao": "Praia famosa pelo calcadao em ondas, quiosques e paisagem urbana classica.",
        "categoria": "Praia",
        "cidade": "Rio de Janeiro",
        "bairro": "Copacabana",
        "endereco": "Avenida Atlantica",
        "latitude": -22.9711,
        "longitude": -43.1822,
        "imagem_url": "https://upload.wikimedia.org/wikipedia/commons/e/e6/Aerial_view_of_Copacabana_beach.jpg",
    },
    {
        "nome": "Praia de Ipanema",
        "descricao": "Praia conhecida pelo Posto 9, pelo por do sol e pela vista para o Morro Dois Irmaos.",
        "categoria": "Praia",
        "cidade": "Rio de Janeiro",
        "bairro": "Ipanema",
        "endereco": "Avenida Vieira Souto",
        "latitude": -22.9868,
        "longitude": -43.2030,
        "imagem_url": "https://upload.wikimedia.org/wikipedia/commons/5/57/Ipaneman_beach_Rio_de_Janeirossa.jpg",
    },
    {
        "nome": "Forte de Copacabana",
        "descricao": "Fortificacao historica com museu militar, cafes e vista para Copacabana.",
        "categoria": "Historico",
        "cidade": "Rio de Janeiro",
        "bairro": "Copacabana",
        "endereco": "Praca Coronel Eugenio Franco, 1",
        "latitude": -22.9866,
        "longitude": -43.1886,
        "imagem_url": "https://upload.wikimedia.org/wikipedia/commons/c/c2/Forte_de_Copacabana_panorama.jpg",
    },
    {
        "nome": "Vista Chinesa",
        "descricao": "Mirante em estilo oriental dentro da Floresta da Tijuca, com vista ampla da cidade.",
        "categoria": "Mirante",
        "cidade": "Rio de Janeiro",
        "bairro": "Alto da Boa Vista",
        "endereco": "Estrada da Vista Chinesa",
        "latitude": -22.9728,
        "longitude": -43.2490,
        "imagem_url": "https://upload.wikimedia.org/wikipedia/commons/2/2a/Vistachinesa5.jpg",
    },
    {
        "nome": "Floresta da Tijuca",
        "descricao": "Floresta urbana com cachoeiras, trilhas, mirantes e grande biodiversidade.",
        "categoria": "Natureza",
        "cidade": "Rio de Janeiro",
        "bairro": "Alto da Boa Vista",
        "endereco": "Estrada da Cascatinha",
        "latitude": -22.9514,
        "longitude": -43.2850,
        "imagem_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/6/6e/Floresta_da_Tijuca_60.jpg/3840px-Floresta_da_Tijuca_60.jpg",
    },
    {
        "nome": "Theatro Municipal",
        "descricao": "Teatro historico no Centro, conhecido por sua arquitetura imponente e programacao cultural.",
        "categoria": "Cultura",
        "cidade": "Rio de Janeiro",
        "bairro": "Centro",
        "endereco": "Praca Floriano",
        "latitude": -22.9092,
        "longitude": -43.1765,
        "imagem_url": "https://upload.wikimedia.org/wikipedia/commons/3/3f/Teatro_Municipal_-_panoramio_%284%29.jpg",
    },
    {
        "nome": "Real Gabinete Portugues de Leitura",
        "descricao": "Biblioteca historica com salao monumental, acervo raro e arquitetura neomanuelina.",
        "categoria": "Cultura",
        "cidade": "Rio de Janeiro",
        "bairro": "Centro",
        "endereco": "Rua Luis de Camoes, 30",
        "latitude": -22.9058,
        "longitude": -43.1823,
        "imagem_url": "https://upload.wikimedia.org/wikipedia/commons/5/59/Real_Gabinete_Portugu%C3%AAs_de_Leitura_11-18.jpg",
    },
    {
        "nome": "Mosteiro de Sao Bento",
        "descricao": "Mosteiro historico com igreja barroca, talha dourada e vista para a zona portuaria.",
        "categoria": "Historico",
        "cidade": "Rio de Janeiro",
        "bairro": "Centro",
        "endereco": "Rua Dom Gerardo, 68",
        "latitude": -22.8956,
        "longitude": -43.1786,
        "imagem_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/5/5a/Mosteiro_de_S%C3%A3o_Bento_1.jpg/3840px-Mosteiro_de_S%C3%A3o_Bento_1.jpg",
    },
    {
        "nome": "Morro Dois Irmaos",
        "descricao": "Trilha e mirante com uma das vistas mais famosas de Ipanema, Leblon e Lagoa.",
        "categoria": "Trilha",
        "cidade": "Rio de Janeiro",
        "bairro": "Vidigal",
        "endereco": "Comunidade do Vidigal",
        "latitude": -22.9944,
        "longitude": -43.2406,
        "imagem_url": "https://commons.wikimedia.org/wiki/Special:FilePath/Morro_Dois_Irm%C3%A3os_rio.jpg?width=1200",
    },
]


USUARIOS_TESTE = [
    {"nome": "Ana Visitante", "email": "ana.teste@tourcheck.com"},
    {"nome": "Bruno Mochileiro", "email": "bruno.teste@tourcheck.com"},
    {"nome": "Carla Carioca", "email": "carla.teste@tourcheck.com"},
    {"nome": "Diego Fotografo", "email": "diego.teste@tourcheck.com"},
]

COMENTARIOS_TESTE = [
    (5, "Lugar muito bonito e bem marcante. Vale separar um tempo para apreciar com calma."),
    (4, "Passeio agradavel, com boa estrutura e visual excelente para fotos."),
    (5, "Experiencia otima. Recomendo ir cedo para aproveitar melhor e evitar filas."),
    (4, "Gostei bastante do passeio. Bom para visitar com amigos ou familia."),
]


def obter_ou_criar_usuarios_teste_mongo():
    usuarios = []
    for dados in USUARIOS_TESTE:
        usuario = mongo_db.usuario_by_email(dados["email"])
        if usuario is None:
            usuario = mongo_db.criar_usuario(
                nome=dados["nome"],
                email=dados["email"],
                senha_hash=gerar_hash_senha("teste123"),
                tipo=TipoUsuario.COMUM,
                telefones=[],
            )
            print(f"Usuario de teste criado: {usuario.email}")
        usuarios.append(usuario)
    return usuarios


def criar_comentarios_teste_mongo():
    usuarios = obter_ou_criar_usuarios_teste_mongo()
    criados = 0
    for indice, dados in enumerate(PONTOS_DATA):
        ponto = mongo_db.ponto_by_id(
            mongo_db.pontos.find_one({"nome": dados["nome"]}, {"id": 1})["id"]
        )
        usuario = usuarios[indice % len(usuarios)]
        nota, comentario = COMENTARIOS_TESTE[indice % len(COMENTARIOS_TESTE)]
        if any(av.usuario_id == usuario.id for av in ponto.avaliacoes):
            continue
        mongo_db.salvar_avaliacao(usuario.id, ponto.id, nota, comentario)
        criados += 1
    print(f"Comentarios de teste criados no MongoDB: {criados}")


def obter_ou_criar_usuarios_teste_sql(db):
    usuarios = []
    for dados in USUARIOS_TESTE:
        usuario = db.query(Usuario).filter_by(email=dados["email"]).first()
        if usuario is None:
            usuario = Usuario(
                nome=dados["nome"],
                email=dados["email"],
                senha_hash=gerar_hash_senha("teste123"),
                tipo=TipoUsuario.COMUM,
            )
            db.add(usuario)
            db.flush()
            print(f"Usuario de teste criado: {usuario.email}")
        usuarios.append(usuario)
    return usuarios


def criar_comentarios_teste_sql(db):
    usuarios = obter_ou_criar_usuarios_teste_sql(db)
    criados = 0
    for indice, dados in enumerate(PONTOS_DATA):
        ponto = db.query(PontoTuristico).filter_by(nome=dados["nome"]).first()
        if ponto is None:
            continue
        usuario = usuarios[indice % len(usuarios)]
        existente = db.query(Avaliacao).filter_by(usuario_id=usuario.id, ponto_id=ponto.id).first()
        if existente is not None:
            continue
        nota, comentario = COMENTARIOS_TESTE[indice % len(COMENTARIOS_TESTE)]
        db.add(Avaliacao(usuario_id=usuario.id, ponto_id=ponto.id, nota=nota, comentario=comentario))
        criados += 1
    print(f"Comentarios de teste criados no SQL: {criados}")


def rodar_seed():
    if using_mongodb():
        mongo_db.init_indexes()
        if not mongo_db.usuario_by_email("admin@rio.com"):
            admin = mongo_db.criar_usuario(
                nome="Administrador",
                email="admin@rio.com",
                senha_hash=gerar_hash_senha("admin123"),
                tipo=TipoUsuario.ADMIN,
                telefones=[],
            )
            print(f"Admin criado: {admin.email}")

        for dados in PONTOS_DATA:
            if not mongo_db.pontos.find_one({"nome": dados["nome"]}):
                mongo_db.criar_ponto(dados, criado_por_id=None, status=StatusPonto.APROVADO)
                print(f"Ponto criado: {dados['nome']}")
        criar_comentarios_teste_mongo()
        print("\nSeed MongoDB concluido com sucesso!")
        return

    db = SessionLocal()
    try:
        if not db.query(Usuario).filter_by(email="admin@rio.com").first():
            admin = Usuario(
                nome="Administrador",
                email="admin@rio.com",
                senha_hash=gerar_hash_senha("admin123"),
                tipo=TipoUsuario.ADMIN,
            )
            db.add(admin)
            db.flush()
            print("Admin criado.")

        for dados in PONTOS_DATA:
            if not db.query(PontoTuristico).filter_by(nome=dados["nome"]).first():
                ponto = PontoTuristico(**dados, status=StatusPonto.APROVADO)
                db.add(ponto)
                print(f"Ponto criado: {dados['nome']}")

        criar_comentarios_teste_sql(db)
        db.commit()
        print("\nSeed concluido com sucesso!")

    except Exception as e:
        db.rollback()
        print(f"Erro no seed: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    rodar_seed()
