import telebot,types
bot=telebot.TeleBot('')
import calendar

import requests
from datetime import datetime, timedelta
import json

def date_convert(date):
    try:
        intdate = datetime.strptime(date, "%Y-%m-%dT%H:%M:%S")
        published = datetime.strftime(intdate, "%d.%m.%Y")
    except Exception as e:
        print(e)
    return published

def connect(url):
    r = None
    try:
        r = requests.get(url, timeout=10)
        print('Connection done well: ', r.status_code)
    except Exception as e:
        print('Что-то не получилось: ')
        print(e)
    return r


value=431

@bot.message_handler(commands=['start',])
def data (message):
    mess = f"Привет, {message.from_user.first_name}! С помощью этого бота можно быстро узнать курс доллара или евро НБ РБ."
    bot.send_message(message.chat.id, mess, parse_mode='html')
    markup = telebot.types.InlineKeyboardMarkup ()#(resize_keyboard=True, row_width=2)
    Euro = telebot.types.InlineKeyboardButton('Euro',callback_data='euro')
    USD = telebot.types.InlineKeyboardButton('USD',callback_data='usd')
    markup.add (Euro,USD)
    bot.send_message(message.chat.id, 'Пожалуйста, выберите валюту', reply_markup=markup)



@bot.callback_query_handler(func=lambda call: True)
def answer_process_calendar_selection (call):
    global value
    if call.data == 'usd' or call.data == 'euro':

        if call.data == 'usd':
            value = 431
            bot.answer_callback_query(callback_query_id=call.id)
        elif call.data == 'euro':
            value = 451
            bot.answer_callback_query(callback_query_id=call.id)
        markup1 = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
        Tod = telebot.types.KeyboardButton('/Сегодня')
        Calen = telebot.types.KeyboardButton('/Календарь')
        markup1.add(Tod, Calen)
        bot.send_message(call.message.chat.id, 'Курс на сегодня или выбрать дату?', reply_markup=markup1)

    else:
        ret_data = (False, None)
        (action, year, month, day) = separate_callback_data(call.data)
        curr = datetime(int(year), int(month), 1)
        if action == "IGNORE":
            bot.answer_callback_query(callback_query_id=call.id)
        elif action == "DAY":
            bot.edit_message_text(text=call.message.text,
                                  chat_id=call.message.chat.id,
                                  message_id=call.message.message_id
                                  )
            ret_data = True, datetime(int(year), int(month), int(day))
        elif action == "PREV-MONTH":
            pre = curr - timedelta(days=1)
            bot.edit_message_text(text=call.message.text,
                                  chat_id=call.message.chat.id,
                                  message_id=call.message.message_id,
                                  reply_markup=create_calendar(call.message, int(pre.year), int(pre.month)))
        elif action == "NEXT-MONTH":
            ne = curr + timedelta(days=31)
            bot.edit_message_text(text=call.message.text,
                                  chat_id=call.message.chat.id,
                                  message_id=call.message.message_id,
                                  reply_markup=create_calendar(call.message, int(ne.year), int(ne.month)))
        else:
            bot.answer_callback_query(callback_query_id=call.id, text="Something went wrong!")
        selected, date = ret_data
        if selected:

            bot.send_message(call.message.chat.id, text='Курс',

                             reply_markup=telebot.types.ReplyKeyboardRemove())

            urldate = date.strftime("%Y-%m-%d")
            try:
                a = connect(f"https://www.nbrb.by/api/exrates/rates/{value}?ondate={urldate}&periodicity=0").json()
                publ = date_convert(a['Date'])
                mess = f"{a['Cur_Abbreviation']} на {publ}: \n{a['Cur_OfficialRate']}"
                bot.send_message(call.message.chat.id, mess, parse_mode='html')
                bot.answer_callback_query(callback_query_id=call.id)
            except Exception as e:
                bot.send_message(call.message.chat.id, "Нет сведений", parse_mode='html')


def create_callback_data(action,year,month,day):
    """ Create the callback data associated to each button"""
    return ";".join([action,str(year),str(month),str(day)])

def separate_callback_data(data):
    """ Separate the callback data"""
    return data.split(";")


def create_calendar(message,year=None,month=None):
    now = datetime.now()
    if year == None:
        year = now.year
    if month == None:
        month = now.month
    data_ignore = create_callback_data("IGNORE", year, month, 0)
    keyboard = []
    row=[]
    row.append(telebot.types.InlineKeyboardButton(calendar.month_name[month]+" "+str(year),callback_data=data_ignore))
    keyboard.append(row)
    row=[]
    for day in ["Mo","Tu","We","Th","Fr","Sa","Su"]:
        row.append(telebot.types.InlineKeyboardButton(day,callback_data=data_ignore))

    keyboard.append(row)
    my_calendar = calendar.monthcalendar(year, month)
    for week in my_calendar:
        row=[]
        for day in week:
            if(day==0):
                row.append(telebot.types.InlineKeyboardButton(" ",callback_data=data_ignore))
            else:
                row.append(telebot.types.InlineKeyboardButton(str(day),callback_data=create_callback_data("DAY",year,month,day)))
        keyboard.append(row)
    row=[]
    row.append(telebot.types.InlineKeyboardButton("<",callback_data=create_callback_data("PREV-MONTH",year,month,day)))
    row.append(telebot.types.InlineKeyboardButton(" ",callback_data=data_ignore))
    row.append(telebot.types.InlineKeyboardButton(">",callback_data=create_callback_data("NEXT-MONTH",year,month,day)))
    keyboard.append(row)
    return telebot.types.InlineKeyboardMarkup(keyboard)

#-------------------------------------------

@bot.message_handler(commands=['Сегодня'])
def no_calendar(message):
    a = connect(f"https://www.nbrb.by/api/exrates/rates/{value}").json()
    publ = date_convert(a['Date'])
    mess = f"Курс {a['Cur_Abbreviation']} на {publ}: \n{a['Cur_OfficialRate']}"
    bot.send_message(message.chat.id, mess, parse_mode='html')
    bot.send_message(message.chat.id, text='----------------------------------------------------------------:)', reply_markup=telebot.types.ReplyKeyboardRemove())


@bot.message_handler(commands=['Календарь'])
def get_calendar(message):
    now = datetime.now() #Текущая дата
    markup = create_calendar(message,now.year,now.month)
    bot.send_message(message.chat.id, "Пожалуйста, выберите дату", reply_markup=markup)


@bot.message_handler()
def get_text (message):
        bot.send_message(message.chat.id, 'Не понимаю, что это', parse_mode='html')

if __name__ == "__main__":
    bot.polling(non_stop=True)
