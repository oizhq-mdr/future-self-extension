# SNU 스무살의 나 (SNU My Twenty-Year-Old Self) 📩

이 프로젝트는 서울대학교(SNU) 학생들을 대상으로 한 다회기 워크숍용 AI 어플리케이션입니다. 학생들이 심리 검사 결과와 자기 탐색 데이터를 바탕으로 자신의 '미래 자아(Future Self)'와 상호작용하며 자아 정체성을 탐구할 수 있도록 돕습니다.

## 🌟 주요 기능

### 1. 다회기 워크숍 지원 (Multi-session Workflow)
- **1회기 (Session 1):** 초기 지식 구조화 및 '스무살의 나'에게 보내는 첫 번째 편지에 대한 답장 생성.
- **2회기 (Session 2):** 추가 활동 및 대화 내용을 바탕으로 지식 업데이트 및 두 번째 답장 생성.
- **3회기 (Session 3):** 최종 지식 업데이트 및 대화 기록(History)을 유지한 상태에서의 세 번째 답장 생성.

### 2. 심리 검사 및 데이터 분석
- **Big Five Personality (BFI):** 5대 성격 특성 분석 및 요약.
- **Portrait Values Questionnaire (PVQ):** 삶의 가치관 및 가이드 원칙 분석.
- **진정성 검사 (Authenticity):** 자기 이해 및 진정성 지표 산출.
- **사전 검사 (Pre-test):** 자아존중감(Self-esteem), 회복탄력성(Resilience), 미래 시간 관점(Future Time Perspective) 등 다각도 분석.

### 3. AI 기반 자아 대화 (Future Self Interaction)
- **지식 구조화 (Knowledge Structuring):** 인구통계학적 정보, 심리 검사 결과, 좋아하고 싫어하는 것, 20세의 미래 프로필 등을 통합하여 AI를 위한 체계적인 지식 베이스 구축.
- **개인화된 답장 생성:** OpenAI GPT-4를 활용하여 사용자의 특징이 반영된 공감적이고 개인화된 미래 자아의 답장 생성.
- **대화 맥락 유지:** 이전 회기의 대화 내용을 기억하여 연속성 있는 대화 경험 제공.

## 🛠 기술 스택

- **Frontend:** [Streamlit](https://streamlit.io/)
- **Data Analysis:** [Pandas](https://pandas.pydata.org/)
- **AI/LLM:** [OpenAI API](https://openai.com/api/) (GPT-4o)
- **Language:** Python 3.x

## 📁 프로젝트 구조

```text
/Users/jaewoolee/Dev/future-self-main/
├── streamlit_app_first.py     # 1회기 메인 애플리케이션
├── streamlit_app_second.py    # 2회기 메인 애플리케이션
├── streamlit_app_third.py     # 3회기 메인 애플리케이션
├── knowledge_structure.py     # 사용자 데이터를 LLM 지식으로 변환하는 로직
├── gpt_structure.py          # OpenAI API 연동 및 프롬프트 실행 모듈
├── bfi_scoring.py            # BFI(Big 5) 성격 검사 채점 로직
├── pvq_scoring.py            # PVQ(가치관) 검사 채점 로직
├── requirements.txt           # 프로젝트 의존성 라이브러리 목록
└── data/
    └── prompt_template/       # LLM 시스템 프롬프트 및 텍스트 템플릿
        ├── first_letter_sys_prompt.txt
        ├── second_letter_sys_prompt.txt
        ├── third_letter_sys_prompt.txt
        ├── BFI_summary_sys.txt
        ├── PVQ_summary_sys.txt
        └── ...
```

## 🚀 시작하기

### 1. 환경 설정
Python 3.x 환경에서 필요한 라이브러리를 설치합니다.
```bash
pip install -r requirements.txt
```

### 2. API 키 설정
Streamlit의 시크릿 관리 기능을 사용하거나 `.streamlit/secrets.toml` 파일을 생성하여 OpenAI API 키를 설정해야 합니다.
```toml
# .streamlit/secrets.toml
OPENAI_API_KEY = "your-api-key-here"
```

### 3. 애플리케이션 실행
진행하고자 하는 회기에 맞춰 명령어를 실행합니다.
```bash
# 1회기 실행
streamlit run streamlit_app_first.py

# 2회기 실행
streamlit run streamlit_app_second.py

# 3회기 실행
streamlit run streamlit_app_third.py
```

## 📝 데이터 처리 및 프롬프트
이 시스템은 구글 스프레드시트에서 데이터를 실시간으로 가져와 분석합니다. 각 회기마다 사용자가 입력한 데이터와 심리 검사 결과가 `knowledge_structure.py`를 통해 통합되며, `data/prompt_template/`에 정의된 페르소나와 지침에 따라 AI가 답변을 구성합니다.

## ⚖️ 라이선스
본 프로젝트는 교육 및 연구 목적으로 제작되었습니다.
