import os

from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI", "mongodb://mongodb:27017")
DATABASE_NAME = os.getenv("DATABASE_NAME", "radar_combustivel")

client = MongoClient(MONGO_URI)

db = client[DATABASE_NAME]


def get_database():
    return db