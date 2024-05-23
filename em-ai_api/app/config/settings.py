import os
from dotenv import load_dotenv

env_file = ".env"
load_dotenv(env_file)

# database
DEV_MARIADB_URL = (
    f'mysql+pymysql://{os.getenv("DEV_MARIADB_USER")}:{os.getenv("DEV_MARIADB_PASSWORD")}'
    f'@{os.getenv("DEV_MARIADB_HOST")}:{os.getenv("DEV_MARIADB_PORT")}'
)
CPU_MARIADB_URL = (
    f'mysql+pymysql://{os.getenv("CPU_MARIADB_USER")}:{os.getenv("CPU_MARIADB_PASSWORD")}'
    f'@{os.getenv("CPU_MARIADB_HOST")}:{os.getenv("CPU_MARIADB_PORT")}'
)

# elasticsearch
ES_CLOUD_ID = os.getenv("ELASTICSEARCH_CLOUD_ID")
ES_API_KEY = os.getenv("ELASTICSEARCH_API_KEY")

# oauth2 secret key
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM")

# huggingface token
HF_TOKEN = os.getenv("HF_TOKEN")


# cors allow origins
CORS_ALLOW_ORIGINS = [
    os.getenv("AWS_GPT_ACTIONS_SERVER_ORIGIN"),
    os.getenv("IDV_ORIGIN"),
    os.getenv("ILLUNEX_OFFICE_ORIGIN"),
    os.getenv("FRONT_DEV_ORIGIN"),
    os.getenv("FRONT_DEV_ORIGIN_2"),
    os.getenv("EM_GPT_ORIGIN"),
    "http://localhost:3000",
    "http://localhost:3001",
]

# file path
FILE_PATHS = {
    "log": "app/common/log/",
}

# api address
API_ADDRESS = {
    "patent_function_diagram": os.getenv("PATENT_FUNCTION_DIAGRAM_API_URL"),
    "patent_claim_gen": os.getenv("PATENT_CLAIM_GEN_API_URL"),
    "embedding": os.getenv("EMBEDDING_API_URL"),
}

# openai
AZURE_OPENAI_API_KEY = os.getenv("AZURE_OPENAI_API_KEY")
AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
AZURE_OPENAI_API_VERSION = os.getenv("AZURE_OPENAI_API_VERSION")

# cuda
os.environ["CUBLAS_WORKSPACE_CONFIG"] = ":4096:8"
