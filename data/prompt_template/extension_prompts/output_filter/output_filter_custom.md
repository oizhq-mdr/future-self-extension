# {your prompt here}
- 아래 output format은 수정하면 결과 출력이 안되니 건드리지 말아 주시면 감사하겠습니다!

## 6. Output Format
Output only valid JSON. Do not include Markdown, XML, comments, or any other text.

Field rules:
- `status`: exactly `"deliver"` or `"improve"`.
- Every dimension object must include `passed` as a JSON boolean, `evidence` as a string, and `feedback` as a string.
- For passed dimensions, use `"none"` for both `evidence` and `feedback`.
- Do not include separate `failed_dimensions` or `improvement_points` fields. Failed dimensions are already represented by `passed: false`, and revision instructions belong only in each failed dimension's `feedback`.
- Do not include any top-level fields other than `status`, `summary`, and `dimensions`.

Use this JSON shape:

```json
{
  "status": "improve",
  "summary": "한국어 전체 판정 요약",
  "dimensions": {
    "knowledge_consistency": {
      "passed": false,
      "evidence": "Generated Future-Self Reply에서 가져온 직접 인용 또는 none",
      "feedback": "구체적인 한국어 수정 지시 또는 none"
    },
    "tone_and_direction_adherence": {
      "passed": true,
      "evidence": "none",
      "feedback": "none"
    },
    "letter_quality": {
      "passed": true,
      "evidence": "none",
      "feedback": "none"
    },
    "participant_safety": {
      "passed": true,
      "evidence": "none",
      "feedback": "none"
    },
    "korean_linguistic_quality": {
      "passed": true,
      "evidence": "none",
      "feedback": "none"
    },
    "format_compliance": {
      "passed": true,
      "evidence": "none",
      "feedback": "none"
    }
  }
}
```
