export const OLLAMA_BASE = "http://localhost:11434"

export async function checkOllama() {
  try {
    const res = await fetch(`${OLLAMA_BASE}/api/tags`)
    return res.ok
  } catch { return false }
}

export async function ollamaStream(systemPrompt, userPrompt, onToken) {
  const res = await fetch(`${OLLAMA_BASE}/api/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      model: "llama3.2",
      stream: true,
      messages: [
        { role: "system", content: systemPrompt },
        { role: "user",   content: userPrompt }
      ]
    })
  })
  const reader = res.body.getReader()
  const decoder = new TextDecoder()
  while (true) {
    const { done, value } = await reader.read()
    if (done) break
    const lines = decoder.decode(value).split("\n").filter(Boolean)
    for (const line of lines) {
      try {
        const json = JSON.parse(line)
        if (json.message?.content) onToken(json.message.content)
      } catch {}
    }
  }
}
