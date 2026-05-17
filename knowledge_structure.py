from pvq_scoring import *
from bfi_scoring import *
from gpt_structure import pvq_summary_gpt4, bfi_summary_gpt4

def future_profile_generate(main_test):
  lib_file = 'data/prompt_template/profile_at_20.txt'
  f = open(lib_file, "r")
  future_profile_template = f.read()
  f.close()
  future_profile = future_profile_template.format(
    AGE = main_test.iloc[0,4],
    JOB = main_test.iloc[0,5],
    LIV = main_test.iloc[0,6],
    APPEAR = main_test.iloc[0,7],
    PERSONALITY = main_test.iloc[0,8],
    BEHAVIOR = main_test.iloc[0,9],
    FAM = main_test.iloc[0,10],
    FRIEND = main_test.iloc[0,11],
    WORK = main_test.iloc[0,12],
  )
  return future_profile

def demo_generate(main_test):
  lib_file = 'data/prompt_template/demo.txt'
  f = open(lib_file, "r")
  demo_template = f.read()
  f.close()
  demo = demo_template.format(
      NAME = main_test.iloc[0,1],
      AGE=main_test.iloc[0, 2],
      SEX=main_test.iloc[0, 3],
      HEA_DIS=str(main_test.iloc[0, 5]) if main_test.iloc[0, 4] == '장애나 건강상의 어려움이 있음' else '장애나 건강상의 어려움이 없음',
      IMPACT=" → Impact on life: " + str(main_test.iloc[0, 6]) if main_test.iloc[0, 4] == '장애나 건강상의 어려움이 있음' else '',
      NATIONALITY=main_test.iloc[0, 7],
      RESIDENCE=main_test.iloc[0, 8],
      EDU=main_test.iloc[0, 9],
      LEAVE_SCHOOL=main_test.iloc[0, 10],
      PER_INC=main_test.iloc[0, 17],
      SAT_INC=main_test.iloc[0, 18],
      LIV=main_test.iloc[0, 19],
      SIB=main_test.iloc[0, 20],
  )
  return demo

def bfi_generate(main_test):
  bfi_intro = '''

**[Big 5 Personality Traits in 2025]**
The following section presents an overview of the person's personality within five key domains, showcasing their traits spectrum and the extent of their qualities in each area. Each domain comprises several facets that provide deeper insights into their unique personality traits.

'''
  new_column_names = [f'D1PB-{i}' for i in range(1, 31)]
  bfi_raw = main_test.iloc[:, 21:51]
  bfi_raw.columns = new_column_names
  bfi_1st = bfi_calculate_scores(bfi_raw)
  bfi_summary = bfi_summary_gpt4(bfi_1st)
  bfi_summary_final = bfi_intro + bfi_summary
  return bfi_summary_final

def pvq_generate(main_test):
  pvq_intro = '''

**[Life-guiding Principles in 2025]**
The information provided below is the values that reflect the relative importance this person places on different aspects of life, guiding their decisions, actions, and perspectives. These values are fundamental components of their personality and play a crucial role in shaping who this person is.

'''
  new_column_names = [f'D2LP-{i}' for i in range(1, 11)]
  pvq_raw = main_test.iloc[:, 51:61]
  pvq_raw.columns = new_column_names
  pvq_1st = generate_pvq_prompt(pvq_raw)
  pvq_summary = pvq_summary_gpt4(pvq_1st)
  pvq_summary_final = pvq_intro + pvq_summary
  return pvq_summary_final

def love_hate_generate(main_test):
  lib_file = 'data/prompt_template/love_hate.txt'
  f = open(lib_file, "r")
  love_hate_template = f.read()
  f.close()
  love_hate = love_hate_template.format(
    LOVE1 = main_test.iloc[0,11],
    LOVE2 = main_test.iloc[0,12],
    LOVE3 = main_test.iloc[0,13],
    HATE1 = main_test.iloc[0,14],
    HATE2 = main_test.iloc[0,15],
    HATE3 = main_test.iloc[0,16],
  )
  return love_hate

def authenticity_generate(authentic_test):
  lib_file = 'data/prompt_template/authenticity.txt'
  f = open(lib_file, "r")
  love_hate_template = f.read()
  f.close()
  authenticity = love_hate_template.format(
    AUTENTIC = authentic_test.iloc[0,7],
    WORDS = authentic_test.iloc[0,8],
    CONCERN = authentic_test.iloc[0,9],
    CONTENTS = authentic_test.iloc[0,10],
  )
  return authenticity

def score_to_level7(score):
    if score <= 1/7:
        return 1
    elif score <= 2/7:
        return 2
    elif score <= 3/7:
        return 3
    elif score <= 4/7:
        return 4
    elif score <= 5/7:
        return 5
    elif score <= 6/7:
        return 6
    else:
        return 7
    
def score_to_level5(score):
    if score <= 1/5:
        return 1
    elif score <= 2/5:
        return 2
    elif score <= 3/5:
        return 3
    elif score <= 4/5:
        return 4
    else:
        return 5


descriptions = {
    # Connectedness with Future Self
    "FS_AVG": [
        "I feel not at all connected to my future self at age 20.",
        "I feel barely connected to my future self at age 20.",
        "I feel slightly connected to my future self at age 20.",
        "I feel neutral about my connection to my future self at age 20.",
        "I feel somewhat connected to my future self at age 20.",
        "I feel mostly connected to my future self at age 20.",
        "I feel strongly connected to my future self at age 20."
    ],
    # Future Envisioning - Self-Directed Future Navigation: Pathways (7-point scale)
    "PATH_AVG": [
        "My ability to think of multiple solutions and pathways is extremely poor.",
        "My ability to think of multiple solutions and pathways is very poor.",
        "My ability to think of multiple solutions and pathways is somewhat poor.",
        "My ability to think of multiple solutions and pathways is moderate.",
        "My ability to think of multiple solutions and pathways is somewhat strong.",
        "My ability to think of multiple solutions and pathways is strong.",
        "My ability to think of multiple solutions and pathways is excellent."
    ],
    # Future Envisioning - Self-Directed Future Navigation: Agency (7-point scale)
    "AGEN_AVG": [
        "My drive and preparedness in pursuing goals is extremely low.",
        "My drive and preparedness in pursuing goals is very low.",
        "My drive and preparedness in pursuing goals is somewhat low.",
        "My drive and preparedness in pursuing goals is moderate.",
        "My drive and preparedness in pursuing goals is somewhat high.",
        "My drive and preparedness in pursuing goals is high.",
        "My drive and preparedness in pursuing goals is very high."
    ],
    # Future Envisioning - Future Time Perspective (7-point scale, 8 items with 3 reverse-coded)
    "FTP_AVG": [
        "My perception of future opportunities and time available is extremely limited.",
        "My perception of future opportunities and time available is very limited.",
        "My perception of future opportunities and time available is somewhat limited.",
        "My perception of future opportunities and time available is moderate.",
        "My perception of future opportunities and time available is somewhat expansive.",
        "My perception of future opportunities and time available is expansive.",
        "My perception of future opportunities and time available is very expansive."
    ],
    # Future Envisioning - Future Work Selves (7-point scale, 5 items averaged)
    "FWS_AVG": [
        "My vision of my future work self is extremely vague.",
        "My vision of my future work self is very vague.",
        "My vision of my future work self is somewhat vague.",
        "My vision of my future work self is moderate.",
        "My vision of my future work self is somewhat clear.",
        "My vision of my future work self is clear.",
        "My vision of my future work self is very clear."
    ],
    # Self-Worth and Identity (7-point scale, 10 items with 5 reverse-coded, Rosenberg Self-Esteem Scale)
    "SI_AVG": [
        "I have extremely low self-esteem and sense of personal worth.",
        "I have very low self-esteem and sense of personal worth.",
        "I have somewhat low self-esteem and sense of personal worth.",
        "I have moderate self-esteem and sense of personal worth.",
        "I have somewhat high self-esteem and sense of personal worth.",
        "I have high self-esteem and sense of personal worth.",
        "I have very high self-esteem and sense of personal worth."
    ],
    # Psychological Resilience (7-point scale, 6 items with 3 reverse-coded, Brief Resilience Scale)
    "PR_AVG": [
        "My ability to recover from difficulties and stress is extremely poor.",
        "My ability to recover from difficulties and stress is very poor.",
        "My ability to recover from difficulties and stress is somewhat poor.",
        "My ability to recover from difficulties and stress is moderate.",
        "My ability to recover from difficulties and stress is somewhat good.",
        "My ability to recover from difficulties and stress is good.",
        "My ability to recover from difficulties and stress is excellent."
    ]
}


def pre_test_generate(pre_test):
    # FS level
    fs_level = score_to_level7(pre_test.iloc[0, 3])
    # Path level
    path_level = score_to_level7(pre_test.iloc[0, 4:8].astype(float).mean())
    # Agency level
    agency_level = score_to_level7(pre_test.iloc[0, 8:12].astype(float).mean())
    # FTP level
    ftp_values = pre_test.iloc[0, 12:20].astype(float).copy()
    ftp_values.iloc[5:8] = 8 - ftp_values.iloc[5:8]
    ftp_level = score_to_level7(ftp_values.mean())
    # FWS level
    fws_level = score_to_level7(pre_test.iloc[0, 20:25].astype(float).mean())
    # SI level
    si_values = pre_test.iloc[0, 25:35].astype(float).copy()
    reverse_indices = [1, 4, 5, 7, 8]
    si_values.iloc[reverse_indices] = 8 - si_values.iloc[reverse_indices]
    si_level = score_to_level7(si_values.mean())
    # PR level
    pr_values = pre_test.iloc[0, 35:41].astype(float).copy()
    reverse_indices = [1, 3, 5]
    pr_values.iloc[reverse_indices] = 8 - pr_values.iloc[reverse_indices]
    pr_level = score_to_level7(pr_values.mean())
    lib_file = 'data/prompt_template/pre_test.txt'
    f = open(lib_file, "r")
    pre_test_template = f.read()
    f.close()
    pre_test = pre_test_template.format(
        FS=descriptions["FS_AVG"][fs_level - 1],  # fs
        PATH=descriptions["PATH_AVG"][path_level - 1],  # path
        AGEN=descriptions["AGEN_AVG"][agency_level - 1],  # agency
        FTP=descriptions["FTP_AVG"][ftp_level - 1],  # ftp
        FWS=descriptions["FWS_AVG"][fws_level - 1],  # fws
        SI=descriptions["SI_AVG"][si_level - 1],  # si
        PR=descriptions["PR_AVG"][pr_level - 1],  # pr
    )
    return pre_test