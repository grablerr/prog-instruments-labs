import telebot
import sqlite3
import threading
from datetime import datetime, timedelta, timezone, tzinfo

bottoken = '1111111111:AAAA1Aa1-11AaAAaAAaaaaAaAAa1AaaaAA'
bot = telebot.TeleBot(bottoken)

conn = sqlite3.connect('tasks.db', check_same_thread=False)
cursor = conn.cursor()

cursor.execute('''
CREATE TABLE IF NOT EXISTS tasks (
id INTEGER PRIMARY KEY,
task TEXT,
description TEXT,
responsible TEXT,
deadline TEXT,
additional TEXT,
remindertime TEXT,
chatid TEXT
)
''')
cursor.execute('''
CREATE TABLE IF NOT EXISTS users (
id INTEGER PRIMARY KEY,
chatid TEXT,
taskid INTEGER,
FOREIGN KEY(taskid) REFERENCES tasks(id)
)
''')
conn.commit()


def sendnotification(taskid, chatid):
    cursor.execute(
        "SELECT task, description, responsible, deadline, additional FROM tasks WHERE id=?",
        (taskid,))
    taskinfo = cursor.fetchone()
    if taskinfo:
        tasktext = (
            f"Название задачи: {taskinfo[0]}\n"
            f"Описание задачи: {taskinfo[1]}\n"
            f"Ответственный: {taskinfo[2]}\n"
            f"Дедлайн: {taskinfo[3]}\n"
            f"Дополнительная информация: {taskinfo[4]}\n"
        )
        try:
            deadlinedatetime = datetime.fromisoformat(taskinfo[3])
            bot.send_message(chatid,
                             tasktext + f"\nВремя дедлайна: {deadlinedatetime.strftime('%Y-%m-%d %H:%M')}",
                             reply_to_message_id=664)
        except ValueError:
            bot.send_message(chatid,
                             "Ошибка при обработке дедлайна. Некорректный формат.",
                             reply_to_message_id=662)
    else:
        bot.send_message(chatid, "Задача не найдена.")


def addtask(task, description, responsible, deadline, additional, chatid,
            remindertime):
    cursor.execute(
        "INSERT INTO tasks (task, description, responsible, deadline, additional, remindertime, chatid) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (task, description, responsible, deadline, additional, remindertime,
         chatid))
    taskid = cursor.lastrowid
    conn.commit()

    tasktext = (
        f"Название задачи: {task}\n"
        f"Описание задачи: {description}\n"
        f"Ответственный: {responsible}\n"
        f"Дедлайн: {deadline}\n"
        f"Дополнительная информация: {additional}\n"
        f"Напоминание за: {remindertime} минут\n"
    )
    bot.send_message(chatid, "Задача успешно добавлена!\n" + tasktext,
                     reply_to_message_id=662)

    cursor.execute("INSERT INTO users (chatid, taskid) VALUES (?, ?)",
                   (chatid, taskid))
    conn.commit()

    sendnotification(taskid, chatid)


def updatetask(taskid, newtask, newdescription, newresponsible, newdeadline,
               newadditional, newremindertime):
    cursor.execute(
        '''UPDATE tasks SET task=?, description=?, responsible=?, deadline=?, additional=?, remindertime=? WHERE id=?''',
        (newtask, newdescription, newresponsible, newdeadline, newadditional,
         newremindertime, taskid))
    conn.commit()


def deletetask(taskid, chatid):
    cursor.execute("DELETE FROM tasks WHERE id=?", (taskid,))
    cursor.execute("DELETE FROM users WHERE taskid=?", (taskid,))
    conn.commit()
    bot.send_message(chatid, f"Задача {taskid} удалена.")


def viewtasks(chatid):
    cursor.execute("SELECT * FROM tasks")
    tasks = cursor.fetchall()
    if tasks:
        for task in tasks:
            tasktext = (
                f"ID задачи: {task[0]}\n"
                f"Название: {task[1]}\n"
                f"Описание: {task[2]}\n"
                f"Ответственный: {task[3]}\n"
                f"Дедлайн: {task[4]}\n"
                f"Дополнительная информация: {task[5]}\n"
                f"Напоминание за: {task[6]} минут\n"
            )
            bot.send_message(chatid, tasktext, reply_to_message_id=662)
    else:
        bot.send_message(chatid, "Активных задач нет.")


def searchtasks(keyword, chatid):
    cursor.execute(
        "SELECT * FROM tasks WHERE task LIKE ? OR description LIKE ?",
        ('%' + keyword + '%', '%' + keyword + '%'))
    tasks = cursor.fetchall()
    if tasks:
        for task in tasks:
            tasktext = (
                f"ID задачи: {task[0]}\n"
                f"Название: {task[1]}\n"
                f"Описание: {task[2]}\n"
                f"Ответственный: {task[3]}\n"
                f"Дедлайн: {task[4]}\n"
                f"Дополнительная информация: {task[5]}\n"
                f"Напоминание за: {task[6]} минут\n"
            )
            bot.send_message(chatid, tasktext, reply_to_message_id=662)
    else:
        bot.send_message(chatid, "Задач по вашему запросу не найдено.")


def clearcompletedtasks(chatid):
    cursor.execute("DELETE FROM tasks WHERE deadline < ?",
                   (datetime.now().isoformat(),))
    conn.commit()
    bot.send_message(chatid, "Все завершенные задачи удалены.")


sentnotifications = {}


def checkdeadlines():
    now = datetime.now()
    cursor.execute("SELECT id, deadline, remindertime, chatid FROM tasks")
    tasks = cursor.fetchall()
    for task in tasks:
        taskid, deadline, remindertime, chatid = task[
            0], datetime.fromisoformat(task[1]), task[2], task[3]

        if taskid in sentnotifications:
            continue

        timeuntildeadline = (deadline - now).totalseconds()
        remindertimesec = int(remindertime) * 60

        if 0 <= timeuntildeadline <= remindertimesec:
            sendnotification(taskid, chatid)
            sentnotifications[taskid] = True

    threading.Timer(10, checkdeadlines).start()


@bot.message_handler(commands=['addtask'])
def addtaskhandler(message):
    bot.send_message(message.chat.id, "Введите задачу:",
                     reply_to_message_id=662)
    bot.register_next_step_handler(message, gettask)


def gettask(message):
    task = message.text
    bot.send_message(message.chat.id, "Введите описание задачи:",
                     reply_to_message_id=662)
    bot.register_next_step_handler(message, getdescription, task)


def getdescription(message, task):
    description = message.text
    bot.send_message(message.chat.id, "Введите ответственного:",
                     reply_to_message_id=662)
    bot.register_next_step_handler(message, getresponsible, task, description)


def getresponsible(message, task, description):
    responsible = message.text
    bot.send_message(message.chat.id,
                     "Введите дедлайн (в формате Год-Месяц-День Час:Минуты)(Пример:2023-05-26 13:00):",
                     reply_to_message_id=662)
    bot.register_next_step_handler(message, getdeadline, task, description,
                                   responsible)


def getdeadline(message, task, description, responsible):
    try:
        deadline = datetime.strptime(message.text, '%Y-%m-%d %H:%M')
        chatid = message.chat.id
        bot.send_message(message.chat.id, "Введите дополнительную информацию:",
                         reply_to_message_id=662)
        bot.register_next_step_handler(message, getadditional, task,
                                       description, responsible, deadline,
                                       chatid)
    except ValueError:
        bot.send_message(message.chat.id,
                         "Некорректный формат дедлайна. Пожалуйста, используйте YYYY-MM-DD HH:MM.",
                         reply_to_message_id=662)
        bot.send_message(message.chat.id,
                         "Пожалуйста, введите дедлайн в формате YYYY-MM-DD HH:MM:",
                         reply_to_message_id=662)
        bot.register_next_step_handler(message, getdeadline, task, description,
                                       responsible)


def getadditional(message, task, description, responsible, deadline, chatid):
    additional = message.text
    bot.send_message(message.chat.id,
                     "Введите время напоминания (в минутах до дедлайна):",
                     reply_to_message_id=662)
    bot.register_next_step_handler(message, savetask, task, description,
                                   responsible, deadline, additional, chatid)


def savetask(message, task, description, responsible, deadline, additional,
             chatid):
    try:
        remindertime = int(message.text)
        addtask(task, description, responsible, deadline, additional, chatid,
                remindertime)
    except ValueError:
        bot.send_message(message.chat.id,
                         "Некорректный формат времени напоминания.")


@bot.message_handler(commands=['deletetask'])
def deletetaskhandler(message):
    bot.send_message(message.chat.id, "Введите ID задачи для удаления:",
                     reply_to_message_id=662)
    bot.register_next_step_handler(message, processdelete)


def processdelete(message):
    try:
        taskid = int(message.text)
        deletetask(taskid, message.chat.id)
    except ValueError:
        bot.send_message(message.chat.id, "ID должен быть числом.")


@bot.message_handler(commands=['updatetask'])
def updatetaskhandler(message):
    bot.send_message(message.chat.id, "Введите ID задачи для обновления:",
                     reply_to_message_id=662)
    bot.register_next_step_handler(message, getupdateinfo)


def getupdateinfo(message):
    try:
        taskid = int(message.text)
        bot.send_message(message.chat.id, "Введите новую задачу:",
                         reply_to_message_id=662)
        bot.register_next_step_handler(message, getnewtaskinfo, taskid)
    except ValueError:
        bot.send_message(message.chat.id, "ID должен быть числом.")


def getnewtaskinfo(message, taskid):
    newtask = message.text
    bot.send_message(message.chat.id, "Введите новое описание:",
                     reply_to_message_id=662)
    bot.register_next_step_handler(message, getnewdescriptioninfo, taskid,
                                   newtask)


def getnewdescriptioninfo(message, taskid, newtask):
    newdescription = message.text
    bot.send_message(message.chat.id, "Введите нового ответственного:",
                     reply_to_message_id=662)
    bot.register_next_step_handler(message, getnewresponsibleinfo, taskid,
                                   newtask, newdescription)


def getnewresponsibleinfo(message, taskid, newtask, newdescription):
    newresponsible = message.text
    bot.send_message(message.chat.id,
                     "Введите новый дедлайн (Год-Месяц-День Час:Минуты):",
                     reply_to_message_id=662)
    bot.register_next_step_handler(message, getnewdeadlineinfo, taskid,
                                   newtask, newdescription, newresponsible)


def getnewdeadlineinfo(message, taskid, newtask, newdescription,
                       newresponsible):
    try:
        newdeadline = datetime.strptime(message.text, '%Y-%m-%d %H:%M')
        bot.send_message(message.chat.id,
                         "Введите новую дополнительную информацию:",
                         reply_to_message_id=662)
        bot.register_next_step_handler(message, getnewadditionalinfo, taskid,
                                       newtask, newdescription, newresponsible,
                                       newdeadline)
    except ValueError:
        bot.send_message(message.chat.id, "Некорректный формат дедлайна.")


def getnewadditionalinfo(message, taskid, newtask, newdescription,
                         newresponsible, newdeadline):
    newadditional = message.text
    bot.send_message(message.chat.id,
                     "Введите новое время напоминания (в минутах):",
                     reply_to_message_id=662)
    bot.register_next_step_handler(message, saveupdatedtask, taskid, newtask,
                                   newdescription, newresponsible, newdeadline,
                                   newadditional)


def saveupdatedtask(message, taskid, newtask, newdescription, newresponsible,
                    newdeadline, newadditional):
    try:
        newremindertime = int(message.text)
        updatetask(taskid, newtask, newdescription, newresponsible,
                   newdeadline, newadditional, newremindertime)
        bot.send_message(message.chat.id, f"Задача {taskid} обновлена.")
    except ValueError:
        bot.send_message(message.chat.id,
                         "Некорректный формат времени напоминания.")


@bot.message_handler(commands=['viewtasks'])
def viewaskshandler(message):
    viewtasks(message.chat.id)


@bot.message_handler(commands=['searchtask'])
def searchtaskhandler(message):
    bot.send_message(message.chat.id,
                     "Введите ключевое слово для поиска задач:",
                     reply_to_message_id=662)
    bot.register_next_step_handler(message, processsearch)


def processsearch(message):
    keyword = message.text
    searchtasks(keyword, message.chat.id)


@bot.message_handler(commands=['clearcompleted'])
def clearcompletedhandler(message):
    clearcompletedtasks(message.chat.id)


@bot.message_handler(commands=['stopbot'])
def stopbothandler(message):
    stopbot(message.chat.id)


def stopbot(chatid):
    bot.send_message(chatid, "Бот остановлен.")
    exit()


@bot.message_handler(commands=['adduser'])
def adduserhandler(message):
    bot.send_message(message.chat.id,
                     "Введите ID задачи, к которой вы хотите привязать этот чат:",
                     reply_to_message_id=662)
    bot.register_next_step_handler(message, processadduser)


def processadduser(message):
    try:
        taskid = int(message.text)
        cursor.execute("INSERT INTO users (chatid, taskid) VALUES (?, ?)",
                       (message.chat.id, taskid))
        conn.commit()
        bot.send_message(message.chat.id,
                         f"Вы успешно привязаны к задаче {taskid}.")
    except ValueError:
        bot.send_message(message.chat.id, "ID задачи должен быть числом.")


@bot.message_handler(commands=['removeuser'])
def removeuserhandler(message):
    bot.send_message(message.chat.id,
                     "Введите ID задачи, от которой вы хотите отписаться:",
                     reply_to_message_id=662)
    bot.register_next_step_handler(message, processremoveuser)


def processremoveuser(message):
    try:
        taskid = int(message.text)
        cursor.execute("DELETE FROM users WHERE chatid=? AND taskid=?",
                       (message.chat.id, taskid))
        conn.commit()
        bot.send_message(message.chat.id,
                         f"Вы успешно отписаны от задачи {taskid}.")
    except ValueError:
        bot.send_message(message.chat.id, "ID задачи должен быть числом.")


if __name__ == '__main__':
    threading.Thread(target=checkdeadlines).start()
    bot.polling()
