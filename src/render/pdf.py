"""PDF rendering — writes ReportLab-generated PDF buffer to file."""

from pathlib import Path
from io import BytesIO


def save_pdf(buf: BytesIO, output_path: str | Path) -> Path:
    """Save a PDF buffer to disk.

    Args:
        buf: BytesIO containing PDF data.
        output_path: Destination path.

    Returns:
        Path to the saved PDF.
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    data = buf.read()
    output_path.write_bytes(data)
    return output_path
