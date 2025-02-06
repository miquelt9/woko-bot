from telegram import Update
from telegram import Bot
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, Updater, filters, MessageHandler, CallbackContext
import time
import string
from datetime import datetime
from telegram.ext import JobQueue
import requests
import re
from bs4 import BeautifulSoup

job_id = {}
users = {}
woko_links = set()
woko_url = "https://www.woko.ch/"
free_rooms_url = "https://www.woko.ch/en/zimmer-in-zuerich"

def set_job_id(job):
    job_id[0] = job

def get_job_id():
    return job_id[0]

def extract_email(html):
    # Use regular expression to find email address
    email_match = re.search(r'href="mailto:([^"]+)"', html)
    if email_match:
        email_address = email_match.group(1)
    else:
        email_address = html
    
    return email_address

def parse_sublet_details(html):
    soup = BeautifulSoup(html, 'html.parser')
    
    try:
        # Retrieve info
        lines_info = [7, 15, 23]  # Dates, place, rent price
        info_table = soup.find('div', class_='inserat-details').find_all('table')[0]
        lines = str(info_table).splitlines()
        specific_lines = []
        for line_number in lines_info:
            if 1 <= line_number <= len(lines):
                specific_lines.append(lines[line_number - 1].strip())
            
        # Retrieve contact
        lines_contact = [7, 15, 24]  # Name, phone (or email), email
        contact_table = soup.find('div', class_='inserat-details').find_all('table')[1]
        lines = str(contact_table).splitlines()
        for line_number in lines_contact:
            if 1 <= line_number <= len(lines):
                specific_lines.append(extract_email(lines[line_number - 1].strip()))

    except AttributeError:
        return None
    
    return specific_lines


def get_room_info(room_link):
    # print(room_link)
    # Make the curl request and store the response
    room_response = requests.get(room_link)
    room_soup = BeautifulSoup(room_response.text, 'html.parser')
    content_section = room_soup.find('div', class_='content-section')
    # print(str(content_section))

    details = parse_sublet_details(content_section.prettify())

    # print(details)

    return details

def read_files():
    global TOKEN
    try:
        TOKEN = open('token.txt').read().strip()
    except Exception as e:
        print("ERROR: Token was not read properly")

    global BASE_URL
    BASE_URL = f'https://api.telegram.org/bot{TOKEN}'


def is_any_user_active(users):
  for user_id, is_active in users.items():
    if is_active:
      return True
  return False


def new_user(user):
    """
    Check if a user already exists, otherwise it creates it with default params.
    """
    if user.id not in users:
        users[user.id] = False

async def check_then_send_message(context, user, message, notification=None, user_id=None):
    if user_id == None:
        try:
            await context.bot.send_message(user.id, str(message), disable_notification=notification)
        except Exception as e:
            print("Error when sending message")
    else:
        try:
            await context.bot.send_message(user_id, str(message), disable_notification=notification)
        except Exception as e:
            print("Error when sending message")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    new_user(user)
    message = update.message
    print("Start " + str(user.id))

    name = user.first_name
    await check_then_send_message(context, user, 'Welcome ' + name + '!')
    await check_then_send_message(context, user, 'Write /help to list the available commands')

    if (users[user.id] == False):
        if (is_any_user_active(users) == False): # This is the first user willing to receive updates
            print("Activate run repeating")
            job_id = context.job_queue.run_repeating(send_woko_updates, interval=300, first=0)  # first=0 means no initial delay
            set_job_id(job_id)
            # print(job_id)
        users[user.id] = True

async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    new_user(user)
    message = update.message

    name = user.first_name
    await check_then_send_message(context, user, 'Stopping sending updates')

    if (users[user.id] == True):
        users[user.id] = False
        if (is_any_user_active(users) == False): # There's no users willing to receive updates
            print("Deactivated run repeating")
            job_id = get_job_id()
            # print(job_id.id)
            context.job_queue.scheduler.remove_job(job_id.id)


async def send_woko_updates_test(context: CallbackContext):
    for user in users:
        if users[user] == True:
            await check_then_send_message(context, None, "A new room is available:", user_id=user)

async def send_woko_updates(context: CallbackContext):

# Make the curl request and store the response
    response = requests.get(free_rooms_url)

# Check for successful response
    if response.status_code == 200:
    # Get the HTML content from the response
        html_content = response.text
        soup = BeautifulSoup(html_content, 'html.parser')
        content_box = soup.find('div', class_='content-box')

        mini_soup = BeautifulSoup(content_box.prettify(), 'html.parser')
        # Find all anchor tags (a)
        links = mini_soup.find_all('a')

        # Loop through each link
        for link in links:
        # Check if the link has an href attribute
            if link not in woko_links and link.has_attr('href'):
                href = woko_url + link['href']
                woko_links.add(link)
                room_details = get_room_info(href)
                room_details_message = href + "\n" + "\n".join(room_details)

                for user in users:
                    if users[user] == True:
                        await check_then_send_message(context, None, "A new room is available:", user_id=user)
                        await check_then_send_message(context, None, room_details_message, user_id=user)
    else:
        print("Error fetching the webpage content!")


async def get_all(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:

    new_user(update.effective_user)
    message = update.message
    user = update.effective_user
# Make the curl request and store the response
    response = requests.get(free_rooms_url)

    # Check for successful response
    if response.status_code == 200:
    # Get the HTML content from the response
        html_content = response.text
        soup = BeautifulSoup(html_content, 'html.parser')
        content_box = soup.find('div', class_='content-box')

        mini_soup = BeautifulSoup(content_box.prettify(), 'html.parser')
        # Find all anchor tags (a)
        links = mini_soup.find_all('a')

        # Loop through each link
        for link in links:
        # Check if the link has an href attribute
            if link.has_attr('href'):
                href = woko_url + link['href']
                woko_links.add(href)
                room_details = get_room_info(href)
                room_details_message = href + "\n" + "\n".join(room_details)

                await check_then_send_message(context, user, room_details_message)
    else:
        print("Error fetching the webpage content!")



async def ping(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    new_user(update.effective_user)
    message = update.message
    user = update.effective_user

    response_time = float(time.time()) - message.date.timestamp()

    await check_then_send_message(context, user, 'Still awake, time to reply: ' + str(int(response_time*1000)) + ' ms')

async def help(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    new_user(update.effective_user)
    message = update.message
    user = update.effective_user

    await check_then_send_message(context, user, "Unfortunately this bot doesn't have more commands a part from:\n> /start (new rooms will be send as message)\n> /stop (the bot won't send messages to you)\n> /help (displays this messsage)\n> /get_all (ensure that the robot works by retrieving all current offers)\n> /ping\n\nHowever it'll message you every time a new apartment is published in Woko!")

async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message:
        return

    message = update.message
    # DO Nothing when receving any message that's not a command

def main():


    read_files()

    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("ping", ping))
    app.add_handler(CommandHandler("help", help))
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("stop", stop))
    app.add_handler(CommandHandler("get_all", get_all))

    app.run_polling()

if __name__ == '__main__':
    main()
