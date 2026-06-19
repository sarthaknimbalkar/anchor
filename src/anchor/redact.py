import re

_M = "[redacted]"
_PATTERNS = [
    re.compile(r"-----BEGIN [^-]+ PRIVATE KEY-----.*?-----END [^-]+ PRIVATE KEY-----", re.DOTALL),
    re.compile(r"eyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+"),
    re.compile(r"\b(?:ghp|gho|ghs)_[A-Za-z0-9]{20,}"),
    re.compile(r"\bxox[bap]-[A-Za-z0-9-]{10,}"),
    re.compile(r"\bsk_live_[A-Za-z0-9]{6,}"),
    re.compile(r"\bAIza[A-Za-z0-9_\-]{20,}"),
    re.compile(r"\bglpat-[A-Za-z0-9_\-]{10,}"),
    re.compile(r"(?i)\b(?:API[_-]?KEY|TOKEN|SECRET|PASSWORD)\s*[=:]\s*\S+"),
    re.compile(r"\b[a-zA-Z]+://[^:/\s]+:[^@/\s]+@"),
    re.compile(r"(?i)authorization:\s*\S+\s+\S+"),
    re.compile(r"(?i)(?:-u|--password)\s+\S+"),
]


def redact(text: str) -> str:
    for pat in _PATTERNS:
        text = pat.sub(_M, text)
    return text
