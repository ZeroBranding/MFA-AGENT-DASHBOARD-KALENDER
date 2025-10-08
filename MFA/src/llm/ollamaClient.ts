export type ChatReq = { 
  model: string; 
  messages: { role: "system" | "user"; content: string }[]; 
};

type ChatResp = { message?: { content: string } };

export async function ollamaChat(
  url: string, 
  req: ChatReq, 
  timeoutMs = 60000
): Promise<string> {
  const ctl = new AbortController();
  const t = setTimeout(() => ctl.abort(), timeoutMs);

  try {
    const res = await fetch(`${url}/api/chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ ...req, stream: false }),
      signal: ctl.signal
    });

    if (!res.ok) throw new Error(`ollama ${res.status} ${res.statusText}`);
    const data = (await res.json()) as ChatResp;
    const content = data?.message?.content ?? "";
    if (!content) throw new Error("empty response");
    return content;
  } finally {
    clearTimeout(t);
  }
}
