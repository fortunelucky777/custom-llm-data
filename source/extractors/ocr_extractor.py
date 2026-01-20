"""OCR-based extractor using PaddleOCR and PP-DocLayoutV2."""

from pathlib import Path
from typing import Optional

import fitz  # PyMuPDF
import numpy as np
from PIL import Image
from paddleocr import LayoutDetection, PaddleOCR

from .base import BaseExtractor


class OCRExtractor(BaseExtractor):
    """Extract text using PaddleOCR with layout detection."""
    
    name = "OCRExtractor"
    description = "OCR-based extractor using PaddleOCR and PP-DocLayoutV2"
    supports_ocr = True
    
    def __init__(
        self,
        layout_model_name: str = "PP-DocLayoutV2",
        recognition_model_name: str = "korean_PP-OCRv5_mobile_rec",
        use_doc_orientation_classify: bool = False,
        use_doc_unwarping: bool = False,
        use_textline_orientation: bool = True,
        dpi: int = 300,
        gap_ratio: float = 0.25,
        margin: int = 8,
    ):
        """
        Initialize the OCR extractor.
        
        Args:
            layout_model_name: Name of the layout detection model
            recognition_model_name: Name of the text recognition model
            use_doc_orientation_classify: Whether to use document orientation classification
            use_doc_unwarping: Whether to use document unwarping
            use_textline_orientation: Whether to use textline orientation
            dpi: DPI for rendering PDF pages to images
            gap_ratio: Ratio for detecting column gaps
            margin: Margin in pixels for cropping regions
        """
        self.layout = LayoutDetection(model_name=layout_model_name)
        self.ocr = PaddleOCR(
            text_recognition_model_name=recognition_model_name,
            use_doc_orientation_classify=use_doc_orientation_classify,
            use_doc_unwarping=use_doc_unwarping,
            use_textline_orientation=use_textline_orientation,
        )
        self.dpi = dpi
        self.gap_ratio = gap_ratio
        self.margin = margin
    
    def render_page_to_rgb(self, page, dpi: Optional[int] = None) -> np.ndarray:
        """Render a PDF page to RGB numpy array."""
        if dpi is None:
            dpi = self.dpi
        mat = fitz.Matrix(dpi / 72, dpi / 72)
        pix = page.get_pixmap(matrix=mat, alpha=False)
        img = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
        return np.array(img)
    
    def order_boxes_two_columns(self, boxes, page_w: float, gap_ratio: Optional[float] = None) -> list:
        """
        Simple 2-column heuristic:
        - Look at x-centers; if there's a big gap, split into left/right columns.
        - Return boxes ordered top->bottom within each column, left column first.
        """
        if not boxes:
            return boxes
        
        if gap_ratio is None:
            gap_ratio = self.gap_ratio
        
        centers = sorted(((b["coordinate"][0] + b["coordinate"][2]) / 2.0) for b in boxes)
        gaps = [centers[i+1] - centers[i] for i in range(len(centers) - 1)]
        if not gaps or max(gaps) < gap_ratio * page_w:
            # probably single column: top->bottom, left->right
            return sorted(boxes, key=lambda b: (b["coordinate"][1], b["coordinate"][0]))
        
        i = max(range(len(gaps)), key=lambda k: gaps[k])
        split_x = (centers[i] + centers[i+1]) / 2.0
        
        left = [b for b in boxes if (b["coordinate"][0] + b["coordinate"][2]) / 2.0 < split_x]
        right = [b for b in boxes if b not in left]
        
        left = sorted(left, key=lambda b: b["coordinate"][1])
        right = sorted(right, key=lambda b: b["coordinate"][1])
        return left + right
    
    def crop_with_margin(self, img, coord, margin: Optional[int] = None) -> np.ndarray:
        """Crop image region with margin."""
        if margin is None:
            margin = self.margin
        h, w = img.shape[:2]
        x1, y1, x2, y2 = map(int, coord)
        x1 = max(0, x1 - margin)
        y1 = max(0, y1 - margin)
        x2 = min(w, x2 + margin)
        y2 = min(h, y2 + margin)
        return img[y1:y2, x1:x2]
    
    def extract(self, pdf_path: Path) -> str:
        """Extract text from PDF using PaddleOCR with layout detection."""
        text_parts = []
        
        with fitz.open(pdf_path) as doc:
            for page_idx, page in enumerate(doc):
                page_img = self.render_page_to_rgb(page)
                page_h, page_w = page_img.shape[:2]
                
                # LayoutDetection supports numpy.ndarray input; output is a Result object with `.json`
                layout_out = self.layout.predict(page_img, batch_size=1, layout_nms=True)
                page_layout = layout_out[0].json["res"]
                
                # Keep only text-like regions
                text_like = []
                for b in page_layout["boxes"]:
                    label = str(b.get("label", "")).lower()
                    if label in {"text", "paragraph_title", "document_title", "abstract", "references", "sidebar_text"}:
                        text_like.append(b)
                
                ordered = self.order_boxes_two_columns(text_like, page_w=page_w)
                
                page_text_parts = []
                for b in ordered:
                    crop = self.crop_with_margin(page_img, b["coordinate"])
                    
                    # OCR the cropped region (detect+recognize inside that region)
                    ocr_out = self.ocr.predict(crop)  # numpy.ndarray input
                    ocr_json = ocr_out[0].json["res"]
                    lines = ocr_json.get("rec_texts", [])
                    block_text = "\n".join(lines).strip()
                    
                    if block_text:
                        page_text_parts.append(block_text)
                
                if page_text_parts:
                    text_parts.append("\n".join(page_text_parts))
        
        return "\n\n".join(text_parts)
