import openai
from openai import OpenAI
from pydantic import BaseModel
import json
from pathlib import Path
from datetime import datetime

MODEL = "gpt-5"
PROMPT_ROOT = Path(__file__).resolve().parent / "data" / "prompt_template"
LLM_CALL_LOGS = []


def clear_llm_call_log():
    LLM_CALL_LOGS.clear()


def get_llm_call_log():
    return list(LLM_CALL_LOGS)


def record_llm_call(stage, messages, output, raw_output=None):
    LLM_CALL_LOGS.append(
        {
            "stage": stage,
            "model": MODEL,
            "timestamp": datetime.now().isoformat(timespec="seconds"),
            "messages": messages,
            "output": output,
            "raw_output": raw_output if raw_output is not None else output,
        }
    )


def build_filter_user_content(letter, knowledge):
    """입력 필터의 user role content를 구성한다.

    사용자 knowledge와 사용자 편지를 명시적인 섹션으로 분리한다. 출력 형식은
    input filter system prompt의 JSON schema 지시를 따른다.
    """
    return f"""[사용자 Knowledge]
{knowledge}

[사용자가 작성한 편지]
{letter}"""


def dd_generate_gpt4_basic(system_prompt, knowledge, user_prompt):
    """미래 자아 답장 본문을 생성한다.

    `system_prompt`는 선택된 답장 생성 프롬프트, `knowledge`는 구조화된
    사용자 배경 정보, `user_prompt`는 사용자가 작성한 편지이다. 세 값을
    각각 system, assistant, user role 메시지로 구성해 `MODEL`에 요청하고,
    생성된 답장 문자열만 반환한다.
    """
    messages = [
        {'role': 'system', 'content': system_prompt},
        {"role": "assistant", "content": knowledge},
        {'role': 'user', 'content': user_prompt}
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

def dd_filter_user_letter_gpt4(filter_prompt, letter, knowledge):
    """사용자 편지와 knowledge를 입력 필터 프롬프트로 검사하고 JSON 결과를 반환한다.

    `filter_prompt`는 input_filter Markdown 파일의 내용이고, `letter`는
    필터링할 사용자 편지 텍스트이며, `knowledge`는 같은 사용자에게서
    구조화한 배경 정보이다. JSON mode를 사용하므로 user 메시지에 JSON 객체
    반환 지시를 함께 넣고, 모델 응답을 `dict`로 파싱해 반환한다.
    """
    user_content = build_filter_user_content(letter, knowledge)

    messages = [
        {'role': 'system', 'content': filter_prompt},
        {'role': 'user', 'content': user_content}
    ]
    completion = openai.chat.completions.create(
        model=MODEL,
        messages=messages,
        response_format={ "type": "json_object" }
    )
    raw_output = completion.choices[0].message.content
    output = json.loads(raw_output)
    record_llm_call("Input screening", messages, output, raw_output)
    return output

def dd_evaluate_letter_with_prompt_gpt4(letter, screening_prompt, original_letter=None, knowledge=None):
    """생성된 답장을 output filter 프롬프트로 평가하고 JSON 결과를 반환한다.

    `letter`는 검수할 생성 답장이고, `screening_prompt`는 output_filter
    Markdown 파일의 내용이다. 원본 편지와 knowledge가 있으면 함께 전달해
    light-touch 품질 검수의 맥락으로 사용한다. 모델 응답은 반드시 JSON
    객체가 되도록 요청하며, 응답 문자열을 `json.loads()`로 파싱해 앱의
    스크리닝 결과로 사용한다.
    """
    context_sections = []
    if original_letter:
        context_sections.append(f"""[Participant's Original Letter]
{original_letter}""")
    if knowledge:
        context_sections.append(f"""[Background Knowledge]
{knowledge}""")
    context_sections.append(f"""[Generated Future-Self Reply]
{letter}

응답은 반드시 JSON 객체로 반환해주세요.""")
    user_content = "\n\n".join(context_sections)

    messages = [
        {'role': 'system', 'content': screening_prompt},
        {'role': 'user', 'content': user_content}
    ]
    completion = openai.chat.completions.create(
        model=MODEL,
        messages=messages,
        response_format={ "type": "json_object" }
    )
    raw_output = completion.choices[0].message.content
    output = json.loads(raw_output)
    record_llm_call("답장 스크리닝", messages, output, raw_output)
    return output

def dd_generate_improvement_prompt_gpt4(
    improvement_prompt,
    participant_name,
    present_self,
    future_self,
    original_letter,
    previous_letter,
    screening_feedback,
):
    """스크리닝 피드백을 바탕으로 이전 답장의 개선본을 생성한다."""
    if isinstance(screening_feedback, (dict, list)):
        feedback_text = json.dumps(screening_feedback, ensure_ascii=False, indent=2)
    else:
        feedback_text = str(screening_feedback)

    user_content = f"""[PARTICIPANT_NAME]
{participant_name}

[PRESENT_SELF]
{present_self}

[FUTURE_SELF]
{future_self}

[LETTER]
{original_letter}

[PREVIOUS_LETTER]
{previous_letter}

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
