# config.py
from dotenv import load_dotenv
import os

load_dotenv()
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
ORIGIN_PATH = os.environ.get("ORIGIN_PATH")
GOAL_PATH = os.environ.get("GOAL_PATH")
JSON_PATH = os.environ.get("JSON_PATH")
GOOGLE_APPLICATION_CREDENTIALS = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")