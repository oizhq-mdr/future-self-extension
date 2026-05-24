import openai
from openai import OpenAI
from pydantic import BaseModel
import json

MODEL = "gpt-5"


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
    completion = openai.chat.completions.create(
        model = MODEL,
        messages = [
            {'role': 'system', 'content': system_prompt},
            {"role": "assistant", "content": knowledge},
            {'role': 'user', 'content': user_prompt}
        ]
    )
    return completion.choices[0].message.content

def dd_generate_with_history(system_prompt, knowledge, history, user_prompt):
    """이전 대화 이력을 포함해 답장 또는 후속 응답을 생성한다.

    기본 답장 생성 요청에 `history` 메시지 목록을 중간에 삽입해 대화
    맥락을 유지한다. 현재 extension 단일 교환 흐름에서는 주로 사용하지
    않지만, 과거 다회기/대화형 워크플로우를 위해 남아 있는 유틸리티이다.
    """
    completion = openai.chat.completions.create(
        model = MODEL,
        messages = [
            {'role': 'system', 'content': system_prompt},
            {"role": "assistant", "content": knowledge},
            *history, # unpack 연산자
            {'role': 'user', 'content': user_prompt}
        ]
    )
    return completion.choices[0].message.content


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
        system_lib_file = 'data/prompt_template/PVQ_summary_sys.txt'
        f = open(system_lib_file, "r")
        sys_prompt = f.read()
        f.close()
    else:
        sys_prompt = system_prompt

    client = OpenAI()

    completion = client.chat.completions.parse(
        model=MODEL,
        messages=[
            {'role': 'system', 'content': sys_prompt},
            {'role': 'user', 'content': summary}
        ],
        response_format=Inference,
    )

    message = completion.choices[0].message
    if message.parsed:
        return "\n\n".join(message.parsed.steps[-1:])
    else:
        return message.refusal

def bfi_summary_gpt4(summary, system_prompt=None):
    """BFI 성격 점수 설명을 최종 자연어 요약으로 압축한다.

    `summary`에는 `bfi_calculate_scores()`가 만든 도메인/패싯별 설명
    문장이 들어온다. 기본적으로 `BFI_summary_sys.txt` 시스템 프롬프트를
    사용하며, `system_prompt`가 있으면 이를 대신 사용한다. 구조화 응답의
    마지막 reasoning step을 사용자 지식에 들어갈 요약으로 반환한다.
    """
    if system_prompt is None:
        system_lib_file = 'data/prompt_template/BFI_summary_sys.txt'
        f = open(system_lib_file, "r")
        sys_prompt = f.read()
        f.close()
    else:
        sys_prompt = system_prompt

    client = OpenAI()

    completion = client.chat.completions.parse(
        model = MODEL,
        messages = [
            {'role': 'system', 'content': sys_prompt},
            {'role': 'user', 'content': summary}
        ],
        response_format=Inference,
    )

    message = completion.choices[0].message
    if message.parsed:
       return "\n\n".join(message.parsed.steps[-1:])
    else:
        return message.refusal

def dd_safeguard_gpt4(safeguard_prompt, replies_text):
    """여러 답장 후보를 별도의 safeguard 프롬프트로 평가한다.

    `safeguard_prompt`를 system role로, 검토할 답장 묶음 `replies_text`를
    user role로 전달한다. 현재 extension 노드 QA 흐름에서는 직접 호출되지
    않지만, 답장 후보 안전성 검토를 위한 공용 함수로 보존되어 있다.
    """
    completion = openai.chat.completions.create(
        model = MODEL,
        messages = [
            {'role': 'system', 'content': safeguard_prompt},
            {'role': 'user', 'content': replies_text}
        ]
    )
    return completion.choices[0].message.content

def dd_filter_user_letter_gpt4(filter_prompt, letter, knowledge):
    """사용자 편지와 knowledge를 입력 필터 프롬프트로 검사하고 JSON 결과를 반환한다.

    `filter_prompt`는 input_filter Markdown 파일의 내용이고, `letter`는
    필터링할 사용자 편지 텍스트이며, `knowledge`는 같은 사용자에게서
    구조화한 배경 정보이다. JSON mode를 사용하므로 user 메시지에 JSON 객체
    반환 지시를 함께 넣고, 모델 응답을 `dict`로 파싱해 반환한다.
    """
    user_content = build_filter_user_content(letter, knowledge)

    completion = openai.chat.completions.create(
        model=MODEL,
        messages=[
            {'role': 'system', 'content': filter_prompt},
            {'role': 'user', 'content': user_content}
        ],
        response_format={ "type": "json_object" }
    )
    return json.loads(completion.choices[0].message.content)

def dd_evaluate_letter_with_prompt_gpt4(letter, screening_prompt):
    """생성된 답장을 output filter 프롬프트로 평가하고 JSON 결과를 반환한다.

    `letter`는 검수할 생성 답장이고, `screening_prompt`는 output_filter
    Markdown 파일의 내용이다. 모델 응답은 반드시 JSON 객체가 되도록
    요청하며, 응답 문자열을 `json.loads()`로 파싱해 앱의 스크리닝 결과로
    사용한다.
    """
    user_content = f"""[검토할 편지]
{letter}

응답은 반드시 JSON 객체로 반환해주세요."""

    completion = openai.chat.completions.create(
        model=MODEL,
        messages=[
            {'role': 'system', 'content': screening_prompt},
            {'role': 'user', 'content': user_content}
        ],
        response_format={ "type": "json_object" }
    )
    return json.loads(completion.choices[0].message.content)

def dd_generate_improvement_prompt_gpt4(improvement_prompt, letter):
    """현재 답장을 바탕으로 다음 생성에 적용할 개선 지시문을 만든다.

    `improvement_prompt`는 improvement Markdown 파일의 시스템 프롬프트이고,
    `letter`는 방금 생성되어 검수된 답장이다. 반환값은 다음 답장 생성 때
    system prompt 뒤에 추가되는 revision guidance 문자열이다.
    """
    completion = openai.chat.completions.create(
        model=MODEL,
        messages=[
            {'role': 'system', 'content': improvement_prompt},
            {
                'role': 'user',
                'content': f"[현재 답장]\n{letter}"
            }
        ]
    )
    return completion.choices[0].message.content
