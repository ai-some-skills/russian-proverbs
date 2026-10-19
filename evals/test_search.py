"""Observable retrieval and interface checks; run with unittest, no packages needed."""
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("proverb_search", ROOT / "scripts/search.py")
search = importlib.util.module_from_spec(spec)
spec.loader.exec_module(search)


class RetrievalTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.records = search.load_records()

    def test_use_case_retrieval(self):
        cases = [
            ("сначала проверить решение которое трудно отменить", "Семь раз примерь, а один отрежь."),
            ("поддержать после первой ошибки", "Первый блин всегда комом."),
            ("нужен результат вместо обещаний", "Соловья баснями не кормят."),
            ("расходы доставка полная стоимость", "За морем телушка полушка, да рубль перевоз."),
            ("чрезмерная медлительность мешает результату", "Тише едешь — никогда не доедешь."),
            ("не обобщать по единственному наблюдению", "Одна ласточка весны не делает."),
            ("слишком долго улучшать простое решение пора попробовать", "Попытка — не пытка, а спрос — не беда."),
        ]
        for query, expected in cases:
            with self.subTest(query=query):
                self.assertIn(expected, [r["text"] for r in search.search(self.records, query)[:3]])

    def test_duration_does_not_become_debt(self):
        candidates = search.search(self.records, "слишком долго улучшать простое решение пора попробовать")
        self.assertNotIn("Долг платежем красен.", [r["text"] for r in candidates[:5]])
        self.assertIn("Долг платежем красен.", [r["text"] for r in search.search(self.records, "возврат долга")[:3]])

    def test_variant_finds_canonical_record(self):
        found = search.search(self.records, "Дело не волк — в лес не убежит")
        self.assertEqual(found[0]["text"], "Дело не медведь — в лес не уйдет.")

    def test_unrelated_and_empty_queries_do_not_invent_candidates(self):
        for query in ("квантовый сверхпроводящий кубит", "", "подбери пословицу", "Kubernetes", "!!!"):
            with self.subTest(query=query):
                self.assertEqual(search.search(self.records, query), [])

    def test_tone_register_and_exclusion_are_real_filters(self):
        selected = search.search(self.records, "учиться ошибка поддержать", tone="supportive")
        self.assertTrue(selected)
        self.assertTrue(all(r["tone"] == "supportive" for r in selected))
        identifier = selected[0]["id"]
        self.assertNotIn(identifier, [r["id"] for r in search.search(self.records, "учиться ошибка поддержать", excluded={identifier})])
        selected = search.search(self.records, "самоиронично", register="colloquial")
        self.assertTrue(selected)
        self.assertTrue(all(r["register"] == "colloquial" for r in selected))

    def test_opposite_sayings_are_separate_and_exact_query_is_first(self):
        for text in ("Тише едешь — дальше будешь.", "Тише едешь — никогда не доедешь."):
            self.assertEqual(search.search(self.records, text)[0]["text"], text)

    def test_output_is_bounded_valid_json_and_preserves_cautions(self):
        candidates = search.search(self.records, "слово ошибка обещание время")
        for details in (True, False):
            for budget in (1000, 2200, 5000, 12000):
                with self.subTest(details=details, budget=budget):
                    output = search.bounded_output(candidates, limit=10, max_chars=budget, details=details)
                    self.assertLessEqual(len(output), budget)
                    parsed = json.loads(output)
                    self.assertLessEqual(parsed["returned"], 10)
                    self.assertEqual(parsed["returned"], len(parsed["matches"]))
                    for returned in parsed["matches"]:
                        original = next(r for r in self.records if r["id"] == returned["id"])
                        if original["caution"]:
                            self.assertEqual(returned["caution"], original["caution"])
                        self.assertIn("source", returned)
                        if not details:
                            self.assertNotIn("source_text", returned)

    def test_cli_works_outside_skill_directory_and_can_read_source(self):
        identifier = self.records[0]["id"]
        result = subprocess.run([sys.executable, str(ROOT / "scripts/search.py"), "--id", identifier, "--details"],
                                cwd="/private/tmp" if Path("/private/tmp").exists() else "/tmp",
                                capture_output=True, text=True, check=True)
        record = json.loads(result.stdout)["matches"][0]
        self.assertEqual(record["id"], identifier)
        self.assertGreater(record["source"]["pdf_page"], 0)
        self.assertIn("verification", record)

    def test_cli_rejects_invalid_limits_and_conflicting_modes(self):
        for arguments in (["ошибка", "--limit", "0"], ["ошибка", "--limit", "100"],
                          ["ошибка", "--max-chars", "1"], ["ошибка", "--id", "ryb-0001"]):
            result = subprocess.run([sys.executable, str(ROOT / "scripts/search.py"), *arguments],
                                    capture_output=True, text=True)
            self.assertEqual(result.returncode, 2)


if __name__ == "__main__":
    unittest.main()
