import os
import shutil
from fastapi import UploadFile
from PIL import Image, ImageEnhance
import pytesseract


def save_upload_file(upload_file: UploadFile, destination: str):
    try:
        with open(destination, "wb") as buffer:
            shutil.copyfileobj(upload_file.file, buffer)
    finally:
        upload_file.file.close()


def extract_text_from_image(image_path: str) -> str:
    import platform

    if platform.system() == "Windows":
        pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

    image = Image.open(image_path)
    image = image.convert("L")
    scale_factor = 2
    image = image.resize(
        (image.width * scale_factor, image.height * scale_factor),
        Image.LANCZOS,
    )
    image = ImageEnhance.Contrast(image).enhance(1.5)

    custom_config = r"--oem 3 --psm 6"
    text = pytesseract.image_to_string(image, lang="eng", config=custom_config)
    return text


def extract_text_from_lab_document(file_path: str) -> str:
    ext = os.path.splitext(file_path)[1].lower()

    if ext != ".pdf":
        return extract_text_from_image(file_path)

    try:
        import pdfplumber
        pages_text = []
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                pages_text.append(page.extract_text() or "")
        text = "\n".join(pages_text).strip()
        if text:
            return text
    except Exception as e:
        print(f"[lab-report] pdfplumber text extraction failed: {e}")

    try:
        from pdf2image import convert_from_path
        import platform

        if platform.system() == "Windows":
            pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

        page_images = convert_from_path(file_path)
        ocr_text = [pytesseract.image_to_string(img, lang='eng') for img in page_images]
        text = "\n".join(ocr_text).strip()
        if text:
            return text
    except Exception as e:
        print(f"[lab-report] PDF OCR fallback failed: {e}")

    raise ValueError(
        "PDF se koi text nahi nikal paya (na embedded text mila, na OCR chala). "
        "File corrupted, password-protected, ya blank ho sakti hai."
    )

