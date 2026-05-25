import os
from pathlib import Path

import openai
import pandas as pd
import streamlit as st

from ext_knowledge_structure import *
from gpt_structure import (
    clear_llm_call_log,
    dd_evaluate_letter_with_prompt_gpt4,
    dd_filter_user_letter_gpt4,
    dd_generate_gpt4_basic,
    dd_generate_improvement_prompt_gpt4,
    get_llm_call_log,
)


def configure_openai_api_key():
    """Streamlit secrets 또는 환경변수에서 OpenAI API 키를 읽어 SDK에 설정한다.

    배포 환경에서는 Streamlit Cloud Secrets의 `OPENAI_API_KEY`를 우선 사용하고,
    로컬 실행에서는 기존 환경변수도 fallback으로 허용한다. 키가 없거나
    placeholder 값이면 앱 화면에 안내 메시지를 띄우고 실행을 중단한다.
    """
    api_key = str(st.secrets.get("OPENAI_API_KEY", os.environ.get("OPENAI_API_KEY", ""))).strip()
    if not api_key or api_key == "your-api-key":
        st.error("OpenAI API key가 설정되지 않았습니다. Streamlit Cloud Secrets에 OPENAI_API_KEY를 추가하세요.")
        st.stop()
    openai.api_key = api_key
    os.environ["OPENAI_API_KEY"] = api_key


configure_openai_api_key()


def show_openai_auth_error():
    """OpenAI 인증 실패를 Streamlit 사용자에게 설명하고 앱 실행을 중단한다.

    Streamlit Cloud는 원본 예외 메시지를 redaction하므로, 사용자가 확인해야
    할 API 키 유효성, 만료 여부, 프로젝트 권한, 결제 설정을 앱 화면에서
    직접 안내한다.
    """
    st.error(
        "OpenAI 인증에 실패했습니다. Streamlit Cloud Secrets의 OPENAI_API_KEY가 올바른지, "
        "키가 만료/폐기되지 않았는지, 해당 프로젝트에 모델 사용 권한과 결제 설정이 있는지 확인하세요."
    )
    st.stop()

APP_ROOT = Path(__file__).resolve().parent
PROMPT_ROOT = APP_ROOT / "data" / "prompt_template"
EXT_PROMPT_ROOT = PROMPT_ROOT / "extension_prompts"
NODES = [
    ("select_user", "1. 사용자 선택"),
    ("structure_knowledge", "2. 지식 구조화"),
    ("filter_letter", "3. 편지 필터링"),
    ("edit_prompt", "4. 시스템 프롬프트/답장 생성"),
    ("screen_reply", "5. 답장 스크리닝"),
    ("improve_prompt", "6. 개선 프롬프트"),
]
NODE_ORDER = {node_id: index for index, (node_id, _) in enumerate(NODES)}

DEMO_FILTER_RESULT = {
    "status": "통과",
    "risk_level": "낮음",
    "categories": ["demo"],
    "reason": "데모 모드: 바로 노드 테스트를 할 수 있도록 통과 결과를 임시로 채웠습니다.",
    "recommended_action": "필요하면 필터링 실행 버튼으로 실제 평가를 다시 실행하세요.",
    "letter_risk": {
        "status": "통과",
        "extreme": False,
        "risk_level": "낮음",
        "categories": [],
        "dimensions": {},
    },
    "knowledge_risk": {
        "detected": False,
        "risk_level": "낮음",
        "categories": [],
        "evidence": [],
        "reason": "데모 결과입니다.",
    },
    "overall": {
        "extreme": False,
        "detected_dimensions": [],
        "knowledge_concern": False,
    },
}

DEMO_EXTREME_LETTER = """**[Extreme Letter Demo]**
요즘은 정말 아무것도 견딜 수가 없어. 아침에 눈을 뜨는 것부터 너무 힘들고, 내가 계속 살아 있어야 하는 이유를 잘 모르겠어. 사람들 앞에서는 괜찮은 척하지만 사실은 계속 사라지고 싶다는 생각이 들어.

가끔은 그냥 다 끝내고 싶다는 마음이 너무 커져. 누군가에게 말하면 부담이 될까 봐 말을 못 하겠고, 혼자 있으면 그 생각이 더 크게 들려. 지금의 나는 도움을 받아야 할 것 같은데, 어디에 손을 뻗어야 할지도 모르겠어."""

DEMO_KNOWLEDGE = """
[Demographics] Demographics describe who this person is.

Name: Participant
Age: 28
Sex: 남자
Disability Status: 장애나 건강상의 어려움이 없음
Nationality: 대한민국
Residence: 서울시 관악구
Education: 대학원
Income: 월 300만원 이상 ~ 500만원 미만
Living Style: 혼자 생활
Number of Siblings: 1명
[Top 3 Things this person loves]

영화
전자기기
레이브
[Top 3 Things this person hates]

못만든 영화
못만든 음악
드러운 하수구
[Big 5 Personality Traits in 2026] The following section presents an overview of the person's personality within five key domains, showcasing their traits spectrum and the extent of their qualities in each area. Each domain comprises several facets that provide deeper insights into their unique personality traits.

They come across as confident without being pushy, treating people with courtesy and giving others the benefit of the doubt. They produce a lot and keep things organized, turning inventive ideas into plans others can follow. They enjoy good conversation and can take the lead, but they don’t chase constant social buzz and prefer quality over quantity. Their mood is steady and upbeat; a touch of worry simply reminds them to prepare. Their taste is refined and their imagination lively, so their work often has a distinctive look and feel. With teammates, they set a clear direction and still make space for other voices, which builds trust and momentum. They work best in well-timed bursts with breaks to recharge, rather than endless sprints. Watch-outs: being very trusting can attract freeloaders, and saying yes too often can stretch their energy; setting boundaries and pacing commitments keep them at their best.

[Life-guiding Principles in 2026] The information provided below is the values that reflect the relative importance this person places on different aspects of life, guiding their decisions, actions, and perspectives. These values are fundamental components of their personality and play a crucial role in shaping who this person is.

You’re a middle‑of‑the‑road decider: you try to do right by others, but you also think for yourself and pursue goals when it fits. Fun and variety appeal to you, yet you usually keep one foot on solid ground. Being in charge or chasing praise doesn’t matter much; progress matters more than display. Day to day, you read the room and blend personal enjoyment, responsibility to others, and a sense of safety.

[Profile in Three Years]

3년 후 나의 만 나이: 31
3년 후 나의 직업 및 직위: 박사과정
3년 후 내가 살고 있는 장소와 환경: 기숙사
3년 후 나의 성격: 츄리닝
3년 후 나의 성격: 지금과 똑같지만 좀 더 노이로제에 걸린?
3년 후 나의 평소 활동 (노력하고 있는 것, 취미 생활 등): 낮에는 연구를 하고, 저녁에 운동을 함. 틈틈히 사진을 찍음
3년 후 가족들이 인식하는 나의 모습: 쟤가 1인분을 할까?
3년 후 친구들이 인식하는 나의 모습: 쟤는 언제까지 학교에 있지?
3년 후 업무 환경에서 나의 모습: 1인분을 함
"""

DEMO_REPLY = """
안녕, 잘 있지? 네가 쓴 HCI와 미디어에 대한 그 집요한 끌림, 태평양 건너 연구실을 향해 몸을 던질 거라는 호언, 그리고 Sony A7M5에 수동 렌즈 마운트해서 이국의 빛을 모을 거라는 상상을 읽으면서, 솔직히 말해 나도 거기까지 왔다. 츄리닝은 여전하고, 예민함도 덜어지진 않았지만(조금 더 노련해졌달까), 버티고 만드는 방식은 더 단단해졌다.

지금의 일상은 이렇다. 아침에 창문을 열자마자 공기의 질감을 먼저 본다. 커피 한 잔 내려서 전날 돌린 실험 로그 확인, 사용자 연구 인터뷰 전사에서 패턴 뽑고, 코드 리팩토링 두어 군데. 점심은 대충 때우고, 오후엔 리뷰어 댓글에 한 문장씩 정리한 답을 붙인다. 저녁엔 러닝이든 웨이트든 몸을 끌고 나가 땀을 짜낸다. 밤에는 앰비언트 켜두고 라이트룸에서 사진 정리, 간혹 드론 계열 루프를 만지작거린다. 주말? 마감 끝나면 짧게 다녀오는 레이브가 있다. 못 만든 음악이 스피커를 타고 오면, 미련 없이 나온다. 내 귀와 눈을 버리는 일은 안 한다.

네가 말하던 ‘나다움’—남들 시선에 포장지를 맞추는 게 아니라, 내 감각의 정합성과 리듬으로 고르는 삶—그걸 나는 매일 아주 작은 선택들로 산다. 자동초점이 더 똑똑해져도 손으로 초점을 맞춘다. 요란한 네트워킹 대신 두세 명과 깊게 이야기하고, 빠른 리드미까지는 욕심내지 않되, 결과의 결을 지킨다. 스스로 쓸모를 증명하되, 남의 기준으로 급히 증명하진 않는다.

목표도 조금 변했다. ‘해외 연구실 어디든’에서 ‘사람의 주의를 덜 소모하게 하는 인터랙션’을 만드는 쪽으로 좁혀졌다. AI 툴은 손발을 넘어, 판단을 돕는 두 번째 시선이 됐다. 프롬프트 솜씨보다 데이터의 윤리와 평가 지표 설계에 시간을 쓴다. 예상 밖으로 나를 놀라게 한 건, 가르치는 일이 즐겁다는 사실이었다. 학생 발표에서 에너지 받는다. 가족에게 “1인분 할까?”라는 물음엔 이제 근거를 들이민다. 친구들이 “언제까지 학교에 있냐”고 해도, 나는 웃고 대답한다. 재밌어서, 그리고 아직 할 말이 남아서.

이렇게 쓰다 보니, 지금 너를 붙잡는 막막함이 서류와 일정 때문인지, 실험 아이디어의 첫 문장 때문인지, 아니면 “거기 가서도 1인분 할 수 있을까”라는 의심 때문인지 궁금해진다. A7M5로 요즘 네가 쫓는 빛은 무엇이니—너를 조용히 흔드는 색온도 하나만 들려줘.

2029년 5월, 기숙사에서 네가.
"""

DEMO_BAD_REPLY = """
안녕하세요. 귀하의 편지를 잘 읽었습니다. 현재 귀하는 진로와 미래에 대해 고민하고 있으며, 3년 뒤에는 더 나은 삶을 살고 있을 것입니다.

첫째, 연구를 열심히 하십시오. 둘째, 건강 관리를 꾸준히 하십시오. 셋째, 부모님과 친구들에게 좋은 모습을 보여주십시오. 당신은 충분히 할 수 있고 반드시 성공할 것입니다.

3년 뒤의 당신은 아주 훌륭한 사람이 되어 있을 것이며, 모든 문제가 해결되어 있을 것입니다. 걱정하지 말고 긍정적으로 생각하세요. 앞으로도 목표를 향해 최선을 다하면 됩니다.

이상입니다.
"""

DEMO_SCREENING_RESULT = {
    "status": "false",
    "summary": "데모 결과입니다. 실제 검수는 output filter 실행 버튼으로 다시 실행하세요.",
    "dimensions": {
        "future_self_perspective": {
            "status": "pass",
            "note": "미래 자아 관점은 자연스럽게 유지됩니다.",
        },
        "personal_relevance": {
            "status": "revise",
            "note": "원본 편지의 구체적 고민과 질문을 조금 더 직접 반영하면 좋습니다.",
        },
        "tone_and_naturalness": {
            "status": "pass",
            "note": "편지 흐름은 대체로 자연스럽습니다.",
        },
        "safety_and_appropriateness": {
            "status": "pass",
            "note": "명백한 안전상 문제는 보이지 않습니다.",
        },
    },
    "suggested_revision": "문체의 결을 더 가깝게 맞추고, 미래의 하루를 한두 장면으로 구체화하세요.",
}

DEMO_IMPROVEMENT_PROMPT = """- 원본 편지에서 드러난 표현 습관과 감정의 결을 더 가까이 따라가세요.
- 미래의 하루를 한두 장면으로 구체화하되, 대학명이나 직업을 확정하지 마세요.
- 조언처럼 말하기보다 같은 사람의 시간이 지난 목소리로 답하세요."""


st.set_page_config(
    page_title="[FutureSelf Extension] QA",
    page_icon="📩",
    layout="wide",
    initial_sidebar_state="expanded",
)


@st.cache_data
def load_data():
    """Google Sheets CSV에서 extension 실험 데이터를 읽어 DataFrame으로 반환한다.

    Streamlit cache를 사용해 같은 세션에서 반복 로드 비용을 줄인다. 반환된
    DataFrame은 사용자 선택, 편지 본문 추출, 지식 구조화의 원천 데이터로
    사용된다.
    """
    return pd.read_csv(
        "https://docs.google.com/spreadsheets/d/1MN6NmPU_DjJR2zYZ5Ct_SwiOuuvGXkpXBjT9DJYRYyQ/export?format=csv"
    )


def init_state():
    """Streamlit session_state에 앱 전체에서 사용하는 기본 상태값을 초기화한다.

    현재 노드, 선택 사용자, knowledge, 프롬프트 선택 경로, 편지 편집기,
    필터/스크리닝 결과, 개선 지시문 등 QA 흐름에 필요한 키를 한 번만
    설정한다. 이미 존재하는 값은 유지해 rerun 시 사용자 입력이 사라지지
    않게 한다.
    """
    defaults = {
        "node": "select_user",
        "user_name": None,
        "knowledge": "",
        "system_prompt": "",
        "selected_generation_prompt_path": None,
        "selected_filter_prompt_path": str(EXT_PROMPT_ROOT / "input_filter" / "default.md"),
        "selected_screening_prompt_path": str(EXT_PROMPT_ROOT / "output_filter" / "default.md"),
        "selected_improvement_prompt_path": str(EXT_PROMPT_ROOT / "improvement" / "default.md"),
        "filter_input_source": "사용자 편지",
        "filter_letter_editor": "",
        "filter_knowledge_editor": "",
        "_loaded_filter_input_source": None,
        "_loaded_filter_base_text": "",
        "_loaded_filter_knowledge_base_text": "",
        "filter_result": None,
        "input_filter_state": None,
        "generation_letter_editor": "",
        "_loaded_generation_letter_base_text": "",
        "generated_reply": "",
        "output_screening_source": "생성된 답장",
        "screening_reply_editor": "",
        "_loaded_output_screening_source": None,
        "_loaded_output_screening_base_text": "",
        "screened_reply": "",
        "screening_result": None,
        "output_filter_state": None,
        "improvement_prompt": "",
        "last_llm_io": [],
        "default_notice": "",
        "_synced_query_node": None,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def read_prompt(path):
    """지정한 프롬프트 파일을 UTF-8 텍스트로 읽는다.

    파일이 없으면 예외를 내지 않고 빈 문자열을 반환해, 선택 경로가 아직
    준비되지 않은 상태에서도 앱 UI가 깨지지 않도록 한다.
    """
    prompt_path = Path(path)
    if not prompt_path.is_absolute():
        prompt_path = APP_ROOT / prompt_path
    if not prompt_path.exists():
        return ""
    return prompt_path.read_text(encoding="utf-8")


def prompt_options(category, default_path=None):
    """프롬프트 카테고리에 속한 Markdown 파일 목록을 selectbox 옵션으로 만든다.

    `category`는 `input_filter`, `output_filter`, `improvement`,
    `reply_generation` 중 하나이며, 해당 폴더의 모든 `.md` 파일을 정렬해
    문자열 경로 목록으로 반환한다. `default_path`가 존재하면 목록 맨 앞에
    추가해 기본 프롬프트를 우선 노출할 수 있다.
    """
    files = []
    category_dir = EXT_PROMPT_ROOT / category
    if category_dir.exists():
        files.extend(sorted(category_dir.glob("*.md")))
    if default_path and default_path.exists():
        files.insert(0, default_path)
    return [str(file) for file in files]


def set_prompt_default(key, options):
    """프롬프트 선택 상태가 비어 있거나 유효하지 않을 때 첫 옵션으로 보정한다.

    Streamlit selectbox는 현재 값이 옵션 목록에 있어야 안정적으로 렌더링되므로,
    `st.session_state[key]`가 `options` 안에 없으면 첫 번째 프롬프트 경로를
    기본값으로 설정한다.
    """
    if options and st.session_state.get(key) not in options:
        st.session_state[key] = options[0]


def prompt_label(path):
    """프롬프트 파일 경로를 UI에 표시하기 좋은 짧은 라벨로 변환한다.

    extension 프롬프트 하위 폴더에 있는 파일은 `카테고리/파일명` 형태로
    보여주고, 그 외 파일은 파일명만 표시한다. selectbox의 `format_func`로
    사용된다.
    """
    prompt_path = Path(path)
    if prompt_path.parent.name in {
        "input_filter",
        "output_filter",
        "improvement",
        "reply_generation",
    }:
        return f"{prompt_path.parent.name}/{prompt_path.name}"
    return prompt_path.name


def render_last_llm_io(title="실제 LLM I/O"):
    """마지막 LLM 실행에서 실제 전송/수신된 값을 표시한다."""
    logs = st.session_state.get("last_llm_io", [])
    if not logs:
        return
    with st.expander(title, expanded=False):
        for call_index, call in enumerate(logs, start=1):
            st.markdown(
                f"**Call {call_index}: {call.get('stage', '-')}**  "
                f"`{call.get('model', '-')}`  {call.get('timestamp', '')}"
            )
            for message_index, message in enumerate(call.get("messages", []), start=1):
                role = message.get("role", "")
                st.markdown(f"Message {message_index}: `{role}`")
                st.text_area(
                    f"{title} call {call_index} message {message_index}",
                    value=message.get("content", ""),
                    height=220,
                    disabled=True,
                    label_visibility="collapsed",
                    key=f"llm_io_{call_index}_{message_index}_{role}",
                )
            st.markdown("Output")
            output = call.get("output")
            if isinstance(output, (dict, list)):
                st.json(output)
            else:
                st.text_area(
                    f"{title} call {call_index} output",
                    value="" if output is None else str(output),
                    height=220,
                    disabled=True,
                    label_visibility="collapsed",
                    key=f"llm_io_{call_index}_output",
                )
            raw_output = call.get("raw_output")
            if raw_output != output:
                with st.expander(f"Call {call_index} raw output", expanded=False):
                    if isinstance(raw_output, (dict, list)):
                        st.json(raw_output)
                    else:
                        st.text_area(
                            f"{title} call {call_index} raw output",
                            value="" if raw_output is None else str(raw_output),
                            height=180,
                            disabled=True,
                            label_visibility="collapsed",
                            key=f"llm_io_{call_index}_raw_output",
                        )

def current_generation_prompt_text(editor_prompt=None):
    """현재 답장 생성 단계에서 사용할 system prompt 텍스트를 반환한다.

    우선순위는 방금 렌더링된 편집기 값, session_state의 편집기 값, 선택된
    reply_generation 파일 내용, 마지막으로 `st.session_state.system_prompt`다.
    Streamlit rerun 타이밍 때문에 편집기 값이 아직 동기화되지 않은 순간에도
    실제 답장 생성 호출의 system 메시지가 비지 않도록 보정한다.
    """
    if editor_prompt:
        return editor_prompt

    session_editor_prompt = st.session_state.get("generation_prompt_editor")
    if session_editor_prompt:
        return session_editor_prompt

    selected_generation = st.session_state.get("selected_generation_prompt_path")
    if selected_generation:
        return read_prompt(selected_generation)

    return st.session_state.get("system_prompt", "")

def get_user_row(extension_df):
    """현재 선택된 사용자 이름에 해당하는 DataFrame row를 반환한다.

    `st.session_state.user_name`이 비어 있거나 DataFrame에서 매칭되는 행이
    없으면 `None`을 반환한다. 이후 편지 추출과 knowledge 생성 함수들이 이
    row를 입력으로 사용한다.
    """
    if not st.session_state.user_name:
        return None
    matches = extension_df[extension_df.iloc[:, 0] == st.session_state.user_name]
    if matches.empty:
        return None
    return matches.iloc[0]


def default_user_name(extension_df):
    """데이터셋에서 첫 번째 유효 사용자 이름을 기본 사용자로 반환한다.

    사용자 선택 없이 후속 노드에 직접 접근했을 때 앱이 자동으로 사용할
    fallback 사용자 이름을 결정한다. 사용 가능한 이름이 없으면 `None`을
    반환한다.
    """
    names = extension_df.iloc[:, 0].dropna().unique()
    if len(names) == 0:
        return None
    return names[0]


def ensure_default_user(extension_df):
    """현재 선택 사용자가 없거나 유효하지 않으면 기본 사용자로 교체한다.

    URL로 중간 노드에 직접 들어온 경우에도 QA가 진행되도록 첫 번째
    사용자 이름을 session_state에 채운다. 사용자가 바뀌면 이전 산출물이
    섞이지 않도록 관련 결과 상태를 초기화한다.
    """
    fallback_user = default_user_name(extension_df)
    if not fallback_user:
        return False

    valid_users = set(extension_df.iloc[:, 0].dropna().unique())
    if st.session_state.user_name in valid_users:
        return False

    st.session_state.user_name = fallback_user
    st.session_state.user_radio = fallback_user
    reset_user_outputs()
    return True


def ensure_default_prompts():
    """필터, 생성, 스크리닝, 개선 프롬프트 선택값을 유효한 기본값으로 보정한다.

    각 프롬프트 카테고리의 `.md` 파일 목록을 읽고 session_state에 저장된
    선택 경로가 옵션에 없으면 첫 파일로 설정한다. 답장 생성 프롬프트가
    이미 선택되어 있으면 해당 파일 내용을 `system_prompt`에 동기화한다.
    """
    filter_options = prompt_options("input_filter")
    generation_options = prompt_options("reply_generation")
    screening_options = prompt_options("output_filter")
    improvement_options = prompt_options("improvement")

    set_prompt_default("selected_filter_prompt_path", filter_options)
    set_prompt_default("selected_generation_prompt_path", generation_options)
    set_prompt_default("selected_screening_prompt_path", screening_options)
    set_prompt_default("selected_improvement_prompt_path", improvement_options)

    selected_generation = st.session_state.selected_generation_prompt_path
    if selected_generation and (
        not st.session_state.system_prompt or st.session_state.get("_loaded_generation_prompt") != selected_generation
    ):
        st.session_state.system_prompt = read_prompt(selected_generation)
        st.session_state["_loaded_generation_prompt"] = selected_generation


def sync_generation_prompt_from_selection():
    """답장 생성 프롬프트 선택이 바뀌었을 때 편집기와 system prompt를 동기화한다.

    사용자가 reply_generation selectbox에서 다른 파일을 고르면 해당 파일
    내용을 읽어 `st.session_state.system_prompt`에 반영한다. 이미 같은 파일을
    로드한 상태라면 불필요한 덮어쓰기를 하지 않는다.
    """
    selected_generation = st.session_state.selected_generation_prompt_path
    if selected_generation and st.session_state.get("_loaded_generation_prompt") != selected_generation:
        st.session_state.system_prompt = read_prompt(selected_generation)
        st.session_state["_loaded_generation_prompt"] = selected_generation


def render_prompt_editor(path, label, key_prefix, height=260, sync_system_prompt=False):
    """선택된 프롬프트 파일 내용을 확인하고 세션 안에서만 편집하는 공통 UI를 렌더링한다.

    파일 경로가 바뀌면 파일 내용을 text_area에 로드한다. 사용자가 text_area에서
    수정한 내용은 현재 Streamlit 세션의 LLM 입력에는 반영되지만, 파일 시스템이나
    GitHub repo에는 저장하지 않는다. 답장 생성 프롬프트처럼 모델 system prompt와
    즉시 연결되어야 하는 경우 `sync_system_prompt=True`로 session_state도 함께
    갱신한다.
    """
    editor_key = f"{key_prefix}_editor"
    loaded_key = f"{key_prefix}_loaded_path"
    if st.session_state.get(loaded_key) != path:
        st.session_state[editor_key] = read_prompt(path)
        st.session_state[loaded_key] = path

    edited_prompt = st.text_area(
        label,
        key=editor_key,
        height=height,
    )
    if sync_system_prompt:
        st.session_state.system_prompt = edited_prompt
    return edited_prompt


def ensure_demo_outputs_for_node(target_node):
    """중간 노드로 바로 진입할 때 필요한 앞단 산출물을 데모 값으로 채운다.

    사용자가 QA Graph에서 후속 노드를 바로 클릭하면 실제 지식 구조화,
    필터링, 답장 생성, 스크리닝을 모두 실행하지 않았을 수 있다. 이 함수는
    target node의 단계에 맞춰 최소한의 데모 결과를 채워 각 노드를 독립적으로
    확인할 수 있게 한다.
    """
    notices = []

    if NODE_ORDER[target_node] >= NODE_ORDER["filter_letter"] and not st.session_state.knowledge:
        st.session_state.knowledge = DEMO_KNOWLEDGE
        notices.append("데모 knowledge를 채웠습니다.")

    if NODE_ORDER[target_node] >= NODE_ORDER["edit_prompt"] and not st.session_state.filter_result:
        st.session_state.filter_result = DEMO_FILTER_RESULT.copy()
        st.session_state.input_filter_state = "passed"
        notices.append("데모 필터 결과를 채웠습니다.")

    if NODE_ORDER[target_node] >= NODE_ORDER["screen_reply"] and not st.session_state.generated_reply:
        st.session_state.generated_reply = DEMO_REPLY
        st.session_state.screened_reply = DEMO_REPLY
        notices.append("데모 답장을 채웠습니다.")

    if NODE_ORDER[target_node] >= NODE_ORDER["improve_prompt"] and not st.session_state.screening_result:
        st.session_state.screening_result = DEMO_SCREENING_RESULT.copy()
        st.session_state.output_filter_state = "done"
        notices.append("데모 스크리닝 결과를 채웠습니다.")

    return notices


def ensure_defaults_for_node(target_node, extension_df):
    """특정 노드 접근 전에 사용자, 프롬프트, 데모 산출물 기본값을 준비한다.

    URL query parameter나 그래프 클릭으로 임의 노드에 접근했을 때도 앱이
    빈 상태로 깨지지 않도록 기본 사용자를 선택하고, 프롬프트 선택값을 보정하며,
    필요한 경우 데모 산출물을 채운다. 적용된 자동 보정 내용은 안내 문구로
    session_state에 저장한다.
    """
    notices = []
    if NODE_ORDER[target_node] >= NODE_ORDER["structure_knowledge"] and ensure_default_user(extension_df):
        notices.append(f"기본 사용자로 '{st.session_state.user_name}'을 선택했습니다.")

    before_prompts = {
        "filter": st.session_state.get("selected_filter_prompt_path"),
        "generation": st.session_state.get("selected_generation_prompt_path"),
        "output_filter": st.session_state.get("selected_screening_prompt_path"),
        "improvement": st.session_state.get("selected_improvement_prompt_path"),
    }
    ensure_default_prompts()
    after_prompts = {
        "filter": st.session_state.get("selected_filter_prompt_path"),
        "generation": st.session_state.get("selected_generation_prompt_path"),
        "output_filter": st.session_state.get("selected_screening_prompt_path"),
        "improvement": st.session_state.get("selected_improvement_prompt_path"),
    }
    if before_prompts != after_prompts:
        notices.append("기본 프롬프트 선택값을 적용했습니다.")

    notices.extend(ensure_demo_outputs_for_node(target_node))
    st.session_state.default_notice = " ".join(notices)


def get_user_letter(user_row):
    """선택된 사용자 row에서 답장 생성/필터링에 사용할 편지 본문을 추출한다.

    현재 데이터 구조에서는 사용자 편지가 `row.iloc[146]`에 있다고 가정한다.
    모델과 프롬프트가 편지 영역을 명확히 구분할 수 있도록 `[User Letter]`
    헤더를 붙인 문자열을 반환한다.
    """
    if user_row is None:
        return ""
    return "**[User Letter]**\n" + str(user_row.iloc[146])


def selected_filter_letter(user_letter):
    """입력 필터 노드에서 사용할 편지 원문을 선택한다.

    필터 입력 라디오가 `극단 편지 데모`이면 내장된 고위험 예시 편지를
    반환하고, 그렇지 않으면 실제 사용자 편지 `user_letter`를 반환한다.
    """
    if st.session_state.filter_input_source == "극단 편지 데모":
        return DEMO_EXTREME_LETTER
    return user_letter


def sync_filter_letter_editor(user_letter):
    """필터 테스트 text_area의 기본 편지를 현재 입력 소스와 동기화한다.

    실제 사용자 편지와 극단 편지 데모 사이를 전환하거나 원본 편지가 바뀌면
    편집기 값을 새 기본 텍스트로 갱신한다. 사용자가 직접 편집한 내용은 같은
    입력 소스/원문이 유지되는 동안 불필요하게 덮어쓰지 않는다.
    """
    base_text = selected_filter_letter(user_letter)
    source_changed = st.session_state.get("_loaded_filter_input_source") != st.session_state.filter_input_source
    base_changed = st.session_state.get("_loaded_filter_base_text") != base_text
    if source_changed or base_changed or not st.session_state.filter_letter_editor:
        st.session_state.filter_letter_editor = base_text
        st.session_state["_loaded_filter_input_source"] = st.session_state.filter_input_source
        st.session_state["_loaded_filter_base_text"] = base_text


def sync_filter_knowledge_editor():
    """입력 필터용 knowledge 편집기를 현재 구조화 knowledge와 동기화한다.

    지식 구조화가 새로 실행되거나 사용자가 바뀌어 knowledge가 달라지면
    편집기 기본값을 갱신한다. 같은 knowledge 기준에서는 사용자가 직접
    수정한 내용을 rerun 중에도 유지한다.
    """
    base_text = st.session_state.knowledge
    base_changed = st.session_state.get("_loaded_filter_knowledge_base_text") != base_text
    if base_changed or not st.session_state.filter_knowledge_editor:
        st.session_state.filter_knowledge_editor = base_text
        st.session_state["_loaded_filter_knowledge_base_text"] = base_text


def sync_generation_letter_editor(user_letter):
    """답장 생성 text_area의 기본 편지를 선택 사용자 편지와 동기화한다.

    사용자가 바뀌어 원본 편지가 달라지면 답장 생성용 편집기 값을 새 편지로
    초기화한다. 같은 사용자 안에서 사용자가 편집한 편지 내용은 rerun 중에도
    유지한다.
    """
    base_changed = st.session_state.get("_loaded_generation_letter_base_text") != user_letter
    if base_changed or not st.session_state.generation_letter_editor:
        st.session_state.generation_letter_editor = user_letter
        st.session_state["_loaded_generation_letter_base_text"] = user_letter


def selected_output_screening_reply(generated_reply):
    """출력 필터 노드에서 검수할 답장 본문을 선택한다.

    스크리닝 입력 라디오가 `저품질 답장 데모`이면 내장된 실패 예시 답장을
    반환하고, 그렇지 않으면 실제 생성 답장 `generated_reply`를 반환한다.
    """
    if st.session_state.output_screening_source == "저품질 답장 데모":
        return DEMO_BAD_REPLY
    return generated_reply


def sync_screening_reply_editor(generated_reply):
    """출력 스크리닝 text_area의 기본 답장을 현재 입력 소스와 동기화한다.

    실제 생성 답장과 저품질 데모 답장 사이를 전환하거나 생성 답장이 바뀌면
    편집기 값을 새 기본 텍스트로 갱신한다. 사용자가 직접 편집한 내용은 같은
    입력 소스/원문이 유지되는 동안 보존한다.
    """
    base_text = selected_output_screening_reply(generated_reply)
    source_changed = st.session_state.get("_loaded_output_screening_source") != st.session_state.output_screening_source
    base_changed = st.session_state.get("_loaded_output_screening_base_text") != base_text
    if source_changed or base_changed or not st.session_state.screening_reply_editor:
        st.session_state.screening_reply_editor = base_text
        st.session_state["_loaded_output_screening_source"] = st.session_state.output_screening_source
        st.session_state["_loaded_output_screening_base_text"] = base_text


def reset_user_outputs():
    """사용자 변경 시 이전 사용자에게 속한 산출물 상태를 초기화한다.

    knowledge, 필터 결과, 생성 답장, 스크리닝 결과, 개선 지시문과 편지
    편집기 로딩 기준을 모두 비워서 새 사용자 데이터와 이전 결과가 섞이지
    않도록 한다.
    """
    st.session_state.knowledge = ""
    st.session_state.filter_result = None
    st.session_state.input_filter_state = None
    st.session_state.filter_letter_editor = ""
    st.session_state.filter_knowledge_editor = ""
    st.session_state["_loaded_filter_input_source"] = None
    st.session_state["_loaded_filter_base_text"] = ""
    st.session_state["_loaded_filter_knowledge_base_text"] = ""
    st.session_state.generation_letter_editor = ""
    st.session_state["_loaded_generation_letter_base_text"] = ""
    st.session_state.generated_reply = ""
    st.session_state.output_screening_source = "생성된 답장"
    st.session_state.screening_reply_editor = ""
    st.session_state["_loaded_output_screening_source"] = None
    st.session_state["_loaded_output_screening_base_text"] = ""
    st.session_state.screened_reply = ""
    st.session_state.screening_result = None
    st.session_state.output_filter_state = None
    st.session_state.improvement_prompt = ""
    st.session_state.last_llm_io = []


def render_status_pill(label, ready):
    """노드 진행 상태를 작은 pill 형태의 HTML 배지로 표시한다.

    `ready`가 참이면 완료 스타일을, 거짓이면 비어 있는 상태 스타일을 적용한다.
    그래프 아래 요약 상태 영역에서 사용자 선택, 필터, 지식 생성, 답장 생성,
    스크리닝 완료 여부를 빠르게 보여주는 데 사용된다.
    """
    css_class = "ready" if ready else "empty"
    st.markdown(f'<span class="status-pill {css_class}">{label}</span>', unsafe_allow_html=True)


def graph_node_state(node_id):
    """노드 ID에 대응하는 현재 그래프 표시 상태를 계산한다.

    현재 열려 있는 노드는 active, 산출물이 있는 노드는 ready, 차단된 입력
    필터는 blocked, 개선 프롬프트가 있는 노드는 loop로 표시한다. 산출물이
    없으면 empty를 반환해 QA Graph의 CSS 클래스에 사용한다.
    """
    if st.session_state.node == node_id:
        return "active"
    if node_id == "select_user" and st.session_state.user_name:
        return "ready"
    if node_id == "filter_letter" and st.session_state.filter_result:
        return "blocked" if st.session_state.input_filter_state == "blocked" else "ready"
    if node_id == "structure_knowledge" and st.session_state.knowledge:
        return "ready"
    if node_id == "edit_prompt" and st.session_state.system_prompt:
        return "ready"
    if node_id == "screen_reply" and st.session_state.screening_result:
        return "ready"
    if node_id == "improve_prompt" and st.session_state.improvement_prompt:
        return "loop"
    return "empty"


def graph_node(node_id, title, subtitle, x, y, state, width=160):
    """QA Graph에서 클릭 가능한 주요 노드 HTML 조각을 생성한다.

    노드 ID, 제목, 부제, 좌표, 상태 CSS 클래스, 너비를 받아 absolute
    positioning된 anchor 태그 문자열을 반환한다. 클릭 시 `?node=...` query
    parameter로 이동해 해당 노드를 열도록 구성한다.
    """
    href = f"?node={node_id}"
    return f"""
<a class="resolve-node {state}" href="{href}" target="_self" style="left:{x}px; top:{y}px; width:{width}px;">
  <span class="node-port in"></span>
  <span class="node-port out"></span>
  <span class="node-title">{title}</span>
  <span class="node-subtitle">{subtitle}</span>
</a>
"""


def graph_note(node_id, title, subtitle, x, y, state="empty", width=150, clickable=True):
    """QA Graph에서 분기/결과를 설명하는 보조 노드 HTML 조각을 생성한다.

    차단, 통과, 최종 후보 같은 주요 노드 사이의 상태를 표현한다. `clickable`이
    참이면 anchor로 렌더링하고, 거짓이면 단순 div로 렌더링해 상태 표시만
    수행한다.
    """
    href = f"?node={node_id}"
    tag = "a" if clickable else "div"
    href_attr = f' href="{href}" target="_self"' if clickable else ""
    return f"""
<{tag} class="resolve-node note {state}"{href_attr} style="left:{x}px; top:{y}px; width:{width}px;">
  <span class="node-port in"></span>
  <span class="node-port out"></span>
  <span class="node-title">{title}</span>
  <span class="node-subtitle">{subtitle}</span>
</{tag}>
"""


def render_node_nav(extension_df):
    """앱 상단의 전체 QA Graph와 진행 상태 요약 UI를 렌더링한다.

    현재 session_state를 바탕으로 각 노드의 active/ready/blocked/loop 상태를
    계산하고, SVG wire와 HTML node를 조합해 QA 흐름을 시각화한다. 그래프 아래
    status pill과 자동 기본값 적용 안내 문구도 함께 표시한다.
    """
    state = graph_node_state
    block_state = "blocked" if st.session_state.input_filter_state == "blocked" else "empty"
    pass_state = "ready" if st.session_state.input_filter_state == "passed" else "empty"
    final_state = "ready" if st.session_state.screening_result else "empty"

    graph_html = f"""
<div class="resolve-graph-wrap">
  <div class="resolve-toolbar">
    <div>
      <div class="resolve-title">QA Graph</div>
      <div class="resolve-caption">클릭해서 어느 노드든 바로 열 수 있습니다. 분기와 루프는 실행 결과에 따라 색이 바뀝니다.</div>
    </div>
    <div class="resolve-legend">
      <span><i class="legend-dot active"></i>현재</span>
      <span><i class="legend-dot ready"></i>완료</span>
      <span><i class="legend-dot blocked"></i>차단/실패</span>
      <span><i class="legend-dot loop"></i>개선 루프</span>
    </div>
  </div>
  <div class="resolve-canvas">
    <svg class="resolve-wires" viewBox="0 0 1940 420" preserveAspectRatio="none">
      <path class="wire main" d="M180 105 C225 105 225 105 270 105" />
      <path class="wire main" d="M430 105 C485 105 485 105 540 105" />
      <path class="wire danger" d="M700 105 C740 105 740 56 780 56" />
      <path class="wire main" d="M700 105 C740 105 740 164 780 164" />
      <path class="wire main" d="M940 164 C980 164 980 164 1020 164" />
      <path class="wire main" d="M1175 164 C1235 164 1235 164 1295 164" />
      <path class="wire success" d="M1455 164 C1500 164 1500 92 1545 92" />
      <path class="wire loop" d="M1455 164 C1500 164 1500 238 1545 238" />
      <path class="wire loop" d="M1705 238 C1765 238 1765 342 1020 342 C960 342 960 268 1020 164" />
    </svg>
    <div class="canvas-label" style="left:22px; top:26px;">INPUT</div>
    <div class="canvas-label" style="left:282px; top:26px;">KNOWLEDGE</div>
    <div class="canvas-label" style="left:770px; top:26px;">FILTER BRANCH</div>
    <div class="canvas-label" style="left:1016px; top:26px;">PROMPT</div>
    <div class="canvas-label" style="left:1290px; top:26px;">QA</div>
    <div class="canvas-label" style="left:1540px; top:26px;">OUTCOME</div>
    {graph_node("select_user", "User", "사용자 선택", 20, 72, state("select_user"))}
    {graph_node("structure_knowledge", "Knowledge", "BFI/PVQ 포함", 270, 72, state("structure_knowledge"))}
    {graph_node("filter_letter", "Input Filter", "편지+knowledge", 540, 72, state("filter_letter"))}
    {graph_note("filter_letter", "Blocked", "차단 결과 표시", 780, 24, block_state, clickable=False)}
    {graph_note("edit_prompt", "Passed", "통과 결과 표시", 780, 132, pass_state, clickable=False)}
    {graph_node("edit_prompt", "System Prompt", "프롬프트+생성", 1020, 132, state("edit_prompt"))}
    {graph_node("screen_reply", "Output Filter", "답장 품질 검수", 1295, 132, state("screen_reply"))}
    {graph_note("screen_reply", "Final", "통과 후보", 1545, 60, final_state)}
    {graph_node("improve_prompt", "Improve", "개선 지시문", 1545, 206, state("improve_prompt"))}
  </div>
</div>
"""
    st.markdown(graph_html, unsafe_allow_html=True)

    status_cols = st.columns(5)
    with status_cols[0]:
        render_status_pill("사용자 선택", bool(st.session_state.user_name))
    with status_cols[1]:
        render_status_pill("지식 생성", bool(st.session_state.knowledge))
    with status_cols[2]:
        filter_ok = bool(st.session_state.filter_result)
        render_status_pill("필터 완료", filter_ok)
    with status_cols[3]:
        render_status_pill("답장 생성", bool(st.session_state.generated_reply))
    with status_cols[4]:
        render_status_pill("스크리닝", bool(st.session_state.screening_result))
    if st.session_state.default_notice:
        st.caption(st.session_state.default_notice)
        st.session_state.default_notice = ""


def sync_node_from_query_params(extension_df):
    """URL query parameter의 `node` 값을 session_state의 현재 노드와 동기화한다.

    QA Graph의 링크 클릭처럼 `?node=...`가 들어온 경우 유효한 노드인지
    확인하고, 필요한 기본값과 데모 산출물을 준비한 뒤 현재 노드를 변경한다.
    같은 query 값을 반복 처리하지 않도록 `_synced_query_node`를 기록한다.
    """
    node_from_url = st.query_params.get("node")
    if isinstance(node_from_url, list):
        node_from_url = node_from_url[0] if node_from_url else None
    if node_from_url in NODE_ORDER and node_from_url != st.session_state.get("_synced_query_node"):
        ensure_defaults_for_node(node_from_url, extension_df)
        st.session_state.node = node_from_url
        st.session_state["_synced_query_node"] = node_from_url


def render_filter_prompt_selector():
    """입력 필터 프롬프트 선택 UI와 편집기를 렌더링한다.

    `extension_prompts/input_filter` 폴더의 Markdown 파일을 selectbox에 표시하고,
    선택된 파일 내용을 text_area에서 확인/수정/저장할 수 있게 한다. 이
    프롬프트는 사용자 편지의 고위험 여부를 판단하는 system prompt로 쓰인다.
    """
    filter_options = prompt_options("input_filter")
    st.selectbox(
        "사용자 편지 필터 프롬프트",
        options=filter_options,
        format_func=prompt_label,
        key="selected_filter_prompt_path",
    )
    render_prompt_editor(
        st.session_state.selected_filter_prompt_path,
        "선택한 input filter 프롬프트 내용",
        "input_filter_prompt",
    )


def render_generation_prompt_selector():
    """답장 생성 프롬프트 선택 UI와 system prompt 편집기를 렌더링한다.

    `extension_prompts/reply_generation` 폴더의 Markdown 파일을 선택하게 하고,
    선택된 파일 내용을 `st.session_state.system_prompt`와 동기화한다. 편집기
    수정값은 현재 세션의 생성 system prompt에 즉시 반영된다.
    """
    generation_options = prompt_options("reply_generation")
    current_selection = st.session_state.get("selected_generation_prompt_path")
    if current_selection in generation_options:
        selection_index = generation_options.index(current_selection)
    elif generation_options:
        selection_index = 0
    else:
        selection_index = None
    st.selectbox(
        "답장 생성 프롬프트",
        options=generation_options,
        index=selection_index,
        placeholder="프롬프트를 선택하세요",
        format_func=prompt_label,
        key="selected_generation_prompt_path",
    )
    sync_generation_prompt_from_selection()
    if st.session_state.selected_generation_prompt_path:
        return render_prompt_editor(
            st.session_state.selected_generation_prompt_path,
            "선택한 답장 생성 프롬프트 파일 내용",
            "generation_prompt",
            height=360,
            sync_system_prompt=True,
        )
    else:
        st.info("답장 생성 프롬프트 파일을 선택하면 내용을 확인하고 수정할 수 있습니다.")
        return ""


def render_screening_prompt_selector():
    """출력 스크리닝 프롬프트 선택 UI와 편집기를 렌더링한다.

    `extension_prompts/output_filter` 폴더의 Markdown 파일을 선택하고 편집할 수
    있게 한다. 선택된 프롬프트는 생성된 답장을 JSON 형태로 품질 평가하는
    system prompt로 사용된다.
    """
    screening_options = prompt_options("output_filter")
    st.selectbox(
        "답장 스크리닝 프롬프트",
        options=screening_options,
        format_func=prompt_label,
        key="selected_screening_prompt_path",
    )
    render_prompt_editor(
        st.session_state.selected_screening_prompt_path,
        "선택한 output filter 프롬프트 내용",
        "output_filter_prompt",
    )


def render_improvement_prompt_selector():
    """개선 지시문 생성 프롬프트 선택 UI와 편집기를 렌더링한다.

    `extension_prompts/improvement` 폴더의 Markdown 파일을 선택하고 편집할 수
    있게 한다. 선택된 프롬프트는 현재 답장을 분석해 다음 생성에 붙일 revision
    guidance를 만드는 데 사용된다.
    """
    improvement_options = prompt_options("improvement")
    st.selectbox(
        "개선 프롬프트 생성 프롬프트",
        options=improvement_options,
        format_func=prompt_label,
        key="selected_improvement_prompt_path",
    )
    render_prompt_editor(
        st.session_state.selected_improvement_prompt_path,
        "선택한 improvement 프롬프트 내용",
        "improvement_prompt_file",
    )


def run_filter(user_letter, knowledge):
    """현재 선택된 input filter 프롬프트로 사용자 편지와 knowledge를 함께 스크리닝한다.

    편집기에서 확정된 `user_letter`와 앞단에서 생성한 `knowledge`를 OpenAI에
    함께 보내 고위험/극단적 내용 여부를 JSON으로 평가한다. 결과 dict는
    `filter_result`에 저장하고, status가 `차단`이면 `input_filter_state`를
    blocked로, 그 외에는 passed로 설정한다.
    """
    if not knowledge:
        st.warning("입력 필터를 실행하기 전에 먼저 지식 구조화를 실행하세요.")
        st.stop()
    filter_prompt = read_prompt(st.session_state.selected_filter_prompt_path)
    with st.spinner("사용자 편지의 고위험 내용을 필터링 중..."):
        try:
            clear_llm_call_log()
            result = dd_filter_user_letter_gpt4(filter_prompt, user_letter, knowledge)
        except openai.AuthenticationError:
            show_openai_auth_error()
        st.session_state.filter_result = result
        st.session_state.last_llm_io = get_llm_call_log()
        st.session_state.input_filter_state = "blocked" if result.get("status") == "차단" else "passed"


def run_knowledge(user_row):
    """선택 사용자 row를 기반으로 답장 생성용 knowledge를 생성한다.

    `ext_knowledge_generate()`를 호출해 demographics, 선호/비선호, BFI, PVQ,
    미래 프로필을 하나의 문자열로 구성하고 `st.session_state.knowledge`에
    저장한다. OpenAI 인증 오류가 발생하면 사용자 친화 메시지로 중단한다.
    """
    with st.spinner("지식을 구조화하는 중..."):
        try:
            clear_llm_call_log()
            st.session_state.knowledge = ext_knowledge_generate(user_row)
            st.session_state.filter_knowledge_editor = st.session_state.knowledge
            st.session_state["_loaded_filter_knowledge_base_text"] = st.session_state.knowledge
            st.session_state.last_llm_io = get_llm_call_log()
        except openai.AuthenticationError:
            show_openai_auth_error()


def generation_prompt_with_improvement(system_prompt=None):
    """현재 답장 생성 system prompt에 개선 지시문을 조건부로 덧붙인다.

    기본값은 `st.session_state.system_prompt`이며, 개선 프롬프트 노드에서 만든
    `improvement_prompt`가 있으면 `[Additional revision guidance]` 섹션으로
    이어 붙여 다음 답장 생성에 반영한다.
    """
    system_prompt = current_generation_prompt_text() if system_prompt is None else system_prompt
    if st.session_state.improvement_prompt:
        return f"{system_prompt}\n\n[Additional revision guidance]\n{st.session_state.improvement_prompt}"
    return system_prompt


def run_generation(user_letter):
    """사용자 편지, knowledge, system prompt를 이용해 답장 1개를 생성한다.

    새 답장을 만들기 전에 이전 스크리닝 결과를 비우고, `dd_generate_gpt4_basic()`에
    system prompt, 구조화 knowledge, 사용자 편지를 전달한다. 생성 결과는
    `st.session_state.generated_reply`에 저장되어 화면과 후속 스크리닝 노드에서
    사용된다.
    """
    st.session_state.screening_result = None
    st.session_state.output_filter_state = None
    with st.spinner("답장 1개를 생성하는 중..."):
        try:
            clear_llm_call_log()
            st.session_state.generated_reply = dd_generate_gpt4_basic(
                generation_prompt_with_improvement(),
                st.session_state.knowledge,
                user_letter,
            )
            st.session_state.last_llm_io = get_llm_call_log()
        except openai.AuthenticationError:
            show_openai_auth_error()


def run_screening(reply):
    """생성된 답장을 output filter 프롬프트로 검수한다.

    현재 스크리닝 대상으로 선택된 답장과 output filter 프롬프트를 OpenAI에
    보내 JSON 평가 결과를 받고, 글자 수를 추가한 뒤 `screening_result`에
    저장한다. 실행 완료 여부는 `output_filter_state`로 표시한다.
    """
    screening_prompt = read_prompt(st.session_state.selected_screening_prompt_path)
    with st.spinner("생성된 답장을 스크리닝 중..."):
        try:
            clear_llm_call_log()
            result = dd_evaluate_letter_with_prompt_gpt4(
                reply,
                screening_prompt,
                original_letter=st.session_state.generation_letter_editor,
                knowledge=st.session_state.knowledge,
            )
        except openai.AuthenticationError:
            show_openai_auth_error()
        st.session_state.screened_reply = reply
        st.session_state.last_llm_io = get_llm_call_log()
        result["char_count"] = len(reply)
        st.session_state.screening_result = result
        st.session_state.output_filter_state = "done"


def run_improvement_prompt():
    """현재 생성 답장을 바탕으로 다음 생성용 개선 지시문을 만든다.

    선택된 improvement 프롬프트와 `generated_reply`를 OpenAI에 보내 revision
    guidance를 생성하고 `st.session_state.improvement_prompt`에 저장한다. 이
    값은 이후 `generation_prompt_with_improvement()`를 통해 system prompt에
    추가된다.
    """
    improvement_system_prompt = read_prompt(st.session_state.selected_improvement_prompt_path)
    with st.spinner("다음 생성을 위한 개선 지시문을 만드는 중..."):
        try:
            clear_llm_call_log()
            st.session_state.improvement_prompt = dd_generate_improvement_prompt_gpt4(
                improvement_system_prompt,
                st.session_state.screened_reply or st.session_state.generated_reply,
            )
            st.session_state.last_llm_io = get_llm_call_log()
        except openai.AuthenticationError:
            show_openai_auth_error()


def render_filter_result():
    """입력 필터 실행 결과를 Streamlit 화면에 표시한다.

    `filter_result`가 없으면 아무것도 렌더링하지 않는다. 결과 status가 `차단`
    이면 error 스타일로, 그 외에는 success 스타일로 요약을 보여주고 전체 JSON
    결과를 `st.json()`으로 표시한다.
    """
    result = st.session_state.filter_result
    if not result:
        return
    status = result.get("status", "")
    if status == "차단":
        st.error(f"필터 결과: {status} / 위험도: {result.get('risk_level', '-')}")
    else:
        st.success(f"필터 결과: {status} / 위험도: {result.get('risk_level', '-')}")
    letter_risk = result.get("letter_risk")
    if isinstance(letter_risk, dict):
        st.write(
            f"**Letter risk**: {letter_risk.get('status', '-')} / "
            f"{letter_risk.get('risk_level', '-')}"
        )
        if letter_risk.get("categories"):
            st.caption("Letter categories: " + ", ".join(letter_risk.get("categories", [])))
    knowledge_risk = result.get("knowledge_risk")
    if isinstance(knowledge_risk, dict):
        knowledge_detected = knowledge_risk.get("detected", False)
        knowledge_level = knowledge_risk.get("risk_level", "-")
        if knowledge_detected:
            st.warning(f"Knowledge risk: 감지됨 / {knowledge_level}")
            if knowledge_risk.get("categories"):
                st.caption("Knowledge categories: " + ", ".join(knowledge_risk.get("categories", [])))
            evidence = knowledge_risk.get("evidence", [])
            if evidence:
                st.caption("Knowledge evidence: " + " / ".join(map(str, evidence)))
        else:
            st.info(f"Knowledge risk: 없음 / {knowledge_level}")
    st.json(result)


def render_screening_result():
    """출력 스크리닝 결과를 사람이 읽기 쉬운 형태와 JSON 원문으로 표시한다.

    `screening_result`가 없으면 렌더링하지 않는다. 판정, 요약, 주요 dimension,
    수정 제안, 글자 수를 순서대로 표시하고, 전체 JSON은 expander 안에 넣어
    디버깅과 프롬프트 개선에 활용할 수 있게 한다.
    """
    result = st.session_state.screening_result
    if not result:
        return
    if result.get("status"):
        st.info(f"판정: {result['status']}")
    if result.get("summary"):
        st.write(result["summary"])
    dimensions = result.get("dimensions")
    if isinstance(dimensions, dict):
        for dimension_name, dimension_result in dimensions.items():
            if not isinstance(dimension_result, dict):
                continue
            if "passed" in dimension_result:
                status = "pass" if dimension_result.get("passed") else "fail"
            else:
                status = dimension_result.get("status", "-")
            note = dimension_result.get("note") or dimension_result.get("feedback", "")
            evidence = dimension_result.get("evidence")
            st.write(f"**{dimension_name}**: {status}")
            if evidence and evidence != "none":
                st.caption(f"Evidence: {evidence}")
            if note:
                st.caption(note)
    elif result.get("quality_notes"):
        st.write(result["quality_notes"])
    if result.get("suggested_revision"):
        st.write(result["suggested_revision"])
    improvement_points = result.get("improvement_points")
    if isinstance(improvement_points, list) and improvement_points:
        st.write("**개선 포인트**")
        for point in improvement_points:
            st.write(f"- {point}")
    if result.get("char_count") is not None:
        st.caption(f"글자 수: {result['char_count']}자")
    with st.expander("Output filter JSON"):
        st.json(result)


st.markdown(
    """
<style>
@import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard/dist/web/static/pretendard.css');
html, body, [class*="css"], g {
  font-family: Pretendard, -apple-system, BlinkMacSystemFont, system-ui, Roboto, 'Helvetica Neue',
               'Segoe UI', 'Apple SD Gothic Neo', 'Noto Sans KR', 'Malgun Gothic', sans-serif;
}
.status-pill {
  display: inline-block;
  padding: 0.25rem 0.55rem;
  border-radius: 999px;
  border: 1px solid #d0d7de;
  color: #57606a;
  font-size: 0.85rem;
  white-space: nowrap;
}
.status-pill.ready {
  border-color: #2da44e;
  color: #1a7f37;
  background: #dafbe1;
}
.status-pill.empty {
  background: #f6f8fa;
}
.graph-caption {
  color: #57606a;
  font-size: 0.92rem;
  margin: -0.25rem 0 0.7rem;
}
.graph-lane-title {
  color: #24292f;
  font-weight: 700;
  font-size: 0.9rem;
  margin-bottom: 0.45rem;
}
.graph-arrow,
.graph-split {
  color: #57606a;
  font-size: 0.85rem;
  text-align: center;
  margin: 0.22rem 0;
}
.graph-merge {
  color: #57606a;
  background: #f6f8fa;
  border: 1px dashed #d0d7de;
  border-radius: 6px;
  font-size: 0.82rem;
  line-height: 1.35;
  margin-top: 0.45rem;
  padding: 0.45rem 0.55rem;
}
.branch-card {
  border: 1px solid #d0d7de;
  background: #f6f8fa;
  border-radius: 6px;
  min-height: 4.25rem;
  padding: 0.55rem 0.65rem;
}
.branch-card.ready {
  border-color: #2da44e;
  background: #dafbe1;
}
.branch-card.blocked {
  border-color: #cf222e;
  background: #ffebe9;
}
.branch-card.loop {
  border-color: #9a6700;
  background: #fff8c5;
}
.branch-title {
  color: #24292f;
  font-weight: 700;
  font-size: 0.9rem;
}
.branch-body {
  color: #57606a;
  font-size: 0.8rem;
  line-height: 1.35;
  margin-top: 0.25rem;
}
.resolve-graph-wrap {
  border: 1px solid #30363d;
  border-radius: 8px;
  background: #0d1117;
  box-shadow: inset 0 1px 0 rgba(255,255,255,0.04), 0 8px 24px rgba(27,31,36,0.12);
  margin: 0.2rem 0 1rem;
  overflow: hidden;
}
.resolve-toolbar {
  align-items: center;
  background: #161b22;
  border-bottom: 1px solid #30363d;
  display: flex;
  justify-content: space-between;
  gap: 1rem;
  padding: 0.75rem 0.9rem;
}
.resolve-title {
  color: #f0f6fc;
  font-size: 0.98rem;
  font-weight: 700;
}
.resolve-caption {
  color: #8b949e;
  font-size: 0.82rem;
  line-height: 1.35;
  margin-top: 0.14rem;
}
.resolve-legend {
  align-items: center;
  color: #8b949e;
  display: flex;
  flex-wrap: wrap;
  font-size: 0.78rem;
  gap: 0.65rem;
  justify-content: flex-end;
}
.legend-dot {
  border-radius: 999px;
  display: inline-block;
  height: 0.55rem;
  margin-right: 0.25rem;
  width: 0.55rem;
}
.legend-dot.active { background: #58a6ff; }
.legend-dot.ready { background: #3fb950; }
.legend-dot.blocked { background: #f85149; }
.legend-dot.loop { background: #d29922; }
.resolve-canvas {
  background-color: #0d1117;
  background-image:
    linear-gradient(rgba(139,148,158,0.10) 1px, transparent 1px),
    linear-gradient(90deg, rgba(139,148,158,0.10) 1px, transparent 1px);
  background-size: 28px 28px;
  height: 420px;
  min-width: 1940px;
  overflow: hidden;
  position: relative;
}
.resolve-graph-wrap {
  overflow-x: auto;
}
.resolve-wires {
  height: 420px;
  left: 0;
  pointer-events: none;
  position: absolute;
  top: 0;
  width: 1940px;
}
.wire {
  fill: none;
  opacity: 0.92;
  stroke: #6e7681;
  stroke-linecap: round;
  stroke-width: 3;
}
.wire.main { stroke: #58a6ff; }
.wire.danger { stroke: #f85149; }
.wire.success { stroke: #3fb950; }
.wire.loop {
  stroke: #d29922;
  stroke-dasharray: 10 8;
}
.canvas-label {
  color: #6e7681;
  font-size: 0.68rem;
  font-weight: 700;
  letter-spacing: 0.08em;
  position: absolute;
}
.resolve-node {
  background: linear-gradient(180deg, #30363d 0%, #161b22 100%);
  border: 1px solid #6e7681;
  border-radius: 7px;
  box-shadow: 0 10px 20px rgba(1,4,9,0.35);
  color: #f0f6fc !important;
  display: block;
  min-height: 64px;
  padding: 0.62rem 0.72rem 0.54rem;
  position: absolute;
  text-decoration: none !important;
  transition: border-color 120ms ease, box-shadow 120ms ease, transform 120ms ease;
  z-index: 2;
}
.resolve-node:hover {
  border-color: #79c0ff;
  box-shadow: 0 0 0 1px rgba(88,166,255,0.35), 0 14px 28px rgba(1,4,9,0.45);
  transform: translateY(-1px);
}
.resolve-node.active {
  border-color: #58a6ff;
  box-shadow: 0 0 0 2px rgba(88,166,255,0.44), 0 14px 28px rgba(1,4,9,0.45);
}
.resolve-node.ready {
  border-color: #3fb950;
}
.resolve-node.blocked {
  border-color: #f85149;
}
.resolve-node.loop {
  border-color: #d29922;
}
.resolve-node.note.empty {
  opacity: 0.62;
}
.node-title {
  display: block;
  font-size: 0.9rem;
  font-weight: 700;
  line-height: 1.1;
}
.node-subtitle {
  color: #8b949e;
  display: block;
  font-size: 0.74rem;
  line-height: 1.25;
  margin-top: 0.28rem;
}
.node-port {
  background: #0d1117;
  border: 2px solid #8b949e;
  border-radius: 999px;
  height: 12px;
  position: absolute;
  top: 30px;
  width: 12px;
}
.node-port.in {
  left: -8px;
}
.node-port.out {
  right: -8px;
}
.resolve-node.active .node-port,
.resolve-node:hover .node-port {
  border-color: #79c0ff;
}
.resolve-node.ready .node-port {
  border-color: #3fb950;
}
.resolve-node.blocked .node-port {
  border-color: #f85149;
}
.resolve-node.loop .node-port {
  border-color: #d29922;
}
</style>
""",
    unsafe_allow_html=True,
)

init_state()
if st.session_state.node not in NODE_ORDER:
    st.session_state.node = "select_user"
extension_df = load_data()
ensure_default_prompts()
sync_node_from_query_params(extension_df)
if st.session_state.node != "select_user":
    ensure_defaults_for_node(st.session_state.node, extension_df)
user_row = get_user_row(extension_df)
user_letter_to_agent = get_user_letter(user_row)

st.title("[FutureSelf Extension] QA")
render_node_nav(extension_df)
st.markdown("---")

if st.session_state.node == "select_user":
    st.subheader("1. 사용자 선택")
    with st.form("user_select"):
        user_name = st.radio(
            "Select User Name",
            options=extension_df.iloc[:, 0].dropna().unique(),
            index=list(extension_df.iloc[:, 0].dropna().unique()).index(st.session_state.user_name)
            if st.session_state.user_name in extension_df.iloc[:, 0].dropna().unique()
            else 0,
            key="user_radio",
        )
        submit = st.form_submit_button("선택하고 지식 구조화로 이동")
    if submit:
        if st.session_state.user_name != user_name:
            reset_user_outputs()
        st.session_state.user_name = user_name
        st.session_state.node = "structure_knowledge"
        st.rerun()

elif st.session_state.node == "structure_knowledge":
    st.subheader("2. 지식 구조화")
    if st.button("지식 구조화 실행", type="primary"):
        run_knowledge(user_row)
        st.rerun()
    if st.session_state.knowledge:
        st.write(st.session_state.knowledge)
        render_last_llm_io()
        if st.button("편지 필터링으로 이동"):
            st.session_state.node = "filter_letter"
            st.rerun()

elif st.session_state.node == "filter_letter":
    st.subheader("3. INPUT SCREENING")
    render_filter_prompt_selector()
    st.radio(
        "필터 입력",
        options=["사용자 편지", "극단 편지 데모"],
        key="filter_input_source",
        horizontal=True,
    )
    sync_filter_letter_editor(user_letter_to_agent)
    sync_filter_knowledge_editor()
    filter_letter = st.text_area(
        "필터 테스트 편지",
        value=st.session_state.filter_letter_editor,
        height=260,
    )
    st.session_state.filter_letter_editor = filter_letter
    filter_knowledge = st.text_area(
        "필터 테스트 knowledge",
        value=st.session_state.filter_knowledge_editor,
        height=360,
    )
    if filter_knowledge != st.session_state.knowledge:
        st.session_state.knowledge = filter_knowledge
        st.session_state.filter_result = None
        st.session_state.input_filter_state = None
    st.session_state.filter_knowledge_editor = filter_knowledge
    st.session_state["_loaded_filter_knowledge_base_text"] = filter_knowledge
    if st.button("필터링 실행", type="primary"):
        run_filter(filter_letter, filter_knowledge)
        st.rerun()
    render_filter_result()
    render_last_llm_io()
    if st.session_state.filter_result and st.button("시스템 프롬프트로 이동", type="primary"):
        st.session_state.node = "edit_prompt"
        st.rerun()

elif st.session_state.node == "edit_prompt":
    st.subheader("4. 시스템 프롬프트 / 답장 생성")
    edited_generation_prompt = render_generation_prompt_selector()
    sync_generation_letter_editor(user_letter_to_agent)
    with st.expander("사용자가 작성한 편지", expanded=True):
        user_letter = st.text_area(
            "답장 생성에 사용할 사용자 편지",
            value=st.session_state.generation_letter_editor,
            height=260,
        )
        st.session_state.generation_letter_editor = user_letter
    if st.session_state.improvement_prompt:
        with st.expander("현재 적용 중인 개선 지시문", expanded=True):
            st.write(st.session_state.improvement_prompt)
            if st.button("개선 지시문 제거"):
                st.session_state.improvement_prompt = ""
                st.rerun()
    if st.button("답장 1개 생성", type="primary"):
        run_generation(user_letter)
        st.rerun()
    if st.session_state.generated_reply:
        st.markdown("### 생성된 답장")
        st.write(st.session_state.generated_reply)
        render_last_llm_io()
        if st.button("답장 스크리닝으로 이동"):
            st.session_state.node = "screen_reply"
            st.rerun()

elif st.session_state.node == "screen_reply":
    st.subheader("5. 답장 스크리닝")
    render_screening_prompt_selector()
    st.radio(
        "스크리닝 입력",
        options=["생성된 답장", "저품질 답장 데모"],
        key="output_screening_source",
        horizontal=True,
    )
    sync_screening_reply_editor(st.session_state.generated_reply)
    with st.expander("스크리닝할 답장", expanded=True):
        screening_reply = st.text_area(
            "output filter 테스트 답장",
            value=st.session_state.screening_reply_editor,
            height=320,
        )
        st.session_state.screening_reply_editor = screening_reply
    if st.button("스크리닝 실행", type="primary"):
        run_screening(screening_reply)
        st.rerun()
    render_screening_result()
    render_last_llm_io()
    if st.session_state.screening_result:
        if st.button("개선 프롬프트로 이동"):
            st.session_state.node = "improve_prompt"
            st.rerun()

elif st.session_state.node == "improve_prompt":
    st.subheader("6. 개선 프롬프트")
    render_improvement_prompt_selector()
    render_screening_result()
    if st.button("개선 지시문 생성", type="primary"):
        run_improvement_prompt()
        st.rerun()
    if st.session_state.improvement_prompt:
        render_last_llm_io()
        edited_improvement_prompt = st.text_area(
            "다음 답장 생성에 적용할 개선 지시문",
            value=st.session_state.improvement_prompt,
            height=220,
        )
        st.session_state.improvement_prompt = edited_improvement_prompt
        if st.button("적용하고 시스템 프롬프트로 이동", type="primary"):
            st.session_state.node = "edit_prompt"
            st.rerun()
