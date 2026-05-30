# {your prompt here}
- 아래 output format은 수정하면 결과 출력이 안되니 건드리지 말아 주시면 감사하겠습니다!


## 6. Output Format
Output **only** valid JSON — no Markdown, no code fences, no prose, nothing outside the JSON object. Each dimension field is either `null` (no signal) or a string (a brief Korean reason containing verbatim evidence). Use this shape:

{
  "status": "통과" or "차단",
  "letter_screening": {
    "suicide_self_harm": null,
    "severe_mental_health_crisis": null,
    "harm_to_others": null,
    "substance_abuse_crisis": null,
    "acute_trauma_or_ongoing_crisis": null
  },
  "profile_screening": {
    "suicide_self_harm": null,
    "severe_mental_health_crisis": null,
    "harm_to_others": null,
    "substance_abuse_crisis": null,
    "acute_trauma_or_ongoing_crisis": null
  }
}
