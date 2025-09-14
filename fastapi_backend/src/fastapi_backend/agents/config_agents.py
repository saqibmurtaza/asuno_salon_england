from openai import AsyncOpenAI
from agents import Agent, OpenAIChatCompletionsModel, RunConfig, set_tracing_disabled
from dotenv import load_dotenv
import os

load_dotenv()

BASE_URL= os.getenv("BASE_URL")
MODEL_NAME= os.getenv("MODEL_NAME")
API_KEY= os.getenv("API_KEY")

client = AsyncOpenAI(
    api_key=API_KEY,
    base_url=BASE_URL,
)

set_tracing_disabled(disabled=True)

model= OpenAIChatCompletionsModel(
    model=MODEL_NAME,
    openai_client=client
)

config= RunConfig(
    model=model,
    model_provider=client,
    tracing_disabled=True
)


    