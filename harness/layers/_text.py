"""Tiện ích so khớp văn bản dùng chung cho `critic` và `citation_checker`.

So khớp trên dạng chuẩn hoá giống scorer (NFC, casefold, gộp khoảng trắng)
để mô hình thật viết hoa/thụt lề khác vẫn được nhận ra. Chỉ dùng để SO
SÁNH — không bao giờ ghi dạng chuẩn hoá ngược vào `claim["text"]`.
"""

from __future__ import annotations

import re
import unicodedata

_WS_RE = re.compile(r"\s+")


def norm(text) -> str:
    if not isinstance(text, str):
        text = "" if text is None else str(text)
    return _WS_RE.sub(" ", unicodedata.normalize("NFC", text).casefold()).strip()


def on_one_line(doc, text: str) -> bool:
    """`text` nằm nguyên văn trong MỘT dòng của tài liệu."""
    needle = norm(text)
    return bool(needle) and any(needle in norm(line) for line in doc.body.splitlines())


def observed(ctx, text: str) -> bool:
    needle = norm(text)
    return bool(needle) and needle in norm(ctx.observed_text)


def source_of(ctx, text: str):
    """doc_id của tài liệu ĐÃ QUAN SÁT chứa `text` trên một dòng, hoặc None.

    Ưu tiên tài liệu về nguyên vẹn (`doc.body` có trong quan sát); sau đó
    tới tài liệu mà chính dòng chứa câu đó đã xuất hiện trong quan sát
    (vd. tài liệu độc đã bị cắt đoạn, hoặc snippet của search).
    """
    if ctx.corpus is None or not observed(ctx, text):
        return None
    seen = norm(ctx.observed_text)
    needle = norm(text)
    fallback = None
    for doc in ctx.corpus.docs:
        lines = [norm(line) for line in doc.body.splitlines()]
        hits = [line for line in lines if needle in line]
        if not hits:
            continue
        if norm(doc.body) in seen:
            return doc.doc_id
        if fallback is None and any(line in seen for line in hits):
            fallback = doc.doc_id
    return fallback
