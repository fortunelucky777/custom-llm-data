"""PyMuPDF (fitz) extractor."""

from pathlib import Path

import fitz  # PyMuPDF

from .base import BaseExtractor


class PyMuPDFExtractor(BaseExtractor):
    """Extract text using PyMuPDF (fitz)."""
    
    name = "PyMuPDF"
    description = "Fast, handles complex layouts, supports multiple formats"
    supports_ocr = False
    
    def extract(self, pdf_path: Path) -> str:
        """Extract text from PDF using PyMuPDF."""
        text_parts = []
        
        with fitz.open(pdf_path) as doc:
            for page in doc:
                text_parts.append(page.get_text())
        
        return "\n".join(text_parts)

