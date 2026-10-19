#!/usr/bin/env python3
"""Bounded offline lexical retrieval over the bundled proverb corpus (Python 3.9+)."""
from __future__ import annotations

import argparse
from collections import Counter
import json
import math
from pathlib import Path
import re
import sys
import unicodedata

ROOT = Path(__file__).resolve().parents[1]
TONES = ("neutral", "supportive", "ironic", "critical")
REGISTERS = ("standard", "colloquial", "old-fashioned")
STOP = set("а без бы был была были было в во вот все всего всем для до да же за и из или к как ко кто ли на над не ни но о об от по под при про с со так то у что это этот эта эти тот та те я ты он она мы вы они мне мне моя свой себя его ее их чем тем чтобы если где когда после перед надо нужно можно есть будет быть уже еще очень самый такой такой здесь там подбери подобрать пословица пословицы поговорка поговорки выражение выражения вариант варианты подходящий текст сказать дело дела ситуацию ситуации".split())
# Light stemming, deliberately not a morphological analyzer. Preserve negations
# inside words (неудача != удача), normalize е/ё, then approximate common endings.
SUFFIXES = sorted(set("иями ями ами иями иями остью ости ость аться яться иться ивать ывать ировать ивание ение ание ения ания ать ять ить еть ют ут ит ат ят ет ыми ими ого его ому ему ая яя ое ее ые ие ой ый ий ых их ам ям ах ях ов ев ей ом ем ы и а я у ю е о ь".split()), key=len, reverse=True)


def normalize(text: str) -> str:
    return unicodedata.normalize("NFKC", text).lower().replace("ё", "е")


def stem(word: str) -> str:
    # Keep duration separate from debt: stripping "о" from "долго" is harmful.
    if word in {"долго", "долгий", "долгая", "долгое", "долгие", "долгую", "долгого", "долгому", "долгим", "долгих"}:
        return "медл"
    # Common lexical alternatives for making a low-cost attempt.
    if word.startswith(("попроб", "пробов", "попыт", "эксперимент")):
        return "проба"
    if word.startswith(("медл", "затягив", "затянут", "затяну", "длитель")):
        return "медл"
    for suffix in SUFFIXES:
        if word.endswith(suffix) and len(word) - len(suffix) >= 3:
            word = word[:-len(suffix)]
            break
    # A few high-value derivational families used in the editorial descriptions.
    for prefix in ("провер", "ошиб", "обуч", "необрат", "подготов", "осторож", "тороп", "поддерж", "поспеш", "опозд", "повтор", "договор", "обещан", "вниман", "надежд"):
        if word.startswith(prefix):
            return prefix
    return word


STOP_STEMS = {stem(word) for word in STOP}


def terms(text: str) -> list[str]:
    return [key for word in re.findall(r"[а-яa-z]+", normalize(text))
            if len(word) > 1 and word not in STOP
            and (key := stem(word)) not in STOP_STEMS]


def load_records(path: Path | None = None) -> list[dict]:
    with (path or ROOT / "data" / "sayings.jsonl").open(encoding="utf-8") as stream:
        return [json.loads(line) for line in stream if line.strip()]


def field_texts(record: dict) -> list[tuple[str, float]]:
    return [(record["text"], 2.2),
            (" ".join(v["text"] for v in record["variants"]), 2.0),
            (record["meaning"], 2.0),
            (" ".join(record["situations"]), 3.0),
            (" ".join(record["tags"]), 2.5)]


def search(records: list[dict], query: str, *, tone: str | None = None,
           register: str | None = None, excluded: set[str] | None = None) -> list[dict]:
    query_terms = set(terms(query))
    if not query_terms:
        return []
    documents = []
    frequency: Counter = Counter()
    for record in records:
        weighted: Counter = Counter()
        for text, weight in field_texts(record):
            for term, count in Counter(terms(text)).items():
                weighted[term] += weight * min(count, 2)
        frequency.update(weighted.keys())
        documents.append((record, weighted))
    average_length = sum(sum(d.values()) for _, d in documents) / max(1, len(documents))
    exact_query = " ".join(re.findall(r"[а-яa-z]+", normalize(query)))
    results = []
    for record, document in documents:
        if ((tone and record["tone"] != tone)
                or (register and record["register"] != register)
                or record["id"] in (excluded or set())):
            continue
        matched = query_terms & document.keys()
        if not matched:
            continue
        length = sum(document.values())
        score = 0.0
        for term in matched:
            idf = math.log(1 + (len(documents) - frequency[term] + 0.5) / (frequency[term] + 0.5))
            tf = document[term]
            score += idf * (tf * 2.2) / (tf + 1.2 * (0.25 + 0.75 * length / max(1, average_length)))
        score *= 0.5 + len(matched) / len(query_terms)
        for wording in [record["text"], *(v["text"] for v in record["variants"])]:
            phrase = " ".join(re.findall(r"[а-яa-z]+", normalize(wording)))
            if exact_query == phrase or (len(exact_query.split()) >= 3 and exact_query in phrase):
                score += 30.0
                break
        results.append((score, record["id"], record))
    results.sort(key=lambda item: (-item[0], item[1]))
    return [record for _, _, record in results]


def compact(record: dict) -> dict:
    source = record["source"]
    result = {key: record[key] for key in ("id", "text", "meaning", "tone", "register")}
    if record["caution"]:
        result["caution"] = record["caution"]
    result["source"] = f"Рыбникова, 1961, с. {source['book_page']} (PDF {source['pdf_page']})"
    return result


def bounded_output(records: list[dict], *, limit: int = 5, max_chars: int = 5000,
                   details: bool = False) -> str:
    result = {"matches": [], "returned": 0, "budget_limited": False,
              "note": "Лексические кандидаты; уместность и современную распространенность оценить отдельно."}
    for record in records[:limit]:
        item = dict(record) if details else compact(record)
        trial = dict(result, matches=[*result["matches"], item], returned=len(result["matches"]) + 1)
        if len(json.dumps(trial, ensure_ascii=False, separators=(",", ":"))) > max_chars:
            result["budget_limited"] = True
            break
        result = trial
    return json.dumps(result, ensure_ascii=False, separators=(",", ":"))


def ranged_int(low: int, high: int):
    def parse(value: str) -> int:
        number = int(value)
        if not low <= number <= high:
            raise argparse.ArgumentTypeError(f"Допустимо {low}..{high}")
        return number
    return parse


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("query", nargs="?", help="Смысл, ситуация или текст выражения")
    parser.add_argument("--id", dest="record_id", help="Прочитать одну запись по постоянному ID")
    parser.add_argument("--tone", choices=TONES)
    parser.add_argument("--register", choices=REGISTERS)
    parser.add_argument("--exclude-id", action="append", default=[])
    parser.add_argument("--limit", type=ranged_int(1, 10), default=5)
    parser.add_argument("--max-chars", type=ranged_int(1000, 12000), default=5000)
    parser.add_argument("--details", action="store_true")
    args = parser.parse_args()
    if bool(args.query) == bool(args.record_id):
        parser.error("Передай либо запрос, либо --id")
    if args.record_id and (args.tone or args.register or args.exclude_id):
        parser.error("Фильтры применяются к поиску; --id читает запись напрямую")
    try:
        records = load_records()
    except (OSError, ValueError) as exc:
        print(json.dumps({"error": "Не удалось прочитать корпус", "reason": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 1
    if args.record_id:
        candidates = [r for r in records if r["id"] == args.record_id]
    else:
        candidates = search(records, args.query, tone=args.tone, register=args.register, excluded=set(args.exclude_id))
    print(bounded_output(candidates, limit=args.limit, max_chars=args.max_chars, details=args.details))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
