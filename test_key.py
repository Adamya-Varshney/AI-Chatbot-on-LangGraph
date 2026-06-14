import os
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv(dotenv_path=Path(__file__).resolve().parent / ".env", override=True)

key = os.getenv("OPENAI_API_KEY")
print("Loaded suffix:", key[-6:] if key else "NONE")

client = OpenAI()
resp = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[{"role": "user", "content": "say hi"}],
)
print("OpenAI says:", resp.choices[0].message.content)