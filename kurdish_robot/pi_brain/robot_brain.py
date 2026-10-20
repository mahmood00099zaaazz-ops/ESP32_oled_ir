"""Brain of a Kurdish (Badini) talking robot, for Raspberry Pi 5.

Flow:  listen (mic or keyboard) -> Claude answers in Badini -> speak (MMS Kurmanji TTS)
The ESP32 face is on USB serial; it shows IDLE / LISTEN / THINK / TALK and
sends "PERSON" when its IR sensor sees someone.

Run:
    export ANTHROPIC_API_KEY=...
    python3 robot_brain.py                 # type questions on the keyboard
    python3 robot_brain.py --asr mms       # speak into a USB mic (needs 8 GB RAM)
"""

import argparse
import threading
import time

import anthropic
import numpy as np
import serial
import sounddevice as sd
import torch
from transformers import AutoProcessor, AutoTokenizer, VitsModel, Wav2Vec2ForCTC

SYSTEM_PROMPT = """You are "Zîrek", a small friendly robot that lives in Duhok.
Always answer in Kurdish Badini (Behdînî Kurmancî), written in Latin letters
(the Kurmancî alphabet: ç, ê, î, ş, û, x, q, w), because your voice can only
read Latin letters. Keep every answer short: 1 to 3 sentences, no lists, no emoji.
Be smart, kind and a little funny. If you do not know something, say so."""

SAMPLE_RATE = 16000


class Face:
    def __init__(self, port):
        self.ser = None
        if port:
            try:
                self.ser = serial.Serial(port, 115200, timeout=0.1)
            except serial.SerialException as e:
                print(f"[face] ESP32 not found on {port}: {e}")

    def show(self, mood):
        if self.ser:
            self.ser.write((mood + "\n").encode())

    def person_seen(self):
        if self.ser and self.ser.in_waiting:
            return self.ser.readline().decode(errors="ignore").strip() == "PERSON"
        return False


class Voice:
    """Text-to-speech with Meta MMS, Northern Kurdish (Kurmanji) in Latin script."""

    def __init__(self):
        name = "facebook/mms-tts-kmr-script_latin"
        self.model = VitsModel.from_pretrained(name)
        self.tokenizer = AutoTokenizer.from_pretrained(name)

    def say(self, text):
        inputs = self.tokenizer(text, return_tensors="pt")
        with torch.no_grad():
            wav = self.model(**inputs).waveform[0].numpy()
        sd.play(wav, self.model.config.sampling_rate)
        sd.wait()


class Ears:
    """Speech-to-text with Meta MMS-1B (Kurmanji adapter). Needs about 5 GB RAM."""

    def __init__(self):
        name = "facebook/mms-1b-all"
        self.processor = AutoProcessor.from_pretrained(name, target_lang="kmr-script_latin")
        self.model = Wav2Vec2ForCTC.from_pretrained(
            name, target_lang="kmr-script_latin", ignore_mismatched_sizes=True
        )

    def listen(self, seconds=5):
        audio = sd.rec(int(seconds * SAMPLE_RATE), samplerate=SAMPLE_RATE, channels=1)
        sd.wait()
        inputs = self.processor(audio[:, 0], sampling_rate=SAMPLE_RATE, return_tensors="pt")
        with torch.no_grad():
            ids = torch.argmax(self.model(**inputs).logits, dim=-1)[0]
        return self.processor.decode(ids)


class Brain:
    def __init__(self):
        self.client = anthropic.Anthropic()
        self.history = []

    def answer(self, text):
        self.history.append({"role": "user", "content": text})
        response = self.client.beta.messages.create(
            model="claude-opus-5-5",
            max_tokens=1024,
            system=SYSTEM_PROMPT,
            output_config={"effort": "low"},
            betas=["server-side-fallback-2026-07-01"],
            fallbacks="default",
            messages=self.history,
        )
        if response.stop_reason == "refusal":
            self.history.pop()
            return "Bibore, ez nikarim bersiva vê pirsê bidim."
        # Keep the full content (thinking blocks included) so history stays append-only.
        self.history.append({"role": "assistant", "content": response.content})
        return "".join(b.text for b in response.content if b.type == "text").strip()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", default="/dev/ttyUSB0", help="ESP32 serial port")
    parser.add_argument("--asr", choices=["keyboard", "mms"], default="keyboard")
    args = parser.parse_args()

    face = Face(args.port)
    voice = Voice()
    brain = Brain()
    ears = Ears() if args.asr == "mms" else None

    greet = threading.Event()

    def watch_ir():
        while True:
            if face.person_seen():
                greet.set()
            time.sleep(0.05)

    threading.Thread(target=watch_ir, daemon=True).start()

    face.show("IDLE")
    print("Zîrek amade ye. (Ctrl+C bo derketinê)")
    while True:
        if greet.is_set():
            greet.clear()
            face.show("TALK")
            voice.say("Silav! Ez Zîrek im. Tu çawa yî?")
            face.show("IDLE")

        face.show("LISTEN")
        if ears:
            question = ears.listen()
            print(f"Te got: {question}")
        else:
            question = input("Tu: ").strip()
        if not question:
            face.show("IDLE")
            continue

        face.show("THINK")
        reply = brain.answer(question)
        print(f"Zîrek: {reply}")

        face.show("TALK")
        voice.say(reply)
        face.show("IDLE")


if __name__ == "__main__":
    main()
