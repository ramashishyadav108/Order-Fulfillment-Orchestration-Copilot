
from __future__ import annotations
import re
from pathlib import Path
from typing import Dict, List, Optional
from pydantic import BaseModel

from src.config import settings


class DocumentChunk(BaseModel):
    chunk_id: str
    source: str
    title: str
    content: str
    metadata: Dict[str, str]


class DocumentLoader:

    def __init__(self, docs_dir: Optional[Path] = None):
        self.docs_dir = docs_dir or settings.RAG_DOCS_DIR
        self.chunk_size = settings.RAG_CHUNK_SIZE
        self.chunk_overlap = settings.RAG_CHUNK_OVERLAP

    def load_all(self) -> List[DocumentChunk]:
        if not self.docs_dir.exists():
            return []

        all_chunks = []
        for file_path in self.docs_dir.glob("*.md"):
            chunks = self._process_file(file_path)
            all_chunks.extend(chunks)

        return all_chunks

    def _process_file(self, file_path: Path) -> List[DocumentChunk]:
        content = file_path.read_text(encoding="utf-8")
        
        # Simple markdown splitting by headers
        sections = re.split(r'\n(?=## )', content)
        
        chunks = []
        source_name = file_path.stem
        main_title = source_name.replace('_', ' ').title()
        
        for i, section in enumerate(sections):
            if not section.strip():
                continue
                
            # Extract section title if present
            title_match = re.match(r'^##\s+(.+)$', section.strip(), re.MULTILINE)
            section_title = title_match.group(1) if title_match else f"Section {i+1}"
            
            # If section is too large, split it further (simplified for this capstone)
            if len(section) > self.chunk_size * 2:
                paragraphs = section.split('\n\n')
                current_chunk = ""
                part = 1
                for p in paragraphs:
                    if len(current_chunk) + len(p) > self.chunk_size and current_chunk:
                        chunks.append(
                            DocumentChunk(
                                chunk_id=f"{source_name}_{i}_{part}",
                                source=source_name,
                                title=f"{main_title} - {section_title} (Part {part})",
                                content=current_chunk.strip(),
                                metadata={"source": source_name, "section": section_title}
                            )
                        )
                        current_chunk = p
                        part += 1
                    else:
                        current_chunk += "\n\n" + p
                
                if current_chunk:
                    chunks.append(
                        DocumentChunk(
                            chunk_id=f"{source_name}_{i}_{part}",
                            source=source_name,
                            title=f"{main_title} - {section_title} (Part {part})",
                            content=current_chunk.strip(),
                            metadata={"source": source_name, "section": section_title}
                        )
                    )
            else:
                chunks.append(
                    DocumentChunk(
                        chunk_id=f"{source_name}_{i}",
                        source=source_name,
                        title=f"{main_title} - {section_title}",
                        content=section.strip(),
                        metadata={"source": source_name, "section": section_title}
                    )
                )
                
        return chunks
