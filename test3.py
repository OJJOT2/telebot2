import telebot
import http.client
import json
import threading
import time
from datetime import datetime
from flask import Flask
import threading

# Create a Flask app
app = Flask('')

@app.route('/')
def home():
    return "Bot is running!"

def run():
    app.run(host='0.0.0.0', port=8080)

# Start the Flask server in a separate thread
threading.Thread(target=run, daemon=True).start()

# Set up the bot with your token
TOKEN = "7577429699:AAFDna2WDWzLRhQehvVUyjVqIwyPd7-Ix7A"  # Replace with your bot's token
bot = telebot.TeleBot(TOKEN)

# Udemy API details
conn = http.client.HTTPSConnection("udemy-paid-courses-for-free-api.p.rapidapi.com")
headers = {
    'x-rapidapi-key': "9b440ee187msh29987a6568674e8p1ac199jsnf546c2c45e5a",
    'x-rapidapi-host': "udemy-paid-courses-for-free-api.p.rapidapi.com"
}

# Store reminders for users
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
    # Define the format of the sale end date
    sale_end_format = "%Y-%m-%dT%H:%M:%S"

    # Convert the sale end date string to a datetime object
    sale_end_datetime = datetime.strptime(sale_end, sale_end_format)

    # Get the current time
    current_datetime = datetime.now()

    # Calculate the time difference between the sale end and current time
    time_difference = sale_end_datetime - current_datetime

    # Get the number of days, hours, and minutes remaining
    days_remaining = time_difference.days
    hours_remaining = time_difference.seconds // 3600
    minutes_remaining = (time_difference.seconds % 3600) // 60

    # Create the remaining time string, only including non-zero values
    remaining_time_parts = []

    if days_remaining > 0:
        remaining_time_parts.append(f"{days_remaining} days")
    if hours_remaining > 0:
        remaining_time_parts.append(f"{hours_remaining} hours")
    if minutes_remaining > 0:
        remaining_time_parts.append(f"{minutes_remaining} minutes")

    # Join the parts into a single string
    remaining_time = " ".join(remaining_time_parts)

    return remaining_time

def get_formatted_date():
    current_time = datetime.now()
    return current_time.strftime("%d/%m/%y (%I:%M %p)")
# Function to get Udemy courses based on search query
def get_udemy_free_courses(query="python"):

        # Make the API request to get free courses based on the query
        conn.request("GET", f"/rapidapi/courses/search?page=1&page_size=10&query={query}", headers=headers)

        # Get the response
        res = conn.getresponse()
        print(res)
        data = res.read()

        # Decode and load JSON response
        courses_data = json.loads(data.decode("utf-8"))
        courses = []
        courses_list(courses_data)
        # Process the courses and format them
        return courses_list(courses_data)

def auth_user(message):
    # Access the user ID from the 'from_user' attribute
    user_id = message.from_user['id'] if isinstance(message.from_user, dict) else message.from_user.id

    # Check if the user ID matches
    if user_id == 5075265669:
        return True
    else:
        return False

def get_courses():
    try:
        # Make the API request to get free courses based on the query
        conn.request("GET", "/rapidapi/courses/?page=1&page_size=10", headers=headers)


        # Get the response
        res = conn.getresponse()
        data = res.read()
        print(data)
        # Decode and load JSON response
        courses_data = json.loads(data.decode("utf-8"))
        print(courses_data)
        courses = []

        # Process the courses and format them

        return courses_list(courses_data)

    except Exception as e:
        print(f"Error: {e}")
        return ["error"]

@bot.message_handler(commands=['courses'])
def courses(message):
    if auth_user(message):
        courses = get_courses()
        bot.reply_to(message, f"Free Courses for Today {get_formatted_date()} !\n\n" + "\n\n".join(courses[:5]))
        bot.reply_to(message, f"Free Courses for Today {get_formatted_date()} !\n\n" + "\n\n".join(courses[5:]))
    else:
        bot.reply_to(message,"Unautorized access?")


# Command to fetch courses by tag
@bot.message_handler(commands=['search_courses'])
def search_courses(message):
    if auth_user(message):
        query = message.text.replace("/search_courses", "").strip()
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
        bot.reply_to(message, "unautorized access?")

# Command to send daily courses
def send_daily_courses():
    while True:
        # Wait until it's midnight to send the daily courses
        current_time = datetime.now().strftime("%H:%M")
        if current_time == "00:00":
            courses = get_udemy_free_courses()
            for user_id in user_reminders:
                bot.send_message(user_id, f"Here are today's free Udemy courses {get_formatted_date()}:\n\n" + "\n\n".join(courses[:5]))
                bot.send_message(user_id, "".join(courses[5:]))
        time.sleep(60)  # Check the time every minute


# Command to send courses manually
@bot.message_handler(commands=['send_daily_courses'])
def handle_send_daily_courses(message):
    courses = get_udemy_free_courses()
    bot.reply_to(message, "Here are today's free Udemy courses:\n\n" + "\n\n".join(courses[:]))


# Command to set a course reminder
@bot.message_handler(commands=['set_course_reminder'])
def set_course_reminder(message):
    try:
        time_str = message.text.replace("/set_course_reminder", "").strip()
        user_id = message.chat.id
        user_reminders[user_id] = time_str
        bot.reply_to(message,
                     f"Your daily reminder has been set to {time_str}. You'll receive free course updates at this time daily.")
    except Exception as e:
        bot.reply_to(message, "Invalid time format. Please enter the time in HH:MM format.")


# Command to cancel a reminder
@bot.message_handler(commands=['cancel_course_reminder'])
def cancel_course_reminder(message):
    user_id = message.chat.id
    if user_id in user_reminders:
        del user_reminders[user_id]
        bot.reply_to(message, "Your course reminder has been cancelled.")
    else:
        bot.reply_to(message, "You don't have a reminder set.")


# Command to show help information
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


# Start the bot in a separate thread for daily reminders
threading.Thread(target=send_daily_courses, daemon=True).start()

# Start the bot
bot.polling(none_stop=True)
