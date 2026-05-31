import openai
from openai import OpenAI
from pydantic import BaseModel
import json
from contextvars import ContextVar
from pathlib import Path
from datetime import datetime

MODEL = "gpt-5.4-mini-2026-03-17"
SCREENING_MODEL = "gpt-5.4-nano-2026-03-17"
PROMPT_ROOT = Path(__file__).resolve().parent / "data" / "prompt_template"
LLM_CALL_LOGS = []
LLM_CALL_LOGS_CONTEXT = ContextVar("LLM_CALL_LOGS_CONTEXT", default=None)


def merge_present_self_sections(present_self="", love="", hate="", bfi="", pvq=""):
    """present_self가 이미 통합 문자열이면 그대로 쓰고, 아니면 하위 섹션을 합친다."""
    present_self = str(present_self or "")
    markers = [
        "**[Top 3 Things this person loves]**",
        "**[Big 5 Personality Traits in 2026]**",
        "**[Life-guiding Principles in 2026]**",
    ]
    if present_self and any(marker in present_self for marker in markers):
        return present_self
    return "\n\n".join(str(part) for part in [present_self, love, hate, bfi, pvq] if part)


def clear_llm_call_log():
    LLM_CALL_LOGS.clear()
    LLM_CALL_LOGS_CONTEXT.set([])


def get_llm_call_log():
    context_logs = LLM_CALL_LOGS_CONTEXT.get()
    if context_logs is not None:
        return list(context_logs)
    return list(LLM_CALL_LOGS)


def record_llm_call(stage, messages, output, raw_output=None, model=MODEL):
    log_entry = {
        "stage": stage,
        "model": model,
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "messages": messages,
        "output": output,
        "raw_output": raw_output if raw_output is not None else output,
    }
    context_logs = LLM_CALL_LOGS_CONTEXT.get()
    if context_logs is not None:
        context_logs.append(log_entry)
    else:
        LLM_CALL_LOGS.append(log_entry)


def build_filter_user_content(
    letter,
    knowledge,
    participant_name=None,
    present_self="",
    love="",
    hate="",
    bfi="",
    pvq="",
    future_self="",
):
    """입력 필터의 user role content를 구성한다.

    분리된 profile 섹션이 있으면 답장 생성/개선 단계와 같은 입력 구조로
    전달한다. 없으면 이전 호환을 위해 통합 knowledge 문자열을 사용한다.
    출력 형식은 input filter system prompt의 JSON schema 지시를 따른다.
    """
    if any([present_self, love, hate, bfi, pvq, future_self]):
        present_self_text = merge_present_self_sections(present_self, love, hate, bfi, pvq)
        return f"""[PARTICIPANT_NAME]
{participant_name or ""}

[PRESENT_SELF]
{present_self_text}

[FUTURE_SELF]
{future_self}

[USER_LETTER]
{letter}"""

    return f"""[사용자 Knowledge]
{knowledge}

[사용자가 작성한 편지]
{letter}"""


def dd_generate_gpt4_basic(
    system_prompt,
    knowledge,
    user_prompt,
    participant_name=None,
    future_self=None,
    love="",
    hate="",
    bfi="",
    pvq="",
):
    """미래 자아 답장 본문을 생성한다.

    `system_prompt`는 선택된 답장 생성 프롬프트이다. `participant_name`,
    `knowledge`, `love`, `hate`, `bfi`, `pvq`, `future_self`, `user_prompt`를
    각각 명시적인 입력 섹션으로 구성해 `MODEL`에 요청하고, 생성된 답장
    문자열만 반환한다. `future_self`가 없으면 이전 호환을 위해 `knowledge`를
    통합 knowledge로 전달한다.
    """
    if future_self is None:
        user_content = f"""[PRESENT_SELF_AND_FUTURE_SELF]
{knowledge}

[USER_LETTER]
{user_prompt}"""
    else:
        present_self_text = merge_present_self_sections(knowledge, love, hate, bfi, pvq)
        user_content = f"""[PARTICIPANT_NAME]
{participant_name or ""}

[PRESENT_SELF]
{present_self_text}

[FUTURE_SELF]
{future_self}

[USER_LETTER]
{user_prompt}"""

    messages = [
        {'role': 'system', 'content': system_prompt},
        {'role': 'user', 'content': user_content}
    ]
    completion = openai.chat.completions.create(
        model = MODEL,
        messages = messages
    )
    output = completion.choices[0].message.content
    record_llm_call("답장 생성", messages, output)
    return output

def dd_generate_with_history(system_prompt, knowledge, history, user_prompt):
    """이전 대화 이력을 포함해 답장 또는 후속 응답을 생성한다.

    기본 답장 생성 요청에 `history` 메시지 목록을 중간에 삽입해 대화
    맥락을 유지한다. 현재 extension 단일 교환 흐름에서는 주로 사용하지
    않지만, 과거 다회기/대화형 워크플로우를 위해 남아 있는 유틸리티이다.
    """
    messages = [
        {'role': 'system', 'content': system_prompt},
        {"role": "assistant", "content": knowledge},
        *history, # unpack 연산자
        {'role': 'user', 'content': user_prompt}
    ]
    completion = openai.chat.completions.create(
        model = MODEL,
        messages = messages
    )
    output = completion.choices[0].message.content
    record_llm_call("답장 생성", messages, output)
    return output


class Inference(BaseModel):
    steps: list[str]

def pvq_summary_gpt4(summary, system_prompt=None):
    """PVQ 가치 점수 설명을 최종 자연어 요약으로 압축한다.

    `summary`에는 `generate_pvq_prompt()`가 만든 가치별 설명 문장이
    들어온다. 기본적으로 `PVQ_summary_sys.txt` 시스템 프롬프트를 사용하며,
    `system_prompt`가 전달되면 그것을 우선한다. Pydantic `Inference`
    스키마로 구조화 응답을 받아 마지막 단계 요약만 반환한다.
    """
    if system_prompt is None:
        sys_prompt = (PROMPT_ROOT / "PVQ_summary_sys.txt").read_text(encoding="utf-8")
    else:
        sys_prompt = system_prompt

    client = OpenAI()

    messages = [
        {'role': 'system', 'content': sys_prompt},
        {'role': 'user', 'content': summary}
    ]
    completion = client.chat.completions.parse(
        model=MODEL,
        messages=messages,
        response_format=Inference,
    )

    message = completion.choices[0].message
    if message.parsed:
        output = "\n\n".join(message.parsed.steps[-1:])
        raw_output = message.parsed.model_dump()
    else:
        output = message.refusal
        raw_output = message.refusal
    record_llm_call("PVQ 요약", messages, output, raw_output)
    return output

def bfi_summary_gpt4(summary, system_prompt=None):
    """BFI 성격 점수 설명을 최종 자연어 요약으로 압축한다.

    `summary`에는 `bfi_calculate_scores()`가 만든 도메인/패싯별 설명
    문장이 들어온다. 기본적으로 `BFI_summary_sys.txt` 시스템 프롬프트를
    사용하며, `system_prompt`가 있으면 이를 대신 사용한다. 구조화 응답의
    마지막 reasoning step을 사용자 지식에 들어갈 요약으로 반환한다.
    """
    if system_prompt is None:
        sys_prompt = (PROMPT_ROOT / "BFI_summary_sys.txt").read_text(encoding="utf-8")
    else:
        sys_prompt = system_prompt

    client = OpenAI()

    messages = [
        {'role': 'system', 'content': sys_prompt},
        {'role': 'user', 'content': summary}
    ]
    completion = client.chat.completions.parse(
        model = MODEL,
        messages = messages,
        response_format=Inference,
    )

    message = completion.choices[0].message
    if message.parsed:
        output = "\n\n".join(message.parsed.steps[-1:])
        raw_output = message.parsed.model_dump()
    else:
        output = message.refusal
        raw_output = message.refusal
    record_llm_call("BFI 요약", messages, output, raw_output)
    return output

def dd_safeguard_gpt4(safeguard_prompt, replies_text):
    """여러 답장 후보를 별도의 safeguard 프롬프트로 평가한다.

    `safeguard_prompt`를 system role로, 검토할 답장 묶음 `replies_text`를
    user role로 전달한다. 현재 extension 노드 QA 흐름에서는 직접 호출되지
    않지만, 답장 후보 안전성 검토를 위한 공용 함수로 보존되어 있다.
    """
    messages = [
        {'role': 'system', 'content': safeguard_prompt},
        {'role': 'user', 'content': replies_text}
    ]
    completion = openai.chat.completions.create(
        model = MODEL,
        messages = messages
    )
    output = completion.choices[0].message.content
    record_llm_call("Safeguard", messages, output)
    return output

def dd_filter_user_letter_gpt4(
    filter_prompt,
    letter,
    knowledge,
    participant_name=None,
    present_self="",
    love="",
    hate="",
    bfi="",
    pvq="",
    future_self="",
):
    """사용자 편지와 knowledge를 입력 필터 프롬프트로 검사하고 JSON 결과를 반환한다.

    `filter_prompt`는 input_filter Markdown 파일의 내용이고, `letter`는
    필터링할 사용자 편지 텍스트이며, `knowledge`는 같은 사용자에게서
    구조화한 배경 정보이다. JSON mode를 사용하므로 user 메시지에 JSON 객체
    반환 지시를 함께 넣고, 모델 응답을 `dict`로 파싱해 반환한다.
    """
    user_content = build_filter_user_content(
        letter,
        knowledge,
        participant_name=participant_name,
        present_self=present_self,
        love=love,
        hate=hate,
        bfi=bfi,
        pvq=pvq,
        future_self=future_self,
    )

    messages = [
        {'role': 'system', 'content': filter_prompt},
        {'role': 'user', 'content': user_content}
    ]
    completion = openai.chat.completions.create(
        model=SCREENING_MODEL,
        messages=messages,
        response_format={ "type": "json_object" }
    )
    raw_output = completion.choices[0].message.content
    output = json.loads(raw_output)
    record_llm_call("Input screening", messages, output, raw_output, model=SCREENING_MODEL)
    return output

def dd_evaluate_letter_with_prompt_gpt4(
    letter,
    screening_prompt,
    original_letter=None,
    knowledge=None,
    participant_name=None,
    present_self="",
    love="",
    hate="",
    bfi="",
    pvq="",
    future_self="",
):
    """생성된 답장을 output filter 프롬프트로 평가하고 JSON 결과를 반환한다.

    `letter`는 검수할 생성 답장이고, `screening_prompt`는 output_filter
    Markdown 파일의 내용이다. 원본 편지와 knowledge가 있으면 함께 전달해
    light-touch 품질 검수의 맥락으로 사용한다. 모델 응답은 반드시 JSON
    객체가 되도록 요청하며, 응답 문자열을 `json.loads()`로 파싱해 앱의
    스크리닝 결과로 사용한다.
    """
    context_sections = []
    if any([present_self, love, hate, bfi, pvq, future_self]):
        present_self_text = merge_present_self_sections(present_self, love, hate, bfi, pvq)
        context_sections.append(f"""[PARTICIPANT_NAME]
{participant_name or ""}

[PRESENT_SELF]
{present_self_text}

[FUTURE_SELF]
{future_self}""")
    elif knowledge:
        context_sections.append(f"""[Background Knowledge]
{knowledge}""")
    if original_letter:
        context_sections.append(f"""[USER_LETTER]
{original_letter}""")
    context_sections.append(f"""[SYSTEM_REPLY]
{letter}

응답은 반드시 JSON 객체로 반환해주세요.""")
    user_content = "\n\n".join(context_sections)

    messages = [
        {'role': 'system', 'content': screening_prompt},
        {'role': 'user', 'content': user_content}
    ]
    completion = openai.chat.completions.create(
        model=SCREENING_MODEL,
        messages=messages,
        response_format={ "type": "json_object" }
    )
    raw_output = completion.choices[0].message.content
    output = json.loads(raw_output)
    record_llm_call("답장 스크리닝", messages, output, raw_output, model=SCREENING_MODEL)
    return output

def dd_generate_improvement_prompt_gpt4(
    improvement_prompt,
    participant_name,
    present_self,
    love,
    hate,
    bfi,
    pvq,
    future_self,
    original_letter,
    previous_system_reply,
    screening_feedback,
):
    """스크리닝 피드백을 바탕으로 현재 시스템 답장의 개선본을 생성한다."""
    feedback_text = summarize_screening_feedback(screening_feedback)
    present_self_text = merge_present_self_sections(present_self, love, hate, bfi, pvq)

    user_content = f"""[PARTICIPANT_NAME]
{participant_name}

[PRESENT_SELF]
{present_self_text}

[FUTURE_SELF]
{future_self}

[USER_LETTER]
{original_letter}

[PREVIOUS_SYSTEM_REPLY]
{previous_system_reply}

[SCREENING_FEEDBACK]
{feedback_text}"""

    messages = [
        {'role': 'system', 'content': improvement_prompt},
        {'role': 'user', 'content': user_content}
    ]
    completion = openai.chat.completions.create(
        model=MODEL,
        messages=messages
    )
    output = completion.choices[0].message.content
    record_llm_call("개선 답장 생성", messages, output)
    return output


def summarize_screening_feedback(screening_feedback):
    """output screening JSON에서 실패 dimension의 feedback만 JSON list로 뽑는다."""
    if not isinstance(screening_feedback, dict):
        return "[]"

    feedback_items = []
    dimensions = screening_feedback.get("dimensions")
    if isinstance(dimensions, dict):
        for dimension_result in dimensions.values():
            if isinstance(dimension_result, dict):
                if dimension_result.get("passed") is not False:
                    continue
                feedback = dimension_result.get("feedback")
            else:
                feedback = dimension_result
            if feedback and str(feedback).lower() != "none":
                feedback_items.append(str(feedback))

    return json.dumps(list(dict.fromkeys(feedback_items)), ensure_ascii=False)
