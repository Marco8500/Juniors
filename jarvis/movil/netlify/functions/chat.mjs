// Cerebro de Jarvis: recibe la conversación y devuelve la respuesta de Claude en streaming (texto plano).
// Usa el AI Gateway de Netlify, que inyecta las credenciales: no hace falta ninguna clave.
import Anthropic from "@anthropic-ai/sdk";

const MODEL = "claude-haiku-5-5"; // rápido y muy barato: cabe de sobra en el plan gratis

const SYSTEM =
  "Eres Jarvis, un asistente personal. Hablas en español de España, con tono cercano, " +
  "seguro y con un punto de humor. Tus respuestas se leen en voz alta, así que: " +
  "frases cortas, como mucho 3 o 4 frases, nada de markdown, listas, emojis ni símbolos raros. " +
  "Si no sabes algo actual (noticias, tiempo, hora exacta), dilo con naturalidad.";

export default async (req) => {
  if (req.method !== "POST") return new Response("Usa POST", { status: 405 });
  if (!process.env.ANTHROPIC_BASE_URL) {
    return new Response("El cerebro de Jarvis todavía no está activo en Netlify.", { status: 503 });
  }

  let body;
  try {
    body = await req.json();
  } catch {
    return new Response("JSON no válido", { status: 400 });
  }

  // Limpieza y límites: como mucho 12 turnos de 600 caracteres
  const raw = Array.isArray(body?.messages) ? body.messages.slice(-12) : [];
  const messages = raw
    .filter((m) => (m?.role === "user" || m?.role === "assistant") && typeof m.content === "string" && m.content.trim())
    .map((m) => ({ role: m.role, content: m.content.slice(0, 600) }));
  while (messages.length && messages[0].role !== "user") messages.shift();
  if (!messages.length || messages[messages.length - 1].role !== "user") {
    return new Response("Falta el mensaje", { status: 400 });
  }

  const now = new Date().toLocaleString("es-ES", { timeZone: "Europe/Madrid", dateStyle: "full", timeStyle: "short" });
  const client = new Anthropic();
  const encoder = new TextEncoder();

  const stream = new ReadableStream({
    async start(controller) {
      try {
        const s = client.messages.stream({
          model: MODEL,
          max_tokens: 350,
          system: `${SYSTEM} Ahora mismo en España es ${now}.`,
          messages,
        });
        for await (const ev of s) {
          if (ev.type === "content_block_delta" && ev.delta?.type === "text_delta") {
            controller.enqueue(encoder.encode(ev.delta.text));
          }
        }
      } catch (e) {
        controller.enqueue(encoder.encode("\n[ERROR] Ahora mismo no puedo pensar. Prueba otra vez en un momento."));
        console.error(e);
      } finally {
        controller.close();
      }
    },
  });

  return new Response(stream, {
    headers: { "Content-Type": "text/plain; charset=utf-8", "Cache-Control": "no-store" },
  });
};

export const config = {
  path: "/api/chat",
  method: "POST",
  // Frena abusos: 20 mensajes por minuto por IP
  rateLimit: { windowLimit: 20, windowSize: 60, aggregateBy: ["ip", "domain"] },
};
