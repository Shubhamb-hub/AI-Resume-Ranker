import re
import unicodedata


def clean_text(text: str) -> str:
    """
    Clean OCR / resume text for NLP, embeddings, and extraction.

    Goals:
    - Remove OCR noise
    - Preserve semantic meaning
    - Keep emails, skills, dates intact
    """

    if not text or not isinstance(text, str):
        return ""

    # Normalize unicode characters
    text = unicodedata.normalize("NFKD", text)

    # Remove common OCR junk & bullets
    text = re.sub(
        r"[•●▪■◆►◦▪️▸➤]+",
        " ",
        text
    )

    # Fix broken words (e.g., d a t a → data)
    text = re.sub(
        r"\b([a-zA-Z])\s+([a-zA-Z])\b",
        r"\1\2",
        text
    )

    # Remove page numbers & headers
    text = re.sub(
        r"\bpage\s*\d+\b",
        " ",
        text,
        flags=re.IGNORECASE
    )

    # Remove excessive punctuation (keep useful ones)
    text = re.sub(
        r"[^\w\s@.+,/:-]",
        " ",
        text
    )

    # Normalize whitespace
    text = re.sub(r"\s+", " ", text)

    # Lowercase (best for embeddings)
    text = text.lower()

    # Strip final text
    return text.strip()

