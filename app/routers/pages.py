import os

from fastapi import APIRouter, Request
from fastapi.responses import FileResponse


router = APIRouter(tags=["pages"])


def entregar_template(nome_arquivo: str):
    template_path = os.path.join("app", "templates", nome_arquivo)
    if os.path.exists(template_path):
        return FileResponse(template_path)
    return {"error": f"Template nao encontrado: {template_path}"}


@router.get("/")
async def index(request: Request):
    return entregar_template("index.html")


@router.get("/login")
async def login(request: Request):
    return entregar_template("login.html")


@router.get("/cadastro")
async def cadastro(request: Request):
    return entregar_template("cadastro.html")


@router.get("/ponto_cadastro")
async def ponto_cadastro(request: Request):
    return entregar_template("ponto_cadastro.html")


@router.get("/admin")
async def admin(request: Request):
    return entregar_template("admin.html")


@router.get("/ponto/{ponto_id}")
async def ponto_detalhe(ponto_id: int, request: Request):
    return entregar_template("ponto.html")
