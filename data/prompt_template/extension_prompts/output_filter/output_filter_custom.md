# {your prompt here}
- 아래 output format은 수정하면 결과 출력이 안되니 건드리지 말아 주시면 감사하겠습니다!

## 6. Output Format
Output **only** valid JSON — no Markdown, no code fences, no prose, nothing outside the JSON object. Each dimension field is either `null` (no signal) or a string (a brief Korean reason containing verbatim evidence). Use this shape:

{
  "status": "deliver | improve",
  "dimensions": {
    "knowledgeConsistency": null,
    "toneAndDirectionAdherence": null,
    "letterQuality": null,
    "participantSafety": null,
    "koreanLinguisticQuality": null,
    "formatCompliance": null
  }
}
