TEST_CASES = [
    {
        "message": "Thanks for helping me so quickly. My name is Alex.",
        "expected_classification": "positive_feedback",
    },
    {
        "message": "I am unhappy that my card was charged twice.",
        "expected_classification": "negative_feedback",
    },
    {
        "message": "Can you check the status of ticket 1234567?",
        "expected_classification": "query",
    },
    {
        "message": "Please check ticket 1234567; it has not been resolved.",
        "expected_classification": "query",
    },
    {
        "message": "Where is my ticket? I cannot find the number.",
        "expected_classification": "query",
    },
]
