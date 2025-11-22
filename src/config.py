import os
from pathlib import Path

# Project paths
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
DATABASE_PATH = DATA_DIR / "robot_vacuum.db"
DEFAULT_CSV_PATH = DATA_DIR / "RobotVacuumDepot_MasterData.csv"

# Database configuration
DATABASE_URL = f"sqlite:///{DATABASE_PATH}"

# LLM configuration
LLM_MODEL = os.getenv("LLM_MODEL", "gpt-4o-mini")
LLM_TEMPERATURE = float(os.getenv("LLM_TEMPERATURE", "0"))

# Agent configuration
MAX_ITERATIONS = 5
ENABLE_VISUALIZATION_PRIORITY = True

# Streamlit configuration
PAGE_TITLE = "Agentic Data Analysis"
PAGE_ICON = "📊"
LAYOUT = "wide"
