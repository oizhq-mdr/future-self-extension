# FutureSelf Extension QA

FutureSelf Extension은 사용자의 편지와 설문 데이터를 바탕으로 미래 자아 답장을 생성하고, 그 과정을 노드 단위로 점검하기 위한 Streamlit 앱입니다.

이 앱은 하나의 end-to-end 파이프라인을 여러 단계로 나누어 확인합니다. 지식 구조화, 입력 편지와 knowledge 기반 필터링, 답장 생성 프롬프트 편집, 답장 생성, 출력 스크리닝, 개선 프롬프트 생성까지 한 화면에서 순서대로 테스트할 수 있습니다.

## 주요 기능

- 사용자 선택: Google Sheets CSV에서 사용자를 불러옵니다.
- 지식 구조화: 인구통계, BFI, PVQ, 선호/비선호, 미래 프로필을 하나의 knowledge로 구성합니다.
- 입력 필터링: 사용자가 작성한 편지와 구조화된 knowledge를 함께 보고 안전성/위험도 기준으로 JSON 평가합니다.
- 프롬프트 편집: `data/prompt_template/extension_prompts/` 아래의 Markdown 프롬프트를 앱에서 직접 확인하고 저장할 수 있습니다.
- 답장 생성: 선택한 생성 프롬프트와 구조화된 knowledge를 사용해 미래 자아 답장을 생성합니다.
- 출력 스크리닝: 생성된 답장을 품질/안전성 기준으로 JSON 평가합니다.
- 개선 루프: 스크리닝 결과를 바탕으로 다음 생성을 위한 개선 지시문을 만듭니다.

## 프로젝트 구조

```text
.
├── streamlit_app_extension.py
├── ext_knowledge_structure.py
├── gpt_structure.py
├── bfi_scoring.py
├── pvq_scoring.py
├── requirements.txt
└── data/
    └── prompt_template/
        ├── BFI_summary_sys.txt
        ├── PVQ_summary_sys.txt
        ├── demo.txt
        ├── love_hate.txt
        ├── profile_in_three_years.txt
        └── extension_prompts/
            ├── input_filter/
            ├── output_filter/
            ├── improvement/
            └── reply_generation/
```

## 설치

Python 3.12 기준으로 확인했습니다.

```bash
python -m pip install -r requirements.txt
```

## OpenAI API 키 설정

Streamlit secrets에 OpenAI API 키가 필요합니다.

```toml
# .streamlit/secrets.toml
OPENAI_API_KEY = "your-api-key"
```

앱에서는 다음 방식으로 키를 읽습니다.

```python
openai.api_key = st.secrets["OPENAI_API_KEY"]
```

## 실행

```bash
streamlit run streamlit_app_extension.py
```

앱이 열리면 상단 QA Graph에서 각 단계를 클릭해 바로 이동할 수 있습니다. 중간 단계로 바로 진입하면 데모 데이터가 필요한 상태값을 임시로 채워 빠르게 단계별 QA를 할 수 있습니다.

## Streamlit Community Cloud 배포

1. 이 프로젝트를 GitHub repository에 push합니다.
2. [Streamlit Community Cloud](https://share.streamlit.io/)에서 `Create app`을 선택합니다.
3. GitHub repository, branch, entrypoint file을 지정합니다.
   - Entrypoint file: `streamlit_app_extension.py`
4. `Advanced settings`에서 Python version을 선택합니다.
   - 로컬 검증 기준: Python 3.12
5. `Secrets` 입력란에 아래 내용을 붙여넣습니다.

```toml
OPENAI_API_KEY = "your-api-key"
```

6. `Deploy`를 누릅니다.

배포 로그에서 dependency 설치 오류가 나면 `requirements.txt`를 먼저 확인합니다. 앱이 실행된 뒤 OpenAI 오류가 나면 Streamlit Cloud secrets에 `OPENAI_API_KEY`가 정확히 저장됐는지 확인합니다.

## 데이터 입력

앱은 `streamlit_app_extension.py`의 `load_data()`에서 Google Sheets CSV를 읽습니다.

```python
pd.read_csv(
    "https://docs.google.com/spreadsheets/d/1MN6NmPU_DjJR2zYZ5Ct_SwiOuuvGXkpXBjT9DJYRYyQ/export?format=csv"
)
```

현재 컬럼 위치 기반으로 데이터를 읽기 때문에 스프레드시트 구조가 바뀌면 `ext_knowledge_structure.py`와 `streamlit_app_extension.py`의 `row.iloc[...]` 인덱스도 함께 확인해야 합니다.

## 프롬프트 파일

노드별 프롬프트는 아래 위치에서 관리합니다.

- 입력 필터: `data/prompt_template/extension_prompts/input_filter/*.md`
- 답장 생성: `data/prompt_template/extension_prompts/reply_generation/*.md`
- 출력 필터: `data/prompt_template/extension_prompts/output_filter/*.md`
- 개선 프롬프트: `data/prompt_template/extension_prompts/improvement/*.md`

BFI/PVQ 요약과 knowledge 템플릿은 아래 파일을 사용합니다.

- `data/prompt_template/BFI_summary_sys.txt`
- `data/prompt_template/PVQ_summary_sys.txt`
- `data/prompt_template/demo.txt`
- `data/prompt_template/love_hate.txt`
- `data/prompt_template/profile_in_three_years.txt`

## 의존성 메모

`streamlit_app_extension.py` 실행에 필요한 Python 패키지는 `requirements.txt`에 정리되어 있습니다.

삭제된 이전 회기 앱 파일(`streamlit_app_first.py`, `streamlit_app_second.py`, `streamlit_app_third.py`)은 현재 extension 앱 실행에는 필요하지 않습니다.

단, `gpt_structure.py`의 `update_knowledge()`는 과거 워크플로우용 함수이며 삭제된 `data/prompt_template/update_knowledge_sys.txt`를 참조합니다. 현재 extension 앱에서는 호출하지 않습니다.
