"""OCR and document processing worker tasks package."""

from workers.ocr.tasks import process_document_task

__all__ = ["process_document_task"]
