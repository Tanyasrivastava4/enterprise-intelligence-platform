import os
import io
from typing import List, Dict, Any, Tuple
import pypdf
import pandas as pd

class DocumentParser:
    """Extracts raw text and structural metadata (page / row numbers) from various file formats."""

    @staticmethod
    def parse_pdf(file_path: str) -> List[Dict[str, Any]]:
        """Parses PDF page by page, returning text and page numbers."""
        pages_content = []
        with open(file_path, "rb") as f:
            reader = pypdf.PdfReader(f)
            for page_idx, page in enumerate(reader.pages):
                text = page.extract_text() or ""
                cleaned_text = text.strip()
                if cleaned_text:
                    pages_content.append({
                        "text": cleaned_text,
                        "page_or_row": page_idx + 1,
                        "source_type": "pdf_page"
                    })
        return pages_content

    @staticmethod
    def parse_csv(file_path: str) -> List[Dict[str, Any]]:
        """Parses CSV row by row, converting rows into structured text representations."""
        records = []
        df = pd.read_csv(file_path)
        # Fill NaN values with empty string or N/A
        df = df.fillna("N/A")
        columns = list(df.columns)
        
        # Batch every 5-10 rows or row-by-row if large
        for row_idx, row in df.iterrows():
            row_repr = ", ".join([f"{col}: {row[col]}" for col in columns])
            text = f"Record [Row {row_idx + 1}]: {row_repr}"
            records.append({
                "text": text,
                "page_or_row": row_idx + 1,
                "source_type": "csv_row"
            })
        return records

    @staticmethod
    def parse_markdown(file_path: str) -> List[Dict[str, Any]]:
        """Parses Markdown text, splitting sections by headers when possible."""
        with open(file_path, "r", encoding="utf-8", errors="replace") as f:
            content = f.read()
        
        # Split by top-level or second-level headers while keeping headers
        sections = []
        lines = content.splitlines()
        current_section = []
        section_idx = 1
        
        for line in lines:
            if line.startswith("# ") or line.startswith("## "):
                if current_section:
                    sections.append({
                        "text": "\n".join(current_section).strip(),
                        "page_or_row": section_idx,
                        "source_type": "markdown_section"
                    })
                    section_idx += 1
                    current_section = []
            current_section.append(line)
            
        if current_section:
            sections.append({
                "text": "\n".join(current_section).strip(),
                "page_or_row": section_idx,
                "source_type": "markdown_section"
            })
            
        return sections if sections else [{
            "text": content.strip(),
            "page_or_row": 1,
            "source_type": "markdown_file"
        }]

    @staticmethod
    def parse_txt(file_path: str) -> List[Dict[str, Any]]:
        """Parses plain text file."""
        with open(file_path, "r", encoding="utf-8", errors="replace") as f:
            content = f.read()
            
        paragraphs = [p.strip() for p in content.split("\n\n") if p.strip()]
        if not paragraphs:
            return [{"text": content.strip(), "page_or_row": 1, "source_type": "txt_file"}]
            
        return [{
            "text": para,
            "page_or_row": idx + 1,
            "source_type": "txt_paragraph"
        } for idx, para in enumerate(paragraphs)]

    @classmethod
    def parse(cls, file_path: str, file_type: str) -> List[Dict[str, Any]]:
        ext = file_type.lower().replace(".", "")
        if ext == "pdf":
            return cls.parse_pdf(file_path)
        elif ext == "csv":
            return cls.parse_csv(file_path)
        elif ext in ["md", "markdown"]:
            return cls.parse_markdown(file_path)
        elif ext in ["txt", "text"]:
            return cls.parse_txt(file_path)
        else:
            raise ValueError(f"Unsupported file type: {file_type}")
