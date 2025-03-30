import fitz  # type: ignore
import io  # type: ignore
from PIL import Image, ImageEnhance  # type: ignore
import pytesseract  # type: ignore
import pathlib
from pathlib import Path
import filetype  # type: ignore
import magic  # type: ignore
import openai  # type: ignore
from pydantic import BaseModel,Field # type: ignore
from dotenv import load_dotenv # type: ignore
import os # type: ignore
import re # type: ignore
import time
import json
from thefuzz import process # type: ignore