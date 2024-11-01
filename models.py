from sqlalchemy import Column, Integer, Text, VARCHAR, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship


Base = declarative_base()


# Database for Questions and Answers
class triviaques(Base):
    __tablename__ = "QnA"
    id = Column(Integer, primary_key=True, nullable=False)
    questions = Column(Text, nullable=False)
    answers = Column(Text, nullable=False)

    sessions = relationship("QuestionSession", back_populates="question")

    def __repr__(self):
        return f"<triviaques(id={self.id}, questions='{self.questions}', answers='{self.answers}')>"

class QuestionSession(Base):
    __tablename__ = "Question_Session"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, unique=True, nullable=True)
    question_id = Column(Integer, ForeignKey("QnA.id"))
    correct_answer = Column(Text, nullable=True)

    question = relationship("triviaques", back_populates="sessions")


# Database for game players
class Player_1(Base):
    __tablename__ = "Player1"
    id = Column(Integer, primary_key=True)
    username = Column(VARCHAR, unique=False, nullable=True)
    chat_id = Column(Integer, unique=True, nullable=True)
    points = Column(Integer, unique=False, nullable=True)
    session_id = Column(Text, unique=True, nullable=True)

    game_session = relationship("GameSession", back_populates="player1")

class Player_2(Base):
    __tablename__ = "Player2"
    id = Column(Integer, primary_key=True)
    username = Column(VARCHAR, unique=False, nullable=True)
    chat_id = Column(Integer, unique=True, nullable=True)
    points = Column(Integer, unique=False, nullable=True)
    session_id = Column(Text, unique=True, nullable=True)

class GameSession(Base):
    __tablename__ = "Game_Session"
    id = Column(Integer, primary_key=True)
    name = Column(Text, nullable=True)
    target_point = Column(Integer, nullable=True)
    current_player = Column(VARCHAR, nullable=True)
    game_id = Column(Text, ForeignKey("Player1.session_id"), unique=True, nullable=True)
    player1_id = Column(Integer, nullable=True)
    player2_id = Column(Integer, nullable=True)

    player1 = relationship("Player_1", back_populates="game_session")