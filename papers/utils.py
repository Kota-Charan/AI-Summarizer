import re

from pypdf import PdfReader
from transformers import AutoTokenizer, pipeline


# Load AI model and tokenizer once
_MODEL_NAME = "sshleifer/distilbart-cnn-12-6"
# Lazy-loaded model and tokenizer to avoid heavy work at import/startup
_summarizer = None
_tokenizer = None
_MODEL_TOKEN_LIMIT = None
CHUNK_TOKEN_LIMIT = 1024  # fallback token chunk size until tokenizer is loaded


def _ensure_model_loaded():
    """Load the summarization pipeline and tokenizer on first use."""
    global _summarizer, _tokenizer, _MODEL_TOKEN_LIMIT, CHUNK_TOKEN_LIMIT
    if _summarizer is None or _tokenizer is None:
        try:
            _summarizer = pipeline("summarization", model=_MODEL_NAME)
            _tokenizer = AutoTokenizer.from_pretrained(_MODEL_NAME, use_fast=True)
            _MODEL_TOKEN_LIMIT = _tokenizer.model_max_length if _tokenizer.model_max_length else 1024
            CHUNK_TOKEN_LIMIT = max(256, _MODEL_TOKEN_LIMIT - 100)
        except Exception as e:
            # If model loading fails (e.g., limited memory or network), raise a clear error
            raise RuntimeError(f"Failed to load summarization model: {e}")


def extract_text_from_pdf(pdf_path):
    try:
        reader = PdfReader(pdf_path)
        text = ""

        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"

        return text if text.strip() else "No readable text found in PDF"

    except Exception as e:
        return f"PDF Error: {str(e)}"


def _split_text_into_chunks(text, max_tokens=None):
    sentences = re.split(r'(?<=[.!?])\s+', text)
    chunks = []
    current_chunk = ""

    # ensure model/tokenizer available and determine token limit
    _ensure_model_loaded()
    if max_tokens is None:
        max_tokens = CHUNK_TOKEN_LIMIT

    def token_count(value):
        return len(_tokenizer(value, return_tensors='pt', truncation=False)['input_ids'][0])

    for sentence in sentences:
        sentence = sentence.strip()
        if not sentence:
            continue

        if current_chunk:
            candidate = f"{current_chunk} {sentence}"
        else:
            candidate = sentence

        if token_count(candidate) <= max_tokens:
            current_chunk = candidate
            continue

        if current_chunk:
            chunks.append(current_chunk)
            current_chunk = ""

        if token_count(sentence) <= max_tokens:
            current_chunk = sentence
            continue

        words = sentence.split()
        word_chunk = ""
        for word in words:
            if word_chunk:
                candidate = f"{word_chunk} {word}"
            else:
                candidate = word

            if token_count(candidate) <= max_tokens:
                word_chunk = candidate
            else:
                if word_chunk:
                    chunks.append(word_chunk)
                word_chunk = word

        if word_chunk:
            current_chunk = word_chunk

    if current_chunk:
        chunks.append(current_chunk)

    return chunks


def _summarize_chunks(chunks, max_len, min_len):
    partial_summaries = []
    _ensure_model_loaded()
    for chunk in chunks:
        result = _summarizer(
            chunk,
            max_length=max_len,
            min_length=min_len,
            do_sample=False
        )
        partial_summaries.append(result[0]['summary_text'])

    combined_summary = " ".join(partial_summaries)
    if len(partial_summaries) == 1:
        return combined_summary

    if len(_tokenizer(combined_summary, return_tensors='pt', truncation=False)['input_ids'][0]) <= CHUNK_TOKEN_LIMIT:
        result = _summarizer(
            combined_summary,
            max_length=max_len,
            min_length=min_len,
            do_sample=False
        )
        return result[0]['summary_text']

    return combined_summary


def generate_summary(text, summary_size='medium'):
    if summary_size == 'small':
        max_len = 100
        min_len = 40
    elif summary_size == 'medium':
        max_len = 250
        min_len = 120
    else:  # large
        max_len = 500
        min_len = 400

    try:
        chunks = _split_text_into_chunks(text)
        if not chunks:
            return "No readable text found in PDF"

        summary_text = _summarize_chunks(chunks, max_len, min_len)
        return summary_text
    except Exception as e:
        return f"Summary generation failed: {str(e)}"

