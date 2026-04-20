import os
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

load_dotenv("config.env")

client = AsyncIOMotorClient(os.getenv("mongodb+srv://akshatkulshrestha209_db_user:7hI94vQ2Ppy4D5A3@cluster0.wgzfzve.mongodb.net/?appName=Cluster0"))
db = client["job_recommender"]

users_col = db["users"]
resumes_col = db["resumes"]
recommendations_col = db["recommendations"]
chats_col = db["chats"]
