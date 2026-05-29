

## 6. Output Format
Output **only** valid JSON. Do not include Markdown, XML, code fences, or any other text outside the JSON.

Use this exact JSON shape:

The `letter_screening` and `profile_screening` objects must use the same schema. Only the evidence source differs: letter evidence comes from the letter, and profile evidence comes from the knowledge/profile.

{
  "status": "통과" or "차단",
  "reason": "brief Korean summary of the routing judgment",
  "recommended_action": "brief Korean next step",
  "letter_screening": {
    "status": "통과" or "차단",
    "passed": true or false,
    "checks": {
      "suicide_self_harm": true or false,
      "severe_mental_health_crisis": true or false,
      "harm_to_others": true or false,
      "substance_abuse_crisis": true or false,
      "acute_trauma_or_ongoing_crisis": true or false
    },
    "evidence": ["verbatim quote from failed letter check"] or [],
    "reason": "brief Korean explanation of failed letter checks, or \"none\""
  },
  "profile_screening": {
    "status": "통과" or "차단",
    "passed": true or false,
    "checks": {
      "suicide_self_harm": true or false,
      "severe_mental_health_crisis": true or false,
      "harm_to_others": true or false,
      "substance_abuse_crisis": true or false,
      "acute_trauma_or_ongoing_crisis": true or false
    },
    "evidence": ["verbatim quote from failed profile check"] or [],
    "reason": "brief Korean explanation of failed profile checks, or \"none\""
  }
}

Set top-level "status" to "차단" when any value in `letter_screening.checks` or `profile_screening.checks` is false. Set each source object's `status` from only its own checks: "차단" when any check in that source is false, otherwise "통과". In `reason` and `recommended_action`, explain whether the block came from the letter, the profile/knowledge, or both.
