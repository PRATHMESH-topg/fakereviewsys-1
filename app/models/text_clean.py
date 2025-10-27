import re

URL_RE = re.compile(r"http\S+|www\.\S+")
HTML_RE = re.compile(r"<.*?>")
MULTI_WS = re.compile(r"\s+")

def clean_text(s: str) -> str:
    s = s or ""
    s = s.lower()
    s = URL_RE.sub(" ", s)
    s = HTML_RE.sub(" ", s)
    s = re.sub(r"[^a-z0-9\s\!\?\'\,\.\-]", " ", s)
    s = MULTI_WS.sub(" ", s).strip()
    return s
