# file_utils.py
from pathlib import Path
import shutil
import filetype
import magic

def object_type_recognizer(path):
    """Recognizes if the path is a file or a directory."""
    return Path(path).is_file()

def pdf_detector(pdf_path):
    """Checks if file is a valid PDF."""
    with open(pdf_path, "rb") as f:
        kind = filetype.guess(f.read(261))
    if kind:
        return kind.mime == "application/pdf"
    return magic.from_file(str(pdf_path), mime=True) == "application/pdf"

def pdf_suffix_adding(ORIGIN_PATH, GOAL_PATH):
    """ checking if the current file is actually a file and actually a pdf file, 
    and adding .pdf suffix in order to make sure the file will open without any problems"""
    path = Path(ORIGIN_PATH)
    goal = Path(GOAL_PATH)

    if not object_type_recognizer(path): 
        return None

    if not pdf_detector(path):
        not_pdf_dir = goal / "not_a_pdf"
        not_pdf_dir.mkdir(parents=True, exist_ok=True)
        path.replace(not_pdf_dir / path.name)
        print(f"Moved non-PDF: {path} -> {not_pdf_dir / path.name}")
        return None

    if path.suffix.lower() != ".pdf":
        new_path = path.with_suffix('.pdf')
        path.rename(new_path)
        print(f"Renamed: {path} -> {new_path}")
        return new_path
    return path

def safe_file_move(src, dst):
    """Safely moves a file from source to destination."""
    if dst.exists():
        base, ext = dst.stem, dst.suffix
        counter = 1
        while (new_dst := dst.with_stem(f"{base}_{counter}")).exists():
            counter += 1
        dst = new_dst
    shutil.move(src, dst)
    return dst