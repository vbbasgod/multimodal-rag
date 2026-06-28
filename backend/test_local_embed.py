import asyncio
import traceback

from app.services.embedding_service import EmbeddingService


async def main():
    try:
        svc = EmbeddingService()
        emb = await svc.embed_text("hello world")
        print("embedding length:", len(emb))
    except Exception:
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
