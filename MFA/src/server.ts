import fastify from "fastify";
import { register } from "./observability/metrics";

const app = fastify();

app.get("/health", async () => ({ ok: true, ts: new Date().toISOString() }));

app.get("/metrics", async (req, reply) => {
  reply.header("Content-Type", register.contentType);
  return register.metrics();
});

app.listen({ port: 8081, host: "127.0.0.1" }, (err, addr) => {
  if (err) {
    console.error(err);
    process.exit(1);
  }
  console.log(`🚀 Health & Metrics Server läuft auf ${addr}`);
});
