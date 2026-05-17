# 1회기

import streamlit as st
import pandas as pd
import openai
from gpt_structure import dd_generate_gpt4_basic
from knowledge_structure import *

openai.api_key = st.secrets["OPENAI_API_KEY"]

st.set_page_config(
    page_title="[SNU 스무살의 나] Knowledge & First letter",
    page_icon="📩",
    layout="wide",
    initial_sidebar_state="expanded",
)

# 단계 초기화
if "step" not in st.session_state:
    st.session_state.step = 1
if "user_name" not in st.session_state:
    st.session_state.user_name = None
if "knowledge" not in st.session_state:
    st.session_state.knowledge = ""
if "system_prompt" not in st.session_state:
    st.session_state.system_prompt = ""


# 워크숍 마무리팀
# spc_df = pd.read_csv("https://docs.google.com/spreadsheets/d/1DI8Nc1v9qIhFcg2SloNsVj-33nTF8NeAiatnf_7TKwA/export?format=csv&gid=117892638")
# authentic_df = pd.read_csv("https://docs.google.com/spreadsheets/d/1h84YK25uLQUQyD4u_TGQOeQEQgDvvQeto8ynkmowK6I/export?format=csv&gid=902877586")
# future_df = pd.read_csv("https://docs.google.com/spreadsheets/d/1o7bkh7SZ7vD-XLDgdoV-DOouDIl64PVx3K13iWLeSCk/export?format=csv&gid=397229261")
# pre_df = pd.read_csv("https://docs.google.com/spreadsheets/d/12jnbvjOgdLy96UCeXgc5p2A3-0BWH1RLKD3gF5sqdRU/export?format=csv&gid=1266426431")

# 워크숍 병행팀
spc_df = pd.read_csv("https://docs.google.com/spreadsheets/d/1DI8Nc1v9qIhFcg2SloNsVj-33nTF8NeAiatnf_7TKwA/export?format=csv&gid=117892638")
authentic_df = pd.read_csv("https://docs.google.com/spreadsheets/d/1QWP_fLAeFfeqDFW__8fJAsPCHzNPNN9WTM-SL4He7cU/export?format=csv&gid=387718419")
future_df = pd.read_csv("https://docs.google.com/spreadsheets/d/1o7bkh7SZ7vD-XLDgdoV-DOouDIl64PVx3K13iWLeSCk/export?format=csv&gid=397229261")
pre_df = pd.read_csv("https://docs.google.com/spreadsheets/d/12jnbvjOgdLy96UCeXgc5p2A3-0BWH1RLKD3gF5sqdRU/export?format=csv&gid=1266426431")

# 스타일 적용
st.markdown("""
<style>
@import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard/dist/web/static/pretendard.css');
html, body, [class*="css"], g {
  font-family: Pretendard, -apple-system, BlinkMacSystemFont, system-ui, Roboto, 'Helvetica Neue',
               'Segoe UI', 'Apple SD Gothic Neo', 'Noto Sans KR', 'Malgun Gothic', sans-serif;
}
</style>
""", unsafe_allow_html=True)

st.title('[SNU 스무살의 나] Knowledge & First letter')
st.markdown('---')

# -------------------
# STEP 1: 사용자 선택
# -------------------
if st.session_state.step == 1:
    with st.form("user_select"):
        user_name = st.radio(
            "Select User Name 👉",
            options=spc_df.iloc[:, 1].unique(),
            key="user_radio"
        )
        submit = st.form_submit_button("다음 단계")
    if submit:
        # 사용자 바뀔 때 knowledge 초기화
        if st.session_state.user_name != user_name:
            st.session_state.knowledge = ""
        st.session_state.user_name = user_name
        st.session_state.step = 2
        st.rerun()

# -------------------
# STEP 2: Structuring Knowledge
# -------------------
elif st.session_state.step == 2:
    st.subheader("Step 2. Structuring Knowledge")

    if not st.session_state.knowledge:
        main_test = spc_df[spc_df.iloc[:,1] == st.session_state.user_name]
        authentic_test = authentic_df[authentic_df.iloc[:,1] == st.session_state.user_name]
        future_test = future_df[future_df.iloc[:,3] == st.session_state.user_name]
        pre_test_data = pre_df[pre_df.iloc[:,2] == st.session_state.user_name]

        with st.spinner("Wait for structuring knowledge..."):
            demo = demo_generate(main_test)
            love_hate = love_hate_generate(main_test)
            bfi = bfi_generate(main_test)
            pvq = pvq_generate(main_test)
            authenticity = authenticity_generate(authentic_test)
            pre_test_text = pre_test_generate(pre_test_data)
            future_profile = future_profile_generate(future_test)

            knowledge = "\n\n".join([
                demo, love_hate, bfi, pvq, authenticity, pre_test_text, future_profile
            ])
            st.session_state.knowledge = knowledge

    st.write(st.session_state.knowledge)

    col1, col2 = st.columns(2)
    with col1:
        if st.button("이전 단계"):
            st.session_state.step = 1
            st.rerun()
    with col2:
        if st.button("다음 단계"):
            st.session_state.step = 3
            st.rerun()

# -------------------
# STEP 3: System Prompt 입력
# -------------------
elif st.session_state.step == 3:
    st.subheader("Step 3. First Letter System Prompt 입력")

    system_lib_file = 'data/prompt_template/first_letter_sys_prompt.txt'
    with open(system_lib_file, "r") as f:
        default_prompt = f.read()

    st.session_state.system_prompt = st.text_area(
        "First Letter System Prompt 수정",
        value=default_prompt,
        height=600
    )

    col1, col2 = st.columns(2)
    with col1:
        if st.button("이전 단계"):
            st.session_state.step = 2
            st.rerun()
    with col2:
        if st.button("다음 단계"):
            st.session_state.step = 4
            st.rerun()

# -------------------
# STEP 4: 편지 생성
# -------------------
elif st.session_state.step == 4:
    st.subheader("Step 4. 편지 생성")

    future_test = future_df[future_df.iloc[:,3] == st.session_state.user_name]
    first_letter_to_agent = "**[First Letter to Twenty-Year-Old Self]**\n" + future_test.iloc[0, 13]
    st.write(first_letter_to_agent)

    # ✅ GPT 호출은 여기 버튼 안쪽에서만 실행됨
    if st.button("✉️ 편지 생성하기"):
        with st.spinner("Wait for generating first letter..."):
            for i in range(1, 4):
                reply = dd_generate_gpt4_basic(
                    st.session_state.system_prompt,
                    st.session_state.knowledge,
                    first_letter_to_agent
                )
                st.subheader(f"3년 후 나의 답장 {i}")
                st.write(reply)

    # 네비게이션 버튼
    col1, col2 = st.columns(2)
    with col1:
        if st.button("이전 단계"):
            st.session_state.step = 3
            st.rerun()
    with col2:
        if st.button("처음으로 돌아가기"):
            st.session_state.step = 1
            st.session_state.user_name = None
            st.session_state.knowledge = ""
            st.rerun()