# {your prompt here}
- 아래 output format은 수정하면 결과 출력이 안되니 건드리지 말아 주시면 감사하겠습니다!

## 6. Output Format
Output only valid JSON. Do not include Markdown, XML, comments, or any other text.

Field rules:
- `status`: exactly `"deliver"` or `"improve"`.
- Every dimension object must include `passed` as a JSON boolean, `evidence` as a string, and `feedback` as a string.
- For passed dimensions, use `"none"` for both `evidence` and `feedback`.
- `failed_dimensions`: an array of failed dimension keys. Use an empty array if none failed.
- `improvement_points`: exactly 3 to 5 Korean strings when `status` is `"improve"`. Use an empty array when `status` is `"deliver"`.

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
  },
  "failed_dimensions": ["knowledge_consistency"],
  "improvement_points": [
    "구체적인 개선 포인트 1",
    "구체적인 개선 포인트 2",
    "구체적인 개선 포인트 3"
  ]
}
```