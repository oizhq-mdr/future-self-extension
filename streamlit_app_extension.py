import os
from pathlib import Path

import openai
import pandas as pd
import streamlit as st

from ext_knowledge_structure import *
from gpt_structure import (
    dd_evaluate_letter_with_prompt_gpt4,
    dd_filter_user_letter_gpt4,
    dd_generate_gpt4_basic,
    dd_generate_improvement_prompt_gpt4,
)


def configure_openai_api_key():
    api_key = str(st.secrets.get("OPENAI_API_KEY", os.environ.get("OPENAI_API_KEY", ""))).strip()
    if not api_key or api_key == "your-api-key":
        st.error("OpenAI API key가 설정되지 않았습니다. Streamlit Cloud Secrets에 OPENAI_API_KEY를 추가하세요.")
        st.stop()
    openai.api_key = api_key
    os.environ["OPENAI_API_KEY"] = api_key


configure_openai_api_key()


def show_openai_auth_error():
    st.error(
        "OpenAI 인증에 실패했습니다. Streamlit Cloud Secrets의 OPENAI_API_KEY가 올바른지, "
        "키가 만료/폐기되지 않았는지, 해당 프로젝트에 모델 사용 권한과 결제 설정이 있는지 확인하세요."
    )
    st.stop()

PROMPT_ROOT = Path("data/prompt_template")
EXT_PROMPT_ROOT = PROMPT_ROOT / "extension_prompts"
NODES = [
    ("select_user", "1. 사용자 선택"),
    ("filter_letter", "2. 편지 필터링"),
    ("structure_knowledge", "3. 지식 구조화"),
    ("edit_prompt", "4. 시스템 프롬프트"),
    ("generate_reply", "5. 답장 생성"),
    ("screen_reply", "6. 답장 스크리닝"),
    ("improve_prompt", "7. 개선 프롬프트"),
]
NODE_ORDER = {node_id: index for index, (node_id, _) in enumerate(NODES)}

DEMO_FILTER_RESULT = {
    "status": "통과",
    "risk_level": "낮음",
    "categories": ["demo"],
    "reason": "데모 모드: 바로 노드 테스트를 할 수 있도록 통과 결과를 임시로 채웠습니다.",
    "recommended_action": "필요하면 필터링 실행 버튼으로 실제 평가를 다시 실행하세요.",
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
[Big 5 Personality Traits in 2025] The following section presents an overview of the person's personality within five key domains, showcasing their traits spectrum and the extent of their qualities in each area. Each domain comprises several facets that provide deeper insights into their unique personality traits.

They come across as confident without being pushy, treating people with courtesy and giving others the benefit of the doubt. They produce a lot and keep things organized, turning inventive ideas into plans others can follow. They enjoy good conversation and can take the lead, but they don’t chase constant social buzz and prefer quality over quantity. Their mood is steady and upbeat; a touch of worry simply reminds them to prepare. Their taste is refined and their imagination lively, so their work often has a distinctive look and feel. With teammates, they set a clear direction and still make space for other voices, which builds trust and momentum. They work best in well-timed bursts with breaks to recharge, rather than endless sprints. Watch-outs: being very trusting can attract freeloaders, and saying yes too often can stretch their energy; setting boundaries and pacing commitments keep them at their best.

[Life-guiding Principles in 2025] The information provided below is the values that reflect the relative importance this person places on different aspects of life, guiding their decisions, actions, and perspectives. These values are fundamental components of their personality and play a crucial role in shaping who this person is.

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

DEMO_SCREENING_RESULT = {
    "status": "false",
    "summary": "데모 결과입니다. 실제 검수는 output filter 실행 버튼으로 다시 실행하세요.",
    "quality_notes": "원본 편지의 구체적 표현과 미래 일상 장면을 더 생생하게 반영하면 좋습니다.",
    "suggested_revision": "문체의 결을 더 가깝게 맞추고, 미래의 하루를 한두 장면으로 구체화하세요.",
}

DEMO_IMPROVEMENT_PROMPT = """- 원본 편지에서 드러난 표현 습관과 감정의 결을 더 가까이 따라가세요.
- 미래의 하루를 한두 장면으로 구체화하되, 대학명이나 직업을 확정하지 마세요.
- 조언처럼 말하기보다 같은 사람의 시간이 지난 목소리로 답하세요."""


st.set_page_config(
    page_title="[FutureSelf Extension] Node QA",
    page_icon="📩",
    layout="wide",
    initial_sidebar_state="expanded",
)


@st.cache_data
def load_data():
    return pd.read_csv(
        "https://docs.google.com/spreadsheets/d/1MN6NmPU_DjJR2zYZ5Ct_SwiOuuvGXkpXBjT9DJYRYyQ/export?format=csv"
    )


def init_state():
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
        "_loaded_filter_input_source": None,
        "_loaded_filter_base_text": "",
        "filter_result": None,
        "input_filter_state": None,
        "generation_letter_editor": "",
        "_loaded_generation_letter_base_text": "",
        "generated_reply": "",
        "screening_result": None,
        "output_filter_state": None,
        "improvement_prompt": "",
        "default_notice": "",
        "_synced_query_node": None,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def read_prompt(path):
    prompt_path = Path(path)
    if not prompt_path.exists():
        return ""
    return prompt_path.read_text(encoding="utf-8")


def write_prompt(path, content):
    Path(path).write_text(content, encoding="utf-8")


def prompt_options(category, default_path=None):
    files = []
    category_dir = EXT_PROMPT_ROOT / category
    if category_dir.exists():
        files.extend(sorted(category_dir.glob("*.md")))
    if default_path and default_path.exists():
        files.insert(0, default_path)
    return [str(file) for file in files]


def set_prompt_default(key, options):
    if options and st.session_state.get(key) not in options:
        st.session_state[key] = options[0]


def prompt_label(path):
    prompt_path = Path(path)
    if prompt_path.parent.name in {
        "input_filter",
        "output_filter",
        "improvement",
        "reply_generation",
    }:
        return f"{prompt_path.parent.name}/{prompt_path.name}"
    return prompt_path.name


def get_user_row(extension_df):
    if not st.session_state.user_name:
        return None
    matches = extension_df[extension_df.iloc[:, 0] == st.session_state.user_name]
    if matches.empty:
        return None
    return matches.iloc[0]


def default_user_name(extension_df):
    names = extension_df.iloc[:, 0].dropna().unique()
    if len(names) == 0:
        return None
    return names[0]


def ensure_default_user(extension_df):
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
    filter_options = prompt_options("input_filter")
    screening_options = prompt_options("output_filter")
    improvement_options = prompt_options("improvement")

    set_prompt_default("selected_filter_prompt_path", filter_options)
    set_prompt_default("selected_screening_prompt_path", screening_options)
    set_prompt_default("selected_improvement_prompt_path", improvement_options)

    selected_generation = st.session_state.selected_generation_prompt_path
    if selected_generation and (
        not st.session_state.system_prompt or st.session_state.get("_loaded_generation_prompt") != selected_generation
    ):
        st.session_state.system_prompt = read_prompt(selected_generation)
        st.session_state["_loaded_generation_prompt"] = selected_generation


def sync_generation_prompt_from_selection():
    selected_generation = st.session_state.selected_generation_prompt_path
    if selected_generation and st.session_state.get("_loaded_generation_prompt") != selected_generation:
        st.session_state.system_prompt = read_prompt(selected_generation)
        st.session_state["_loaded_generation_prompt"] = selected_generation


def render_prompt_editor(path, label, key_prefix, height=260, sync_system_prompt=False):
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
    if st.button("프롬프트 저장", key=f"{key_prefix}_save"):
        write_prompt(path, edited_prompt)
        if sync_system_prompt:
            st.session_state["_loaded_generation_prompt"] = path
        st.success("프롬프트를 저장했습니다.")


def ensure_demo_outputs_for_node(target_node):
    notices = []

    if NODE_ORDER[target_node] >= NODE_ORDER["structure_knowledge"] and not st.session_state.filter_result:
        st.session_state.filter_result = DEMO_FILTER_RESULT.copy()
        st.session_state.input_filter_state = "passed"
        notices.append("데모 필터 결과를 채웠습니다.")

    if NODE_ORDER[target_node] >= NODE_ORDER["edit_prompt"] and not st.session_state.knowledge:
        st.session_state.knowledge = DEMO_KNOWLEDGE
        notices.append("데모 knowledge를 채웠습니다.")

    if NODE_ORDER[target_node] >= NODE_ORDER["screen_reply"] and not st.session_state.generated_reply:
        st.session_state.generated_reply = DEMO_REPLY
        notices.append("데모 답장을 채웠습니다.")

    if NODE_ORDER[target_node] >= NODE_ORDER["improve_prompt"] and not st.session_state.screening_result:
        st.session_state.screening_result = DEMO_SCREENING_RESULT.copy()
        st.session_state.output_filter_state = "done"
        notices.append("데모 스크리닝 결과를 채웠습니다.")

    return notices


def ensure_defaults_for_node(target_node, extension_df):
    notices = []
    if NODE_ORDER[target_node] >= NODE_ORDER["filter_letter"] and ensure_default_user(extension_df):
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
    if user_row is None:
        return ""
    return "**[User Letter]**\n" + str(user_row.iloc[146])


def selected_filter_letter(user_letter):
    if st.session_state.filter_input_source == "극단 편지 데모":
        return DEMO_EXTREME_LETTER
    return user_letter


def sync_filter_letter_editor(user_letter):
    base_text = selected_filter_letter(user_letter)
    source_changed = st.session_state.get("_loaded_filter_input_source") != st.session_state.filter_input_source
    base_changed = st.session_state.get("_loaded_filter_base_text") != base_text
    if source_changed or base_changed or not st.session_state.filter_letter_editor:
        st.session_state.filter_letter_editor = base_text
        st.session_state["_loaded_filter_input_source"] = st.session_state.filter_input_source
        st.session_state["_loaded_filter_base_text"] = base_text


def sync_generation_letter_editor(user_letter):
    base_changed = st.session_state.get("_loaded_generation_letter_base_text") != user_letter
    if base_changed or not st.session_state.generation_letter_editor:
        st.session_state.generation_letter_editor = user_letter
        st.session_state["_loaded_generation_letter_base_text"] = user_letter


def reset_user_outputs():
    st.session_state.knowledge = ""
    st.session_state.filter_result = None
    st.session_state.input_filter_state = None
    st.session_state.filter_letter_editor = ""
    st.session_state["_loaded_filter_input_source"] = None
    st.session_state["_loaded_filter_base_text"] = ""
    st.session_state.generation_letter_editor = ""
    st.session_state["_loaded_generation_letter_base_text"] = ""
    st.session_state.generated_reply = ""
    st.session_state.screening_result = None
    st.session_state.output_filter_state = None
    st.session_state.improvement_prompt = ""


def render_status_pill(label, ready):
    css_class = "ready" if ready else "empty"
    st.markdown(f'<span class="status-pill {css_class}">{label}</span>', unsafe_allow_html=True)


def graph_node_state(node_id):
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
    if node_id == "generate_reply" and st.session_state.generated_reply:
        return "ready"
    if node_id == "screen_reply" and st.session_state.screening_result:
        return "ready"
    if node_id == "improve_prompt" and st.session_state.improvement_prompt:
        return "loop"
    return "empty"


def graph_node(node_id, title, subtitle, x, y, state, width=160):
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
    state = graph_node_state
    block_state = "blocked" if st.session_state.input_filter_state == "blocked" else "empty"
    pass_state = "ready" if st.session_state.input_filter_state == "passed" else "empty"
    final_state = "ready" if st.session_state.screening_result else "empty"

    graph_html = f"""
<div class="resolve-graph-wrap">
  <div class="resolve-toolbar">
    <div>
      <div class="resolve-title">Node Graph</div>
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
      <path class="wire danger" d="M430 105 C485 105 485 56 540 56" />
      <path class="wire main" d="M430 105 C485 105 485 164 540 164" />
      <path class="wire main" d="M700 164 C740 164 740 164 780 164" />
      <path class="wire main" d="M940 164 C980 164 980 164 1020 164" />
      <path class="wire main" d="M1175 164 C1215 164 1215 164 1255 164" />
      <path class="wire main" d="M1415 164 C1455 164 1455 164 1495 164" />
      <path class="wire success" d="M1655 164 C1698 164 1698 92 1740 92" />
      <path class="wire loop" d="M1655 164 C1698 164 1698 238 1740 238" />
      <path class="wire loop" d="M1900 238 C1960 238 1960 342 1255 342 C1195 342 1195 268 1255 164" />
    </svg>
    <div class="canvas-label" style="left:22px; top:26px;">INPUT</div>
    <div class="canvas-label" style="left:528px; top:26px;">FILTER BRANCH</div>
    <div class="canvas-label" style="left:790px; top:26px;">KNOWLEDGE</div>
    <div class="canvas-label" style="left:1016px; top:26px;">PROMPT</div>
    <div class="canvas-label" style="left:1250px; top:26px;">QA</div>
    <div class="canvas-label" style="left:1736px; top:26px;">OUTCOME</div>
    {graph_node("select_user", "User", "사용자 선택", 20, 72, state("select_user"))}
    {graph_node("filter_letter", "Input Filter", "극단 편지 게이트", 270, 72, state("filter_letter"))}
    {graph_note("filter_letter", "Blocked", "차단 결과 표시", 540, 24, block_state, clickable=False)}
    {graph_note("structure_knowledge", "Passed", "통과 결과 표시", 540, 132, pass_state, clickable=False)}
    {graph_node("structure_knowledge", "Knowledge", "BFI/PVQ 포함", 780, 132, state("structure_knowledge"))}
    {graph_node("edit_prompt", "System Prompt", "생성 지시문", 1020, 132, state("edit_prompt"))}
    {graph_node("generate_reply", "Generate", "답장 1개", 1255, 132, state("generate_reply"))}
    {graph_node("screen_reply", "Output Filter", "답장 품질 검수", 1495, 132, state("screen_reply"))}
    {graph_note("screen_reply", "Final", "통과 후보", 1740, 60, final_state)}
    {graph_node("improve_prompt", "Improve", "개선 지시문", 1740, 206, state("improve_prompt"))}
  </div>
</div>
"""
    st.markdown(graph_html, unsafe_allow_html=True)

    status_cols = st.columns(5)
    with status_cols[0]:
        render_status_pill("사용자 선택", bool(st.session_state.user_name))
    with status_cols[1]:
        filter_ok = bool(st.session_state.filter_result)
        render_status_pill("필터 완료", filter_ok)
    with status_cols[2]:
        render_status_pill("지식 생성", bool(st.session_state.knowledge))
    with status_cols[3]:
        render_status_pill("답장 생성", bool(st.session_state.generated_reply))
    with status_cols[4]:
        render_status_pill("스크리닝", bool(st.session_state.screening_result))
    if st.session_state.default_notice:
        st.caption(st.session_state.default_notice)
        st.session_state.default_notice = ""


def sync_node_from_query_params(extension_df):
    node_from_url = st.query_params.get("node")
    if isinstance(node_from_url, list):
        node_from_url = node_from_url[0] if node_from_url else None
    if node_from_url in NODE_ORDER and node_from_url != st.session_state.get("_synced_query_node"):
        ensure_defaults_for_node(node_from_url, extension_df)
        st.session_state.node = node_from_url
        st.session_state["_synced_query_node"] = node_from_url


def render_filter_prompt_selector():
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
    generation_options = prompt_options("reply_generation")
    current_selection = st.session_state.get("selected_generation_prompt_path")
    selection_index = generation_options.index(current_selection) if current_selection in generation_options else None
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
        render_prompt_editor(
            st.session_state.selected_generation_prompt_path,
            "선택한 답장 생성 프롬프트 파일 내용",
            "generation_prompt",
            height=360,
            sync_system_prompt=True,
        )
    else:
        st.info("답장 생성 프롬프트 파일을 선택하면 내용을 확인하고 수정할 수 있습니다.")


def render_screening_prompt_selector():
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


def run_filter(user_letter):
    filter_prompt = read_prompt(st.session_state.selected_filter_prompt_path)
    with st.spinner("사용자 편지의 고위험 내용을 필터링 중..."):
        try:
            result = dd_filter_user_letter_gpt4(filter_prompt, user_letter)
        except openai.AuthenticationError:
            show_openai_auth_error()
        st.session_state.filter_result = result
        st.session_state.input_filter_state = "blocked" if result.get("status") == "차단" else "passed"


def run_knowledge(user_row):
    with st.spinner("지식을 구조화하는 중..."):
        try:
            st.session_state.knowledge = ext_knowledge_generate(user_row)
        except openai.AuthenticationError:
            show_openai_auth_error()


def generation_prompt_with_improvement():
    system_prompt = st.session_state.system_prompt
    if st.session_state.improvement_prompt:
        return f"{system_prompt}\n\n[Additional revision guidance]\n{st.session_state.improvement_prompt}"
    return system_prompt


def run_generation(user_letter):
    st.session_state.screening_result = None
    st.session_state.output_filter_state = None
    with st.spinner("답장 1개를 생성하는 중..."):
        try:
            st.session_state.generated_reply = dd_generate_gpt4_basic(
                generation_prompt_with_improvement(),
                st.session_state.knowledge,
                user_letter,
            )
        except openai.AuthenticationError:
            show_openai_auth_error()


def run_screening():
    screening_prompt = read_prompt(st.session_state.selected_screening_prompt_path)
    with st.spinner("생성된 답장을 스크리닝 중..."):
        try:
            result = dd_evaluate_letter_with_prompt_gpt4(
                st.session_state.generated_reply,
                screening_prompt,
            )
        except openai.AuthenticationError:
            show_openai_auth_error()
        result["char_count"] = len(st.session_state.generated_reply)
        st.session_state.screening_result = result
        st.session_state.output_filter_state = "done"


def run_improvement_prompt():
    improvement_system_prompt = read_prompt(st.session_state.selected_improvement_prompt_path)
    with st.spinner("다음 생성을 위한 개선 지시문을 만드는 중..."):
        try:
            st.session_state.improvement_prompt = dd_generate_improvement_prompt_gpt4(
                improvement_system_prompt,
                st.session_state.generated_reply,
            )
        except openai.AuthenticationError:
            show_openai_auth_error()


def render_filter_result():
    result = st.session_state.filter_result
    if not result:
        return
    status = result.get("status", "")
    if status == "차단":
        st.error(f"필터 결과: {status} / 위험도: {result.get('risk_level', '-')}")
    else:
        st.success(f"필터 결과: {status} / 위험도: {result.get('risk_level', '-')}")
    st.json(result)


def render_screening_result():
    result = st.session_state.screening_result
    if not result:
        return
    if result.get("status"):
        st.info(f"판정: {result['status']}")
    if result.get("summary"):
        st.write(result["summary"])
    if result.get("quality_notes"):
        st.write(result["quality_notes"])
    if result.get("suggested_revision"):
        st.write(result["suggested_revision"])
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
extension_df = load_data()
ensure_default_prompts()
sync_node_from_query_params(extension_df)
if st.session_state.node != "select_user":
    ensure_defaults_for_node(st.session_state.node, extension_df)
user_row = get_user_row(extension_df)
user_letter_to_agent = get_user_letter(user_row)

st.title("[FutureSelf Extension] Node QA")
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
        submit = st.form_submit_button("선택하고 편지 필터링으로 이동")
    if submit:
        if st.session_state.user_name != user_name:
            reset_user_outputs()
        st.session_state.user_name = user_name
        st.session_state.node = "filter_letter"
        st.rerun()

elif st.session_state.node == "filter_letter":
    st.subheader("2. 사용자가 작성한 편지 필터링")
    render_filter_prompt_selector()
    st.radio(
        "필터 입력",
        options=["사용자 편지", "극단 편지 데모"],
        key="filter_input_source",
        horizontal=True,
    )
    sync_filter_letter_editor(user_letter_to_agent)
    filter_letter = st.text_area(
        "필터 테스트 편지",
        value=st.session_state.filter_letter_editor,
        height=260,
    )
    st.session_state.filter_letter_editor = filter_letter
    if st.button("필터링 실행", type="primary"):
        run_filter(filter_letter)
        st.rerun()
    render_filter_result()
    if st.button("지식 구조화로 이동", type="primary"):
        st.session_state.node = "structure_knowledge"
        st.rerun()

elif st.session_state.node == "structure_knowledge":
    st.subheader("3. 지식 구조화")
    if st.button("지식 구조화 실행", type="primary"):
        run_knowledge(user_row)
        st.rerun()
    if st.session_state.knowledge:
        st.write(st.session_state.knowledge)
        if st.button("시스템 프롬프트로 이동"):
            st.session_state.node = "edit_prompt"
            st.rerun()

elif st.session_state.node == "edit_prompt":
    st.subheader("4. 시스템 프롬프트 조정")
    render_generation_prompt_selector()
    if st.session_state.improvement_prompt:
        with st.expander("현재 적용 중인 개선 지시문", expanded=True):
            st.write(st.session_state.improvement_prompt)
            if st.button("개선 지시문 제거"):
                st.session_state.improvement_prompt = ""
                st.rerun()
    if st.button("답장 생성으로 이동", type="primary"):
        st.session_state.node = "generate_reply"
        st.rerun()

elif st.session_state.node == "generate_reply":
    st.subheader("5. 답장 생성")
    sync_generation_letter_editor(user_letter_to_agent)
    with st.expander("사용자가 작성한 편지", expanded=True):
        user_letter_for_generation = st.text_area(
            "답장 생성에 사용할 사용자 편지",
            value=st.session_state.generation_letter_editor,
            height=260,
        )
        st.session_state.generation_letter_editor = user_letter_for_generation
    if st.session_state.improvement_prompt:
        with st.expander("이번 생성에 추가되는 개선 지시문", expanded=True):
            st.write(st.session_state.improvement_prompt)
    if st.button("답장 1개 생성", type="primary"):
        run_generation(user_letter_for_generation)
        st.rerun()
    if st.session_state.generated_reply:
        st.markdown("### 생성된 답장")
        st.write(st.session_state.generated_reply)
        if st.button("답장 스크리닝으로 이동"):
            st.session_state.node = "screen_reply"
            st.rerun()

elif st.session_state.node == "screen_reply":
    st.subheader("6. 답장 스크리닝")
    render_screening_prompt_selector()
    with st.expander("생성된 답장", expanded=True):
        st.write(st.session_state.generated_reply)
    if st.button("스크리닝 실행", type="primary"):
        run_screening()
        st.rerun()
    render_screening_result()
    if st.session_state.screening_result:
        if st.button("개선 프롬프트로 이동"):
            st.session_state.node = "improve_prompt"
            st.rerun()

elif st.session_state.node == "improve_prompt":
    st.subheader("7. 개선 프롬프트")
    render_improvement_prompt_selector()
    render_screening_result()
    if st.button("개선 지시문 생성", type="primary"):
        run_improvement_prompt()
        st.rerun()
    if st.session_state.improvement_prompt:
        edited_improvement_prompt = st.text_area(
            "다음 답장 생성에 적용할 개선 지시문",
            value=st.session_state.improvement_prompt,
            height=220,
        )
        st.session_state.improvement_prompt = edited_improvement_prompt
        if st.button("적용하고 답장 생성으로 이동", type="primary"):
            st.session_state.node = "generate_reply"
            st.rerun()
