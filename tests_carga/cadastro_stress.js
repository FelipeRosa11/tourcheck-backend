import http from "k6/http";
import { check, sleep } from "k6";
import { Rate } from "k6/metrics";

const taxaFalha = new Rate("taxa_falha");

export const options = {
  stages: [
    { duration: "15s", target: 20 }, // aquecimento
    { duration: "30s", target: 50 }, // carga normal
    { duration: "45s", target: 100 }, // teto máximo permitido pelo plano free (baseline)
    { duration: "15s", target: 0 }, // resfriamento
  ],
  thresholds: {
    http_req_failed: ["rate<0.05"], // aceita até 5% de falha
    http_req_duration: ["p(95)<2000"], // 95% das requisições abaixo de 2s (por causa do Bcrypt)
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
