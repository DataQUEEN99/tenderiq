import fitz
from app.shared.exceptions.custom_exceptions import AIProcessingException


class TextExtractor:
    def __init__(self):
        self.supported_types = {
            "application/pdf": self._extract_pdf,
            "text/plain": self._extract_text,
        }

    async def extract(self, file_path: str, mime_type: str) -> str:
        extractor = self.supported_types.get(mime_type)
        if not extractor:
            raise AIProcessingException(f"Unsupported file type: {mime_type}. Only PDF and text files are supported.")
        return await extractor(file_path)

    async def extract_from_bytes(self, content: bytes, mime_type: str) -> str:
        extractor = self.supported_types.get(mime_type)
        if not extractor:
            raise AIProcessingException(f"Unsupported file type: {mime_type}. Only PDF and text files are supported.")

        if mime_type == "application/pdf":
            return await self._extract_pdf_from_bytes(content)
        elif mime_type == "text/plain":
            return await self._extract_text_from_bytes(content)

        raise AIProcessingException(f"Unsupported file type: {mime_type}. Only PDF and text files are supported.")

    async def _extract_pdf(self, file_path: str) -> str:
        try:
            doc = fitz.open(file_path)
            text_parts = []
            for page in doc:
                text_parts.append(page.get_text())
            doc.close()
            return "\n\n".join(text_parts)
        except Exception as e:
            raise AIProcessingException(f"PDF extraction failed: {str(e)}")

    async def _extract_pdf_from_bytes(self, content: bytes) -> str:
        try:
            doc = fitz.open(stream=content, filetype="pdf")
            text_parts = []
            for page in doc:
                text_parts.append(page.get_text())
            doc.close()
            return "\n\n".join(text_parts)
        except Exception as e:
            raise AIProcessingException(f"PDF extraction failed: {str(e)}")

    async def _extract_text(self, file_path: str) -> str:
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                return f.read()
        except Exception as e:
            raise AIProcessingException(f"Text file extraction failed: {str(e)}")

    async def _extract_text_from_bytes(self, content: bytes) -> str:
        try:
            return content.decode("utf-8", errors="ignore")
        except Exception as e:
            raise AIProcessingException(f"Text extraction failed: {str(e)}")