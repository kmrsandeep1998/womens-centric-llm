from __future__ import annotations

from pathlib import Path
import hashlib
import xml.etree.ElementTree as ET
import zipfile


W_NS = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def iter_unique_docx(paths):
    seen = set()
    for path in paths:
        digest = sha256_file(path)
        if digest in seen:
            continue
        seen.add(digest)
        yield path


def extract_docx_paragraphs(path: Path):
    with zipfile.ZipFile(path) as zf:
        xml = zf.read("word/document.xml")
    root = ET.fromstring(xml)
    paragraphs = []
    for para in root.findall(".//w:p", W_NS):
        parts = [node.text for node in para.findall(".//w:t", W_NS) if node.text]
        text = "".join(parts).strip()
        if text:
            paragraphs.append(text)
    return paragraphs
