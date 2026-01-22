"""Base extractor interface."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
import time
import traceback
from typing import Optional


@dataclass
class ExtractionResult:
    """Result of a PDF text extraction."""
    
    extractor_name: str
    text: str
    success: bool
    error_message: Optional[str] = None
    execution_time_seconds: float = 0.0
    char_count: int = 0
    word_count: int = 0
    line_count: int = 0
    metadata: dict = field(default_factory=dict)
    
    def __post_init__(self):
        if self.success and self.text:
            self.char_count = len(self.text)
            self.word_count = len(self.text.split())
            self.line_count = len(self.text.splitlines())


class BaseExtractor(ABC):
    """Base class for PDF text extractors."""
    
    name: str = "BaseExtractor"
    description: str = "Base extractor class"
    supports_ocr: bool = False
    
    @abstractmethod
    def extract(self, pdf_path: Path) -> str:
        """
        Extract text from a PDF file.
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            Extracted text as a string
        """
        pass
    
    def extract_with_timing(self, pdf_path: Path) -> ExtractionResult:
        """
        Extract text with timing and error handling.
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            ExtractionResult with timing and metadata
        """
        start_time = time.time()
        
        try:
            text = self.extract(pdf_path)
            execution_time = time.time() - start_time
            
            return ExtractionResult(
                extractor_name=self.name,
                text=text,
                success=True,
                execution_time_seconds=execution_time,
            )
        except Exception as e:
            execution_time = time.time() - start_time
            return ExtractionResult(
                extractor_name=self.name,
                text="",
                success=False,
                error_message=f"{type(e).__name__}: {str(e)}\n{traceback.format_exc()}",
                execution_time_seconds=execution_time,
            )

