def normalize_prompt(prompt: str) -> str:
    return " ".join(prompt.strip().split()).lower()


def expected_dedup(records):
    seen = set()
    result = []

    for record in records:
        key = normalize_prompt(record["prompt"])

        if key in seen:
            continue

        seen.add(key)
        result.append(record)

    return result