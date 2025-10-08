import client from "prom-client";

export const register = new client.Registry();
client.collectDefaultMetrics({ register });

export const mailProcessed = new client.Counter({ 
  name: "mail_processed_total", 
  help: "Processed mails", 
  registers: [register] 
});

export const mailErrors = new client.Counter({ 
  name: "mail_errors_total", 
  help: "Processing errors", 
  registers: [register] 
});

export const latency = new client.Histogram({ 
  name: "pipeline_latency_seconds", 
  help: "End-to-end latency", 
  buckets: [0.5, 1, 2, 5, 10], 
  registers: [register] 
});
