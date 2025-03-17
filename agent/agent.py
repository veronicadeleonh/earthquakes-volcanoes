import os
from openai import OpenAI
import streamlit as st
from dotenv import load_dotenv

load_dotenv()


def agent(messages):

    client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv('OPENROUTER_API_KEY'),
    )

    completion = client.chat.completions.create(
    extra_body={},
    model="deepseek/deepseek-r1-zero:free",
    messages=messages)

    return completion.choices[0].message.content.replace(r"\boxed{", "").replace("}", "")