import openai
from openai import OpenAI
from pydantic import BaseModel
import json

MODEL = "gpt-4o-mini"

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


class Inference(BaseModel):
    steps: list[str]

def pvq_summary_gpt4(summary, system_prompt=None):
    if system_prompt is None:
        system_lib_file = 'data/prompt_template/PVQ_summary_sys.txt'
        f = open(system_lib_file, "r")
        sys_prompt = f.read()
        f.close()
    else:
        sys_prompt = system_prompt

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

def bfi_summary_gpt4(summary, system_prompt=None):
    if system_prompt is None:
        system_lib_file = 'data/prompt_template/BFI_summary_sys.txt'
        f = open(system_lib_file, "r")
        sys_prompt = f.read()
        f.close()
    else:
        sys_prompt = system_prompt

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

def dd_safeguard_gpt4(safeguard_prompt, replies_text):
    completion = openai.chat.completions.create(
        model = MODEL,
        messages = [
            {'role': 'system', 'content': safeguard_prompt},
            {'role': 'user', 'content': replies_text}
        ]
    )
    return completion.choices[0].message.content

def dd_filter_user_letter_gpt4(filter_prompt, letter):
    user_content = f"""[사용자가 작성한 편지]
{letter}

응답은 반드시 JSON 객체로 반환해주세요."""

    completion = openai.chat.completions.create(
        model=MODEL,
        messages=[
            {'role': 'system', 'content': filter_prompt},
            {'role': 'user', 'content': user_content}
        ],
        response_format={ "type": "json_object" }
    )
    return json.loads(completion.choices[0].message.content)

def dd_evaluate_letter_with_prompt_gpt4(letter, screening_prompt):
    user_content = f"""[검토할 편지]
{letter}

응답은 반드시 JSON 객체로 반환해주세요."""

    completion = openai.chat.completions.create(
        model=MODEL,
        messages=[
            {'role': 'system', 'content': screening_prompt},
            {'role': 'user', 'content': user_content}
        ],
        response_format={ "type": "json_object" }
    )
    return json.loads(completion.choices[0].message.content)

def dd_generate_improvement_prompt_gpt4(improvement_prompt, letter):
    completion = openai.chat.completions.create(
        model=MODEL,
        messages=[
            {'role': 'system', 'content': improvement_prompt},
            {
                'role': 'user',
                'content': f"[현재 답장]\n{letter}"
            }
        ]
    )
    return completion.choices[0].message.content
