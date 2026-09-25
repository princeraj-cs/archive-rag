import json
from pathlib import Path

from app.rag_chain import answer_question


EVAL_FILE = Path(__file__).with_name("test_questions.json")


def main() -> int:
    cases = json.loads(EVAL_FILE.read_text(encoding="utf-8"))
    passed = 0

    for index, case in enumerate(cases, start=1):
        answer, sources = answer_question(case["question"])
        expected_parts = [part.lower() for part in case["expected_answer_contains"]]
        matched = all(part in answer.lower() for part in expected_parts)
        has_sources = bool(sources)
        status = "PASS" if matched and has_sources else "FAIL"
        print(f"{status} {index}: {case['question']}")
        if status == "PASS":
            passed += 1

    print(f"{passed}/{len(cases)} cases passed")
    return 0 if passed == len(cases) else 1


if __name__ == "__main__":
    raise SystemExit(main())
