import http from "k6/http";
import { check, sleep } from "k6";

export const options = {
  stages: [
    { duration: "10s", target: 20 }, // Sobe para 20 usuários
    { duration: "30s", target: 100 }, // Mantém 100 usuários simultâneos batendo na rota
    { duration: "10s", target: 0 }, // Desce para 0
  ],
};

export default function () {
  const url = "http://127.0.0.1:8000/pontos";
  const res = http.get(url);

  check(res, {
    "status é 200": (r) => r.status === 200,
    "tempo < 200ms": (r) => r.timings.duration < 200,
  });

  sleep(0.5);
}
