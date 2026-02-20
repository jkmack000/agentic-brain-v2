# LEARN-043 — Docling Document Parsing Library
<!-- type: LEARN -->
<!-- updated: 2026-02-18 -->
<!-- tags: docling, document-parsing, PDF, OCR, markdown, ingestion, MCP, IBM, tool -->
<!-- links: LEARN-001 -->

## Discovery
Docling is an open-source document parsing library that converts diverse file formats into structured Markdown/JSON. Useful as a pre-processing step when ingesting knowledge from formats the brain can't natively read (PDFs, DOCX, PPTX, scanned documents, audio).

## Key Details

- **Repo:** github.com/docling-project/docling
- **Maintainer:** IBM Research Zurich, hosted under LF AI & Data Foundation. MIT license. 15K+ stars.
- **Python:** 3.10+, Pydantic v2, UV for deps

### Input Formats
PDF (with layout analysis + OCR), DOCX, PPTX, XLSX, HTML, images (PNG/TIFF/JPEG), audio (WAV/MP3), LaTeX, WebVTT

### Output Formats
Markdown, HTML, DocTags, lossless JSON

### Key Capabilities
- Advanced PDF: layout recognition, reading order, table extraction, formula detection, code identification
- Extensive OCR for scanned PDFs
- Visual Language Model support (GraniteDocling)
- Automatic Speech Recognition for audio
- **MCP server** for agent integration
- Local execution (air-gapped environments)
- Native integrations: LangChain, LlamaIndex, CrewAI, Haystack

## Use Case for Brain System
**Pre-processing for ingestion.** When source material is in PDF, DOCX, PPTX, or scanned format:
1. Run Docling to convert to Markdown
2. Feed Markdown into normal brain ingestion pipeline (LLM reads → extracts knowledge → deposits typed .md files)

Not needed for sources already in text/Markdown/HTML (which the LLM can read directly).

## Installation
```bash
pip install docling
# or
uv add docling
```

## Known Issues
- Heavy dependency tree (ML models for layout analysis, OCR)
- First run downloads models (~1-2GB)
- Overkill for simple text extraction — only needed for complex layouts, tables, scanned docs
