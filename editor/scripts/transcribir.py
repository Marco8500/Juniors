"""Transcribe con faster-whisper y tiempos por palabra. Uso: transcribir.py audio.wav salida.json [modelo]"""
import sys, json, subprocess
import numpy as np
from faster_whisper import WhisperModel
src, out = sys.argv[1], sys.argv[2]
model = sys.argv[3] if len(sys.argv) > 3 else "small"
m = WhisperModel(model, device="cpu", compute_type="int8")
pcm = subprocess.run(["ffmpeg","-v","error","-i",src,"-f","s16le","-ac","1","-ar","16000","-"],capture_output=True,check=True).stdout
audio = np.frombuffer(pcm, np.int16).astype(np.float32)/32768
segs, info = m.transcribe(audio, word_timestamps=True, language=None)
words, segments = [], []
for s in segs:
    segments.append({"start": s.start, "end": s.end, "text": s.text, "no_speech_prob": s.no_speech_prob})
    for w in s.words or []:
        words.append({"word": w.word.strip(), "start": round(w.start, 3), "end": round(w.end, 3), "prob": round(w.probability, 3)})
json.dump({"language": info.language, "segments": segments, "words": words}, open(out, "w"), ensure_ascii=False, indent=1)
print(info.language, round(info.language_probability, 2))
for s in segments: print(f"{s['start']:.2f}-{s['end']:.2f} [{s['no_speech_prob']:.2f}] {s['text']}")
