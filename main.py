import telebot
import http.client
import json
import time
from datetime import datetime
from flask import Flask
import threading
import pytz

# Bot Token and API Configurations
TOKEN = "7577429699:AAFDna2WDWzLRhQehvVUyjVqIwyPd7-Ix7A"
bot = telebot.TeleBot(TOKEN)
conn = http.client.HTTPSConnection("udemy-paid-courses-for-free-api.p.rapidapi.com")
headers = {
    'x-rapidapi-key': "9b440ee187msh29987a6568674e8p1ac199jsnf546c2c45e5a",
    'x-rapidapi-host': "udemy-paid-courses-for-free-api.p.rapidapi.com"
}

# User reminders for daily notifications
user_reminders = {}

# Helper function to format the course list
def courses_list(courses_data):
    courses = []
    for course in courses_data.get("courses", []):
        title = f"[{course.get('name')}]"
        url = course.get("url")
        category = course.get("category")
        price_b = course.get("actual_price_usd", "N/A")
        price_a = course.get("sale_price_usd", "N/A")
        sale_end = calculate_remaining_time(course.get("sale_end", ""))
        description = course.get("description", "")
        courses.append(f"{title}\nCategory: {category}\nDescription: {description[:150]}...\nActual Price: {price_b}$\nSale Price: {price_a}$\nSale Ends: {sale_end}\n[Link to Course]({url})\n------")
    return courses

# Helper function to calculate remaining sale time
def calculate_remaining_time(sale_end):
    try:
        sale_end_format = "%Y-%m-%dT%H:%M:%S"
        sale_end_datetime = datetime.strptime(sale_end, sale_end_format)
        current_datetime = datetime.now()
        time_difference = sale_end_datetime - current_datetime
        days_remaining = time_difference.days
        hours_remaining = time_difference.seconds // 3600
        minutes_remaining = (time_difference.seconds % 3600) // 60
        remaining_time = []
        if days_remaining > 0:
            remaining_time.append(f"{days_remaining} days")
        if hours_remaining > 0:
            remaining_time.append(f"{hours_remaining} hours")
        if minutes_remaining > 0:
            remaining_time.append(f"{minutes_remaining} minutes")
        return " ".join(remaining_time)
    except Exception:
        return "Unknown"

# Helper function to get the current formatted date
def get_formatted_date():
    current_time = datetime.now(pytz.timezone('Africa/Cairo'))
    return current_time.strftime("%d/%m/%y (%I:%M %p)")

# Function to fetch free Udemy courses
def get_udemy_free_courses(query="python"):
    try:
        conn.request("GET", f"/rapidapi/courses/search?page=1&page_size=10&query={query}", headers=headers)
        res = conn.getresponse()
        print(f"Status: {res.status}, Reason: {res.reason}")  # Debugging
        data = res.read()
        courses_data = json.loads(data.decode("utf-8"))
        return courses_list(courses_data)
    except Exception as e:
        print(f"Error fetching courses: {e}")
        return ["Error retrieving courses"]

# Authorization check
def auth_user(message):
    user_id = message.from_user.id
    return user_id == 5075265669  # Replace with your authorized user ID

# Telegram Command: /courses
@bot.message_handler(commands=['courses'])
def courses(message):
    if auth_user(message):
        courses = get_udemy_free_courses()
        if courses:
            bot.reply_to(message, f"Free Courses for Today {get_formatted_date()} !\n\n" + "\n\n".join(courses[:5]))
            if len(courses) > 5:
                bot.reply_to(message, "\n\n".join(courses[5:]))
        else:
            bot.reply_to(message, "No courses found today.")
    else:
        bot.reply_to(message, "Unauthorized access.")

# Telegram Command: /search_courses
@bot.message_handler(commands=['search_courses'])
def search_courses(message):
    if auth_user(message):
        query = message.text.replace("/search_courses", "").strip()
        if query:
            courses = get_udemy_free_courses(query)
            if courses:
                bot.reply_to(message, f"Here are some free courses on {query} For Today ({get_formatted_date()}):\n\n" + "\n\n".join(courses[:5]))
                if len(courses) > 5:
                    bot.reply_to(message, "\n\n".join(courses[5:]))
            else:
                bot.reply_to(message, "No courses found with that tag. Please try another tag.")
        else:
            bot.reply_to(message, "Please provide a tag to search for, e.g., /search_courses python")
    else:
        bot.reply_to(message, "Unauthorized access.")

# Background job to send daily courses
def send_daily_courses():
    while True:
        current_time = datetime.now(pytz.timezone('Africa/Cairo')).strftime("%H:%M")
        for user_id, reminder_time in user_reminders.items():
            if current_time == reminder_time:
                try:
                    courses = get_udemy_free_courses()
                    if courses:
                        bot.send_message(
                            user_id,
                            f"Here are today's free Udemy courses ({get_formatted_date()}):\n\n" + "\n\n".join(courses[:5])
                        )
                        if len(courses) > 5:
                            bot.send_message(user_id, "\n\n".join(courses[5:]))
                except Exception as e:
                    print(f"Error sending courses to user {user_id}: {e}")
        time.sleep(60)  # Check every minute

# Telegram Command: /set_course_reminder
@bot.message_handler(commands=['set_course_reminder'])
def set_course_reminder(message):
    try:
        time_str = message.text.replace("/set_course_reminder", "").strip()
        datetime.strptime(time_str, "%H:%M")  # Validate time format
        user_id = message.chat.id
        user_reminders[user_id] = time_str
        bot.reply_to(message, f"Your daily reminder has been set to {time_str}. You'll receive free course updates at this time daily.")
    except ValueError:
        bot.reply_to(message, "Invalid time format. Please enter the time in HH:MM format (24-hour clock).")

# Telegram Command: /cancel_course_reminder
@bot.message_handler(commands=['cancel_course_reminder'])
def cancel_course_reminder(message):
    user_id = message.chat.id
    if user_id in user_reminders:
        del user_reminders[user_id]
        bot.reply_to(message, "Your course reminder has been cancelled.")
    else:
        bot.reply_to(message, "You don't have a reminder set.")

# Telegram Command: /start or /help
@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    help_text = (
        "Hello! I can help you find free Udemy courses. Here are the available commands:\n\n"
        "/courses - Get a list of free courses\n"
        "/search_courses <tag> - Search for free courses by tag (e.g., python, data science)\n"
        "/set_course_reminder <time> - Set a daily reminder for free courses (e.g., 08:00)\n"
        "/cancel_course_reminder - Cancel your daily reminder"
    )
    bot.reply_to(message, help_text)

# Start the daily reminder thread
threading.Thread(target=send_daily_courses, daemon=True).start()

# Start polling
bot.polling(none_stop=True)
