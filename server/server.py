"""
Roboti Badini - voice server for the ESP32 robot.

ESP32  --(16 kHz 16-bit mono PCM)-->  /talk
       speech-to-text (Meta MMS, Kurmanji)  ->  Claude (answers in Badini)
       ->  text-to-speech (Meta MMS TTS, Kurmanji)
ESP32  <--(16 kHz 16-bit mono PCM)--

Run:
    pip install -r requirements.txt
    export ANTHROPIC_API_KEY=sk-ant-...
    python server.py

Test without the robot:
    python server.py --say "Silav, tu çawa yî?"   # writes answer.wav
"""

import argparse
import os
import sys
import urllib.parse
import wave

import anthropic
import numpy as np
import torch
import uvicorn
from fastapi import FastAPI, Request, Response
from transformers import AutoProcessor, AutoTokenizer, VitsModel, Wav2Vec2ForCTC

SAMPLE_RATE = 16000
MODEL = "claude-opus-5-5"
# MMS language codes for Northern Kurdish (Kurmanji, which includes Badini), Latin script
ASR_LANG = os.environ.get("ASR_LANG", "kmr-script_latin")
TTS_MODEL = os.environ.get("TTS_MODEL", "facebook/mms-tts-kmr-script_latin")
MAX_HISTORY_TURNS = 10

SYSTEM_PROMPT = """Tu robotekî biçûk û dilxweş î, navê te "Roboti Badini" ye.
You are a small, friendly desk robot built with an ESP32. Your voice is a
text-to-speech engine for Northern Kurdish (Kurmanji) in Latin script.

Rules:
- Always answer in the Badini dialect of Kurdish (Duhok / Behdînan), written
  in the Kurdish Latin (Hawar) alphabet: a b c ç d e ê f g h i î j k l m n o p
  q r s ş t u û v w x y z. Never use Arabic script, English, or emoji -
  the speech engine can only read Kurdish Latin letters.
- Keep every answer short: one or two spoken sentences.
- Write numbers as words.
- The user's words come from speech recognition and may contain mistakes;
  guess the most likely meaning. If you really cannot understand, politely
  ask them to say it again.
- Latency-sensitive; begin your visible answer immediately."""

device = "cuda" if torch.cuda.is_available() else "cpu"
print(f"Loading models on {device} ...")
asr_processor = AutoProcessor.from_pretrained("facebook/mms-1b-all")
asr_model = Wav2Vec2ForCTC.from_pretrained("facebook/mms-1b-all").to(device)
for lang in (ASR_LANG, "kmr-script_latin", "kmr"):
    try:
        asr_processor.tokenizer.set_target_lang(lang)
        asr_model.load_adapter(lang)
        print("ASR language:", lang)
        break
    except Exception as e:  # language code not found -> try the next one
        print(f"ASR language {lang!r} not available: {e}")
else:
    sys.exit("No Kurmanji ASR adapter found - set ASR_LANG")
tts_tokenizer = AutoTokenizer.from_pretrained(TTS_MODEL)
tts_model = VitsModel.from_pretrained(TTS_MODEL).to(device)
claude = anthropic.Anthropic()
history: list[dict] = []
print("Ready.")


def speech_to_text(pcm: np.ndarray) -> str:
    audio = pcm.astype(np.float32) / 32768.0
    inputs = asr_processor(audio, sampling_rate=SAMPLE_RATE, return_tensors="pt").to(device)
    with torch.no_grad():
        logits = asr_model(**inputs).logits
    ids = torch.argmax(logits, dim=-1)[0]
    return asr_processor.decode(ids).strip()


def ask_claude(user_text: str) -> str:
    global history
    messages = history + [{"role": "user", "content": user_text}]
    response = claude.beta.messages.create(
        model=MODEL,
        max_tokens=1024,
        system=SYSTEM_PROMPT,
        messages=messages,
        output_config={"effort": "low"},
        betas=["server-side-fallback-2026-07-01"],
        fallbacks="default",
    )
    if response.stop_reason == "refusal":
        return "Biborîne, ez nikarim bersiva vê pirsê bidim."
    answer = " ".join(b.text for b in response.content if b.type == "text").strip()
    if not answer:
        answer = "Biborîne, careke din bêje."
    history = (messages + [{"role": "assistant", "content": answer}])[-2 * MAX_HISTORY_TURNS:]
    return answer


def text_to_speech(text: str) -> np.ndarray:
    inputs = tts_tokenizer(text.lower(), return_tensors="pt").to(device)
    with torch.no_grad():
        wav = tts_model(**inputs).waveform[0].cpu().numpy()
    sr = tts_model.config.sampling_rate
    if sr != SAMPLE_RATE:  # MMS TTS is 16 kHz, resample just in case
        idx = np.linspace(0, len(wav) - 1, int(len(wav) * SAMPLE_RATE / sr))
        wav = np.interp(idx, np.arange(len(wav)), wav)
    peak = max(np.abs(wav).max(), 1e-6)
    return (wav / peak * 0.9 * 32767).astype(np.int16)


def header_text(s: str) -> str:
    # HTTP headers must be ASCII; Kurdish letters like ê ş are percent-encoded
    return urllib.parse.quote(s[:300], safe=" ,.?!'-")


app = FastAPI()


@app.get("/")
def health():
    return {"ok": True}


@app.post("/talk")
async def talk(request: Request):
    body = await request.body()
    pcm = np.frombuffer(body[: len(body) // 2 * 2], dtype=np.int16)
    print(f"Received {len(pcm) / SAMPLE_RATE:.1f} s of audio")
    if len(pcm) < SAMPLE_RATE // 4:
        return Response(status_code=204)

    user_text = speech_to_text(pcm)
    print("You:  ", user_text)
    if len(user_text) < 2:
        return Response(status_code=204)

    try:
        answer = ask_claude(user_text)
    except anthropic.APIError as e:
        print("Claude error:", e)
        answer = "Biborîne, pirsgirêkek heye. Careke din biceribîne."
    print("Robot:", answer)

    audio = text_to_speech(answer)
    return Response(
        content=audio.tobytes(),
        media_type="application/octet-stream",
        headers={"X-User-Text": header_text(user_text), "X-Robot-Text": header_text(answer)},
    )


def save_wav(path: str, audio: np.ndarray) -> None:
    with wave.open(path, "wb") as f:
        f.setnchannels(1)
        f.setsampwidth(2)
        f.setframerate(SAMPLE_RATE)
        f.writeframes(audio.tobytes())


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--say", help="test: send this text to Claude and save answer.wav")
    args = parser.parse_args()

    if args.say:
        reply = ask_claude(args.say)
        print("Robot:", reply)
        save_wav("answer.wav", text_to_speech(reply))
        print("Saved answer.wav")
        sys.exit(0)

    uvicorn.run(app, host=args.host, port=args.port)
