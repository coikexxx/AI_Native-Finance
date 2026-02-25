"""Document parsing and text chunking utilities."""
from bs4 import BeautifulSoup
from typing import List
import re
import logging

logger = logging.getLogger(__name__)


def extract_text_from_html(html: str) -> str:
    """Extract clean text from HTML content."""
    try:
        soup = BeautifulSoup(html, "lxml")
        # Remove script and style elements
        for tag in soup(["script", "style", "nav", "footer", "header"]):
            tag.decompose()
        text = soup.get_text(separator="\n", strip=True)
        # Clean up excessive whitespace
        text = re.sub(r"\n{3,}", "\n\n", text)
        text = re.sub(r" {2,}", " ", text)
        return text.strip()
    except Exception as e:
        logger.error(f"Error extracting HTML text: {e}")
        return ""


def chunk_text(
    text: str,
    chunk_size: int = 1000,
    overlap: int = 100,
    min_chunk_size: int = 100,
) -> List[str]:
    """Split text into overlapping chunks for vector store ingestion."""
    if not text:
        return []

    # Split by paragraphs first
    paragraphs = re.split(r"\n\n+", text)
    chunks = []
    current_chunk = ""

    for para in paragraphs:
        para = para.strip()
        if not para:
            continue

        if len(current_chunk) + len(para) + 2 <= chunk_size:
            current_chunk = (current_chunk + "\n\n" + para).strip()
        else:
            if current_chunk and len(current_chunk) >= min_chunk_size:
                chunks.append(current_chunk)
            if len(para) > chunk_size:
                # Split long paragraph by sentences
                sentences = re.split(r"(?<=[.!?])\s+", para)
                temp = ""
                for sent in sentences:
                    if len(temp) + len(sent) + 1 <= chunk_size:
                        temp = (temp + " " + sent).strip()
                    else:
                        if temp and len(temp) >= min_chunk_size:
                            chunks.append(temp)
                        temp = sent
                if temp and len(temp) >= min_chunk_size:
                    chunks.append(temp)
                current_chunk = ""
            else:
                # Start new chunk with overlap from end of previous
                if chunks and overlap > 0:
                    prev_words = current_chunk.split()[-overlap // 10:]
                    current_chunk = " ".join(prev_words) + "\n\n" + para
                else:
                    current_chunk = para

    if current_chunk and len(current_chunk) >= min_chunk_size:
        chunks.append(current_chunk)

    return chunks


def generate_chunk_ids(ticker: str, source_type: str, chunks: List[str]) -> List[str]:
    """Generate unique IDs for document chunks."""
    return [f"{ticker}_{source_type}_{i:04d}" for i in range(len(chunks))]


def generate_chunk_metadatas(
    ticker: str,
    source_type: str,
    source_label: str,
    source_url: str = "",
    chunks_count: int = 0,
) -> List[dict]:
    """Generate metadata for document chunks."""
    return [
        {
            "ticker": ticker,
            "source_type": source_type,
            "source_label": source_label,
            "source_url": source_url,
            "chunk_index": i,
        }
        for i in range(chunks_count)
    ]
