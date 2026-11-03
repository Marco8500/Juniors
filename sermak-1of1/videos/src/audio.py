"""Sound design for BRASAS: ember crackle, low cello drone, watch tick, final piano note."""
import wave
import numpy as np

SR, DUR = 48000, 16.0
n = int(SR * DUR)
t = np.arange(n) / SR
rng = np.random.default_rng(3)


def env(a, b, fi, fo):
    e = np.zeros(n)
    m = (t >= a) & (t < b)
    e[m] = 1.0
    if fi > 0:
        e *= np.clip((t - a) / fi, 0, 1)
    if fo > 0:
        e *= np.clip((b - t) / fo, 0, 1)
    return e


def lowpass(x, fc):
    a = np.exp(-2 * np.pi * fc / SR)
    y = np.empty_like(x)
    acc = 0.0
    for i in range(len(x)):  # simple one-pole
        acc = (1 - a) * x[i] + a * acc
        y[i] = acc
    return y


def lp_fast(x, fc, passes=2):
    # FFT brickwall-ish lowpass with soft knee (fast)
    X = np.fft.rfft(x)
    f = np.fft.rfftfreq(len(x), 1 / SR)
    X *= 1 / (1 + (f / fc) ** (2 * passes))
    return np.fft.irfft(X, len(x))


def hp_fast(x, fc):
    X = np.fft.rfft(x)
    f = np.fft.rfftfreq(len(x), 1 / SR)
    X *= (f / fc) ** 2 / (1 + (f / fc) ** 2)
    return np.fft.irfft(X, len(x))


L = np.zeros(n)
R = np.zeros(n)

# ---- 1. ember crackle (0–12 s, louder in hook) ----
crk = np.zeros(n)
rate = 22
times = np.cumsum(rng.exponential(1 / rate, 600))
times = times[times < 12.2]
for tt in times:
    i = int(tt * SR)
    ln = int(SR * rng.uniform(0.002, 0.012))
    if i + ln >= n:
        continue
    burst = rng.normal(0, 1, ln) * np.exp(-np.linspace(0, 6, ln))
    crk[i:i + ln] += burst * rng.uniform(0.2, 1.0) ** 2
crk = hp_fast(crk, 900)
hiss = hp_fast(lp_fast(rng.normal(0, 1, n), 6000), 300) * 0.05
rumble = lp_fast(rng.normal(0, 1, n), 120) * 0.9
fire = (crk * 0.55 + hiss + rumble * 0.35)
fire_env = (env(0, 12.6, 0.25, 1.6) * (0.55 + 0.45 * env(0, 2.2, 0, 0.6)))
fire *= fire_env
pan = 0.5 + 0.25 * np.sin(t * 0.7)
L += fire * (1 - pan) * 1.2
R += fire * pan * 1.2

# ---- 2. cello-like drone (2.0 s – 11.0 s hard stop) ----
vib = 1 + 0.004 * np.sin(2 * np.pi * 4.8 * t)
drone = np.zeros(n)
for f0, amp in [(55.0, 1.0), (82.41, 0.55), (110.0, 0.35)]:
    ph = 2 * np.pi * np.cumsum(f0 * vib) / SR
    for k in range(1, 14):  # sawtooth-ish bowed tone
        drone += amp * np.sin(k * ph) / k * (0.85 ** k)
bow = 1 + 0.15 * lp_fast(rng.normal(0, 1, n), 3)  # bow pressure variation
drone = lp_fast(drone * bow, 900)
d_env = env(2.0, 11.0, 2.2, 0.12) * (0.75 + 0.25 * np.clip((t - 5) / 5, 0, 1))
drone *= d_env * 0.22
L += drone * 1.05
R += drone * 0.95

# ---- 3. watch tick during dial macro (5–8 s) ----
for k, tt in enumerate(np.arange(5.25, 8.0, 0.5)):
    i = int(tt * SR)
    ln = int(SR * 0.025)
    c = rng.normal(0, 1, ln) * np.exp(-np.linspace(0, 12, ln))
    c = np.convolve(c, np.sin(2 * np.pi * 3800 * np.arange(60) / SR) * np.hanning(60), 'same')
    g = 0.22 if k % 2 == 0 else 0.15
    L[i:i + ln] += c * g
    R[i:i + ln] += c * g

# ---- 4. piano note at 13.1 s (low A + fifth), with reverb tail ----
pn = np.zeros(n)
i0 = int(13.1 * SR)
tt = t[i0:] - 13.1
for f0, a0 in [(55.0, 1.0), (110.0, 0.7), (164.8, 0.25)]:
    for k in range(1, 12):
        fk = f0 * k * np.sqrt(1 + 0.0004 * k * k)  # slight inharmonicity
        dec = np.exp(-tt * (0.55 + 0.35 * k))
        pn[i0:] += a0 * np.sin(2 * np.pi * fk * tt) * dec / (k ** 1.1)
atk = np.clip(tt / 0.004, 0, 1)
pn[i0:] *= atk
pn *= 0.32
# reverb: convolve with decaying noise (stereo decorrelated)
ir_len = int(SR * 2.2)
irL = rng.normal(0, 1, ir_len) * np.exp(-np.linspace(0, 7, ir_len))
irR = rng.normal(0, 1, ir_len) * np.exp(-np.linspace(0, 7, ir_len))
irL = lp_fast(irL, 4000); irR = lp_fast(irR, 4000)
irL /= np.abs(irL).sum() ** 0.5 * 9; irR /= np.abs(irR).sum() ** 0.5 * 9
wetL = np.convolve(pn, irL)[:n]
wetR = np.convolve(pn, irR)[:n]
L += pn + wetL
R += pn + wetR

# ---- master ----
st = np.stack([L, R], 1)
st = np.tanh(st * 1.2) / np.tanh(1.2)
st /= np.abs(st).max() / 0.89
fade_out = np.clip((DUR - t) / 0.6, 0, 1)[:, None]
st *= fade_out
pcm = (st * 32767).astype(np.int16)
with wave.open('audio.wav', 'wb') as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes(pcm.tobytes())
print('ok')
