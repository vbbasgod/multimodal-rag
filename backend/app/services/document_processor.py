"""
Multimodal Document Processor
Handles: PDF, Images, Plain Text, URLs
Extracts text, tables, and image descriptions
"""

import base64
import io
import logging
import uuid
from pathlib import Path
from typing import Any, Dict, List, Tuple

import fitz  # PyMuPDF
import pytesseract
from app.core.config import settings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from openai import AsyncOpenAI
from PIL import Image

logger = logging.getLogger(__name__)


class DocumentProcessor:
    def __init__(self):
        api_key = settings.GROQ_API_KEY or settings.OPENAI_API_KEY
        base_url = settings.GROQ_BASE_URL if settings.GROQ_API_KEY else None
        self.client = AsyncOpenAI(api_key=api_key, base_url=base_url)
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=settings.CHUNK_SIZE,
            chunk_overlap=settings.CHUNK_OVERLAP,
            separators=["\n\n", "\n", ".", "!", "?", ",", " "],
        )

    async def process_pdf(
        self, file_bytes: bytes, filename: str
    ) -> List[Dict[str, Any]]:
        """Extract text and images from PDF"""
        chunks = []
        doc = fitz.open(stream=file_bytes, filetype="pdf")

        for page_num in range(len(doc)):
            page = doc[page_num]

            # Extract text
            text = page.get_text("text")
            if text.strip():
                text_chunks = self.text_splitter.split_text(text)
                for i, chunk in enumerate(text_chunks):
                    chunks.append(
                        {
                            "id": str(uuid.uuid4()),
                            "content": chunk,
                            "modality": "text",
                            "metadata": {
                                "source": filename,
                                "page": page_num + 1,
                                "chunk_index": i,
                                "type": "pdf_text",
                            },
                        }
                    )

            # Extract images
            image_list = page.get_images(full=True)
            for img_index, img in enumerate(image_list):
                xref = img[0]
                base_image = doc.extract_image(xref)
                image_bytes = base_image["image"]

                # Use GPT-4o vision to describe the image
                description = await self._describe_image(image_bytes)
                chunks.append(
                    {
                        "id": str(uuid.uuid4()),
                        "content": description,
                        "modality": "image",
                        "metadata": {
                            "source": filename,
                            "page": page_num + 1,
                            "image_index": img_index,
                            "type": "pdf_image",
                        },
                    }
                )

        doc.close()
        return chunks

    async def process_image(
        self, file_bytes: bytes, filename: str
    ) -> List[Dict[str, Any]]:
        """Process standalone image files"""
        # OCR text extraction
        image = Image.open(io.BytesIO(file_bytes))
        ocr_text = pytesseract.image_to_string(image)

        # Vision description
        vision_description = await self._describe_image(file_bytes)

        combined = f"Visual Description: {vision_description}"
        if ocr_text.strip():
            combined += f"\n\nExtracted Text (OCR): {ocr_text.strip()}"

        return [
            {
                "id": str(uuid.uuid4()),
                "content": combined,
                "modality": "image",
                "metadata": {
                    "source": filename,
                    "type": "image",
                    "has_ocr": bool(ocr_text.strip()),
                },
            }
        ]

    async def process_text(
        self, text: str, metadata: Dict[str, Any] = {}
    ) -> List[Dict[str, Any]]:
        """Process plain text"""
        text_chunks = self.text_splitter.split_text(text)
        return [
            {
                "id": str(uuid.uuid4()),
                "content": chunk,
                "modality": "text",
                "metadata": {**metadata, "chunk_index": i, "type": "text"},
            }
            for i, chunk in enumerate(text_chunks)
        ]

    async def _describe_image(self, image_bytes: bytes) -> str:
        """Use GPT-4o to describe an image"""
        try:
            b64 = base64.b64encode(image_bytes).decode("utf-8")
            response = await self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image_url",
                                "image_url": {"url": f"data:image/jpeg;base64,{b64}"},
                            },
                            {
                                "type": "text",
                                "text": (
                                    "Describe this image in detail for a RAG system. "
                                    "Include: main subjects, text visible, charts/tables data, "
                                    "spatial relationships, and any quantitative information."
                                ),
                            },
                        ],
                    }
                ],
                max_tokens=500,
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"Image description failed: {e}")
            return "Image content (description unavailable)"
