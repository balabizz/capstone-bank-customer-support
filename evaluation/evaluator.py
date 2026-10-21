from collections.abc import Callable
from typing import Any

from evaluation.test_cases import TEST_CASES


def evaluate_classifier(classify: Callable[[str], str]) -> dict[str, Any]:
    results = []
    correct = 0
    for case in TEST_CASES:
        predicted = classify(case["message"])
        passed = predicted == case["expected_classification"]
        correct += int(passed)
        results.append(
            {
                **case,
                "predicted_classification": predicted,
                "passed": passed,
            }
        )
    return {
        "total": len(TEST_CASES),
        "correct": correct,
        "accuracy": correct / len(TEST_CASES) if TEST_CASES else 0.0,
        "results": results,
    }
