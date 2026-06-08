import http from "k6/http";
import { check, sleep } from "k6";
import { Rate } from "k6/metrics";

const taxaFalha = new Rate("taxa_falha");

export const options = {
  stages: [
    { duration: "15s", target: 10 },   // aquecimento
    { duration: "30s", target: 25 },   // carga leve
    { duration: "30s", target: 50 },   // carga normal (baseline anterior)
    { duration: "30s", target: 75 },   // degrau 1 acima do baseline
    { duration: "30s", target: 100 },  // degrau 2 — zona de stress
    { duration: "30s", target: 150 },  // degrau 3 — zona de ruptura
    { duration: "15s", target: 0 },    // resfriamento
  ],
  thresholds: {
    http_req_failed: ["rate<0.05"],
    http_req_duration: ["p(95)<2000"],
  },
};

export default function () {
  const idAleatorio = Math.floor(Math.random() * 9999999);

  const payload = JSON.stringify({
    nome: `Usuario Teste ${idAleatorio}`,
    email: `teste_${idAleatorio}@tourcheck.com`,
    senha: "senha_de_teste_123",
    telefones: [{ numero: "21999999999", tipo: "celular" }],
  });

  const res = http.post("http://127.0.0.1:8000/auth/cadastro", payload, {
    headers: { "Content-Type": "application/json" },
  });

  const ok = check(res, {
    "status é 201": (r) => r.status === 201,
    "tempo < 500ms": (r) => r.timings.duration < 500,
  });

  taxaFalha.add(!ok);
  sleep(1);
}