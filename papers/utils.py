from pypdf import PdfReader
from transformers import pipeline

def extract_text_from_pdf(pdf_path):
    reader = PdfReader(pdf_path)

    text = ""

    for page in reader.pages:
        text += page.extract_text()

    return text


summarizer = pipeline(
    "summarization",
    model="sshleifer/distilbart-cnn-12-6"
)

def generate_summary(text):

    result = summarizer(
        text[:1000],
        max_length=150,
        min_length=50,
        do_sample=False
    )

    return result[0]['summary_text']


def extract_text_from_pdf(pdf_path):
    try:
        reader = PdfReader(pdf_path)
        text = ""

        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text

        return text if text.strip() else "No readable text found in PDF"

    except Exception as e:
        return f"PDF Error: {str(e)}"