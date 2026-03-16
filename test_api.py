import os

from dotenv import load_dotenv
from openai import OpenAI


def main() -> None:
    load_dotenv(override=True)

    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    base_url = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1").strip()
    api_mode = os.getenv("OPENAI_API_MODE", "auto").strip().lower()
    model_name = os.getenv("MODEL_NAME", "gpt-4o-mini").strip()

    if not api_key:
        raise ValueError("OPENAI_API_KEY is missing. Please configure it in .env first.")

    print(f"Connecting to API: {base_url}")
    print(f"API mode: {api_mode}")
    print(f"Using model: {model_name}")

    client = OpenAI(api_key=api_key, base_url=base_url)

    if api_mode == "responses":
        response = client.responses.create(
            model=model_name,
            input='Please reply with: "API connected".',
        )
        content = response.output_text
    else:
        response = client.chat.completions.create(
            model=model_name,
            messages=[{"role": "user", "content": 'Please reply with: "API connected".'}],
            max_tokens=50,
        )
        content = response.choices[0].message.content

    print("\nAPI test succeeded. Model reply:")
    print(content)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print("\nAPI test failed. Error:")
        print(e)
