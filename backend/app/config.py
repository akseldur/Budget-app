import os

from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.environ["DATABASE_URL"]
APP_API_KEY = os.environ["APP_API_KEY"]

ENABLE_BANKING_APPLICATION_ID = os.environ["ENABLE_BANKING_APPLICATION_ID"]
ENABLE_BANKING_PRIVATE_KEY_PATH = os.environ["ENABLE_BANKING_PRIVATE_KEY_PATH"]
ENABLE_BANKING_REDIRECT_URL = os.environ["ENABLE_BANKING_REDIRECT_URL"]

# Hvilken bank samtykke-flyten peker mot - "Mock ASPSP"/"NO" i sandkasse,
# f.eks. "DNB"/"NO" i production. Konfigurerbar slik at man slipper å
# kode-endre for å bytte mellom sandkasse og ekte bank.
ENABLE_BANKING_ASPSP_NAME = os.environ.get("ENABLE_BANKING_ASPSP_NAME", "Mock ASPSP")
ENABLE_BANKING_ASPSP_COUNTRY = os.environ.get("ENABLE_BANKING_ASPSP_COUNTRY", "NO")
