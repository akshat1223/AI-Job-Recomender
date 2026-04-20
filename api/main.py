import os
import shutil
import tempfile
from datetime import datetime
from bson import ObjectId
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from api.database import users_col, resumes_col, recommendations_col, chats_col
from api.models import UserCreate, RecommendRequest, ChatRequest
from pipeline.ingestor import load_and_chunk_resume
from pipeline.embedder import build_vectorstore, load_vectorstore, vectorstore_exists
from pipeline.retriever import get_relevant_resume_context
from pipeline.recommender import recommend_jobs, chat_with_resume

load_dotenv("config.env")

app = FastAPI(title="Job Recommender API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── in-memory vectorstore cache per user ────────────────────────────────────
_vs_cache: dict = {}


def _get_vs(user_id: str):
    if user_id in _vs_cache:
        return _vs_cache[user_id]
    path = f"vectorstore/{user_id}"
    if os.path.exists(path):
        from pipeline.embedder import load_vectorstore
        vs = load_vectorstore(path)
        _vs_cache[user_id] = vs
        return vs
    return None


# ── Users ────────────────────────────────────────────────────────────────────

@app.post("/users", status_code=201)
async def create_user(body: UserCreate):
    existing = await users_col.find_one({"email": body.email})
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    doc = {"name": body.name, "email": body.email, "created_at": datetime.now()}
    result = await users_col.insert_one(doc)
    return {"id": str(result.inserted_id), "name": body.name, "email": body.email}


@app.get("/users/by-email/{email}")
async def get_user_by_email(email: str):
    user = await users_col.find_one({"email": email})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return {"id": str(user["_id"]), "name": user["name"], "email": user["email"]}


@app.get("/users/{user_id}")
async def get_user(user_id: str):
    user = await users_col.find_one({"_id": ObjectId(user_id)})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return {"id": str(user["_id"]), "name": user["name"], "email": user["email"]}


# ── Resume Upload ─────────────────────────────────────────────────────────────

@app.post("/users/{user_id}/resume")
async def upload_resume(user_id: str, file: UploadFile = File(...)):
    user = await users_col.find_one({"_id": ObjectId(user_id)})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # save uploaded file to temp path
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        shutil.copyfileobj(file.file, tmp)
        tmp_path = tmp.name

    # chunk + embed + save vectorstore per user
    chunks = load_and_chunk_resume(tmp_path)
    vs_path = f"vectorstore/{user_id}"
    vs = build_vectorstore(chunks, vs_path)
    _vs_cache[user_id] = vs
    os.unlink(tmp_path)

    # save resume metadata to MongoDB
    doc = {
        "user_id": user_id,
        "filename": file.filename,
        "chunks": len(chunks),
        "uploaded_at": datetime.now()
    }
    result = await resumes_col.insert_one(doc)
    return {"resume_id": str(result.inserted_id), "chunks_indexed": len(chunks)}


# ── Job Recommendations ───────────────────────────────────────────────────────

@app.post("/recommend")
async def get_recommendations(body: RecommendRequest):
    vs = _get_vs(body.user_id)
    if not vs:
        raise HTTPException(status_code=400, detail="No resume found. Upload a resume first.")

    context = get_relevant_resume_context(vs, body.query or "best job match")
    result = recommend_jobs(context, body.query)

    doc = {
        "user_id": body.user_id,
        "query": body.query,
        "result": result,
        "created_at": datetime.now()
    }
    await recommendations_col.insert_one(doc)
    return {"result": result}


@app.get("/users/{user_id}/recommendations")
async def get_recommendation_history(user_id: str):
    cursor = recommendations_col.find({"user_id": user_id}).sort("created_at", -1).limit(10)
    history = []
    async for doc in cursor:
        history.append({
            "id": str(doc["_id"]),
            "query": doc["query"],
            "result": doc["result"],
            "created_at": doc["created_at"]
        })
    return history


# ── Chat ──────────────────────────────────────────────────────────────────────

@app.post("/chat")
async def chat(body: ChatRequest):
    vs = _get_vs(body.user_id)
    if not vs:
        raise HTTPException(status_code=400, detail="No resume found. Upload a resume first.")

    # load last 6 messages as history
    cursor = chats_col.find({"user_id": body.user_id}).sort("created_at", -1).limit(6)
    history = []
    async for doc in cursor:
        history.append({"role": doc["role"], "content": doc["content"]})
    history.reverse()

    context = get_relevant_resume_context(vs, body.message)
    reply = chat_with_resume(context, body.message, history)

    # save both user message and assistant reply
    now = datetime.now()
    await chats_col.insert_many([
        {"user_id": body.user_id, "role": "user", "content": body.message, "created_at": now},
        {"user_id": body.user_id, "role": "assistant", "content": reply, "created_at": now},
    ])
    return {"reply": reply}


@app.get("/users/{user_id}/chats")
async def get_chat_history(user_id: str):
    cursor = chats_col.find({"user_id": user_id}).sort("created_at", 1)
    history = []
    async for doc in cursor:
        history.append({"role": doc["role"], "content": doc["content"], "created_at": doc["created_at"]})
    return history
