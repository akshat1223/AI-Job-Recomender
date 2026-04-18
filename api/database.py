import os
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

load_dotenv("config.env")

client = AsyncIOMotorClient(os.getenv("MONGODB_URI", "mongodb://localhost:27017"))
db = client["job_recommender"]

users_col = db["users"]
resumes_col = db["resumes"]
recommendations_col = db["recommendations"]
chats_col = db["chats"]
