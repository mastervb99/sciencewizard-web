"""
Velvet Research - Report Generation Service

Uses Claude API directly for manuscript generation.
"""
import os
import asyncio
import traceback
from pathlib import Path
from datetime import datetime
from typing import Optional, Callable


class ReportGenerator:
    """
    Generates manuscripts using Claude API.
    """

    def __init__(self, upload_path: str, output_dir: str):
        self.upload_path = Path(upload_path)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.progress = 0.0
        self.status = "pending"
        self.error = None
        self.report_path = None

    def _categorize_files(self) -> tuple[list, list]:
        """Categorize uploaded files into data and documents."""
        data_files = []
        doc_files = []

        for f in self.upload_path.iterdir():
            if f.is_file():
                ext = f.suffix.lower()
                if ext in {'.csv', '.xlsx', '.xls'}:
                    data_files.append(f)
                elif ext in {'.docx', '.pdf', '.txt'}:
                    doc_files.append(f)

        return data_files, doc_files

    def _extract_text_from_docs(self, doc_files: list) -> str:
        """Extract text content from document files."""
        text_parts = []

        for doc_path in doc_files:
            ext = doc_path.suffix.lower()

            if ext == '.txt':
                try:
                    text_parts.append(doc_path.read_text(errors='ignore'))
                except Exception:
                    pass

            elif ext == '.docx':
                try:
                    from docx import Document
                    doc = Document(str(doc_path))
                    text_parts.append('\n'.join([p.text for p in doc.paragraphs]))
                except Exception:
                    pass

            elif ext == '.pdf':
                try:
                    import fitz  # PyMuPDF
                    with fitz.open(str(doc_path)) as pdf:
                        for page in pdf:
                            text_parts.append(page.get_text())
                except ImportError:
                    # PyMuPDF not available, skip PDF
                    pass
                except Exception:
                    pass

        return '\n\n'.join(text_parts)

    def _read_data_preview(self, data_files: list) -> str:
        """Read preview of data files."""
        previews = []

        for data_path in data_files:
            ext = data_path.suffix.lower()
            try:
                import pandas as pd
                if ext == '.csv':
                    df = pd.read_csv(data_path, nrows=100)
                elif ext in {'.xlsx', '.xls'}:
                    df = pd.read_excel(data_path, nrows=100)
                else:
                    continue

                preview = f"File: {data_path.name}\n"
                preview += f"Columns: {list(df.columns)}\n"
                preview += f"Shape: {df.shape}\n"
                preview += f"Sample:\n{df.head(10).to_string()}\n"
                previews.append(preview)
            except Exception as e:
                previews.append(f"File: {data_path.name} - Error reading: {e}")

        return '\n\n'.join(previews)

    async def generate(
        self,
        progress_callback: Optional[Callable[[float, str], None]] = None
    ) -> str:
        """
        Generate manuscript using Claude API.
        """
        try:
            self.status = "processing"
            await self._update_progress(0.1, "Loading files...", progress_callback)

            data_files, doc_files = self._categorize_files()

            if not data_files and not doc_files:
                raise ValueError("No valid files found in upload")

            # Extract content
            await self._update_progress(0.2, "Analyzing content...", progress_callback)
            doc_content = self._extract_text_from_docs(doc_files) if doc_files else ""
            data_preview = self._read_data_preview(data_files) if data_files else ""

            await self._update_progress(0.4, "Generating manuscript with AI...", progress_callback)

            # Use Anthropic API
            import anthropic

            client = anthropic.Anthropic()

            prompt = f"""Based on the following research materials, generate a complete academic manuscript.

Research Documents:
{doc_content[:10000] if doc_content else "No documents provided."}

Data Summary:
{data_preview[:5000] if data_preview else "No data files provided."}

Please generate a complete academic manuscript with these sections:
1. Title
2. Abstract (250 words)
3. Introduction
4. Methods
5. Results
6. Discussion
7. Conclusion
8. References

Format the output with clear section headings using ## for main sections.
Write in formal academic style appropriate for a peer-reviewed journal.
If data is provided, describe appropriate statistical analyses.
If no data is provided, generate a conceptual manuscript based on the documents."""

            response = client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=8000,
                messages=[{"role": "user", "content": prompt}]
            )

            manuscript_text = response.content[0].text

            await self._update_progress(0.8, "Formatting Word document...", progress_callback)

            # Create Word document
            from docx import Document
            from docx.shared import Pt, Inches
            from docx.enum.text import WD_ALIGN_PARAGRAPH

            doc = Document()

            # Process markdown-style content
            lines = manuscript_text.split('\n')
            for line in lines:
                line = line.strip()
                if not line:
                    continue

                if line.startswith('## '):
                    # Main heading
                    doc.add_heading(line[3:], level=1)
                elif line.startswith('### '):
                    # Subheading
                    doc.add_heading(line[4:], level=2)
                elif line.startswith('# '):
                    # Title
                    title = doc.add_heading(line[2:], level=0)
                    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
                elif line.startswith('**') and line.endswith('**'):
                    # Bold paragraph
                    para = doc.add_paragraph()
                    run = para.add_run(line[2:-2])
                    run.bold = True
                else:
                    # Regular paragraph
                    para = doc.add_paragraph(line)
                    para.paragraph_format.first_line_indent = Inches(0.5)

            # Save
            report_path = self.output_dir / f"manuscript_{datetime.now().strftime('%Y%m%d_%H%M%S')}.docx"
            doc.save(str(report_path))

            await self._update_progress(1.0, "Complete!", progress_callback)
            self.status = "completed"
            self.report_path = str(report_path)

            return str(report_path)

        except Exception as e:
            self.status = "failed"
            self.error = str(e)
            traceback.print_exc()
            raise

    async def _update_progress(
        self,
        progress: float,
        message: str,
        callback: Optional[Callable] = None
    ):
        """Update progress and call callback if provided."""
        self.progress = progress
        if callback:
            try:
                await callback(progress, message)
            except Exception:
                pass


# Background job runner
_running_jobs = {}


async def run_generation_job(
    job_id: str,
    upload_path: str,
    output_dir: str,
    db_update_callback
):
    """
    Run report generation as background task.
    """
    generator = ReportGenerator(upload_path, output_dir)
    _running_jobs[job_id] = generator

    try:
        async def progress_callback(progress, message):
            await db_update_callback(job_id, "processing", progress)

        report_path = await generator.generate(progress_callback=progress_callback)
        await db_update_callback(job_id, "completed", 1.0, report_path=report_path)

    except Exception as e:
        await db_update_callback(job_id, "failed", generator.progress, error=str(e))

    finally:
        if job_id in _running_jobs:
            del _running_jobs[job_id]


def get_job_progress(job_id: str) -> Optional[float]:
    """Get current progress of running job."""
    if job_id in _running_jobs:
        return _running_jobs[job_id].progress
    return None
