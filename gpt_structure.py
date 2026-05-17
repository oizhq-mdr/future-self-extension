import openai
from openai import OpenAI
from pydantic import BaseModel

MODEL = 'gpt-5-2025-08-07'

def dd_generate_gpt4_basic(system_prompt, knowledge, user_prompt):
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


def update_knowledge (knowledge , letters):
    system_lib_file = 'data/prompt_template/update_knowledge_sys.txt'
    f = open(system_lib_file, "r")
    system_prompt = f.read()
    f.close()

    completion = openai.chat.completions.create(
        model=MODEL,
        messages=[
            {'role': 'system', 'content': system_prompt},
            {'role': 'assistant', 'content': f'[Knowledge]\n\n{knowledge}'},
            {'role': 'user', 'content': letters}
        ]
    )
    return completion.choices[0].message.content

class Inference(BaseModel):
    steps: list[str]

def pvq_summary_gpt4(summary):
    system_lib_file = 'data/prompt_template/PVQ_summary_sys.txt'
    f = open(system_lib_file, "r")
    sys_prompt = f.read()
    f.close()

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

def bfi_summary_gpt4(summary):
    system_lib_file = 'data/prompt_template/BFI_summary_sys.txt'
    f = open(system_lib_file, "r")
    sys_prompt = f.read()
    f.close()

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