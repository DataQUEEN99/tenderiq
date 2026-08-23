from typing import List
from app.config import get_settings


class Chunker:
    def __init__(self):
        self.settings = get_settings()
        self.chunk_size = self.settings.chunk_size
        self.chunk_overlap = self.settings.chunk_overlap

    def chunk(self, text: str) -> List[str]:
        if not text or not text.strip():
            return []

        words = text.split()
        if len(words) <= self.chunk_size:
            return [text]

        chunks = []
        start = 0

        while start < len(words):
            end = min(start + self.chunk_size, len(words))
            chunk = " ".join(words[start:end])
            chunks.append(chunk)

            if end == len(words):
                break

            start = end - self.chunk_overlap
            if start < 0:
                start = 0

        return chunks

    def chunk_by_paragraphs(self, text: str, max_chunk_size: int = None) -> List[str]:
        max_size = max_chunk_size or self.chunk_size
        paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]

        chunks = []
        current_chunk = []

        for para in paragraphs:
            current_text = " ".join(current_chunk)
            para_words = len(para.split())

            if len(current_text.split()) + para_words <= max_size:
                current_chunk.append(para)
            else:
                if current_chunk:
                    chunks.append("\n\n".join(current_chunk))
                current_chunk = [para]

        if current_chunk:
            chunks.append("\n\n".join(current_chunk))

        return chunks