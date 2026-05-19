# Inicializa o FastAPI e inclui as rotas (routers)

from fastapi import FastAPI

app = FastAPI(
    title="TourCheck API",
    description="API de busca e avaliação de pontos turísticos do Rio de Janeiro",
    version="1.0.0"
)

@app.get("/")
def read_root():
    return {"status": "TourCheck API funcionando com sucesso!"}