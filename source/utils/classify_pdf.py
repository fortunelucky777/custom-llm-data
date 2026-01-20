import fitz  # PyMuPDF
import re
import unicodedata
import os

CID_RE = re.compile(r"\(cid:\d+\)")

def rect_area(r):
    return max(0.0, (r.x1 - r.x0) * (r.y1 - r.y0))

def image_coverage_ratio(page):
    page_rect = page.rect
    page_area = rect_area(page_rect) or 1.0

    # blocks: (x0, y0, x1, y1, text_or_meta, block_no, block_type)
    blocks = page.get_text("blocks")  # block_type 0=text, 1=image 

    img_area = 0.0
    for x0, y0, x1, y1, _, _, block_type in blocks:
        if block_type == 1:
            r = fitz.Rect(x0, y0, x1, y1) & page_rect
            img_area += rect_area(r)

    return min(1.0, img_area / page_area)

def korean_text_quality(s: str):
    # Strip whitespace for ratios
    stripped = "".join(ch for ch in s if not ch.isspace())
    n = len(stripped)
    if n == 0:
        return {"n": 0, "score": 0.0}

    korean = sum(0xAC00 <= ord(ch) <= 0xD7A3 for ch in stripped)
    replacement = stripped.count("\ufffd")
    cid_hits = len(CID_RE.findall(s))
    control = sum(unicodedata.category(ch)[0] == "C" for ch in stripped)

    korean_ratio = korean / n
    repl_ratio = replacement / n
    ctrl_ratio = control / n

    # Simple scoring: reward korean, penalize garbage signals
    score = 1.0
    score *= min(1.0, korean_ratio / 0.20)  # expect at least ~20% korean in normal Korean text pages
    score *= (1.0 - min(1.0, repl_ratio * 10))
    score *= (1.0 - min(1.0, ctrl_ratio * 10))
    score *= (1.0 - min(1.0, cid_hits / 10))

    return {
        "n": n,
        "korean_ratio": korean_ratio,
        "replacement_ratio": repl_ratio,
        "control_ratio": ctrl_ratio,
        "cid_hits": cid_hits,
        "score": max(0.0, min(1.0, score)),
    }

def should_force_ocr(page,
                     img_cover_threshold=0.85,
                     min_text_chars=50,
                     quality_threshold=0.35):
    img_cover = image_coverage_ratio(page)
    text = page.get_text("text")  # fast plain text
    q = korean_text_quality(text)

    # Rule 1: mostly image => treat as scanned / overlay; OCR anyway
    if img_cover >= img_cover_threshold:
        return True, {"reason": "high_image_coverage", "img_cover": img_cover, **q}

    # Rule 2: little text => likely scanned (or mostly graphics); OCR
    if q["n"] < min_text_chars:
        return True, {"reason": "too_little_text", "img_cover": img_cover, **q}

    # Rule 3: text exists but looks wrong => OCR
    if q["score"] < quality_threshold:
        return True, {"reason": "low_text_quality", "img_cover": img_cover, **q}

    return False, {"reason": "use_pdf_text", "img_cover": img_cover, **q}


def classify_pdf(pdf_path: str, force_ratio_thresh: float = 0.85, avg_size_per_page_thresh: float = 10 * 1024):
    doc = fitz.open(pdf_path)
    total_forces = 0
    for i, page in enumerate(doc):
        force, info = should_force_ocr(page)
        if force:
            total_forces += 1

    # Calculate and print average file size per page
    total_pages = len(doc)
    file_size = os.path.getsize(pdf_path)

    force_ratio = total_forces / total_pages 
    avg_size_per_page = file_size / total_pages

    doc.close()

    if force_ratio > force_ratio_thresh or avg_size_per_page > avg_size_per_page_thresh:
        return "scanned"
    return "docx"
    

# Example usage:
# pdfs = [
#     "samples/1.pdf",
#     "samples/2.pdf",
#     "samples/3.pdf",
#     "samples/4.pdf",
# ]
# for pdf_path in pdfs:
#     classified = classify_pdf(pdf_path)
#     print(f"{pdf_path}: {classified}")
