import re, tempfile, subprocess, pathlib

EMAIL_RE = re.compile(r"\b[\w.%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")
PHONE_RE = re.compile(r"\b(\+?49|0)[1-9]\d{7,}\b")
DOB_RE   = re.compile(r"\b(0[1-9]|[12]\d|3[01])\.(0[1-9]|1[0-2])\.(19|20)\d{2}\b")

def ocr_file(path: str) -> str:
    out = pathlib.Path(tempfile.mkstemp(suffix=".txt")[1])
    subprocess.run(
        ["tesseract", path, str(out)[:-4]],
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )
    return pathlib.Path(str(out)).read_text(encoding="utf-8", errors="ignore")

def redact(txt: str) -> str:
    txt = EMAIL_RE.sub("[email:redacted]", txt)
    txt = PHONE_RE.sub("[phone:redacted]", txt)
    txt = DOB_RE.sub("[dob:redacted]", txt)
    return txt

def extract_and_redact(path: str) -> str:
    try:
        plain = ocr_file(path)
        return redact(plain)
    except Exception:
        return "[attachment:redacted]"
