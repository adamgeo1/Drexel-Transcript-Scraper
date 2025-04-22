import fitz
from pathlib import Path

TARGET_LINES = [
    "Information for",
    "Name :"
]

def redactName(path: Path):
    doc = fitz.open(path)
    page = doc[0]
    for line in TARGET_LINES:
        matches = page.search_for(line)
        for rect in matches:
            fullRect = fitz.Rect(0, rect.y0, page.rect.width, rect.y1)
            page.add_redact_annot(fullRect, fill=(0, 0, 0))
    page.apply_redactions()
    tempPath = path.with_suffix(".tmp.pdf")
    doc.save(tempPath, garbage=4, deflate=True)
    doc.close()
    tempPath.replace(path)

def main():
    folderPath = Path.cwd() / "TranscriptDownloads"
    pdfs = folderPath.glob('*.pdf')
    for pdfPath in pdfs:
        print(f"Redacting {pdfPath.name}")
        redactName(pdfPath)

if __name__ == '__main__':
    main()