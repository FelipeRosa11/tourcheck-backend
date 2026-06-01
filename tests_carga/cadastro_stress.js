import http from "k6/http";
import { check, sleep } from "k6";

export const options = {
  stages: [
    { duration: "10s", target: 10 },
    { duration: "30s", target: 50 },
    { duration: "10s", target: 0 },
  ],
};

export default function () {
  const url = "http://127.0.0.1:8000/auth/cadastro";
  const idAleatorio = Math.floor(Math.random() * 1000000);

  const payload = JSON.stringify({
    nome: `Felipe Teste ${idAleatorio}`,
    email: `teste_${idAleatorio}@tourcheck.com`,
    senha: "senha_de_teste_123",
    telefones: [{ numero: "21999999999", tipo: "celular" }],
  });

  const params = { headers: { "Content-Type": "application/json" } };
  const res = http.post(url, payload, params);

  check(res, {
    "status é 201": (r) => r.status === 201,
    "tempo < 500ms": (r) => r.timings.duration < 500,
  });

  sleep(1);
}
