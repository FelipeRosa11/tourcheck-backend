# seed.py — roda uma vez para popular o banco com dados iniciais
import os
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database import SessionLocal
from app.models.ponto import PontoTuristico, StatusPonto
from app.models.usuario import TipoUsuario, Usuario
from app.security import gerar_hash_senha


def rodar_seed():
    db = SessionLocal()
    try:
        # ── Admin ──────────────────────────────────────────────
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

        # ── Pontos Turísticos ──────────────────────────────────
        pontos_data = [
            {
                "nome": "Cristo Redentor",
                "descricao": "Estátua icônica no topo do Corcovado, com vista panorâmica do Rio de Janeiro.",
                "categoria": "Monumento",
                "cidade": "Rio de Janeiro",
                "bairro": "Santa Teresa",
                "endereco": "Parque Nacional da Tijuca - Alto da Boa Vista",
                "latitude": -22.9519,
                "longitude": -43.2105,
                "imagem_url": "https://upload.wikimedia.org/wikipedia/commons/4/4f/Christ_the_Redeemer_-_Cristo_Redentor.jpg",
                "status": StatusPonto.APROVADO,
            },
            {
                "nome": "Pão de Açúcar",
                "descricao": "Morro com vista panorâmica da Baía de Guanabara, acessível por bondinho.",
                "categoria": "Natureza",
                "cidade": "Rio de Janeiro",
                "bairro": "Urca",
                "endereco": "Praça General Tibúrcio, 68 - Urca",
                "latitude": -22.9489,
                "longitude": -43.1546,
                "imagem_url": "https://upload.wikimedia.org/wikipedia/commons/3/37/P%C3%A3o_de_A%C3%A7%C3%BAcar_ao_anoitecer_edit.jpg",
                "status": StatusPonto.APROVADO,
            },
        ]

        for dados in pontos_data:
            if not db.query(PontoTuristico).filter_by(nome=dados["nome"]).first():
                ponto = PontoTuristico(**dados)
                db.add(ponto)
                print(f"Ponto criado: {dados['nome']}")

        db.commit()
        print("\nSeed concluído com sucesso!")

    except Exception as e:
        db.rollback()
        print(f"Erro no seed: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    rodar_seed()