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
    http_req_duration: ["p(95)<500"], // 95% das requisições abaixo de 500ms
  },
};

export default function () {
  const res = http.get("http://127.0.0.1:8000/pontos");

  const ok = check(res, {
    "status é 200": (r) => r.status === 200,
    "tempo < 200ms": (r) => r.timings.duration < 200,
  });

  taxaFalha.add(!ok);
  sleep(0.5);
}
