import pandas as pd
from pathlib import Path
from pvq_scoring import *
from bfi_scoring import *
from gpt_structure import pvq_summary_gpt4, bfi_summary_gpt4

PROMPT_ROOT = Path(__file__).resolve().parent / "data" / "prompt_template"


def read_template(filename):
    return (PROMPT_ROOT / filename).read_text(encoding="utf-8")


def ext_future_profile_generate(row):
    """사용자의 3년 후 미래 프로필 섹션을 생성한다.

    Google Sheets에서 읽은 한 사용자 row의 미래 자아 관련 응답
    `row.iloc[137:146]`을 `profile_in_three_years.txt` 템플릿에 채워 넣는다.
    결과 문자열은 extension 앱의 knowledge 중 `[Profile in Three Years]`
    계열 정보를 구성하는 데 사용된다.
    """
    future_profile_template = read_template("profile_in_three_years.txt")
    
    future_profile = future_profile_template.format(
        AGE = row.iloc[137],
        JOB = row.iloc[138],
        LIV = row.iloc[139],
        APPEAR = row.iloc[140],
        PERSONALITY = row.iloc[141],
        BEHAVIOR = row.iloc[142],
        FAM = row.iloc[143],
        FRIEND = row.iloc[144],
        WORK = row.iloc[145],
    )
    return future_profile

def ext_demo_generate(row):
    """사용자의 인구통계학 정보 섹션을 생성한다.

    row의 나이, 성별, 건강/장애 여부, 국적, 거주지, 교육 수준, 소득,
    생활 형태, 형제자매 수 응답을 `demo.txt` 템플릿에 넣는다. 이름은
    개인정보 노출을 피하기 위해 Participant로 고정하며, 건강상 어려움이
    있는 경우 영향 설명을 추가한다.
    """
    demo_template = read_template("demo.txt")
        
    hea_dis_val = str(row.iloc[80])
    has_disability = '있' in hea_dis_val
    
    demo = demo_template.format(
        NAME = "Participant",
        AGE=row.iloc[78],
        SEX=row.iloc[79],
        HEA_DIS=hea_dis_val if has_disability else '장애나 건강상의 어려움이 없음',
        IMPACT=" → Impact on life: " + str(row.iloc[82]) if has_disability else '',
        NATIONALITY=row.iloc[83],
        RESIDENCE=row.iloc[84],
        EDU=row.iloc[85],
        INC=row.iloc[88],
        LIV=row.iloc[89],
        SIB=row.iloc[90],
    )
    return demo

def ext_bfi_generate(row, system_prompt=None):
    """BFI 응답을 채점하고 성격 특성 요약 섹션을 생성한다.

    row의 BFI 30문항(`row.iloc[91:121]`)을 `D1PB-*` 키로 재구성한 뒤
    `bfi_calculate_scores()`로 점수 문장을 만들고 `bfi_summary_gpt4()`로
    자연어 요약을 생성한다. `system_prompt`가 주어지면 기본 BFI 요약
    프롬프트 대신 해당 프롬프트를 사용한다.
    """
    bfi_intro = '''

**[Big 5 Personality Traits in 2026]**
The following section presents an overview of the person's personality within five key domains, showcasing their traits spectrum and the extent of their qualities in each area. Each domain comprises several facets that provide deeper insights into their unique personality traits.

'''
    new_column_names = [f'D1PB-{i}' for i in range(1, 31)]
    bfi_series = row.iloc[91:121].copy()
    bfi_series.index = new_column_names
    
    bfi_1st = bfi_calculate_scores(bfi_series)
    bfi_summary = bfi_summary_gpt4(bfi_1st, system_prompt=system_prompt)
    return bfi_intro + bfi_summary

def ext_pvq_generate(row, system_prompt=None):
    """PVQ 응답을 채점하고 삶의 가치 요약 섹션을 생성한다.

    row의 PVQ 10문항(`row.iloc[121:131]`)을 DataFrame으로 재구성해
    가치별 설명 문장을 만든 뒤 `pvq_summary_gpt4()`로 요약한다.
    `system_prompt`가 주어지면 기본 PVQ 요약 프롬프트 대신 사용한다.
    """
    pvq_intro = '''

**[Life-guiding Principles in 2026]**
The information provided below is the values that reflect the relative importance this person places on different aspects of life, guiding their decisions, actions, and perspectives. These values are fundamental components of their personality and play a crucial role in shaping who this person is.

'''
    new_column_names = [f'D2LP-{i}' for i in range(1, 11)]
    pvq_raw = pd.DataFrame([row.iloc[121:131].values], columns=new_column_names)
    pvq_1st = generate_pvq_prompt(pvq_raw)
    pvq_summary = pvq_summary_gpt4(pvq_1st, system_prompt=system_prompt)
    return pvq_intro + pvq_summary

def ext_love_hate_generate(row):
    """사용자가 좋아하는 것과 싫어하는 것 섹션을 생성한다.

    row의 선호 항목 3개와 비선호 항목 3개(`row.iloc[131:137]`)를
    `love_hate.txt` 템플릿에 넣어 knowledge에 포함할 문자열을 만든다.
    """
    love_hate_template = read_template("love_hate.txt")
        
    love_hate = love_hate_template.format(
        LOVE1 = row.iloc[131],
        LOVE2 = row.iloc[132],
        LOVE3 = row.iloc[133],
        HATE1 = row.iloc[134],
        HATE2 = row.iloc[135],
        HATE3 = row.iloc[136],
    )
    return love_hate

def ext_knowledge_generate(row, bfi_system_prompt=None, pvq_system_prompt=None):
    """extension 앱에서 답장 생성에 사용할 통합 knowledge를 만든다.

    인구통계, 선호/비선호, BFI 요약, PVQ 요약, 3년 후 미래 프로필을
    순서대로 생성해 빈 줄로 이어 붙인다. 반환된 문자열은 OpenAI 요청에서
    assistant role 메시지로 전달되어 답장 생성의 배경 정보가 된다.
    """
    demo = ext_demo_generate(row)
    love_hate = ext_love_hate_generate(row)
    bfi = ext_bfi_generate(row, system_prompt=bfi_system_prompt)
    pvq = ext_pvq_generate(row, system_prompt=pvq_system_prompt)
    future_profile = ext_future_profile_generate(row)
    
    knowledge = "\n\n".join([
        demo, love_hate, bfi, pvq, future_profile
    ])
    return knowledge
