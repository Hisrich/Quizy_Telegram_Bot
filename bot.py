import telebot
from telebot.types import InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery
from dotenv import load_dotenv
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import triviaques, QuestionSession, Player_1, Player_2, GameSession
import random, string
from sqlalchemy.sql.expression import func
from sqlalchemy.pool import NullPool
from db_alive import start_game_keep_alive, start_ques_keep_alive



load_dotenv()

start_ques_keep_alive()
start_game_keep_alive()


API_KEY = os.getenv("API_KEY")
QUES_DATABASE = os.getenv("QUES_DATABASE")
GAME_DATABASE = os.getenv("GAME_DATABASE")


bot = telebot.TeleBot(API_KEY)


# Questions and Answers Database connection
QUESTION_DATABASE_URL = QUES_DATABASE
engine1 = create_engine(QUESTION_DATABASE_URL, pool_size=5, pool_recycle=1800, pool_pre_ping=True)
Session1 = sessionmaker(bind=engine1)
ques_session = Session1()


# Users, Game Session and Game Data Database connection
GAME_DATABASE_URL = GAME_DATABASE
engine2 = create_engine(GAME_DATABASE_URL, pool_size=5, pool_recycle=1800, pool_pre_ping=True)
Session2 = sessionmaker(bind=engine2)
game_session = Session2()


@bot.message_handler(commands=["start"])
def start_game(message):
    user_id = message.chat.id
    
    player_keyboard = InlineKeyboardMarkup()

    user1_button = InlineKeyboardButton("User 1\ufe0f\u20e3", callback_data="user_1")
    user2_button = InlineKeyboardButton("User 2\ufe0f\u20e3", callback_data="user_2")

    player_keyboard.add(user1_button, user2_button)

    bot.send_message(user_id, "\U0001f609<b>Welcome to the Genius Trivia Game</b>\n\n<b><u>GAME RULES</u></b>\n\u270d\ufe0fOnly 2 players can play at a time\n\u270d\ufe0fAvoid using 'a', 'the' and 'an' before answers. Answer questions directly and precisely\n\u270d\ufe0fAlways type an asnwer even if you don't know\n\u270d\ufe0fAvoid using symbols(@,-,&) or emojis. Type in full if applicable\n\u270d\ufe0fIf an answer requires a number, type it in words\n\u270d\ufe0fNo shorthand; type words and names in full\n\U0001f91eMay The Best Player Win\U0001f91e", parse_mode="HTML")
    bot.send_message(user_id, "Select if you are *User 1* or *User 2*", parse_mode="Markdown", reply_markup=player_keyboard)


@bot.callback_query_handler(func=lambda call: call.data in ["user_1", "user_2"])
def choose_user(call: CallbackQuery):
    user_id = call.message.chat.id

    if call.data == "user_1":
        user1_data = Player_1(username=None, chat_id=user_id,points=0, session_id=None)
        game_session.add(user1_data)
        game_session.commit()
        bot.send_message(user_id, "\U0001f9d1\u200d\U0001f4bb*Player 1, kindly type your name*", parse_mode="Markdown")

    elif call.data == "user_2":
        user2_data = Player_2(username=None, chat_id=user_id, points=0, session_id=None)
        game_session.add(user2_data)
        game_session.commit()
        bot.send_message(user_id, "\U0001f9d1\u200d\U0001f4bb*Player 2, kindly type your name*", parse_mode="Markdown")

    bot.answer_callback_query(call.id)


@bot.message_handler(func=lambda message: game_session.query(Player_1).filter_by(username=None, chat_id=message.chat.id, points=0, session_id=None).first() or game_session.query(Player_2).filter_by(username=None, chat_id=message.chat.id, points=0, session_id=None).first())
def players_name(message):
    user_id = message.chat.id
    player_name = message.text

    if message.text == "/reset":
        reset(message)
        return
    elif message.text == "/help":
        help(message)
        return

    else:
        player1_name = game_session.query(Player_1).filter_by(chat_id=user_id).first()
        player2_name = game_session.query(Player_2).filter_by(chat_id=user_id).first()

        if player1_name:
            player1_name.username = player_name
            game_session.commit()

            done_keyboard = InlineKeyboardMarkup()
            done_button = InlineKeyboardButton("Done\u2705", callback_data="done")
            done_keyboard.add(done_button)

            player1_session_id = generate_session_id(message)

            player1_name.session_id = player1_session_id

            bot.send_message(user_id, f"Send this code to your partner\n\U0001f50dSession ID: *{player1_session_id}*", parse_mode="Markdown")
            bot.send_message(user_id, f"Tap on *Done* to continue", parse_mode="Markdown", reply_markup=done_keyboard)
            
        elif player2_name:
            player2_name.username = player_name
            game_session.commit()
            bot.send_message(user_id, f"\U0001f50dEnter Session ID")

            bot.register_next_step_handler(message, verify_session_id)


# Verify session id
def verify_session_id(message):
    user_id = message.chat.id
    player2_session_id = message.text

    if message.text == "/reset":
        reset(message)
        return
    elif message.text == "/help":
        help(message)
        return

    else:
        special_id = game_session.query(Player_1).filter_by(session_id=player2_session_id).first()    

        if special_id: 
            player2 = game_session.query(Player_2).filter_by(chat_id=user_id).first()
            player2.session_id = player2_session_id
            game_session.commit()
            player2_username = player2.username

            other_player = game_session.query(Player_1).filter_by(session_id=player2_session_id).first()
            player1_username = other_player.username
            player1_chat_id = other_player.chat_id
            integer_form = int(player1_chat_id)

            # create game session row
            game_data = GameSession(name=None, target_point=0, current_player=None, game_id=special_id.session_id, player1_id=integer_form, player2_id=user_id)
            game_session.add(game_data)
            game_session.commit()

            current = game_session.query(GameSession).filter_by(game_id=special_id.session_id).first()
            current.current_player = player1_chat_id
            game_session.commit()

            proceed_keyboard = InlineKeyboardMarkup()
            proceed_key = InlineKeyboardButton("Proceed\u23ed\ufe0f", callback_data="proceed")
            proceed_keyboard.add(proceed_key)

            bot.send_message(user_id, f"\U0001f51bYou are connected to *{player1_username}*\U0001f51b", parse_mode="Markdown")
            bot.send_message(player1_chat_id, f"\U0001f51bYou are connected to *{player2_username}*\U0001f51b\nTap on *Proceed*", parse_mode="Markdown", reply_markup=proceed_keyboard)

        else:
            if message.text == "/reset":
                reset(message)
                return
            elif message.text == "/help":
                help(message)
                return
            else:
                bot.send_message(user_id, f"Incorrect Session Id. Enter it again")
                bot.register_next_step_handler(message, verify_session_id)


@bot.callback_query_handler(func=lambda call: call.data == "done")
def response_to_done(call: CallbackQuery):
    user_id = call.message.chat.id
    bot.send_message(user_id, "_\U0001f6dcWaiting For Connection..._", parse_mode="Markdown")

    bot.answer_callback_query(call.id)


@bot.callback_query_handler(func=lambda call: call.data == "proceed")
def proceed_response(call: CallbackQuery):
    set_target(call.message)

    bot.answer_callback_query(call.id)


# Set target point
def set_target(message):
    user_id = message.chat.id
    bot.send_message(user_id, "*How many points to win?*\U0001f3c6\n\u2705Correct answer = +5 points\n\U0001f611Wrong answer = -3 points", parse_mode="Markdown")

    if message.text == "/reset":
        reset(message)
        return
    elif message.text == "/help":
        help(message)
        return
    else:
        bot.register_next_step_handler(message, respond_target)


def respond_target(message):
    user_id = message.chat.id
    target_input = message.text

    if message.text == "/reset":
        reset(message)
        return
    elif message.text == "/help":
        help(message)
        return

    else:

        try:
            integer_of_target = int(target_input)
            chat_id = str(user_id)   

            session_row = game_session.query(GameSession).filter_by(current_player=chat_id).first()
            session_row.target_point = target_input
            game_session.commit()

            session = session_row.game_id
            player2 = game_session.query(Player_2).filter_by(session_id=session).first()
            player2_chatid = player2.chat_id

            bot.send_message(user_id, f"\U0001f3afTarget point: *{integer_of_target}*", parse_mode="Markdown")
            bot.send_message(player2_chatid, f"\U0001f3afTarget point: *{integer_of_target}*\nKindly wait for your question", parse_mode="Markdown")
            ask_question(user_id)
        
        except ValueError:
            bot.send_message(user_id, "Input a number not text")
            set_target(message)


def ask_question(user_id):
    question = get_question(ques_session)
    specific_question = question.questions
    specific_answer = question.answers
    specific_id = question.id

    specific_session = QuestionSession(user_id=user_id, question_id=specific_id, correct_answer=specific_answer)
    ques_session.add(specific_session)
    ques_session.commit()

    bot.send_message(user_id, f"\U0001f440Here's your question!\n\u2753*{specific_question}*", parse_mode="Markdown")
    bot.register_next_step_handler_by_chat_id(user_id, handle_answer)


def handle_answer(message):
    user_id = message.chat.id
    player_answer = message.text
    str_user_id = str(user_id)

    if message.text == "reset":
        reset(message)
        return
    elif message.text == "/help":
        help(message)
        return

    else:
        query_answer = ques_session.query(QuestionSession).filter_by(user_id=user_id).first()

        if not query_answer:
            bot.send_message(user_id, "No active question found. Please try again.")
            return

        avail_answer = query_answer.correct_answer

        if player_answer.lower() == avail_answer.lower():
            game_session_row = game_session.query(GameSession).filter_by(current_player=str_user_id).first()

            if not game_session_row:
                bot.send_message(user_id, "Game session not found.")
                return

            p1 = game_session_row.player1_id
            p2 = game_session_row.player2_id

            p1_row = game_session.query(Player_1).filter_by(chat_id=p1).first()
            player1_name = p1_row.username
            player1_point = p1_row.points

            p2_row = game_session.query(Player_2).filter_by(chat_id=p2).first()
            player2_name = p2_row.username
            player2_point = p2_row.points

            if game_session_row.current_player == str(p1):
                p1_row = game_session.query(Player_1).filter_by(chat_id=p1).first()
                p1_row.points += 5
                game_session.commit()
                bot.send_message(user_id, f"*You nailed it(+5 points)*\U0001f973\nCurrent Score: *{p1_row.points}*\n{player2_name}: *{player2_point}*\n\n_Kindly wait for your turn_", parse_mode="Markdown")
                
            elif game_session_row.current_player == str(p2):
                p2_row = game_session.query(Player_2).filter_by(chat_id=p2).first()
                p2_row.points += 5
                game_session.commit()
                bot.send_message(user_id, f"*That's perfect(+5 points)*\U0001f973\nCurrent Score: *{p2_row.points}*\n{player1_name}: *{player1_point}*\n\n_Kindly wait for your turn_", parse_mode="Markdown")
            
            game_session.commit()  

        else:
            game_session_row = game_session.query(GameSession).filter_by(current_player=str_user_id).first()

            if not game_session_row:
                bot.send_message(user_id, "Game session not found.")
                return

            p1 = game_session_row.player1_id
            p2 = game_session_row.player2_id

            p1_row = game_session.query(Player_1).filter_by(chat_id=p1).first()
            player1_name = p1_row.username
            player1_point = p1_row.points

            p2_row = game_session.query(Player_2).filter_by(chat_id=p2).first()
            player2_name = p2_row.username
            player2_point = p2_row.points

            if game_session_row.current_player == str(p1):
                p1_row = game_session.query(Player_1).filter_by(chat_id=p1).first()
                p1_row.points -= 3
                game_session.commit()
                bot.send_message(user_id, f"*Oops, that's not right\U0001f62c(-3 points)*\nCorrect answer: '*{avail_answer}*'\nCurrent Score: *{p1_row.points}*\n{player2_name}: *{player2_point}*\n\n_Kindly wait for your turn_", parse_mode="Markdown")
                
            elif game_session_row.current_player == str(p2):
                p2_row = game_session.query(Player_2).filter_by(chat_id=p2).first()
                p2_row.points -= 3
                game_session.commit()
                bot.send_message(user_id, f"*Whops, that's incorrect\U0001f62c(-3 points)*\nCorrect answer: '*{avail_answer}*'\nCurrent Score: *{p2_row.points}*\n{player1_name}: *{player1_point}*\n\n_Kindly wait for your turn_", parse_mode="Markdown")

            game_session.commit() 

        # Check for winner
        game_session_row = game_session.query(GameSession).filter_by(current_player=str_user_id).first()

        p1 = game_session_row.player1_id
        p2 = game_session_row.player2_id

        p1_row = game_session.query(Player_1).filter_by(chat_id=p1).first()
        p2_row = game_session.query(Player_2).filter_by(chat_id=p2).first()

        session_target = game_session_row.target_point
        if p1_row and p1_row.points >= session_target:
            bot.send_message(p1_row.chat_id, f"*Congratulations {p1_row.username}\U0001f389\nYou are the Quizy Genius*\U0001f38a\n\n{p1_row.username}: *{p1_row.points} points*\n{p2_row.username}: *{p2_row.points} points*", parse_mode="Markdown")
            
            bot.send_message(p2, f"*Sorry {p2_row.username}, you lost*\U0001f614\n\n{p2_row.username}: *{p2_row.points} points*\n{p1_row.username}: *{p1_row.points} points*", parse_mode="Markdown")
            
            unique_code = game_session_row.game_id
            game_session.query(Player_1).filter_by(session_id=unique_code).delete()
            game_session.query(Player_2).filter_by(session_id=unique_code).delete()

            current_id = game_session_row.current_player
            ques_session.query(QuestionSession).filter_by(user_id=current_id).delete()
            ques_session.commit()

            game_session.query(GameSession).filter_by(current_player=str_user_id).delete()

            game_session.commit()

            inquire_to_restart_game(message)
            return  
        
        elif p2_row and p2_row.points >= session_target:
            bot.send_message(p2_row.chat_id, f"*Congratulations {p2_row.username}\U0001f389\nYou are the Quizy Genius*\U0001f38a\n\n{p2_row.username}: *{p2_row.points} points*\n{p1_row.username}: *{p1_row.points} points*", parse_mode="Markdown")

            bot.send_message(p1, f"*Sorry {p1_row.username}, you lost*\U0001f614\n\n{p1_row.username}: *{p1_row.points} points*\n{p2_row.username}: *{p2_row.points} points*", parse_mode="Markdown")    

            unique_code = game_session_row.game_id
            game_session.query(Player_1).filter_by(session_id=unique_code).delete()
            game_session.query(Player_2).filter_by(session_id=unique_code).delete()

            current_id = game_session_row.current_player
            ques_session.query(QuestionSession).filter_by(user_id=current_id).delete()
            ques_session.commit()

            game_session.query(GameSession).filter_by(current_player=str_user_id).delete()

            game_session.commit()

            inquire_to_restart_game(message)
            return

        ques_session.query(QuestionSession).filter_by(user_id=user_id).delete()
        ques_session.commit()

        # Alternate between players
        query_active_player = game_session.query(GameSession).filter_by(current_player=str_user_id).first()

        if not query_active_player:
            bot.send_message(user_id, "Error in retrieving the active player.")
            return

        active_player = query_active_player.current_player
        string_form1 = str(query_active_player.player1_id)
        string_form2 = str(query_active_player.player2_id)

        if active_player == string_form1:
            query_active_player.current_player = string_form2
            game_session.commit()
            bot.send_message(query_active_player.player2_id, "Your turn now")
            ask_question(query_active_player.player2_id)  
        else:
            query_active_player.current_player = string_form1
            game_session.commit()
            bot.send_message(query_active_player.player1_id, "It's your turn")
            ask_question(query_active_player.player1_id)  

        
        query_active_player.target_point


# Inquire to restart game
def inquire_to_restart_game(message):
    user_id = message.chat.id
    new_keyboard = InlineKeyboardMarkup()

    absolutely_button = InlineKeyboardButton("Absolutely\U0001f4af", callback_data='absolutely')
    notnow_button = InlineKeyboardButton("Not Now\U0001f642\u200d\u2194\ufe0f", callback_data='not_now')

    new_keyboard.add(absolutely_button, notnow_button)
    bot.send_message(user_id, "*Do you want to restart the game?*", parse_mode="Markdown", reply_markup=new_keyboard)


@bot.callback_query_handler(func=lambda call: call.data == "absolutely" or call.data == "not_now")
def restart_game(call: CallbackQuery):
    user_id = call.message.chat.id
    if call.data == 'absolutely':   
        # send message of command so the function can start
        start_game(call.message)  
    elif call.data == 'not_now':
        bot.send_message(user_id, "It's been a blast\U0001f4a5Bet you've got some new fun facts now!\n\n*See you next time*\U0001f44b", parse_mode="Markdown")

    bot.answer_callback_query(call.id)

# Generates session_id
def generate_session_id(message):
    characters = string.ascii_letters + string.digits
    token = "".join(random.choice(characters) for i in range(7))
    return token


# Generates random question and answer
def get_question(ques_session):
    count = ques_session.query(func.count(triviaques.id)).scalar()
    random_id = random.randint(0, count - 1)
    random_set = ques_session.query(triviaques).filter(triviaques.id == random_id).first()
    print(random_set)
    return random_set


# help command
@bot.message_handler(commands=["help"])
def help(message):
    user_id = message.chat.id

    help_keyboard = InlineKeyboardMarkup()
    help_bot = InlineKeyboardButton("Help Bot", url="https://t.me/gen_assist_bot")
    help_keyboard.add(help_bot)
    
    bot.send_message(user_id, "Tap on the button below to access the Help Bot", reply_markup=help_keyboard)


# reset command
@bot.message_handler(commands=["reset"])
def reset(message):
    user_id = message.chat.id
    game_session.query(Player_1).filter_by(chat_id=user_id).delete()
    game_session.query(Player_2).filter_by(chat_id=user_id).delete()
    game_session.query(GameSession).filter_by(player1_id=user_id).delete()
    game_session.query(GameSession).filter_by(player2_id=user_id).delete()
    ques_session.query(QuestionSession).filter_by(user_id=user_id).delete()
    game_session.commit()
    ques_session.commit()
    bot.send_message(user_id, "Game Reset Successfully\nGo to the menu to start a new game")


if __name__ == "__main__":
    bot.infinity_polling()