# langchain_g4g

Exploring [LangChain](https://www.langchain.com/) based on the GeeksForGeeks article [Introduction to LangChain](https://www.geeksforgeeks.org/artificial-intelligence/introduction-to-langchain/).

## About

LangChain is an open-source framework for building applications powered by large language models (LLMs). It provides abstractions for chaining together LLM calls, prompt templates, external data retrieval, agents, and memory — enabling patterns like Retrieval-Augmented Generation (RAG).

Key concepts covered in the article:

- **Chains** — sequential workflows combining LLM calls, data processing, and tool invocations
- **Prompt Management** — template-based prompts via `PromptTemplate`
- **Agents** — LLM-driven components that autonomously select and invoke tools
- **Vector Databases** — semantic vector storage for similarity search
- **Models** — support for multiple LLM providers (OpenAI, Hugging Face, etc.)
- **Memory** — maintaining conversational context across interactions

## Example (`main.py`)

[main.py](main.py) demonstrates a simple LCEL (LangChain Expression Language) pipeline using `langchain-openai`:

1. **Direct invocation** — sends a plain prompt to the OpenAI LLM and prints the response
2. **Prompt template** — builds a dynamic prompt using `PromptTemplate` with a `{year}` placeholder
3. **Chain** — composes the template, LLM, and `StrOutputParser` with the `|` pipe operator and invokes it

Requires an `OPENAI_API_KEY` environment variable.

## Setup

```bash
just setup
```

## Run

```bash
just run
```

## Requirements

- [uv](https://github.com/astral-sh/uv)
- [just](https://github.com/casey/just)
- Python 3.13+
- OpenAI API key set as `OPENAI_API_KEY`
