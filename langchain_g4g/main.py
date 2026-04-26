import os
# from dotenv import load_dotenv
from langchain_openai import OpenAI
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser

api_key = os.getenv("OPENAI_API_KEY")

# Initialize the OpenAI LLM
# temperature=0.7: controls creativity (0 = deterministic, 1 = very creative).
# openai_api_key=api_key: authenticates with OpenAI.

llm = OpenAI(
    temperature=0.7,
    openai_api_key=api_key
)


# Run a Simple Prompt
# .invoke(): sends prompt to LLM and returns text output.

prompt = "Suggest me a skill that is in demand?"
response = llm.invoke(prompt)
print(" Suggested Skill:\n", response)


# Create a Prompt Template
# create a dynamic prompt where {year} can be replaced with input values

template = "Give me 3 career skills that are in high demand in {year}."
prompt_template = PromptTemplate.from_template(template)


# Build a Chain
# use LCEL (LangChain Expression Language) to compose LLM workflows using a simple,
# chainable syntax with the | (pipe) operator.
# 1. prompt_template - Fills placeholders (like {year}) with actual inputs.
# 2. llm - Sends the formatted prompt to the OpenAI model.
# 3. StrOutputParser() - Cleans up and ensures the LLM’s response is returned as a string.

chain = prompt_template | llm | StrOutputParser()


# Run the Chain
# run the chain to fetch results
# .invoke({"year": "2025"}) replaces {year} with 2025 in the prompt.
# Final formatted prompt: "Give me 3 career skills that are in high demand in 2025."

response = chain.invoke({"year": "2025"})
print("\n Career Skills in 2025:\n", response)
