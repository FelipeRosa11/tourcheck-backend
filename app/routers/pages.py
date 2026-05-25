import os

from fastapi import Request, APIRouter
from fastapi.responses import FileResponse
from starlette.templating import Jinja2Templates

router = APIRouter(tags=["pages"])
templates = Jinja2Templates(directory="app/templates")


@router.get("/")
async def index(request: Request):
    template_path = "app/templates/index.html"
    if os.path.exists(template_path):
        return FileResponse(template_path)
    return {"error": f"Template não encontrado: {template_path}"}

@router.get("/login")
async def login(request: Request):
    template_path = "app/templates/login.html"
    if os.path.exists(template_path):
        return FileResponse(template_path)
    return {"error": f"Template não encontrado: {template_path}"}

@router.get("/cadastro")
async def cadastro(request: Request):
    template_path = "app/templates/cadastro.html"
    if os.path.exists(template_path):
        return FileResponse(template_path)
    return {"error": f"Template não encontrado: {template_path}"}

@router.get("/ponto_cadastro")
async def ponto_cadastro(request: Request):
    template_path = "app/templates/ponto_cadastro.html"
    if os.path.exists(template_path):
        return FileResponse(template_path)
    return {"error": f"Template não encontrado: {template_path}"}
