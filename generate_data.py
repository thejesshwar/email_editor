import os
import json
from uuid import uuid4
from dotenv import load_dotenv
from openai import OpenAI
load_dotenv()

API_KEY = os.getenv("OPENAI_API_KEY")
API_BASE = os.getenv("OPENAI_API_BASE")

# -----------------------------
# Azure OpenAI client
# -----------------------------
client = OpenAI(
    api_key=API_KEY,
    base_url=API_BASE
)
# -----------------------------
OUTPUT_DIR = "synthetic_data_llm"
os.makedirs(OUTPUT_DIR, exist_ok=True)
EDGE_CASES = {
    "check_in": "Very brief follow-up emails.",
    "acknowledgement": "Minimal acknowledgements.",
    "informational": "Single factual statements.",
    "request": "Direct minimal requests.",
    "constraint": "Messages stating a limitation.",
    "status": "Status-only updates."
}
SYSTEM_PROMPT = (
    "You generate short professional emails. "
    "Each email must be concise and factual."
)

def generate_single_email(edge_type: str, description: str, idx: int):
    user_prompt = f"""
Generate ONE short professional email.

Category: {edge_type}
Description: {description}

Variant index: {idx}

Rules:
- Exactly 1 sentence
- No greetings
- No sign-offs
- No background context
- No inferred intent
- Keep it different in wording from other variants

Return ONLY the email text.
"""

    response = client.chat.completions.create(
        model="gpt-4.1",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt}
        ]
    )

    return response.choices[0].message.content.strip()

def generate_emails(edge_type, description, count=50):
    emails = []
    for i in range(count):
        email = generate_single_email(edge_type, description, i)
        emails.append(email)
    return emails
def write_jsonl(edge_type: str, emails: list[str]):
    path = os.path.join(OUTPUT_DIR, f"{edge_type}.jsonl")
    with open(path, "w", encoding="utf-8") as f:
        for email in emails:
            record = {
                "id": str(uuid4()),
                "type": edge_type,
                "content": email,
                "task": "lengthen",
                "expected_issue": "faithfulness"
            }
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
def main():
    for edge_type, description in EDGE_CASES.items():
        print(f"Generating {edge_type} samples...")
        emails = generate_emails(edge_type, description, count=50)
        write_jsonl(edge_type, emails)
        print(f"  → {len(emails)} written")

    print("\n✅ Synthetic dataset generation complete.")

if __name__ == "__main__":
    main()