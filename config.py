import os
from dotenv import load_dotenv

# Load .env file
load_dotenv()

# Langfuse client
from langfuse import Langfuse

langfuse = Langfuse()

# API Configuration
MINIMAX_URL = os.getenv("MINIMAX_URL")
MODEL = os.getenv("MINIMAX_MODEL")
MINIMAX_API_KEY = os.getenv("MINIMAX_API_KEY")