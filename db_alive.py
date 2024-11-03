import threading
import time
from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError
from dotenv import load_dotenv
import os


load_dotenv()

QUES_DATABASE = os.getenv("QUES_DATABASE")
GAME_DATABASE = os.getenv("GAME_DATABASE")

# Question Database Connection
engine1 = create_engine(
    QUES_DATABASE,
    pool_size=5,
    pool_recycle=1800,
    pool_pre_ping=True
)

# Game Session Database Connection
engine2 = create_engine(
    GAME_DATABASE,
    pool_size=5,
    pool_recycle=1800,
    pool_pre_ping=True
)



# Question Database Function
def start_ques_keep_alive():
    def keep_alive():
        while True:
            try:
                with engine1.connect() as connection:
                    connection.execute(text("SELECT 1;"))
                time.sleep(300)
            except OperationalError:
                print("Question Database Connection lost. Attempting to reconnect...")
                time.sleep(60)

    keep_alive_thread = threading.Thread(target=keep_alive, daemon=True)
    keep_alive_thread.start()


# Game Session Database Function 
def start_game_keep_alive():
    def keep_alive():
        while True:
            try:
                with engine2.connect() as connection:
                    connection.execute(text("SELECT 1;"))
                time.sleep(300)
            except OperationalError:
                print("Game Session Connection lost. Attempting to reconnect...")
                time.sleep(60)

    keep_alive_thread = threading.Thread(target=keep_alive, daemon=True)
    keep_alive_thread.start()