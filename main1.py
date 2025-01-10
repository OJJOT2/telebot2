import telebot
import http.client
import json
import time
from datetime import datetime
from flask import Flask
import threading
import pytz
import os
import sys

app = Flask('')

@app.route('/')
def home():
    return "Bot is running!"

def run():
    app.run(host='0.0.0.0', port=8080)

def start_thread(target):
    thread = threading.Thread(target=target, daemon=True)
    thread.start()
    return thread

def restart_bot():
    """Restarts the bot if an error is encountered (for instance, a duplicate instance error)."""
    print("Bot instance error detected. Restarting...")
    python = sys.executable
    os.execl(python, python, *sys.argv)

start_thread(run)

TOKEN = "7577429699:AAFDna2WDWzLRhQehvVUyjVqIwyPd7-Ix7A"
bot = telebot.TeleBot(TOKEN)
conn = http.client.HTTPSConnection("udemy-paid-courses-for-free-api.p.rapidapi.com")
headers = {
    'x-rapidapi-key': "9b440ee187msh29987a6568674e8p1ac199jsnf546c2c45e5a",
    'x-rapidapi-host': "udemy-paid-courses-for-free-api.p.rapidapi.com"
}
autosend_time = ""

user_reminders = {}

def courses_list(courses_data):
    courses = []
    for course in courses_data.get("courses", []):
        title = course.get("name")
        title = f"[ {title} ]"
        url = course.get("url")
        category = course.get("category")
        price_b = course.get("actual_price_usd")
        price_a = course.get("sale_price_usd")
        sale_end = calculate_remaining_time(course.get("sale_end"))
        description = course.get("description")
        courses.append(f"{title}\ncategory: {category}\ndescription: {description[:150]}...\nactual price: {price_b}$\nSale price: {price_a}$\n Sale end: {sale_end}\n[Link to course] ({url})\n------\n")

    return courses

def calculate_remaining_time(sale_end: str):
    sale_end_format = "%Y-%m-%dT%H:%M:%S"
    sale_end_datetime = datetime.strptime(sale_end, sale_end_format)
    current_datetime = datetime.now()
    time_difference = sale_end_datetime - current_datetime

    days_remaining = time_difference.days
    hours_remaining = time_difference.seconds // 3600
    minutes_remaining = (time_difference.seconds % 3600) // 60

    remaining_time_parts = []

    if days_remaining > 0:
        remaining_time_parts.append(f"{days_remaining} days")
    if hours_remaining > 0:
        remaining_time_parts.append(f"{hours_remaining} hours")
    if minutes_remaining > 0:
        remaining_time_parts.append(f"{minutes_remaining} minutes")

    remaining_time = " ".join(remaining_time_parts)
    return remaining_time

def get_formatted_date():
    current_time = datetime.now(pytz.timezone('Africa/Cairo'))
    return current_time.strftime("%d/%m/%y (%I:%M %p)")

def get_udemy_free_courses(query="python"):
    conn.request("GET", f"/rapidapi/courses/search?page=1&page_size=10&query={query}", headers=headers)
    res = conn.getresponse()
    print(res)
    data = res.read()
    courses_data = json.loads(data.decode("utf-8"))
    courses = []
    return courses_list(courses_data)

# Function to read allowed chat IDs from the external file
def load_allowed_chat_ids(filename="allowed_chat_ids.txt"):
    try:
        with open(filename, "r") as file:
            # Read all lines, strip whitespace, and convert to a set of integers
            return set(int(line.strip()) for line in file if line.strip().isdigit())
    except FileNotFoundError:
        print(f"Error: {filename} not found. No users are authorized.")
        return set()  # Return an empty set if the file is missing
    except Exception as e:
        print(f"Error reading {filename}: {e}")
        return set()

# Function to check if a user is authorized
def auth_user(message):
    user_id = message.from_user.id
    allowed_chat_ids = load_allowed_chat_ids()  # Load IDs from the file
    return [user_id in allowed_chat_ids, user_id]

# Telegram Command: /add_chat_id (for admin to add new IDs dynamically)
@bot.message_handler(commands=['add_chat_id'])
def add_chat_id(message):
    try:
        if auth_user(message)[0]:  # Only admins can add new IDs
            new_chat_id = int(message.text.replace("/add_chat_id", "").strip())
            with open("allowed_chat_ids.txt", "a") as file:
                file.write(str(new_chat_id))
                file.write("\n")
            bot.reply_to(message, f"Chat ID {new_chat_id} has been added to the allowed list.")
        else:
            bot.reply_to(message, f"Unauthorized access.\nuser: {auth_user(message)[1]}")
    except ValueError:
        bot.reply_to(message, "Invalid chat ID. Please provide a valid integer.")
    except Exception as e:
        bot.reply_to(message, f"Error: {e}")

# Telegram Command: /list_chat_ids (for admin to view allowed IDs)
@bot.message_handler(commands=['list_chat_ids'])
def list_chat_ids(message):
    if auth_user(message)[0]:  # Only admins can view the list
        allowed_chat_ids = load_allowed_chat_ids()
        if allowed_chat_ids:
            bot.reply_to(message, f"Allowed Chat IDs:\n{', '.join(map(str, allowed_chat_ids))}")
        else:
            bot.reply_to(message, "No chat IDs are currently allowed.")
    else:
        bot.reply_to(message, f"Unauthorized access.\nuser: {auth_user(message)[1]}")

def get_courses():
    try:
        conn.request("GET", "/rapidapi/courses/?page=1&page_size=10", headers=headers)
        res = conn.getresponse()
        data = res.read()
        print(data)
        courses_data = json.loads(data.decode("utf-8"))
        print(courses_data)
        courses = []
        return courses_list(courses_data)

    except Exception as e:
        print(f"Error: {e}")
        return ["error"]

@bot.message_handler(commands=['courses'])
def courses(message):
    if auth_user(message)[0]:
        courses = get_courses()
        bot.reply_to(message, f"Free Courses for Today {get_formatted_date()} !\n\n" + "\n\n".join(courses[:5]))
        bot.reply_to(message, f"Free Courses for Today {get_formatted_date()} !\n\n" + "\n\n".join(courses[5:]))

@bot.message_handler(commands=['search_courses'])
def search_courses(message):
    if auth_user(message)[0]:
        query = message.text.replace("/search_courses", "").strip()
        query = str(query).replace(" ", "%20")
        if query:
            courses = get_udemy_free_courses(query)
            if courses:
                bot.reply_to(message, f"Here are some free courses on {query} For Today ({get_formatted_date()}):\n\n" + "\n\n".join(courses[:5]))
                bot.reply_to(message,f"Here are some free courses on {query} For Today ({get_formatted_date()}):\n\n" + "\n\n".join(courses[5:]))
            else:
                bot.reply_to(message, "No courses found with that tag. Please try another tag.")
        else:
            bot.reply_to(message, "Please provide a tag to search for, e.g., /search_courses python")
    else:
        bot.reply_to(message, f"unautorized access?\nuser: {auth_user(message)[1]}")

def send_daily_courses():
    while True:
        current_time = datetime.now(pytz.timezone('Africa/Cairo')).strftime("%H:%M")
        for user_id, reminder_time in user_reminders.items():
            if current_time == reminder_time:
                try:
                    courses = get_courses()
                    if courses:
                        bot.send_message(
                            user_id,
                            f"Here are today's free Udemy courses ({get_formatted_date()}):\n\n" + "\n\n".join(courses[:5])
                        )
                        if len(courses) > 5:
                            bot.send_message(
                                user_id,
                                "\n\n".join(courses[5:])
                            )
                except Exception as e:
                    print(f"Error sending courses to user {user_id}: {e}")
        time.sleep(60)  # Check every minute
   
@bot.message_handler(commands=['set_course_reminder'])
def set_course_reminder(message):
    try:
        time_str = message.text.replace("/set_course_reminder", "").strip()
        # Validate time format
        datetime.strptime(time_str, "%H:%M")
        user_id = message.chat.id
        user_reminders[user_id] = time_str
        bot.reply_to(
            message,
            f"Your daily reminder has been set to {time_str}. You'll receive free course updates at this time daily."
        )
    except ValueError:
        bot.reply_to(message, "Invalid time format. Please enter the time in HH:MM format (24-hour clock).")

@bot.message_handler(commands=['cancel_course_reminder'])
def cancel_course_reminder(message):
    user_id = message.chat.id
    if user_id in user_reminders:
        del user_reminders[user_id]
        bot.reply_to(message, "Your course reminder has been cancelled.")
    else:
        bot.reply_to(message, "You don't have a reminder set.")

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    help_text = (
        "Hello! I can help you find free Udemy courses. Here are the available commands:\n\n"
        "/courses - Get a list of free courses\n"
        "/search_courses <tag> - Search for free courses by tag (e.g., python, data science)\n"
        "/send_daily_courses - Get today's free courses manually\n"
        "/set_course_reminder <time> - Set a daily reminder for free courses (e.g., 08:00)\n"
        "/cancel_course_reminder - Cancel your daily reminder"
    )
    bot.reply_to(message, help_text)

# Thread to monitor and restart the bot if it gets duplicated
def check_duplicate_instance():
    try:
        bot.polling(none_stop=True)
    except Exception as e:
        print(f"Error occurred: {e}")
        restart_bot()

start_thread(check_duplicate_instance)
bot.polling(none_stop=True)
