import pandas as pd
from pvq_scoring import *
from bfi_scoring import *
from gpt_structure import pvq_summary_gpt4, bfi_summary_gpt4

def ext_future_profile_generate(row):
    lib_file = 'data/prompt_template/profile_at_20.txt'
    with open(lib_file, "r") as f:
        future_profile_template = f.read()
    
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
    lib_file = 'data/prompt_template/demo.txt'
    with open(lib_file, "r") as f:
        demo_template = f.read()
        
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
    bfi_intro = '''

**[Big 5 Personality Traits in 2025]**
The following section presents an overview of the person's personality within five key domains, showcasing their traits spectrum and the extent of their qualities in each area. Each domain comprises several facets that provide deeper insights into their unique personality traits.

'''
    new_column_names = [f'D1PB-{i}' for i in range(1, 31)]
    bfi_series = row.iloc[91:121].copy()
    bfi_series.index = new_column_names
    
    bfi_1st = bfi_calculate_scores(bfi_series)
    bfi_summary = bfi_summary_gpt4(bfi_1st, system_prompt=system_prompt)
    return bfi_intro + bfi_summary

def ext_pvq_generate(row, system_prompt=None):
    pvq_intro = '''

**[Life-guiding Principles in 2025]**
The information provided below is the values that reflect the relative importance this person places on different aspects of life, guiding their decisions, actions, and perspectives. These values are fundamental components of their personality and play a crucial role in shaping who this person is.

'''
    new_column_names = [f'D2LP-{i}' for i in range(1, 11)]
    pvq_raw = pd.DataFrame([row.iloc[121:131].values], columns=new_column_names)
    pvq_1st = generate_pvq_prompt(pvq_raw)
    pvq_summary = pvq_summary_gpt4(pvq_1st, system_prompt=system_prompt)
    return pvq_intro + pvq_summary

def ext_love_hate_generate(row):
    lib_file = 'data/prompt_template/love_hate.txt'
    with open(lib_file, "r") as f:
        love_hate_template = f.read()
        
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
    demo = ext_demo_generate(row)
    love_hate = ext_love_hate_generate(row)
    bfi = ext_bfi_generate(row, system_prompt=bfi_system_prompt)
    pvq = ext_pvq_generate(row, system_prompt=pvq_system_prompt)
    future_profile = ext_future_profile_generate(row)
    
    knowledge = "\n\n".join([
        demo, love_hate, bfi, pvq, future_profile
    ])
    return knowledge
