import json
from langchain_groq import ChatGroq
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser


def get_llm(temperature=0.3):
    return ChatGroq(model="openai/gpt-oss-120b", temperature=temperature)



def load_jobs(path: str = "data/jobs.json") -> list:
    with open(path, "r") as f:
        return json.load(f)


def recommend_jobs(resume_context: str, query: str = "") -> str:
    jobs = load_jobs()
    jobs_text = "\n".join([
        f"[{j['id']}] {j['title']} at {j['company']} | Skills: {', '.join(j['skills'])} | {j['experience']} | {j['description']}"
        for j in jobs
    ])

    prompt = PromptTemplate(
        input_variables=["resume", "jobs", "query"],
        template="""You are an expert career advisor and job matching AI.

Below is relevant content extracted from a candidate's resume:
{resume}

Here are available job listings:
{jobs}

User question or focus area: {query}

Your task:
1. Identify the candidate's key skills, experience level, and strengths from the resume.
2. Match them to the most suitable jobs from the list above.
3. Recommend the TOP 3 jobs with a brief explanation for each (why it's a good fit).
4. Give one actionable tip to improve their chances.

Be specific, encouraging, and practical.
"""
    )

    chain = prompt | get_llm(0.3) | StrOutputParser()
    return chain.invoke({"resume": resume_context, "jobs": jobs_text, "query": query or "best overall match"})


def chat_with_resume(resume_context: str, user_message: str, chat_history: list) -> str:
    history_text = "\n".join([f"{m['role'].upper()}: {m['content']}" for m in chat_history[-6:]])

    prompt = PromptTemplate(
        input_variables=["resume", "history", "question"],
        template="""You are a helpful career coach. Use the resume context below to answer questions.

Resume Context:
{resume}

Conversation History:
{history}

User: {question}

Answer helpfully and concisely:"""
    )

    chain = prompt | get_llm(0.5) | StrOutputParser()
    return chain.invoke({"resume": resume_context, "history": history_text, "question": user_message})
