#!/usr/bin/env python3
"""Validate corpus structure, provenance and duplicate canonical/variant strings."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]


def normalized(text):
    return re.sub(r"[^а-яa-z]", "", text.lower().replace("ё", "е"))


def validate(pdf_path=None):
    errors = []
    records = []
    for number, line in enumerate((ROOT / "data/sayings.jsonl").read_text(encoding="utf-8").splitlines(), 1):
        try:
            records.append(json.loads(line))
        except ValueError as exc:
            errors.append(f"Строка {number}: {exc}")
    manifest = json.loads((ROOT / "data/sources.json").read_text(encoding="utf-8"))
    source_ids = {s["id"] for s in manifest["sources"]}
    seen_ids, seen_texts = set(), {}
    for record in records:
        identifier = record.get("id", "?")
        required = {"id", "text", "source_text", "variants", "meaning", "situations", "tags", "tone", "register", "caution", "source", "verification"}
        if required - record.keys():
            errors.append(f"{identifier}: отсутствуют {sorted(required - record.keys())}")
            continue
        if identifier in seen_ids:
            errors.append(f"{identifier}: повтор ID")
        seen_ids.add(identifier)
        if not re.fullmatch(r"ryb-\d{4}", identifier):
            errors.append(f"{identifier}: неверный ID")
        if record["tone"] not in {"neutral", "supportive", "ironic", "critical"}:
            errors.append(f"{identifier}: неверный тон")
        if record["register"] not in {"standard", "colloquial", "old-fashioned"}:
            errors.append(f"{identifier}: неверный регистр")
        if not record["meaning"] or not record["situations"] or not record["tags"]:
            errors.append(f"{identifier}: пустая разметка")
        source = record["source"]
        if source.get("id") not in source_ids or not source.get("section"):
            errors.append(f"{identifier}: отсутствует источник/раздел")
        if not (34 <= source.get("pdf_page", 0) <= 197 and source.get("book_page") == source["pdf_page"] + 1):
            errors.append(f"{identifier}: проверить пагинацию")
        if normalized(record["text"]) != normalized(record["source_text"]):
            errors.append(f"{identifier}: текст не соответствует сохраненной исходной форме")
        for wording in [record["text"], *(v["text"] for v in record["variants"])]:
            key = normalized(wording)
            if key in seen_texts:
                errors.append(f"{identifier}: дублирует формулировку {seen_texts[key]}")
            seen_texts[key] = identifier
        for variant in record["variants"]:
            if not (34 <= variant.get("pdf_page", 0) <= 197 and variant.get("book_page") == variant["pdf_page"] + 1):
                errors.append(f"{identifier}: страница варианта не указана или неверна")
        if record["verification"].get("text") not in {"text_layer_matched", "scan_checked"}:
            errors.append(f"{identifier}: отсутствует статус проверки")
    if manifest.get("record_count") != len(records):
        errors.append("Количество записей не совпадает с манифестом")
    if manifest.get("variant_count") != sum(len(r.get("variants", [])) for r in records):
        errors.append("Количество вариантов не совпадает с манифестом")
    if pdf_path:
        try:
            from pypdf import PdfReader
        except ImportError:
            errors.append("Для необязательной сверки PDF требуется pypdf; обычная проверка и поиск работают без него")
            return errors, len(records)
        path = Path(pdf_path)
        source = next(s for s in manifest["sources"] if s["id"] == "rybnikova-1961")
        if hashlib.sha256(path.read_bytes()).hexdigest() != source["sha256"]:
            errors.append("PDF отличается от исходного файла по SHA-256; пагинация и текст требуют повторной проверки")
            return errors, len(records)
        reader = PdfReader(path)
        page_cache = {}
        for record in records:
            phrases = [(record["text"], record["source"]["pdf_page"])]
            phrases.extend((v["text"], v["pdf_page"]) for v in record["variants"])
            for text, page in phrases:
                if page not in page_cache:
                    page_cache[page] = normalized(reader.pages[page - 1].extract_text())
                if normalized(text) not in page_cache[page]:
                    errors.append(f"{record['id']}: формулировка отсутствует в текстовом слое страницы PDF {page}")
    return errors, len(records)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pdf", help="Необязательная сверка с исходным PDF; требует pypdf")
    arguments = parser.parse_args()
    try:
        problems, count = validate(arguments.pdf)
    except (OSError, ValueError, KeyError, TypeError, IndexError) as exc:
        print(f"Ошибка чтения корпуса: {exc}", file=sys.stderr)
        raise SystemExit(1)
    print(json.dumps({"records": count, "errors": problems}, ensure_ascii=False))
    raise SystemExit(bool(problems))
