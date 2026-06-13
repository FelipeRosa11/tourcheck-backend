from datetime import datetime
from types import SimpleNamespace
from typing import Any

from pymongo import ASCENDING, DESCENDING, MongoClient, ReturnDocument
from pymongo.database import Database

from app.database import MONGODB_DATABASE, MONGODB_URL
from app.models.ponto import StatusPonto
from app.models.usuario import TipoTelefone, TipoUsuario


PONTO_CAMPOS_EDITAVEIS = {
    "nome",
    "descricao",
    "categoria",
    "cidade",
    "bairro",
    "endereco",
    "latitude",
    "longitude",
    "imagem_url",
    "imagens_urls",
}


def _enum_value(value: Any) -> Any:
    return value.value if hasattr(value, "value") else value


def _view(data: dict[str, Any] | None) -> SimpleNamespace | None:
    if data is None:
        return None
    cleaned = {key: value for key, value in data.items() if key != "_id"}
    if "tipo" in cleaned:
        cleaned["tipo"] = TipoUsuario(cleaned["tipo"])
    if "status" in cleaned:
        cleaned["status"] = StatusPonto(cleaned["status"])
    if "telefones" in cleaned:
        cleaned["telefones"] = [
            SimpleNamespace(**{**tel, "tipo": TipoTelefone(tel["tipo"])})
            for tel in cleaned.get("telefones", [])
        ]
    if "avaliacoes" in cleaned:
        cleaned["avaliacoes"] = [SimpleNamespace(**avaliacao) for avaliacao in cleaned.get("avaliacoes", [])]
    return SimpleNamespace(**cleaned)


class MongoDatabase:
    def __init__(self, client: MongoClient, database: Database):
        self.client = client
        self.database = database
        self.usuarios = database["usuarios"]
        self.pontos = database["pontos_turisticos"]
        self.salvos = database["pontos_salvos"]
        self.counters = database["counters"]

    def init_indexes(self) -> None:
        self.usuarios.create_index([("email", ASCENDING)], unique=True)
        self.usuarios.create_index([("id", ASCENDING)], unique=True)
        self.pontos.create_index([("id", ASCENDING)], unique=True)
        self.pontos.create_index([("nome", ASCENDING)])
        self.pontos.create_index([("cidade", ASCENDING)])
        self.pontos.create_index([("categoria", ASCENDING)])
        self.salvos.create_index([("usuario_id", ASCENDING), ("ponto_id", ASCENDING)], unique=True)
        self.salvos.create_index([("criado_em", DESCENDING)])

    def next_id(self, name: str) -> int:
        counter = self.counters.find_one_and_update(
            {"_id": name},
            {"$inc": {"seq": 1}},
            upsert=True,
            return_document=ReturnDocument.AFTER,
        )
        return int(counter["seq"])

    def usuario_by_id(self, usuario_id: int) -> SimpleNamespace | None:
        return _view(self.usuarios.find_one({"id": usuario_id}))

    def usuario_by_email(self, email: str) -> SimpleNamespace | None:
        return _view(self.usuarios.find_one({"email": email.lower()}))

    def existe_admin(self) -> bool:
        return self.usuarios.find_one({"tipo": TipoUsuario.ADMIN.value}, {"_id": 1}) is not None

    def criar_usuario(self, nome: str, email: str, senha_hash: str, tipo: TipoUsuario, telefones: list[Any]) -> SimpleNamespace:
        usuario_id = self.next_id("usuarios")
        doc = {
            "id": usuario_id,
            "nome": nome,
            "email": email.lower(),
            "senha_hash": senha_hash,
            "tipo": _enum_value(tipo),
            "telefones": [
                {"id": idx, "tipo": _enum_value(telefone.tipo), "numero": telefone.numero}
                for idx, telefone in enumerate(telefones, start=1)
            ],
        }
        self.usuarios.insert_one(doc)
        return _view(doc)

    def alterar_tipo_usuario(self, usuario_id: int, tipo: TipoUsuario) -> SimpleNamespace | None:
        self.usuarios.update_one({"id": usuario_id}, {"$set": {"tipo": _enum_value(tipo)}})
        return self.usuario_by_id(usuario_id)

    def listar_usuarios(self) -> list[SimpleNamespace]:
        return [_view(doc) for doc in self.usuarios.find().sort("nome", ASCENDING)]

    def _ponto_view(self, doc: dict[str, Any] | None) -> SimpleNamespace | None:
        if doc is None:
            return None
        edicao_pendente = doc.get("edicao_pendente")
        if isinstance(edicao_pendente, dict):
            versao_aprovada = edicao_pendente.get("versao_aprovada")
            if isinstance(versao_aprovada, dict):
                doc = {**doc, **versao_aprovada}
        avaliacoes = doc.get("avaliacoes", [])
        usuarios_ids = {
            avaliacao.get("usuario_id")
            for avaliacao in avaliacoes
            if avaliacao.get("usuario_id") is not None and not avaliacao.get("usuario_nome")
        }
        usuarios_por_id = {
            usuario["id"]: usuario.get("nome")
            for usuario in self.usuarios.find({"id": {"$in": list(usuarios_ids)}}, {"id": 1, "nome": 1})
        }
        avaliacoes = [
            {
                **avaliacao,
                "usuario_nome": avaliacao.get("usuario_nome") or usuarios_por_id.get(avaliacao.get("usuario_id")),
            }
            for avaliacao in avaliacoes
        ]
        doc = {**doc, "avaliacoes": avaliacoes}
        return _view(doc)

    def ponto_by_id(self, ponto_id: int) -> SimpleNamespace | None:
        return self._ponto_view(self.pontos.find_one({"id": ponto_id}))

    def criar_ponto(self, dados: dict[str, Any], criado_por_id: int | None, status: StatusPonto) -> SimpleNamespace:
        doc = {
            **dados,
            "id": self.next_id("pontos_turisticos"),
            "status": _enum_value(status),
            "criado_em": datetime.utcnow(),
            "criado_por_id": criado_por_id,
            "avaliacoes": [],
        }
        self.pontos.insert_one(doc)
        return self._ponto_view(doc)

    def listar_pontos(
        self,
        busca: str | None = None,
        cidade: str | None = None,
        categoria: str | None = None,
        status_ponto: StatusPonto | None = None,
        incluir_pendentes: bool = False,
    ) -> list[SimpleNamespace]:
        filtro: dict[str, Any] = {}
        if status_ponto is not None:
            filtro["status"] = _enum_value(status_ponto)
        elif not incluir_pendentes:
            filtro["status"] = StatusPonto.APROVADO.value
        if cidade:
            filtro["cidade"] = {"$regex": cidade, "$options": "i"}
        if categoria:
            filtro["categoria"] = {"$regex": categoria, "$options": "i"}
        if busca:
            filtro["$or"] = [
                {campo: {"$regex": busca, "$options": "i"}}
                for campo in ("nome", "categoria", "cidade", "bairro")
            ]
        return [self._ponto_view(doc) for doc in self.pontos.find(filtro).sort("nome", ASCENDING)]

    def listar_pontos_admin(self, status_ponto: StatusPonto | None = None) -> list[SimpleNamespace]:
        filtro = {"status": _enum_value(status_ponto)} if status_ponto is not None else {}
        return [self._ponto_view(doc) for doc in self.pontos.find(filtro).sort("criado_em", DESCENDING)]

    def atualizar_ponto(self, ponto_id: int, atualizacoes: dict[str, Any]) -> SimpleNamespace | None:
        dados = {campo: _enum_value(valor) for campo, valor in atualizacoes.items()}
        if dados:
            self.pontos.update_one({"id": ponto_id}, {"$set": dados})
        return self.ponto_by_id(ponto_id)

    def solicitar_edicao_ponto(self, ponto_id: int, atualizacoes: dict[str, Any], usuario_id: int) -> SimpleNamespace | None:
        dados = {campo: _enum_value(valor) for campo, valor in atualizacoes.items()}
        doc_atual = self.pontos.find_one({"id": ponto_id})
        if doc_atual is None:
            return None
        edicao_atual = doc_atual.get("edicao_pendente")
        versao_aprovada = (
            edicao_atual.get("versao_aprovada")
            if isinstance(edicao_atual, dict) and isinstance(edicao_atual.get("versao_aprovada"), dict)
            else {campo: doc_atual.get(campo) for campo in PONTO_CAMPOS_EDITAVEIS if campo in doc_atual}
        )
        self.pontos.update_one(
            {"id": ponto_id},
            {
                "$set": {
                    "edicao_pendente": {
                        "dados": dados,
                        "versao_aprovada": versao_aprovada,
                        "solicitado_por_id": usuario_id,
                        "solicitado_em": datetime.utcnow(),
                    }
                }
            },
        )
        return self.ponto_by_id(ponto_id)

    def listar_edicoes_pendentes(self) -> list[dict[str, Any]]:
        edicoes = []
        for doc in self.pontos.find({"edicao_pendente": {"$exists": True}}).sort("edicao_pendente.solicitado_em", DESCENDING):
            ponto = self._ponto_view(doc)
            edicao = doc.get("edicao_pendente", {})
            edicoes.append(
                {
                    "ponto": ponto,
                    "dados": edicao.get("dados", {}),
                    "solicitado_por_id": edicao.get("solicitado_por_id"),
                    "solicitado_em": edicao.get("solicitado_em"),
                }
            )
        return edicoes

    def aprovar_edicao_ponto(self, ponto_id: int) -> SimpleNamespace | None:
        doc = self.pontos.find_one({"id": ponto_id, "edicao_pendente": {"$exists": True}})
        if doc is None:
            return None
        dados = doc.get("edicao_pendente", {}).get("dados", {})
        self.pontos.update_one({"id": ponto_id}, {"$set": dados, "$unset": {"edicao_pendente": ""}})
        return self.ponto_by_id(ponto_id)

    def rejeitar_edicao_ponto(self, ponto_id: int) -> SimpleNamespace | None:
        doc = self.pontos.find_one({"id": ponto_id, "edicao_pendente": {"$exists": True}})
        if doc is None:
            return None
        versao_aprovada = doc.get("edicao_pendente", {}).get("versao_aprovada", {})
        update: dict[str, Any] = {"$unset": {"edicao_pendente": ""}}
        if versao_aprovada:
            update["$set"] = versao_aprovada
        self.pontos.update_one({"id": ponto_id}, update)
        return self.ponto_by_id(ponto_id)

    def salvos_ids_usuario(self, usuario_id: int) -> set[int]:
        return {doc["ponto_id"] for doc in self.salvos.find({"usuario_id": usuario_id}, {"ponto_id": 1})}

    def salvar_ponto(self, usuario_id: int, ponto_id: int) -> None:
        self.salvos.update_one(
            {"usuario_id": usuario_id, "ponto_id": ponto_id},
            {"$setOnInsert": {"usuario_id": usuario_id, "ponto_id": ponto_id, "criado_em": datetime.utcnow()}},
            upsert=True,
        )

    def remover_ponto_salvo(self, usuario_id: int, ponto_id: int) -> None:
        self.salvos.delete_one({"usuario_id": usuario_id, "ponto_id": ponto_id})

    def listar_pontos_salvos(self, usuario_id: int) -> list[SimpleNamespace]:
        pontos = []
        for salvo in self.salvos.find({"usuario_id": usuario_id}).sort("criado_em", DESCENDING):
            ponto = self.ponto_by_id(salvo["ponto_id"])
            if ponto is not None and ponto.status == StatusPonto.APROVADO:
                pontos.append(ponto)
        return pontos

    def salvar_avaliacao(self, usuario_id: int, ponto_id: int, nota: int, comentario: str | None) -> SimpleNamespace:
        ponto = self.pontos.find_one({"id": ponto_id, "avaliacoes.usuario_id": usuario_id})
        if ponto is None:
            avaliacao = {
                "id": self.next_id("avaliacoes"),
                "usuario_id": usuario_id,
                "usuario_nome": getattr(self.usuario_by_id(usuario_id), "nome", None),
                "ponto_id": ponto_id,
                "nota": nota,
                "comentario": comentario,
                "criado_em": datetime.utcnow(),
            }
            self.pontos.update_one({"id": ponto_id}, {"$push": {"avaliacoes": avaliacao}})
            return SimpleNamespace(**avaliacao)

        self.pontos.update_one(
            {"id": ponto_id, "avaliacoes.usuario_id": usuario_id},
            {
                "$set": {
                    "avaliacoes.$.nota": nota,
                    "avaliacoes.$.comentario": comentario,
                    "avaliacoes.$.usuario_nome": getattr(self.usuario_by_id(usuario_id), "nome", None),
                }
            },
        )
        atualizado = self.pontos.find_one(
            {"id": ponto_id, "avaliacoes.usuario_id": usuario_id},
            {"avaliacoes.$": 1},
        )
        return SimpleNamespace(**atualizado["avaliacoes"][0])

    def apagar_avaliacao(self, ponto_id: int, avaliacao_id: int, usuario_id: int | None = None) -> bool:
        filtro: dict[str, Any] = (
            {"id": ponto_id, "avaliacoes.id": avaliacao_id}
            if usuario_id is None
            else {
                "id": ponto_id,
                "avaliacoes": {
                    "$elemMatch": {
                        "id": avaliacao_id,
                        "usuario_id": usuario_id,
                    }
                },
            }
        )
        resultado = self.pontos.update_one(
            filtro,
            {"$pull": {"avaliacoes": {"id": avaliacao_id}}},
        )
        return resultado.modified_count > 0


mongo_client = MongoClient(MONGODB_URL)
mongo_db = MongoDatabase(mongo_client, mongo_client[MONGODB_DATABASE])
