# 2회기

import streamlit as st
import pandas as pd
import openai
from gpt_structure import dd_generate_gpt4_basic, dd_generate_with_history, update_knowledge
from knowledge_structure import *

openai.api_key = st.secrets["OPENAI_API_KEY"]

st.set_page_config(
    page_title="[SNU 스무살의 나] Knowledge & Second letter",
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

# 데이터 로드
# db_df = pd.read_csv("https://docs.google.com/spreadsheets/d/16BZEnFcJqxwQb2TPsIdQrumRWHlIgK6xJ7fCUZ5ZXt0/export?format=csv&gid=0")
# second_df = pd.read_csv("https://docs.google.com/spreadsheets/d/1pbxxv7o-B2HvCJ1gER4tk1jrdv6FmykOBbggh3EjrMM/export?format=csv&gid=1489981443")
db_df = pd.read_csv("https://docs.google.com/spreadsheets/d/16BZEnFcJqxwQb2TPsIdQrumRWHlIgK6xJ7fCUZ5ZXt0/export?format=csv&gid=0")
second_df = pd.read_csv("https://docs.google.com/spreadsheets/d/1qt4XVgtXtIlRTOiVMt_Bt-eququoRCFaAFX4SlEsR60/export?format=csv&gid=1549047630")

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

st.title('[SNU 스무살의 나] Knowledge Update & Second letter')
st.markdown('---')

# -------------------
# STEP 1: 사용자 선택
# -------------------
if st.session_state.step == 1:
    with st.form("user_select"):
        user_name = st.radio(
            "Select User Name 👉",
            options=db_df.iloc[:, 0].unique(),
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
# STEP 2: Updating Knowledge
# -------------------
elif st.session_state.step == 2:
    st.subheader("Step 2. Updating Knowledge")

    if not st.session_state.knowledge:
        db = db_df[db_df.iloc[:,0] == st.session_state.user_name]
        second_test = second_df[second_df.iloc[:, 3] == st.session_state.user_name]

        with st.spinner("Wait for updating knowledge..."):
            initial_knowledge = db.iloc[0,1]

            first_letter_user = db.iloc[0,2]
            second_letter_user = second_test.iloc[0, 4]
            letters = f"[First Letter]\n{first_letter_user}\n\n[Second Letter]\n{second_letter_user}"

            update = update_knowledge(initial_knowledge, letters)
            update = "**[Update]** " + update

            knowledge = "\n\n".join([
                initial_knowledge, update
            ])

            st.session_state.knowledge = knowledge

            # st.write(st.session_state.knowledge)
            st.write(update)

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
    st.subheader("Step 3. Second Letter System Prompt 입력")

    system_lib_file = 'data/prompt_template/second_letter_sys_prompt.txt'
    with open(system_lib_file, "r") as f:
        default_prompt = f.read()

    st.session_state.system_prompt = st.text_area(
        "Second Letter System Prompt 수정",
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
    st.subheader("Step 4. [2회기] 편지 생성")
    second_test = second_df[second_df.iloc[:,3] == st.session_state.user_name]
    second_letter_to_agent = "**[Second Letter to Twenty-Year-Old Self]**\n" + second_test.iloc[0, 4]
    st.write(second_letter_to_agent)

    # ✅ GPT 호출은 여기 버튼 안쪽에서만 실행됨
    if st.button("✉️ 편지 생성하기"):
        db = db_df[db_df.iloc[:, 0] == st.session_state.user_name]

        with st.spinner("Wait for generating second letter..."):
            first_letter_user = db.iloc[0, 2]
            first_letter_agent = db.iloc[0, 3]

            history = [
                {'role': "user", 'content': "**[First Letter to Twenty-Year-Old Self]**\n" + first_letter_user},
                {'role': "assistant", 'content': first_letter_agent},
            ]

            for i in range(1, 4):
                reply = dd_generate_with_history(
                    st.session_state.system_prompt,
                    st.session_state.knowledge,
                    history,
                    second_letter_to_agent
                )
                st.subheader(f"[2회기] 스무살 나의 답장 {i}")
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