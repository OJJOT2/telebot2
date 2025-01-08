import telebot
import http.client
import json
from datetime import datetime
import pytz
from apscheduler.schedulers.background import BackgroundScheduler

# Bot token and API keys
TOKEN = "7577429699:AAFDna2WDWzLRhQehvVUyjVqIwyPd7-Ix7A"
bot = telebot.TeleBot(TOKEN)
conn = http.client.HTTPSConnection("udemy-paid-courses-for-free-api.p.rapidapi.com")
headers = {
    'x-rapidapi-key': "9b440ee187msh29987a6568674e8p1ac199jsnf546c2c45e5a",
    'x-rapidapi-host': "udemy-paid-courses-for-free-api.p.rapidapi.com"
}

user_reminders = {}  # Stores user reminders


def courses_list(courses_data):
    courses = []
    for course in courses_data.get("courses", []):
        title = f"[ {course.get('name')} ]"
        url = course.get("url")
        category = course.get("category")
        price_b = course.get("actual_price_usd")
        price_a = course.get("sale_price_usd")
        sale_end = calculate_remaining_time(course.get("sale_end"))
        description = course.get("description")
        courses.append(
            f"{title}\ncategory: {category}\ndescription: {description[:150]}...\n"
            f"actual price: {price_b}$\nSale price: {price_a}$\nSale end: {sale_end}\n"
            f"[Link to course] ({url})\n------\n"
        )
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

    return " ".join(remaining_time_parts)


def get_formatted_date():
    current_time = datetime.now(pytz.timezone('Africa/Cairo'))
    return current_time.strftime("%d/%m/%y (%I:%M %p)")


def get_udemy_free_courses(query="python"):
    conn.request("GET", f"/rapidapi/courses/search?page=1&page_size=10&query={query}", headers=headers)
    res = conn.getresponse()
    data = res.read()
    courses_data = json.loads(data.decode("utf-8"))
    return courses_list(courses_data)


def get_courses():
    try:
        conn.request("GET", "/rapidapi/courses/?page=1&page_size=10", headers=headers)
        res = conn.getresponse()
        data = res.read()
        courses_data = json.loads(data.decode("utf-8"))
        return courses_list(courses_data)
    except Exception as e:
        print(f"Error: {e}")
        return ["Error retrieving courses"]


def auth_user(message):
    user_id = message.from_user.id
    # Change this to the authorized user ID
    if user_id == 5075265669:
        return True
    else:
        return False


@bot.message_handler(commands=['courses'])
def courses(message):
    if auth_user(message):
        courses = get_courses()
        bot.reply_to(message, f"Free Courses for Today {get_formatted_date()} !\n\n" + "\n\n".join(courses[:5]))
        if len(courses) > 5:
            bot.reply_to(message, "\n\n".join(courses[5:]))
    else:
        bot.reply_to(message, "Unauthorized access")


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
        bot.reply_to(message, "Unauthorized access")


@bot.message_handler(commands=['set_course_reminder'])
def set_course_reminder(message):
    try:
        time_str = message.text.replace("/set_course_reminder", "").strip()
        datetime.strptime(time_str, "%H:%M")  # Validate time format
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
        "/set_course_reminder <time> - Set a daily reminder for free courses (e.g., 08:00)\n"
        "/cancel_course_reminder - Cancel your daily reminder\n"
    )
    bot.reply_to(message, help_text)


# APScheduler for daily reminders
scheduler = BackgroundScheduler()

def send_daily_courses():
    current_time = datetime.now(pytz.timezone('Africa/Cairo')).strftime("%H:%M")
    for user_id, reminder_time in user_reminders.items():
        if current_time == reminder_time:
            try:
                courses = get_courses()
                bot.send_message(user_id, f"Here are today's free Udemy courses ({get_formatted_date()}):\n\n" + "\n\n".join(courses[:5]))
                if len(courses) > 5:
                    bot.send_message(user_id, "\n\n".join(courses[5:]))
            except Exception as e:
                print(f"Error sending courses to user {user_id}: {e}")

scheduler.add_job(send_daily_courses, 'interval', minutes=1)
scheduler.start()

# Remove webhook and start polling
bot.remove_webhook()
bot.polling(none_stop=True)
