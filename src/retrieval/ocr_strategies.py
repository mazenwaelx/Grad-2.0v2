"""
OCR strategy implementations for text extraction from images.

Strategy pattern:
  - ``GeminiVisionOCR``  — high-accuracy Arabic OCR via Google Gemini
  - ``TesseractOCR``     — local OCR with preprocessing
  - ``CompositeOCR``     — tries Gemini first, falls back to Tesseract
"""
from __future__ import annotations

import io
import os
from abc import ABC, abstractmethod
from typing import List

# ── Optional dependency detection ──────────────────────────────────

try:
    import pytesseract
    from PIL import Image
    OCR_AVAILABLE = True
    print("[INFO] OCR libraries loaded successfully (pytesseract + PIL)")

    if os.name == "nt":
        _tesseract_path = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
        if os.path.exists(_tesseract_path):
            pytesseract.pytesseract.tesseract_cmd = _tesseract_path
            print(f"[INFO] Tesseract configured: {_tesseract_path}")
except Exception as _e:
    print(f"[WARNING] OCR not available: {type(_e).__name__}: {_e}")
    pytesseract = None  # type: ignore[assignment]
    Image = None  # type: ignore[assignment,misc]
    OCR_AVAILABLE = False

try:
    import google.generativeai as genai
    _gemini_api_key = os.environ.get("GOOGLE_API_KEY", "").strip()
    if _gemini_api_key:
        genai.configure(api_key=_gemini_api_key)
        GEMINI_VISION_AVAILABLE = True
        print("[INFO] Gemini Vision API configured for high-accuracy OCR")
    else:
        GEMINI_VISION_AVAILABLE = False
        print("[WARNING] GOOGLE_API_KEY not set — Gemini Vision OCR disabled")
except ImportError:
    genai = None  # type: ignore[assignment]
    GEMINI_VISION_AVAILABLE = False
    print("[WARNING] google-generativeai not installed — Gemini Vision OCR disabled")


# ── Abstract base ──────────────────────────────────────────────────

class OCRStrategy(ABC):
    """Abstract base for text extraction from images."""

    @abstractmethod
    def extract_text(self, image_bytes: bytes) -> str:
        """Extract text from raw image bytes. Returns empty string on failure."""


# ── Gemini Vision ──────────────────────────────────────────────────

class GeminiVisionOCR(OCRStrategy):
    """High-accuracy Arabic OCR using Gemini Vision API."""

    _EXTRACTION_PROMPT = (
        "أنت أداة استخراج نص متخصصة. استخرج كل النص الموجود في هذه الصورة بالضبط كما هو مكتوب.\n\n"
        "القواعد:\n"
        "1. انسخ النص حرفياً كما يظهر في الصورة - لا تغير أي كلمة أو رقم أو تاريخ\n"
        "2. حافظ على الترتيب من أعلى الصفحة إلى أسفلها\n"
        "3. انسخ جميع الأرقام والتواريخ وأرقام المواد القانونية وأرقام الأحكام بدقة تامة\n"
        "4. لا تضف أي شرح أو تعليق أو تلخيص - فقط انسخ النص الموجود\n"
        "5. حافظ على فواصل الأسطر والفقرات كما في الأصل\n"
        "6. إذا كان هناك نص غير واضح، اكتبه كما تراه بأفضل تقدير\n\n"
        "استخرج النص الآن:"
    )

    _MODEL_CANDIDATES = [
        "gemini-2.5-flash",
        "gemini-2.0-flash",
        "gemini-1.5-flash",
    ]

    def extract_text(self, image_bytes: bytes) -> str:
        if not GEMINI_VISION_AVAILABLE:
            return ""
        try:
            model = self._get_model()
            if model is None:
                return ""

            image_part = {
                "mime_type": self._detect_mime(image_bytes),
                "data": image_bytes,
            }

            response = model.generate_content(
                [self._EXTRACTION_PROMPT, image_part],
                generation_config=genai.types.GenerationConfig(
                    temperature=0.0, max_output_tokens=8192,
                ),
            )

            if response and response.text:
                text = response.text.strip()
                print(f"[INFO] Gemini Vision extracted {len(text)} chars")
                return text

            # Retry with simplified prompt
            response = model.generate_content(
                ["Extract all Arabic text from this image exactly as written:", image_part],
                generation_config=genai.types.GenerationConfig(
                    temperature=0.1, max_output_tokens=8192,
                ),
            )
            if response and response.text:
                return response.text.strip()

            return ""

        except Exception as e:
            print(f"[WARNING] Gemini Vision extraction failed: {type(e).__name__}: {e}")
            return ""

    def _get_model(self):
        for name in self._MODEL_CANDIDATES:
            try:
                return genai.GenerativeModel(name)
            except Exception:
                continue
        return None

    @staticmethod
    def _detect_mime(image_bytes: bytes) -> str:
        if image_bytes[:3] == b"\xff\xd8\xff":
            return "image/jpeg"
        return "image/png"


# ── Tesseract ──────────────────────────────────────────────────────

class TesseractOCR(OCRStrategy):
    """OCR using Tesseract with preprocessing and position-aware ordering."""

    def extract_text(self, image_bytes: bytes) -> str:
        if not OCR_AVAILABLE:
            return ""
        try:
            image = Image.open(io.BytesIO(image_bytes))
            processed = self._preprocess(image)
            return self._extract_ordered(processed)
        except Exception as e:
            print(f"[WARNING] Tesseract extraction failed: {e}")
            return ""

    @staticmethod
    def _preprocess(image) -> "Image.Image":
        """Upscale, grayscale, contrast, sharpen, Otsu binarize."""
        try:
            from PIL import ImageEnhance, ImageFilter
            import numpy as np

            w, h = image.size
            if w < 2000:
                scale = 2000 / w
                image = image.resize((int(w * scale), int(h * scale)), Image.LANCZOS)

            if image.mode != "L":
                image = image.convert("L")

            image = ImageEnhance.Contrast(image).enhance(1.5)
            image = image.filter(ImageFilter.SHARPEN)
            image = image.filter(ImageFilter.MedianFilter(size=3))

            img_array = np.array(image)
            hist, _ = np.histogram(img_array, bins=256, range=(0, 256))
            total = img_array.size
            best_t, best_v, w_bg, s_bg = 0, 0, 0, 0
            total_sum = sum(i * hist[i] for i in range(256))

            for t in range(256):
                w_bg += hist[t]
                if w_bg == 0:
                    continue
                w_fg = total - w_bg
                if w_fg == 0:
                    break
                s_bg += t * hist[t]
                v = w_bg * w_fg * (s_bg / w_bg - (total_sum - s_bg) / w_fg) ** 2
                if v > best_v:
                    best_v, best_t = v, t

            img_array = np.where(img_array > best_t, 255, 0).astype(np.uint8)
            return Image.fromarray(img_array)
        except Exception:
            return image

    @staticmethod
    def _extract_ordered(image) -> str:
        """Position-aware text extraction using image_to_data."""
        try:
            data = pytesseract.image_to_data(
                image, lang="ara+eng", config=r"--oem 3 --psm 3",
                output_type=pytesseract.Output.DATAFRAME,
            )
            data = data[data["conf"] != -1].copy()
            if data.empty:
                return TesseractOCR._extract_simple(image)

            blocks = []
            for bn in data["block_num"].unique():
                bd = data[data["block_num"] == bn]
                lines = []
                for ln in sorted(bd["line_num"].unique()):
                    ld = bd[bd["line_num"] == ln].sort_values("left")
                    line = " ".join(w for w in ld["text"].astype(str) if w.strip())
                    if line.strip():
                        lines.append(line.strip())
                block_text = "\n".join(lines)
                if block_text.strip():
                    blocks.append((bd["top"].min(), bd["left"].min(), block_text.strip()))

            if not blocks:
                return TesseractOCR._extract_simple(image)

            blocks.sort(key=lambda b: (b[0] // 30, -b[1]))
            return "\n\n".join(b[2] for b in blocks)
        except Exception:
            return TesseractOCR._extract_simple(image)

    @staticmethod
    def _extract_simple(image) -> str:
        return pytesseract.image_to_string(image, lang="ara+eng", config=r"--oem 3 --psm 6") or ""


# ── Composite ─────────────────────────────────────────────────────

class CompositeOCR(OCRStrategy):
    """Tries Gemini Vision first, then falls back to Tesseract."""

    def __init__(self) -> None:
        self._strategies: List[OCRStrategy] = []
        if GEMINI_VISION_AVAILABLE:
            self._strategies.append(GeminiVisionOCR())
        if OCR_AVAILABLE:
            self._strategies.append(TesseractOCR())

    def extract_text(self, image_bytes: bytes) -> str:
        for s in self._strategies:
            text = s.extract_text(image_bytes)
            if text and text.strip():
                return text
        return ""

    @property
    def is_available(self) -> bool:
        return len(self._strategies) > 0
