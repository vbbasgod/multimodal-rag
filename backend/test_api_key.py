import asyncio
import os
import sys

from dotenv import load_dotenv

load_dotenv()

from openai import AsyncOpenAI


async def main() -> None:
    groq_key = os.environ.get("GROQ_API_KEY")
    openai_key = os.environ.get("OPENAI_API_KEY")

    if groq_key:
        api_key = groq_key
        base_url = os.environ.get("GROQ_BASE_URL", "https://api.groq.com/openai/v1")
        model = os.environ.get("GROQ_MODEL", "gemma-3n-e4b-it")
        source = "Groq"
    elif openai_key:
        api_key = openai_key
        base_url = None
        model = os.environ.get("OPENAI_MODEL", "gpt-4o")
        source = "OpenAI"
    else:
        print("ERROR: Set GROQ_API_KEY or OPENAI_API_KEY in your environment.")
        sys.exit(1)

    client = AsyncOpenAI(api_key=api_key, base_url=base_url)

    print(f"Testing {source} API key with model '{model}'...\n")

    response = await client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": "You are a small test assistant."},
            {
                "role": "user",
                "content": "Say hello and confirm that the API key works.",
            },
        ],
        max_tokens=50,
        temperature=0,
    )

    content = response.choices[0].message.content
    print("API key test succeeded. Response:\n")
    print(content)


if __name__ == "__main__":
    asyncio.run(main())
