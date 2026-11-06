// Habilidades de Jarvis: tiempo, temporizadores, alarmas, abrir apps, notas, Wikipedia, cálculos,
// Google Calendar, Gmail y WhatsApp preparado. Todo gratis y sin servidor.
// handle(texto) devuelve {say, actions?} si sabe hacerlo, o null para que responda el cerebro (IA).
(() => {
  "use strict";

  // ---------------- Utilidades de texto ----------------
  // Normaliza sin cambiar la longitud (para poder recortar el texto original en las mismas posiciones)
  const MAP = { á: "a", à: "a", ä: "a", â: "a", é: "e", è: "e", ë: "e", ê: "e", í: "i", ì: "i", ï: "i", î: "i",
    ó: "o", ò: "o", ö: "o", ô: "o", ú: "u", ù: "u", ü: "u", û: "u", ñ: "n", ç: "c" };
  const norm = (s) => s.toLowerCase().replace(/[áàäâéèëêíìïîóòöôúùüûñç]/g, (c) => MAP[c]);
  const cap = (s) => s.charAt(0).toUpperCase() + s.slice(1);
  const store = {
    get(k, d) { try { const v = localStorage.getItem(k); return v == null ? d : JSON.parse(v); } catch (e) { return d; } },
    set(k, v) { try { localStorage.setItem(k, JSON.stringify(v)); } catch (e) {} },
  };

  const NUMS = { un: 1, uno: 1, una: 1, dos: 2, tres: 3, cuatro: 4, cinco: 5, seis: 6, siete: 7, ocho: 8, nueve: 9,
    diez: 10, once: 11, doce: 12, trece: 13, catorce: 14, quince: 15, dieciseis: 16, diecisiete: 17, dieciocho: 18,
    diecinueve: 19, veinte: 20, veinticinco: 25, treinta: 30, cuarenta: 40, cincuenta: 50, sesenta: 60, noventa: 90, cien: 100 };
  const toNum = (w) => (w == null ? NaN : /^\d+([.,]\d+)?$/.test(w) ? parseFloat(w.replace(",", ".")) : NUMS[w] ?? NaN);
  const NUMW = "(\\d+(?:[.,]\\d+)?|un|uno|una|dos|tres|cuatro|cinco|seis|siete|ocho|nueve|diez|once|doce|trece|catorce|quince|dieciseis|diecisiete|dieciocho|diecinueve|veinte|veinticinco|treinta|cuarenta|cincuenta|sesenta|noventa|cien)";

  // Hora hablada: "las 5 y media de la tarde"
  function sayTime(d) {
    const h = d.getHours(), m = d.getMinutes();
    const h12 = h % 12 === 0 ? 12 : h % 12;
    const art = h12 === 1 ? "la 1" : `las ${h12}`;
    const mins = m === 0 ? "" : m === 15 ? " y cuarto" : m === 30 ? " y media" : m === 45 ? " menos cuarto" : ` y ${m}`;
    const shown = m === 45 ? (h12 % 12) + 1 : h12;
    const art2 = m === 45 ? (shown === 1 ? "la 1" : `las ${shown}`) : art;
    const part = h < 6 ? "de la madrugada" : h < 13 ? "de la mañana" : h < 21 ? "de la tarde" : "de la noche";
    return `${art2}${mins} ${h === 12 && m === 0 ? "del mediodía" : part}`;
  }
  const DAYS = ["domingo", "lunes", "martes", "miércoles", "jueves", "viernes", "sábado"];
  const MONTHS = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"];
  const sayDay = (d) => {
    const today = new Date(); today.setHours(0, 0, 0, 0);
    const x = new Date(d); x.setHours(0, 0, 0, 0);
    const diff = Math.round((x - today) / 86400000);
    if (diff === 0) return "hoy";
    if (diff === 1) return "mañana";
    if (diff === 2) return "pasado mañana";
    return `el ${DAYS[d.getDay()]} ${d.getDate()} de ${MONTHS[d.getMonth()]}`;
  };

  // ---------------- Fechas y horas habladas ----------------
  // Devuelve {date, hasTime, spans:[[i,j],...]} con las partes del texto que eran fecha/hora
  function parseWhen(n, { defaultPM = true } = {}) {
    const spans = [];
    const mark = (m, offset = 0) => { if (m) spans.push([m.index + offset, m.index + offset + m[0].length]); };
    const base = new Date();
    let day = null, ampm = null, h = null, min = 0;

    let m = n.match(/\b(de la|por la) (manana|tarde|noche|madrugada)\b/);
    if (m) { ampm = m[2]; mark(m); }
    const n2 = m ? n.slice(0, m.index) + " ".repeat(m[0].length) + n.slice(m.index + m[0].length) : n;

    if ((m = n2.match(/\bpasado manana\b/))) { day = 2; mark(m); }
    else if ((m = n2.match(/\bmanana\b/))) { day = 1; mark(m); }
    else if ((m = n2.match(/\bhoy\b|\besta (tarde|noche|manana)\b/))) { day = 0; mark(m); if (m[1]) ampm = m[1]; }
    const wd = ["domingo", "lunes", "martes", "miercoles", "jueves", "viernes", "sabado"];
    if (day == null && (m = n2.match(/\b(?:el |este |el proximo |el que viene )?(domingo|lunes|martes|miercoles|jueves|viernes|sabado)\b/))) {
      const target = wd.indexOf(m[1]);
      let diff = (target - base.getDay() + 7) % 7;
      if (diff === 0) diff = 7;
      day = diff; mark(m);
    }
    let explicitDate = null;
    if (day == null && (m = n2.match(/\bel (\d{1,2})(?: de (enero|febrero|marzo|abril|mayo|junio|julio|agosto|septiembre|octubre|noviembre|diciembre))?\b/))) {
      const dd = parseInt(m[1], 10);
      const mo = m[2] ? MONTHS.indexOf(m[2]) : base.getMonth();
      explicitDate = new Date(base.getFullYear(), mo, dd);
      if (explicitDate < new Date(base.getFullYear(), base.getMonth(), base.getDate())) {
        if (m[2]) explicitDate.setFullYear(base.getFullYear() + 1); else explicitDate.setMonth(mo + 1);
      }
      mark(m);
    }

    if ((m = n2.match(/\ba(?:l)? mediodia\b/))) { h = 12; min = 0; mark(m); }
    else if ((m = n2.match(new RegExp("\\ba (?:las|la) " + NUMW + "(?:(?:[:.h]| y )(\\d{1,2}))?( y media| y cuarto| menos cuarto| en punto)?(?: ?(am|pm|a\\.m\\.|p\\.m\\.))?\\b")))) {
      h = toNum(m[1]);
      if (m[2]) min = parseInt(m[2], 10);
      if (m[3] === " y media") min = 30;
      if (m[3] === " y cuarto") min = 15;
      if (m[3] === " menos cuarto") { min = 45; h -= 1; }
      if (m[4]) ampm = /p/.test(m[4]) ? "tarde" : "manana";
      mark(m);
    }
    if (h != null && !isNaN(h)) {
      if ((ampm === "tarde" || ampm === "noche") && h < 12) h += 12;
      else if (ampm === "madrugada" && h === 12) h = 0;
      else if (!ampm && defaultPM && h >= 1 && h <= 7) h += 12;
    } else h = null;

    let date = explicitDate || new Date(base);
    if (!explicitDate && day != null) date.setDate(base.getDate() + day);
    date.setSeconds(0, 0);
    if (h != null) date.setHours(h, min);
    return { date, hasTime: h != null, hasDay: day != null || !!explicitDate, spans };
  }

  function cutSpans(original, spans) {
    const keep = original.split("");
    for (const [a, b] of spans) for (let i = a; i < b; i++) keep[i] = " ";
    return keep.join("").replace(/\s+/g, " ").trim();
  }

  // ---------------- Duraciones ----------------
  function parseDuration(n) {
    let secs = 0, found = false;
    const re = new RegExp(NUMW + "\\s*(horas?|h|minutos?|min|mins|segundos?|seg|s)\\b", "g");
    let m;
    while ((m = re.exec(n))) {
      const v = toNum(m[1]);
      if (isNaN(v)) continue;
      found = true;
      secs += /^h/.test(m[2]) ? v * 3600 : /^m/.test(m[2]) ? v * 60 : v;
    }
    if (/\bmedia hora\b/.test(n)) { secs += 1800; found = true; }
    if (/\by media\b/.test(n) && /hora/.test(n)) secs += 1800;
    if (/\bun cuarto de hora\b/.test(n)) { secs += 900; found = true; }
    return found ? Math.round(secs) : null;
  }
  const sayDuration = (s) => {
    const h = Math.floor(s / 3600), m = Math.floor((s % 3600) / 60), sec = s % 60;
    const parts = [];
    if (h) parts.push(`${h} ${h === 1 ? "hora" : "horas"}`);
    if (m) parts.push(`${m} ${m === 1 ? "minuto" : "minutos"}`);
    if (sec && !h) parts.push(`${sec} ${sec === 1 ? "segundo" : "segundos"}`);
    return parts.join(" y ") || "0 segundos";
  };

  // ---------------- Avisos (temporizadores y alarmas) ----------------
  let announce = (text) => {};       // la app lo sustituye para hablar
  let ringing = null;
  let audioCtx = null;
  function ring(text) {
    stopRing();
    try {
      audioCtx = audioCtx || new (window.AudioContext || window.webkitAudioContext)();
      audioCtx.resume?.();
    } catch (e) {}
    let n = 0;
    const beep = () => {
      if (!audioCtx) return;
      const t0 = audioCtx.currentTime;
      [0, 0.25, 0.5].forEach((dt) => {
        const o = audioCtx.createOscillator(), g = audioCtx.createGain();
        o.type = "sine"; o.frequency.value = 880;
        g.gain.setValueAtTime(0.0001, t0 + dt);
        g.gain.exponentialRampToValueAtTime(0.4, t0 + dt + 0.02);
        g.gain.exponentialRampToValueAtTime(0.0001, t0 + dt + 0.2);
        o.connect(g).connect(audioCtx.destination);
        o.start(t0 + dt); o.stop(t0 + dt + 0.22);
      });
      navigator.vibrate?.([300, 150, 300]);
      if (++n > 40) stopRing();
    };
    beep();
    ringing = setInterval(beep, 1500);
    try {
      if (Notification?.permission === "granted") navigator.serviceWorker?.ready.then((r) => r.showNotification("Jarvis", { body: text, tag: "jarvis-alarm", renotify: true }));
    } catch (e) {}
    announce(text + " Di «Ey Jarvis, para» o toca el orbe para pararla.", { ringing: true });
  }
  function stopRing() {
    if (ringing) { clearInterval(ringing); ringing = null; navigator.vibrate?.(0); return true; }
    return false;
  }
  function askNotify() {
    try { if (window.Notification && Notification.permission === "default") Notification.requestPermission(); } catch (e) {}
  }

  // Temporizadores y alarmas guardados (se recuperan si recargas la app)
  let timers = store.get("jarvis-timers", []).filter((t) => t.at > Date.now() - 60000);
  const handles = new Map();
  function scheduleAll() {
    for (const t of timers) {
      if (handles.has(t.id)) continue;
      const ms = Math.max(0, t.at - Date.now());
      handles.set(t.id, setTimeout(() => fire(t.id), ms));
    }
    store.set("jarvis-timers", timers);
  }
  function fire(id) {
    const t = timers.find((x) => x.id === id);
    timers = timers.filter((x) => x.id !== id);
    handles.delete(id);
    store.set("jarvis-timers", timers);
    if (t) ring(t.kind === "alarm" ? `¡Son ${sayTime(new Date(t.at))}! ${t.label ? "Alarma: " + t.label + "." : "Tu alarma."}` : `¡Tiempo! Ha terminado el temporizador${t.label ? " de " + t.label : ""}.`);
  }
  function cancelTimers(kind) {
    const gone = timers.filter((t) => !kind || t.kind === kind);
    gone.forEach((t) => { clearTimeout(handles.get(t.id)); handles.delete(t.id); });
    timers = timers.filter((t) => kind && t.kind !== kind);
    store.set("jarvis-timers", timers);
    return gone.length;
  }
  scheduleAll();

  // ---------------- Cálculos ----------------
  function calcExpr(n) {
    let e = " " + n + " ";
    e = e.replace(/\b(cuanto|cuanta)s? (es|son|da|sale|seria)\b|\bcalcula(me)?\b|\bcuanto\b|\bresultado de\b|\bdime\b|\?|¿|=/g, " ");
    e = e.replace(/(\d),(\d)/g, "$1.$2");
    e = e.replace(new RegExp(NUMW + " por ciento de " + NUMW, "g"), (_, a, b) => `(${toNum(a)}/100*${toNum(b)})`);
    e = e.replace(/raiz cuadrada de|raiz de/g, " r ");
    e = e.replace(/\bal cuadrado\b/g, "^2").replace(/\bal cubo\b/g, "^3").replace(/elevado a( la)?/g, "^");
    e = e.replace(/multiplicado por|\bpor\b|\bx\b|×/g, "*").replace(/dividido (entre|por)|\bentre\b|÷/g, "/");
    e = e.replace(/\bmas\b/g, "+").replace(/\bmenos\b/g, "-");
    e = e.replace(new RegExp("\\b" + NUMW + "\\b", "g"), (w) => (isNaN(toNum(w)) ? w : String(toNum(w))));
    e = e.replace(/\s+/g, "");
    if (!/\d/.test(e) || !/^[\d.+\-*/^()r]+$/.test(e) || !/[+\-*/^r]/.test(e)) return null;
    // Analizador sencillo (sin eval)
    let i = 0;
    const peek = () => e[i];
    const num = () => { const m = e.slice(i).match(/^\d+(\.\d+)?/); if (!m) throw 0; i += m[0].length; return parseFloat(m[0]); };
    const factor = () => {
      if (peek() === "-") { i++; return -factor(); }
      if (peek() === "+") { i++; return factor(); }
      if (peek() === "r") { i++; return Math.sqrt(factor()); }
      let v;
      if (peek() === "(") { i++; v = expr(); if (peek() !== ")") throw 0; i++; } else v = num();
      if (peek() === "^") { i++; v = Math.pow(v, factor()); }
      return v;
    };
    const term = () => { let v = factor(); while (peek() === "*" || peek() === "/") { const o = e[i++]; const w = factor(); v = o === "*" ? v * w : v / w; } return v; };
    const expr = () => { let v = term(); while (peek() === "+" || peek() === "-") { const o = e[i++]; const w = term(); v = o === "+" ? v + w : v - w; } return v; };
    try {
      const v = expr();
      if (i !== e.length || !isFinite(v)) return null;
      return v;
    } catch (x) { return null; }
  }
  const sayNum = (v) => (Math.round(v * 1000) / 1000).toLocaleString("es-ES", { maximumFractionDigits: 3 });

  // ---------------- Tiempo (Open-Meteo, gratis y sin clave) ----------------
  const WMO = (c) => c === 0 ? "despejado" : c <= 2 ? "con algunas nubes" : c === 3 ? "nublado" : c <= 48 ? "con niebla"
    : c <= 57 ? "con llovizna" : c <= 67 ? "con lluvia" : c <= 77 ? "con nieve" : c <= 82 ? "con chubascos"
    : c <= 86 ? "con chubascos de nieve" : "con tormenta";
  async function geocode(name) {
    const r = await fetch(`https://geocoding-api.open-meteo.com/v1/search?name=${encodeURIComponent(name)}&count=1&language=es&format=json`);
    const j = await r.json();
    const g = j.results?.[0];
    return g ? { lat: g.latitude, lon: g.longitude, name: g.name } : null;
  }
  function myPosition() {
    return new Promise((res) => {
      if (!navigator.geolocation) return res(null);
      navigator.geolocation.getCurrentPosition((p) => res({ lat: p.coords.latitude, lon: p.coords.longitude, name: "" }), () => res(null), { timeout: 8000, maximumAge: 3600000 });
    });
  }
  async function weather(n, original) {
    let place = null;
    const m = original.match(/\b(?:en|para|de)\s+([A-ZÁÉÍÓÚÑa-záéíóúñ][\wáéíóúñ .-]{1,40}?)(?:\s+(?:hoy|mañana|manana|pasado|esta|este|el)\b|[?¿!.,]|$)/i);
    const city = m && !/^(la|el|hoy|mañana|manana|esta|este|semana|fin)$/i.test(m[1].trim()) ? m[1].trim() : null;
    if (city) place = await geocode(city);
    if (!place) {
      const def = store.get("jarvis-city", "");
      if (def && !city) place = await geocode(def);
    }
    if (!place && !city) place = await myPosition();
    if (!place) return { say: city ? `No encuentro ${city}. Prueba con el nombre de la ciudad.` : "No sé dónde estás. Dime la ciudad, por ejemplo: «qué tiempo hace en Madrid», o ponla en Ayuda." };

    const r = await fetch(`https://api.open-meteo.com/v1/forecast?latitude=${place.lat}&longitude=${place.lon}&current=temperature_2m,weather_code&daily=weather_code,temperature_2m_max,temperature_2m_min,precipitation_probability_max&timezone=auto&forecast_days=3`);
    const w = await r.json();
    const where = place.name ? ` en ${place.name}` : "";
    const idx = /pasado manana/.test(n) ? 2 : /\bmanana\b/.test(n) && !/de la manana/.test(n) ? 1 : 0;
    const d = w.daily;
    const rain = d.precipitation_probability_max?.[idx];
    const rainTxt = rain == null ? "" : rain >= 60 ? ` Probabilidad de lluvia alta, del ${rain}%: coge paraguas.` : rain >= 25 ? ` Puede llover, un ${rain}% de probabilidad.` : " No se espera lluvia.";
    if (idx === 0) {
      return { say: `Ahora mismo${where} hace ${Math.round(w.current.temperature_2m)} grados y está ${WMO(w.current.weather_code)}. Hoy, máxima de ${Math.round(d.temperature_2m_max[0])} y mínima de ${Math.round(d.temperature_2m_min[0])}.${rainTxt}` };
    }
    return { say: `${idx === 1 ? "Mañana" : "Pasado mañana"}${where} estará ${WMO(d.weather_code[idx])}, con máxima de ${Math.round(d.temperature_2m_max[idx])} y mínima de ${Math.round(d.temperature_2m_min[idx])} grados.${rainTxt}` };
  }

  // ---------------- Wikipedia ----------------
  async function wikipedia(query) {
    const s = await fetch(`https://es.wikipedia.org/w/api.php?action=query&list=search&srsearch=${encodeURIComponent(query)}&srlimit=1&format=json&origin=*`).then((r) => r.json());
    const title = s.query?.search?.[0]?.title;
    if (!title) return null;
    const p = await fetch(`https://es.wikipedia.org/api/rest_v1/page/summary/${encodeURIComponent(title)}`).then((r) => r.json());
    if (!p.extract) return null;
    const sentences = p.extract.replace(/\s*\([^)]*\)/g, "").match(/[^.!?]+[.!?]+/g) || [p.extract];
    return { say: sentences.slice(0, 2).join(" ").replace(/\s+/g, " ").trim(), actions: [{ label: "Leer en Wikipedia", href: p.content_urls?.mobile?.page || `https://es.wikipedia.org/wiki/${encodeURIComponent(title)}` }] };
  }

  // ---------------- Contactos guardados (para WhatsApp y llamadas) ----------------
  function contacts() {
    const txt = store.get("jarvis-contacts", "");
    const out = {};
    for (const line of String(txt).split(/\n/)) {
      const m = line.match(/^\s*([^:=]+?)\s*[:=]\s*([+\d][\d\s-]{5,})\s*$/);
      if (m) out[norm(m[1]).trim()] = m[2].replace(/[\s-]/g, "").replace(/^00/, "+");
    }
    return out;
  }
  function findContact(name) {
    const c = contacts(), k = norm(name).trim();
    if (c[k]) return { name: cap(name.trim()), phone: c[k] };
    const hit = Object.keys(c).find((x) => x.split(" ")[0] === k.split(" ")[0]);
    return hit ? { name: cap(hit), phone: c[hit] } : null;
  }
  const waPhone = (p) => p.replace(/^\+/, "").replace(/^(?=[67]\d{8}$)/, "34");

  // ---------------- Google (Calendar y Gmail) ----------------
  const G_SCOPES = "https://www.googleapis.com/auth/calendar.events https://www.googleapis.com/auth/gmail.readonly";
  let gisLoaded = null;
  let tokenClient = null;
  let pendingRetry = null; // orden que se repite al reconectar
  function loadGIS() {
    if (gisLoaded) return gisLoaded;
    gisLoaded = new Promise((res, rej) => {
      const s = document.createElement("script");
      s.src = "https://accounts.google.com/gsi/client";
      s.onload = res;
      s.onerror = () => { gisLoaded = null; rej(new Error("No puedo cargar Google.")); };
      document.head.appendChild(s);
    });
    return gisLoaded;
  }
  const gToken = () => {
    const t = store.get("jarvis-gtoken", null);
    return t && t.exp > Date.now() + 60000 ? t.token : null;
  };
  const gClientId = () => store.get("jarvis-gclient", "");
  // Debe llamarse desde un toque del usuario (abre la ventana de Google)
  async function googleConnect() {
    const id = gClientId();
    if (!id) throw new Error("Primero pega tu ID de cliente de Google en Ayuda.");
    await loadGIS();
    return new Promise((res, rej) => {
      tokenClient = google.accounts.oauth2.initTokenClient({
        client_id: id,
        scope: G_SCOPES,
        callback: (r) => {
          if (r.error) return rej(new Error("Google no ha dado permiso."));
          store.set("jarvis-gtoken", { token: r.access_token, exp: Date.now() + (r.expires_in || 3600) * 1000 });
          store.set("jarvis-gconnected", true);
          res(r.access_token);
        },
        error_callback: () => rej(new Error("Se cerró la ventana de Google.")),
      });
      tokenClient.requestAccessToken({ prompt: store.get("jarvis-gconnected", false) ? "" : "consent" });
    });
  }
  class NeedGoogle extends Error {}
  async function gfetch(url, opts = {}) {
    const token = gToken();
    if (!token) throw new NeedGoogle();
    const r = await fetch(url, { ...opts, headers: { ...(opts.headers || {}), Authorization: `Bearer ${token}`, "Content-Type": "application/json" } });
    if (r.status === 401) { store.set("jarvis-gtoken", null); throw new NeedGoogle(); }
    if (r.status === 403) throw new Error("Google no me deja: revisa que activaste la API de Gmail y la de Calendar en tu proyecto.");
    if (!r.ok) throw new Error("Google ha dado un error. Prueba otra vez.");
    return r.json();
  }
  function needGoogleAnswer(retryText) {
    pendingRetry = retryText;
    if (!gClientId()) {
      return { say: "Para eso necesito conectarme a tu cuenta de Google. Abre Ayuda y sigue los pasos de «Conectar Google». Solo hay que hacerlo una vez.", actions: [{ label: "Abrir Ayuda", run: "help" }] };
    }
    return { say: "Necesito que me des permiso en Google. Toca el botón «Conectar Google» y lo hago enseguida.", actions: [{ label: "Conectar Google", run: "google" }] };
  }

  async function calendarDay(n) {
    const w = parseWhen(n);
    let start = new Date(w.date); start.setHours(0, 0, 0, 0);
    let end = new Date(start);
    let label;
    if (/esta semana|la semana/.test(n)) { end.setDate(end.getDate() + 7); label = "esta semana"; }
    else { end.setDate(end.getDate() + 1); label = sayDay(start); }
    const tz = Intl.DateTimeFormat().resolvedOptions().timeZone;
    const j = await gfetch(`https://www.googleapis.com/calendar/v3/calendars/primary/events?singleEvents=true&orderBy=startTime&maxResults=15&timeZone=${encodeURIComponent(tz)}&timeMin=${start.toISOString()}&timeMax=${end.toISOString()}`);
    const items = (j.items || []).filter((e) => e.status !== "cancelled");
    if (!items.length) return { say: `No tienes nada en el calendario ${label}. Día libre.`, actions: [{ label: "Abrir Calendar", href: "https://calendar.google.com/" }] };
    const parts = items.slice(0, 6).map((e) => {
      const t = e.start.dateTime ? new Date(e.start.dateTime) : null;
      const when = t ? (label === "esta semana" ? `${DAYS[t.getDay()]} a ${sayTime(t)}` : `a ${sayTime(t)}`) : "todo el día";
      return `${when}, ${e.summary || "un evento sin título"}`;
    });
    const more = items.length > 6 ? ` Y ${items.length - 6} más.` : "";
    return {
      say: `${cap(label)} tienes ${items.length === 1 ? "una cosa" : items.length + " cosas"}: ${parts.join("; ")}.${more}`,
      actions: [{ label: "Abrir Calendar", href: "https://calendar.google.com/" }],
    };
  }

  async function calendarAdd(text, n) {
    const w = parseWhen(n);
    if (!w.hasTime && !w.hasDay) return { say: "¿Para cuándo? Dímelo así: «mañana a las 5 tengo dentista, ponlo en el calendario»." };
    const removers = [
      /\b(ey |hey |oye )?jarvis\b/g, /\b(ponlo|apuntalo|anotalo|guardalo|agendalo|metelo)\b/g,
      /\b(pon|apunta|anota|anade|agrega|crea|mete|guarda|agenda|recuerdame|recuerda)\b/g,
      /\b(en|a) (el |mi )?(calendario|agenda|google calendar)\b/g, /\b(un|una) (evento|cita|recordatorio)( de| para)?\b/g,
      /\b(tengo|hay|voy a tener)( que)?\b/g, /\bque\b/g, /\bpor favor\b/g,
    ];
    const spans = [...w.spans];
    for (const re of removers) { let m; re.lastIndex = 0; while ((m = re.exec(n))) spans.push([m.index, m.index + m[0].length]); }
    let title = cutSpans(text, spans).replace(/^[\s,.:;y]+|[\s,.:;y]+$/g, "").replace(/^(de|para|con|el|la|una?|y)\s+/i, "");
    if (!title) title = "Evento";
    title = cap(title);

    const tz = Intl.DateTimeFormat().resolvedOptions().timeZone;
    let body;
    if (w.hasTime) {
      const end = new Date(w.date.getTime() + 60 * 60000);
      body = { summary: title, start: { dateTime: w.date.toISOString(), timeZone: tz }, end: { dateTime: end.toISOString(), timeZone: tz } };
    } else {
      const ymd = (d) => `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`;
      const next = new Date(w.date); next.setDate(next.getDate() + 1);
      body = { summary: title, start: { date: ymd(w.date) }, end: { date: ymd(next) } };
    }
    const ev = await gfetch("https://www.googleapis.com/calendar/v3/calendars/primary/events", { method: "POST", body: JSON.stringify(body) });
    return {
      say: `Hecho. He puesto «${title}» ${sayDay(w.date)}${w.hasTime ? " a " + sayTime(w.date) : ", todo el día"}.`,
      actions: ev.htmlLink ? [{ label: "Ver en Calendar", href: ev.htmlLink }] : [],
    };
  }

  async function gmailUnread(prefix = "") {
    const j = await gfetch("https://gmail.googleapis.com/gmail/v1/users/me/messages?q=" + encodeURIComponent("is:unread in:inbox category:primary") + "&maxResults=10");
    const ids = (j.messages || []).map((m) => m.id);
    const total = j.resultSizeEstimate || ids.length;
    if (!ids.length) return { say: `${prefix}No tienes correos nuevos sin leer. Todo al día.`, actions: [{ label: "Abrir Gmail", href: "https://mail.google.com/" }] };
    const metas = await Promise.all(ids.slice(0, 3).map((id) =>
      gfetch(`https://gmail.googleapis.com/gmail/v1/users/me/messages/${id}?format=metadata&metadataHeaders=From&metadataHeaders=Subject`)));
    const lines = metas.map((mm) => {
      const hs = mm.payload?.headers || [];
      const from = (hs.find((h) => h.name === "From")?.value || "alguien").replace(/<.*>/, "").replace(/"/g, "").trim();
      const subj = (hs.find((h) => h.name === "Subject")?.value || "sin asunto").trim();
      return `de ${from}: ${subj}`;
    });
    const n = total > 10 ? "más de 10" : String(total);
    return {
      say: `${prefix}Tienes ${n} ${total === 1 ? "correo sin leer" : "correos sin leer"}. ${total > 1 ? "Los últimos: " : ""}${lines.join("; ")}.`,
      actions: [{ label: "Abrir Gmail", href: "https://mail.google.com/" }],
    };
  }

  // ---------------- Abrir apps ----------------
  const APPS = {
    whatsapp: "https://wa.me/", youtube: "https://www.youtube.com/", spotify: "https://open.spotify.com/",
    instagram: "https://www.instagram.com/", tiktok: "https://www.tiktok.com/", gmail: "https://mail.google.com/",
    correo: "https://mail.google.com/", calendario: "https://calendar.google.com/", "google maps": "https://maps.google.com/",
    maps: "https://maps.google.com/", mapas: "https://maps.google.com/", twitter: "https://x.com/", x: "https://x.com/",
    facebook: "https://www.facebook.com/", netflix: "https://www.netflix.com/", amazon: "https://www.amazon.es/",
    telegram: "https://t.me/", google: "https://www.google.com/", drive: "https://drive.google.com/", fotos: "https://photos.google.com/",
    twitch: "https://www.twitch.tv/", "prime video": "https://www.primevideo.com/", wallapop: "https://es.wallapop.com/",
  };
  const APP_ALIASES = { guasap: "whatsapp", wasap: "whatsapp", watsap: "whatsapp", wasa: "whatsapp", "whats app": "whatsapp", yutub: "youtube", insta: "instagram", "tik tok": "tiktok", "el correo": "correo", "el calendario": "calendario" };

  // ---------------- Notas ----------------
  const notes = () => store.get("jarvis-notes", []);
  const saveNotes = (a) => store.set("jarvis-notes", a);

  // ---------------- El enrutador ----------------
  async function handle(text) {
    const original = text.trim();
    const n = norm(original).replace(/[¿?¡!]/g, " ").replace(/\s+/g, " ").trim();
    let m;

    // Parar alarma
    if (/^(para|parar|basta|stop|silencio|callate|calla|vale|ya|apagala|apaga(la| la alarma| el temporizador| la alarma)?)$/.test(n) || (ringing && /\b(para|basta|apaga|vale|ok)\b/.test(n))) {
      if (stopRing()) return { say: "Alarma parada." };
      if (/^(para|parar|basta|stop|silencio|callate|calla)$/.test(n)) return { say: "Vale." };
    }

    // Hora y fecha
    if (/\b(que hora es|que horas son|dime la hora|hora es)\b/.test(n)) {
      const d = new Date();
      return { say: `Son ${sayTime(d)}.`.replace("Son la 1", "Es la 1") };
    }
    if (/\b(que dia es|a que (dia )?estamos|que fecha es|fecha de hoy|dia es hoy)\b/.test(n)) {
      const d = new Date();
      return { say: `Hoy es ${DAYS[d.getDay()]}, ${d.getDate()} de ${MONTHS[d.getMonth()]} de ${d.getFullYear()}.` };
    }

    // Temporizadores
    if (/\b(temporizador|cuenta atras|timer)\b/.test(n) || /\bavisame (en|dentro de)\b/.test(n)) {
      if (/\b(cancela|quita|borra|para|elimina)\b/.test(n)) {
        const c = cancelTimers("timer");
        return { say: c ? "Temporizador cancelado." : "No tienes temporizadores puestos." };
      }
      if (/\bcuanto (queda|falta)\b/.test(n)) {
        const t = timers.filter((x) => x.kind === "timer").sort((a, b) => a.at - b.at)[0];
        return { say: t ? `Quedan ${sayDuration(Math.max(1, Math.round((t.at - Date.now()) / 1000)))}.` : "No tienes temporizadores puestos." };
      }
      const secs = parseDuration(n);
      if (!secs) return { say: "¿De cuánto lo pongo? Por ejemplo: «pon un temporizador de 10 minutos»." };
      const lm = original.match(/\bpara (?:el |la |los |las )?(.+)$/i);
      const label = lm && !/\d/.test(lm[1]) ? lm[1].replace(/[.?!]+$/, "") : "";
      timers.push({ id: Date.now() + Math.random(), kind: "timer", at: Date.now() + secs * 1000, label });
      scheduleAll();
      askNotify();
      return { say: `Temporizador de ${sayDuration(secs)} en marcha. Deja la app abierta y te aviso.` };
    }
    if (/\bcuanto (queda|falta)\b/.test(n) && timers.length) {
      const t = timers.slice().sort((a, b) => a.at - b.at)[0];
      return { say: `Quedan ${sayDuration(Math.max(1, Math.round((t.at - Date.now()) / 1000)))}.` };
    }

    // Alarmas
    if (/\b(alarmas?|despiertame|despertador)\b/.test(n)) {
      if (/\b(cancela|quita|borra|elimina|desactiva)\b/.test(n)) {
        const c = cancelTimers("alarm");
        return { say: c ? (c === 1 ? "Alarma cancelada." : `${c} alarmas canceladas.`) : "No tienes alarmas puestas." };
      }
      if (/\b(que|cuales|tengo) alarmas?\b/.test(n) && !/\ba las\b/.test(n)) {
        const a = timers.filter((x) => x.kind === "alarm");
        return { say: a.length ? `Tienes ${a.length === 1 ? "una alarma" : a.length + " alarmas"}: ${a.map((x) => sayDay(new Date(x.at)) + " a " + sayTime(new Date(x.at))).join(", ")}.` : "No tienes alarmas puestas." };
      }
      const dur = /\b(en|dentro de)\b/.test(n) ? parseDuration(n) : null;
      let at;
      if (dur) at = new Date(Date.now() + dur * 1000);
      else {
        const w = parseWhen(n, { defaultPM: false });
        if (!w.hasTime) return { say: "¿A qué hora? Por ejemplo: «pon una alarma a las 7 y media»." };
        at = w.date;
        if (!w.hasDay && at <= new Date()) at.setDate(at.getDate() + 1);
      }
      timers.push({ id: Date.now() + Math.random(), kind: "alarm", at: at.getTime(), label: "" });
      scheduleAll();
      askNotify();
      return { say: `Alarma puesta para ${sayDay(at)} a ${sayTime(at)}. Deja la app abierta con la pantalla encendida y te despierto.` };
    }

    // WhatsApp: «tengo mensajes de WhatsApp» (no se puede leer)
    const isWA = /\b(whatsapp|whats app|guasap|wasap|watsap|wasa|wassap|whatsap)\b/.test(n);
    if (isWA && /\b(tengo|hay|lee|leeme|mira)\b/.test(n) && /\bmensajes?\b/.test(n) && !/\b(manda|envia|escribe|dile)\b/.test(n)) {
      let mail = null;
      try { mail = await gmailUnread("Por cierto, en el correo: "); } catch (e) {}
      return {
        say: "WhatsApp no deja que ninguna aplicación lea tus mensajes, así que esos tienes que mirarlos tú. " + (mail ? mail.say : ""),
        actions: [{ label: "Abrir WhatsApp", href: "https://wa.me/" }, ...(mail?.actions || [])],
      };
    }
    // Abrir WhatsApp sin mensaje
    if (isWA && /^(abre|abreme|abrir|entra en|ve a)\b/.test(n) && !/\b(manda|envia|escribe|dile|mensaje)\b/.test(n)) {
      return { say: "Toca el botón para abrir WhatsApp.", actions: [{ label: "Abrir WhatsApp", href: "https://wa.me/", primary: true }] };
    }
    // WhatsApp: preparar mensaje
    if (isWA || /^(manda|envia|escribe)(le)? (un )?mensaje\b/.test(n) || /^dile a\b/.test(n)) {
      m = original.match(/\b(?:a|para)\s+([A-ZÁÉÍÓÚÑa-záéíóúñ]+(?:\s+[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+)?)\s*(?:,|:)?\s*(?:diciendo(?:le)?|que diga|diciendole|y dile|dile|que|:)\s+(.+)$/i)
        || original.match(/^dile a\s+([A-ZÁÉÍÓÚÑa-záéíóúñ]+)\s+(?:que\s+)?(.+)$/i);
      let name = m ? m[1] : null;
      let msg = m ? m[2].replace(/[.]+$/, "") : null;
      if (!msg) {
        const m2 = original.match(/\b(?:diciendo|que diga|dile|que)\s+(.+)$/i);
        msg = m2 ? m2[1] : "";
        const m3 = original.match(/\b(?:a|para)\s+([A-ZÁÉÍÓÚÑa-záéíóúñ]+)\b/i);
        if (m3 && !/^(whatsapp|guasap|wasap)$/i.test(m3[1])) name = m3[1];
      }
      if (name && /^(whatsapp|guasap|wasap|watsap)$/i.test(name)) name = null;
      const contact = name ? findContact(name) : null;
      const txt = msg ? cap(msg.trim()) : "";
      const href = contact ? `https://wa.me/${waPhone(contact.phone)}${txt ? "?text=" + encodeURIComponent(txt) : ""}` : `https://wa.me/${txt ? "?text=" + encodeURIComponent(txt) : ""}`;
      const who = contact ? `para ${contact.name}` : name ? `para ${cap(name)} (no lo tengo en tus contactos de Jarvis, elígelo en WhatsApp)` : "";
      return {
        say: `Mensaje preparado ${who}${txt ? ": «" + txt + "»" : ""}. Toca «Enviar por WhatsApp» para mandarlo.`.replace("  ", " "),
        actions: [{ label: "Enviar por WhatsApp", href, primary: true }],
      };
    }

    // Llamar
    if ((m = original.match(/^\s*(?:llama|llamar|llamame a|marca)\s+(?:a\s+)?(.+?)[.?!]*$/i))) {
      const c = findContact(m[1]);
      if (c) return { say: `Llamando a ${c.name}. Toca el botón para llamar.`, actions: [{ label: `Llamar a ${c.name}`, href: `tel:${c.phone}`, primary: true }] };
      return { say: `No tengo el número de ${cap(m[1])}. Puedes añadirlo en Ayuda, en «Contactos».`, actions: [{ label: "Abrir teléfono", href: "tel:" }] };
    }

    // Correo (Gmail): «tengo mensajes / correos»
    if (/\b(tengo|hay|me han llegado|alguno|algun)\b.*\b(mensajes?|correos?|emails?|e-mails?|mails?)\b|\b(lee|leeme|mira|revisa)\b.*\b(correo|correos|emails?|mails?|gmail|bandeja)\b|\bcorreo nuevo\b/.test(n)) {
      try { return await gmailUnread(); } catch (e) { if (e instanceof NeedGoogle) return needGoogleAnswer(original); throw e; }
    }

    // Calendario: añadir
    const timeExpr = /\ba (las|la) \w+|\bal mediodia\b/.test(n);
    const dayExpr = /\b(hoy|manana|pasado manana|esta (tarde|noche)|lunes|martes|miercoles|jueves|viernes|sabado|domingo|el \d{1,2})\b/.test(n);
    const isQuestion = /^(que|cuando|tengo algo|a que hora)\b/.test(n);
    if (!isQuestion && (
      (/\b(calendario|agenda|google calendar)\b/.test(n) && /\b(pon|ponlo|apunta|apuntalo|anota|anotalo|anade|agrega|crea|mete|metelo|guarda|agenda|agendalo)\b/.test(n)) ||
      (/\b(tengo|hay)\b/.test(n) && timeExpr && dayExpr) ||
      (/^(recuerdame|apuntame|anotame)\b/.test(n) && (timeExpr || dayExpr))
    )) {
      try { return await calendarAdd(original, n); } catch (e) { if (e instanceof NeedGoogle) return needGoogleAnswer(original); throw e; }
    }
    // Calendario: leer
    if (/\b(que tengo|tengo algo|que hay|que planes|mi agenda|mis eventos|mi calendario|que me toca)\b/.test(n) &&
        (/\b(hoy|manana|pasado|semana|para hoy|lunes|martes|miercoles|jueves|viernes|sabado|domingo|calendario|agenda|el \d{1,2})\b/.test(n) || /^que tengo$/.test(n))) {
      if (!/\b(lista|notas|nevera)\b/.test(n)) {
        try { return await calendarDay(n); } catch (e) { if (e instanceof NeedGoogle) return needGoogleAnswer(original); throw e; }
      }
    }

    // Notas y lista de la compra
    if (/\b(borra|vacia|limpia|elimina) (todas )?(las |mis |la )?(notas|lista)\b/.test(n)) {
      const c = notes().length; saveNotes([]);
      return { say: c ? "Notas borradas." : "No tenías notas." };
    }
    if (/\b(que (hay|tengo) (apuntado|en (la|mi) (lista|notas))|lee(me)? (mis |las )?notas|mis notas|(la )?lista de la compra)\b/.test(n) && !/\b(anade|apunta|agrega|pon)\b/.test(n)) {
      const a = notes();
      if (!a.length) return { say: "No tienes nada apuntado." };
      const list = a.filter((x) => x.list), other = a.filter((x) => !x.list);
      const parts = [];
      if (list.length) parts.push(`En la lista de la compra: ${list.map((x) => x.text).join(", ")}.`);
      if (other.length) parts.push(`Notas: ${other.map((x) => x.text).join(". ")}.`);
      return { say: parts.join(" ") };
    }
    if ((m = original.match(/^\s*(?:jarvis,?\s*)?(?:apunta|anota|toma nota de|toma nota|añade|anade|agrega|pon|guarda)(?:\s+(?:que|una nota|en (?:las|mis) notas))?[:,]?\s+(.+?)(?:\s+(?:a|en) (?:la|mi) lista(?: de la compra)?)?[.]*$/i))) {
      const toList = /\b(a|en) (la|mi) lista\b/.test(n) || /lista de la compra/.test(n);
      if (toList || /^(apunta|anota|toma nota|guarda)/.test(n)) {
        const items = toList ? m[1].split(/\s*(?:,| y )\s*/).filter(Boolean) : [m[1]];
        const a = notes();
        items.forEach((t) => a.push({ text: t.trim(), list: toList, at: Date.now() }));
        saveNotes(a);
        return { say: toList ? `Añadido a la lista: ${items.join(", ")}.` : "Apuntado." };
      }
    }

    // Tiempo (meteorológico)
    if (/\b(tiempo|clima|temperatura|llover|lluvia|llueve|lloviendo|grados|calor|frio|nevar|paraguas)\b/.test(n) &&
        !/\b(cuanto tiempo|temporizador|tiempo libre|perder el tiempo|a tiempo|hace tiempo que|tiempo de)\b/.test(n)) {
      return await weather(n, original);
    }

    // Abrir apps / buscar / música / mapas
    if ((m = n.match(/^(?:pon|ponme|reproduce|busca|buscame)\s+(.+?)\s+en\s+(youtube|yutub|spotify)$/))) {
      const q = original.slice(original.length - m[0].length).match(/^\S+\s+(.+?)\s+en\s+\S+$/i)?.[1] || m[1];
      const yt = /you|yut/.test(m[2]);
      return { say: `Te lo busco en ${yt ? "YouTube" : "Spotify"}. Toca el botón.`, actions: [{ label: `Abrir ${yt ? "YouTube" : "Spotify"}`, href: yt ? `https://www.youtube.com/results?search_query=${encodeURIComponent(q)}` : `https://open.spotify.com/search/${encodeURIComponent(q)}`, primary: true }] };
    }
    if ((m = original.match(/^\s*(?:como (?:llego|voy|se va) a|cómo (?:llego|voy|se va) a|llevame a|llévame a|ruta a|direccion a|dirección a|navega a)\s+(.+?)[?.!]*$/i))) {
      return { say: `Ruta a ${m[1]} lista. Toca el botón para abrir Maps.`, actions: [{ label: "Abrir en Maps", href: `https://www.google.com/maps/dir/?api=1&destination=${encodeURIComponent(m[1])}`, primary: true }] };
    }
    if ((m = original.match(/^\s*(?:busca(?:me)?|buscar)\s+(.+?)(?:\s+en google)?[?.!]*$/i)) && !/wikipedia/i.test(original)) {
      return { say: `Te dejo la búsqueda de «${m[1]}» preparada.`, actions: [{ label: "Buscar en Google", href: `https://www.google.com/search?q=${encodeURIComponent(m[1])}`, primary: true }] };
    }
    if ((m = n.match(/^(?:abre|abreme|abrir|lanza|entra en|ve a)\s+(?:el |la |los |las |mi )?(.+)$/))) {
      let app = m[1].trim();
      app = APP_ALIASES[app] || app;
      const url = APPS[app];
      if (url) return { say: `Toca el botón para abrir ${cap(app)}.`, actions: [{ label: `Abrir ${cap(app)}`, href: url, primary: true }] };
      return { say: `No conozco esa app, pero te dejo la búsqueda.`, actions: [{ label: `Buscar ${app}`, href: `https://www.google.com/search?q=${encodeURIComponent(app)}` }] };
    }

    // Cálculos
    if (/\d/.test(n) && /\b(cuanto|cuanta|calcula|mas|menos|por|entre|dividido|multiplicado|raiz|cuadrado|elevado|ciento)\b|[+\-*/×÷^=]/.test(n)) {
      const v = calcExpr(n);
      if (v != null) return { say: `Son ${sayNum(v)}.` };
    }

    // Wikipedia
    if ((m = n.match(/^(?:quien es|quien era|quien fue|quienes son|que es|que son|que fue|que significa|hablame de|hablame sobre|cuentame (?:sobre|de)|busca en wikipedia|wikipedia|informacion (?:de|sobre))\s+(?:el |la |los |las |un |una )?(.+)$/))) {
      const q = original.slice(original.length - m[1].length).replace(/[?.!]+$/, "");
      if (q.split(" ").length <= 8) {
        try { const w = await wikipedia(q); if (w) return w; } catch (e) {}
      }
    }

    return null; // que conteste la IA
  }

  // ---------------- Ajustes (Google, ciudad, contactos) ----------------
  function setupSettings(ui) {
    const $ = (id) => document.getElementById(id);
    const cid = $("gClient"), city = $("cityInput"), cts = $("contactsInput");
    if (!cid) return;
    const paint = () => {
      const has = !!gClientId();
      cid.value = gClientId();
      $("gStatus").textContent = gToken() ? "Conectado ✔" : has ? (store.get("jarvis-gconnected", false) ? "Conectado antes: toca para renovar el permiso" : "Falta dar permiso") : "Sin configurar";
      $("gConnect").disabled = !has;
    };
    city.value = store.get("jarvis-city", "");
    cts.value = store.get("jarvis-contacts", "");
    paint();
    cid.addEventListener("change", () => { store.set("jarvis-gclient", cid.value.trim()); paint(); });
    city.addEventListener("change", () => store.set("jarvis-city", city.value.trim()));
    cts.addEventListener("change", () => store.set("jarvis-contacts", cts.value));
    $("gConnect").onclick = async () => {
      store.set("jarvis-gclient", cid.value.trim());
      try { await googleConnect(); $("gMsg").textContent = "Listo, ya puedo leer tu calendario y tu correo."; }
      catch (e) { $("gMsg").textContent = e.message; }
      paint();
    };
    $("gOrigin").textContent = location.origin;
  }

  // Botón «Conectar Google» desde una respuesta: conecta y repite la orden
  async function connectAndRetry() {
    await googleConnect();
    const t = pendingRetry;
    pendingRetry = null;
    return t;
  }

  window.JarvisSkills = {
    handle,
    setupSettings,
    connectAndRetry,
    stopRing,
    isRinging: () => !!ringing,
    setAnnouncer: (fn) => { announce = fn; },
    unlockAudio: () => { try { audioCtx = audioCtx || new (window.AudioContext || window.webkitAudioContext)(); audioCtx.resume?.(); } catch (e) {} },
    _test: { parseWhen, parseDuration, calcExpr, norm, cutSpans },
  };
})();
