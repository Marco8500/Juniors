// Jarvis móvil: escucha «Ey Jarvis», pregunta a /api/chat y contesta en voz alta.
(() => {
  "use strict";
  const $ = (id) => document.getElementById(id);
  const cv = $("cv"), ctx = cv.getContext("2d");
  const statusEl = $("status"), saidEl = $("said"), replyEl = $("reply"), errEl = $("err"), input = $("msg");

  // ---------------- Estado ----------------
  // mode: off | waiting (espera «Ey Jarvis») | listening (escucha la orden) | thinking | speaking
  let mode = "off";
  let level = 0;
  let voiceOn = true;
  let active = false;           // el usuario ha pulsado «Activar»
  const turns = [];
  let chatCtl = null;
  let wakeLock = null;

  const isIOS = /iP(hone|ad|od)/.test(navigator.userAgent) || (navigator.platform === "MacIntel" && navigator.maxTouchPoints > 1);
  const Recog = window.SpeechRecognition || window.webkitSpeechRecognition || null;

  try { voiceOn = localStorage.getItem("jarvis-voz") !== "off"; } catch (e) {}

  const LABEL = {
    off: "Toca «Activar» para empezar",
    waiting: "Di <b>«Ey Jarvis»</b>",
    listening: "Te escucho…",
    thinking: "Pensando…",
    speaking: "Hablando…",
  };
  function setMode(m) {
    mode = m;
    statusEl.innerHTML = (m === "waiting" && !Recog) ? "Escríbele abajo" : LABEL[m];
  }
  const showErr = (msg) => { errEl.textContent = msg || ""; errEl.hidden = !msg; };

  // ---------------- Orbe ----------------
  const reduce = matchMedia("(prefers-reduced-motion: reduce)").matches;
  let t = 0, smooth = 0;
  function draw() {
    requestAnimationFrame(draw);
    const dpr = Math.min(2, window.devicePixelRatio || 1);
    const W = Math.max(10, cv.clientWidth), H = Math.max(10, cv.clientHeight);
    if (cv.width !== Math.round(W * dpr) || cv.height !== Math.round(H * dpr)) { cv.width = Math.round(W * dpr); cv.height = Math.round(H * dpr); }
    const size = Math.min(W, H);
    ctx.setTransform(dpr, 0, 0, dpr, (W - size) / 2 * dpr, (H - size) / 2 * dpr);
    ctx.clearRect(-W, -H, W * 3, H * 3);
    t += reduce ? 0.004 : 1 / 60;

    let target = 0.05 + Math.sin(t * 1.5) * 0.03;
    if (mode === "off") target = 0.03;
    else if (mode === "listening") target = 0.2 + level;
    else if (mode === "thinking") target = 0.15;
    else if (mode === "speaking") target = Math.max(level, 0.25 + 0.2 * Math.abs(Math.sin(t * 9)));
    level *= 0.92;
    smooth += (target - smooth) * 0.2;

    const cx = size / 2, cy = size / 2, base = size * 0.22;
    const hue = mode === "listening" ? 190 : mode === "thinking" ? 265 : mode === "speaking" ? 175 : mode === "off" ? 210 : 200;
    const sat = mode === "off" ? 40 : 100;

    const glow = ctx.createRadialGradient(cx, cy, base * 0.4, cx, cy, base * (2.2 + smooth));
    glow.addColorStop(0, `hsla(${hue},${sat}%,60%,${0.35 + smooth * 0.4})`);
    glow.addColorStop(1, `hsla(${hue},${sat}%,50%,0)`);
    ctx.fillStyle = glow;
    ctx.fillRect(-W, -H, W * 3, H * 3);

    ctx.lineWidth = 1.5;
    for (let r = 0; r < 3; r++) {
      const radius = base * (1.45 + r * 0.22) + smooth * base * 0.25;
      const start = t * (0.6 + r * 0.35) * (r % 2 ? -1 : 1) * (mode === "thinking" ? 2.5 : 1);
      ctx.strokeStyle = `hsla(${hue},${sat}%,70%,${0.5 - r * 0.12})`;
      ctx.beginPath();
      ctx.arc(cx, cy, radius, start, start + Math.PI * (mode === "thinking" ? 0.6 : 1.3));
      ctx.stroke();
    }

    const pts = 96;
    ctx.beginPath();
    for (let i = 0; i <= pts; i++) {
      const a = (i / pts) * Math.PI * 2;
      const wob = Math.sin(a * 3 + t * 2) * 0.06
        + Math.sin(a * 5 - t * 3) * 0.04 * (1 + smooth * 4)
        + Math.sin(a * 8 + t * 5) * 0.03 * smooth * 3;
      const rr = base * (1 + smooth * 0.35 + wob);
      const x = cx + Math.cos(a) * rr, y = cy + Math.sin(a) * rr;
      i ? ctx.lineTo(x, y) : ctx.moveTo(x, y);
    }
    const core = ctx.createRadialGradient(cx - base * 0.3, cy - base * 0.3, base * 0.1, cx, cy, base * 1.4);
    core.addColorStop(0, `hsla(${hue},${sat}%,85%,1)`);
    core.addColorStop(0.5, `hsla(${hue},${sat - 5}%,55%,0.95)`);
    core.addColorStop(1, `hsla(${hue + 30},${sat - 10}%,30%,0.9)`);
    ctx.fillStyle = core;
    ctx.fill();
  }
  draw();

  // ---------------- Voz (salida) ----------------
  let voice = null;
  function pickVoice() {
    const vs = window.speechSynthesis ? speechSynthesis.getVoices() : [];
    const es = vs.filter((v) => /^es/i.test(v.lang));
    voice = es.find((v) => /es-ES/i.test(v.lang) && /google|neural|natural|premium|enhanced|m[oó]nica|jorge|helena|pablo/i.test(v.name))
      || es.find((v) => /es-ES/i.test(v.lang))
      || es[0] || null;
  }
  if (window.speechSynthesis) {
    pickVoice();
    speechSynthesis.addEventListener?.("voiceschanged", pickVoice);
  }

  // Desbloquea el audio en móviles: hay que hablar dentro de un toque del usuario
  function unlockAudio() {
    if (!window.speechSynthesis) return;
    try {
      const u = new SpeechSynthesisUtterance(" ");
      u.volume = 0.01;
      speechSynthesis.speak(u);
    } catch (e) {}
  }

  const keep = new Set(); // evita que el navegador "pierda" las frases (bug de Chrome/Safari)
  function speakOne(text) {
    return new Promise((resolve) => {
      const u = new SpeechSynthesisUtterance(text);
      u.lang = voice?.lang || "es-ES";
      if (voice) u.voice = voice;
      u.rate = 1.03;
      u.volume = 1;
      keep.add(u);
      let done = false;
      const finish = () => { if (done) return; done = true; keep.delete(u); clearInterval(pulse); clearTimeout(guard); resolve(); };
      u.onboundary = () => { level = 0.7 + Math.random() * 0.3; };
      u.onend = finish;
      u.onerror = finish;
      // Por si el navegador no avisa del final o de las palabras
      const pulse = setInterval(() => { level = Math.max(level, 0.45 + Math.random() * 0.35); }, 160);
      const guard = setTimeout(finish, 2500 + text.length * 120);
      speechSynthesis.speak(u);
      // Chrome Android a veces se queda pausado
      setTimeout(() => { try { speechSynthesis.resume(); } catch (e) {} }, 50);
    });
  }

  // Cola de frases: empieza a hablar en cuanto llega la primera frase completa
  let speakQueue = Promise.resolve();
  function queueSpeech(sentence) {
    sentence = sentence.replace(/[*_#`>~]/g, "").trim();
    if (!sentence) return;
    speakQueue = speakQueue.then(() => {
      if (mode !== "speaking" && mode !== "thinking") return;
      setMode("speaking");
      if (!voiceOn || !window.speechSynthesis) {
        // Sin voz: el orbe se mueve igualmente un rato
        return new Promise((r) => {
          const iv = setInterval(() => { level = 0.6 + Math.random() * 0.3; }, 140);
          setTimeout(() => { clearInterval(iv); r(); }, Math.min(5000, 500 + sentence.length * 45));
        });
      }
      return speakOne(sentence);
    });
  }
  function stopSpeech() {
    try { speechSynthesis.cancel(); } catch (e) {}
    keep.clear();
    speakQueue = Promise.resolve();
  }

  // ---------------- Cerebro ----------------
  async function ask(text) {
    text = text.trim();
    if (!text) return;
    showErr("");
    stopWake();
    chatCtl?.abort();
    const ctl = (chatCtl = new AbortController());
    saidEl.textContent = "«" + text + "»";
    replyEl.textContent = "";
    setMode("thinking");
    turns.push({ role: "user", content: text });
    while (turns.length > 12) turns.shift();

    // En iPhone, esperar un poco tras soltar el micrófono hace que la voz salga por el altavoz
    await new Promise((r) => setTimeout(r, isIOS ? 350 : 80));

    let full = "", pending = "";
    try {
      const res = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ messages: turns }),
        signal: ctl.signal,
      });
      if (res.status === 429) throw new Error("Demasiados mensajes seguidos. Espera un minuto.");
      if (!res.ok || !res.body) throw new Error((await res.text().catch(() => "")) || "No he podido conectar con mi cerebro.");
      const reader = res.body.getReader();
      const dec = new TextDecoder();
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        const chunk = dec.decode(value, { stream: true });
        full += chunk;
        pending += chunk;
        replyEl.textContent = full.replace(/\n?\[ERROR\].*/s, "");
        level = Math.min(1, level + chunk.length / 40);
        // Habla frase a frase
        let m;
        while ((m = pending.match(/^([\s\S]*?[.!?…:;])(\s+|$)/)) && m[1].length > 1 && m[2]) {
          queueSpeech(m[1]);
          pending = pending.slice(m[0].length);
        }
      }
      if (full.includes("[ERROR]")) throw new Error(full.split("[ERROR]")[1].trim());
      queueSpeech(pending);
      turns.push({ role: "assistant", content: full.trim() });
      await speakQueue;
    } catch (e) {
      if (ctl.signal.aborted) return;
      turns.pop();
      showErr(e.message || "Algo ha fallado. Vuelve a intentarlo.");
    }
    if (chatCtl === ctl) {
      chatCtl = null;
      afterTurn();
    }
  }

  function afterTurn() {
    if (!active) { setMode("off"); return; }
    setMode("waiting");
    setTimeout(startWake, isIOS ? 400 : 200);
  }

  // ---------------- «Ey Jarvis» (entrada) ----------------
  const WAKE = /\b(?:(?:hey|ey|ei|hei|oye|eh|hola)\s*,?\s+)?(?:j|y|h|ll|ch)?ar(?:v|b)i(?:s|z)\b/;
  function findWake(raw) {
    const txt = raw.toLowerCase().normalize("NFD").replace(/[̀-ͯ]/g, "");
    const plain = raw.normalize("NFD").replace(/[̀-ͯ]/g, "");
    const m = txt.match(WAKE);
    if (!m) return null;
    return { rest: plain.slice(m.index + m[0].length).replace(/^[\s,.:;!?¡¿]+/, "").trim() };
  }

  let rec = null;
  let wantWake = false;
  let cmdTimer = null;
  let restartDelay = 250;

  function stopWake() {
    wantWake = false;
    clearTimeout(cmdTimer);
    if (rec) {
      const r = rec;
      rec = null;
      try { r.abort(); } catch (e) {}
    }
  }

  function startWake(directCommand) {
    if (!Recog || !active) return;
    if (mode === "thinking" || mode === "speaking") return;
    wantWake = true;
    if (rec) {
      if (directCommand) enterCommand();
      return;
    }
    const r = new Recog();
    r.lang = "es-ES";
    r.continuous = true;
    r.interimResults = true;
    r.maxAlternatives = 1;
    rec = r;
    if (directCommand) enterCommand();
    else if (mode !== "listening") setMode("waiting");

    r.onresult = (e) => {
      if (rec !== r) return;
      for (let i = e.resultIndex; i < e.results.length; i++) {
        const res = e.results[i];
        const raw = res[0].transcript;
        level = Math.min(1, level + 0.25);
        const found = findWake(raw);
        if (mode === "waiting") {
          if (!found) continue;
          enterCommand();
          if (found.rest) saidEl.textContent = found.rest;
          if (res.isFinal && found.rest.length > 2) { ask(found.rest); return; }
        } else if (mode === "listening") {
          const rest = found ? found.rest : raw.trim();
          saidEl.textContent = rest;
          armCommandTimer();
          if (res.isFinal && rest.length > 1) { ask(rest); return; }
        }
      }
    };
    r.onspeechstart = () => { level = Math.min(1, level + 0.3); };
    r.onerror = (e) => {
      if (e.error === "not-allowed" || e.error === "service-not-allowed") {
        wantWake = false;
        showErr("No tengo permiso para el micrófono. Actívalo en los ajustes del navegador para esta web y vuelve a abrir Jarvis.");
        setMode("waiting");
      } else if (e.error === "network") {
        restartDelay = 1500;
      } else if (e.error === "audio-capture") {
        showErr("No encuentro el micrófono. ¿Lo está usando otra app?");
        restartDelay = 2000;
      }
    };
    r.onend = () => {
      if (rec === r) rec = null;
      // Los navegadores cortan la escucha cada poco: la reanudamos sola
      if (wantWake && active && (mode === "waiting" || mode === "listening") && !document.hidden) {
        const d = restartDelay;
        restartDelay = 250;
        setTimeout(() => { if (!rec && wantWake) startWake(); }, d);
      }
    };
    try { r.start(); } catch (e) { rec = null; }
  }

  function enterCommand() {
    stopSpeech();
    setMode("listening");
    saidEl.textContent = "";
    replyEl.textContent = "";
    showErr("");
    navigator.vibrate?.(30);
    armCommandTimer();
  }
  function armCommandTimer() {
    clearTimeout(cmdTimer);
    cmdTimer = setTimeout(() => { if (mode === "listening") { setMode("waiting"); saidEl.textContent = ""; } }, 8000);
  }

  // ---------------- Pantalla encendida ----------------
  async function keepAwake() {
    try { wakeLock = await navigator.wakeLock?.request("screen"); } catch (e) {}
  }
  document.addEventListener("visibilitychange", () => {
    if (document.hidden) {
      stopWake();
    } else if (active) {
      keepAwake();
      if (mode === "waiting" || mode === "listening") { setMode("waiting"); startWake(); }
    }
  });

  // ---------------- Controles ----------------
  function paintVoice() {
    $("voiceBtn").textContent = voiceOn ? "🔊 Voz" : "🔇 Voz";
    $("voiceBtn").setAttribute("aria-pressed", String(voiceOn));
  }
  paintVoice();
  $("voiceBtn").onclick = () => {
    voiceOn = !voiceOn;
    try { localStorage.setItem("jarvis-voz", voiceOn ? "on" : "off"); } catch (e) {}
    if (!voiceOn) stopSpeech(); else unlockAudio();
    paintVoice();
  };
  $("helpBtn").onclick = () => { $("help").hidden = false; };
  $("helpClose").onclick = () => { $("help").hidden = true; };

  $("startBtn").onclick = async () => {
    unlockAudio();
    active = true;
    $("start").hidden = true;
    keepAwake();
    if (!Recog) {
      setMode("waiting");
      showErr(isIOS
        ? "Este modo no permite escuchar «Ey Jarvis». Abre la página en Safari (no desde la pantalla de inicio) o escríbele abajo."
        : "Este navegador no reconoce la voz. Usa Chrome, o escríbele abajo.");
      return;
    }
    // Pedimos el permiso del micrófono de forma explícita (algunos móviles lo necesitan)
    try {
      const s = await navigator.mediaDevices?.getUserMedia({ audio: true });
      s?.getTracks().forEach((tr) => tr.stop());
    } catch (e) {
      showErr("Necesito permiso para el micrófono para oír «Ey Jarvis». También puedes escribirle abajo.");
    }
    replyEl.textContent = "Estoy listo. Di «Ey Jarvis» cuando quieras.";
    setMode("waiting");
    startWake();
  };

  $("orb").onclick = () => {
    if (!active) { $("startBtn").click(); return; }
    unlockAudio();
    if (mode === "speaking" || mode === "thinking") {
      chatCtl?.abort();
      chatCtl = null;
      stopSpeech();
      afterTurn();
      return;
    }
    if (Recog) startWake(true);
    else input.focus();
  };

  $("form").addEventListener("submit", (ev) => {
    ev.preventDefault();
    unlockAudio();
    if (!active) { active = true; $("start").hidden = true; keepAwake(); }
    const v = input.value;
    input.value = "";
    input.blur();
    ask(v);
  });

  // ---------------- App instalable ----------------
  if ("serviceWorker" in navigator) {
    window.addEventListener("load", () => navigator.serviceWorker.register("sw.js").catch(() => {}));
  }
  window.__jarvis = { findWake }; // para pruebas
})();
