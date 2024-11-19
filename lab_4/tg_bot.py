from loguru import logger
import telebot
import sqlite3
import threading
from datetime import datetime

logger.add("bot_logs.log", rotation="10 MB", compression="zip", level="DEBUG")

logger.info("Инициализация бота...")
bottoken = '1111111111:AAAA1Aa1-11AaAAaAAaaaaAaAAa1AaaaAA'
bot = telebot.TeleBot(bottoken)

logger.info("Подключение к базе данных...")
conn = sqlite3.connect('tasks.db', check_same_thread=False)
cursor = conn.cursor()

try:
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
    logger.info("Таблицы успешно созданы или уже существуют.")
except Exception as e:
    logger.exception("Ошибка при создании таблиц: {}", e)


def sendnotification(taskid, chatid):
    try:
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
                                tasktext + f"\nВремя дедлайна: {deadlinedatetime.strftime('%Y-%m-%d %H:%M')}",reply_to_message_id=664)
                logger.info("Уведомление отправлено по задаче ID {}", taskid)
            except ValueError:
                bot.send_message(chatid,
                                "Ошибка при обработке дедлайна. Некорректный формат.", reply_to_message_id=662)
                logger.warning("Некорректный формат дедлайна для задачи ID {}",
                               taskid)
        else:
            bot.send_message(chatid, "Задача не найдена.")
            logger.warning("Задача с ID {} не найдена.", taskid)
    except Exception as e:
        logger.exception(
            "Ошибка при отправке уведомления для задачи ID {}: {}", taskid, e)


def addtask(task, description, responsible, deadline, additional, chatid, remindertime):
    try:
        cursor.execute(
            "INSERT INTO tasks (task, description, responsible, deadline, additional, remindertime, chatid) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (task, description, responsible, deadline, additional, remindertime, chatid)
        )
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

        bot.send_message(chatid, "Задача успешно добавлена!\n" + tasktext, reply_to_message_id=662)

        logger.info("Задача успешно добавлена с ID {} для чата ID {}", taskid, chatid)

        cursor.execute("INSERT INTO users (chatid, taskid) VALUES (?, ?)", (chatid, taskid))
        conn.commit()

        sendnotification(taskid, chatid)
    
    except Exception as e:
        logger.exception("Ошибка при добавлении задачи для чата ID {}: {}", chatid, e)


def updatetask(taskid, newtask, newdescription, newresponsible, newdeadline,
               newadditional, newremindertime):
    try:
        cursor.execute(
            '''UPDATE tasks SET task=?, description=?, responsible=?, deadline=?, additional=?, remindertime=? WHERE id=?''',
            (newtask, newdescription, newresponsible, newdeadline, newadditional, newremindertime, taskid)
        )
        conn.commit()

        logger.info("Задача с ID {} успешно обновлена для новых данных: Название задачи: {}, Ответственный: {}, Дедлайн: {}, Напоминание за: {} минут",
                    taskid, newtask, newresponsible, newdeadline, newremindertime)
        
    except Exception as e:
        logger.exception("Ошибка при обновлении задачи с ID {}: {}", taskid, e)


def deletetask(taskid, chatid):
    try:
        cursor.execute("DELETE FROM tasks WHERE id=?", (taskid,))
        cursor.execute("DELETE FROM users WHERE taskid=?", (taskid,))
        conn.commit()

        logger.info("Задача с ID {} успешно удалена для чата ID {}", taskid, chatid)

        bot.send_message(chatid, f"Задача {taskid} удалена.")
    
    except Exception as e:
        logger.exception("Ошибка при удалении задачи с ID {} для чата ID {}: {}", taskid, chatid, e)


def viewtasks(chatid):
    try:
        cursor.execute("SELECT * FROM tasks")
        tasks = cursor.fetchall()
        
        if tasks:
            logger.info("Получены задачи для чата ID {}. Количество задач: {}", chatid, len(tasks))

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
            logger.info("Для чата ID {} нет активных задач.", chatid)
            bot.send_message(chatid, "Активных задач нет.")
    
    except Exception as e:
        logger.exception("Ошибка при получении задач для чата ID {}: {}", chatid, e)


def searchtasks(keyword, chatid):
    try:
        cursor.execute(
            "SELECT * FROM tasks WHERE task LIKE ? OR description LIKE ?",
            ('%' + keyword + '%', '%' + keyword + '%')
        )
        tasks = cursor.fetchall()
        
        if tasks:
            logger.info("Найдено {} задач по запросу '{}' для чата ID {}", len(tasks), keyword, chatid)

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
            logger.info("Для чата ID {} не найдены задачи по запросу '{}'.", chatid, keyword)
            bot.send_message(chatid, "Задач по вашему запросу не найдено.")
    
    except Exception as e:
        logger.exception("Ошибка при поиске задач по запросу '{}' для чата ID {}: {}", keyword, chatid, e)


def clearcompletedtasks(chatid):
    try:
        cursor.execute("DELETE FROM tasks WHERE deadline < ?", (datetime.now().isoformat(),))
        conn.commit()
        
        logger.info("Все завершенные задачи удалены для чата ID {}", chatid)

        bot.send_message(chatid, "Все завершенные задачи удалены.")
    
    except Exception as e:
        logger.exception("Ошибка при удалении завершенных задач для чата ID {}: {}", chatid, e)


sentnotifications = {}


def checkdeadlines():
    try:
        now = datetime.now()
        cursor.execute("SELECT id, deadline, remindertime, chatid FROM tasks")
        tasks = cursor.fetchall()

        if not tasks:
            logger.info("Нет задач для проверки дедлайнов.")
        
        for task in tasks:
            taskid, deadline, remindertime, chatid = task[0], datetime.fromisoformat(task[1]), task[2], task[3]

            if taskid in sentnotifications:
                continue

            timeuntildeadline = (deadline - now).total_seconds()
            remindertimesec = int(remindertime) * 60

            if 0 <= timeuntildeadline <= remindertimesec:
                sendnotification(taskid, chatid)
                sentnotifications[taskid] = True
                logger.info("Уведомление отправлено для задачи с ID {} чату ID {}", taskid, chatid)

        threading.Timer(10, checkdeadlines).start()

    except Exception as e:
        logger.exception("Ошибка при проверке дедлайнов: {}", e)


@bot.message_handler(commands=['addtask'])
def addtaskhandler(message):
    try:
        logger.info("Получена команда /addtask от чата ID {}", message.chat.id)
        bot.send_message(message.chat.id, "Введите задачу:", reply_to_message_id=662)
        bot.register_next_step_handler(message, gettask)
    except Exception as e:
        logger.exception("Ошибка при обработке команды /addtask для чата ID {}: {}", message.chat.id, e)


def gettask(message):
    try:
        task = message.text
        logger.info("Получено название задачи: '{}' от чата ID {}", task, message.chat.id)
        bot.send_message(message.chat.id, "Введите описание задачи:", reply_to_message_id=662)
        bot.register_next_step_handler(message, getdescription, task)

    except Exception as e:
        logger.exception("Ошибка при получении текста задачи от чата ID {}: {}", message.chat.id, e)


def getdescription(message, task):
    try:
        description = message.text
        logger.info("Получено описание задачи: '{}' от чата ID {}", description, message.chat.id)
        bot.send_message(message.chat.id, "Введите ответственного:", reply_to_message_id=662)
        bot.register_next_step_handler(message, getresponsible, task, description)

    except Exception as e:
        logger.exception("Ошибка при получении описания задачи от чата ID {}: {}", message.chat.id, e)


def getresponsible(message, task, description):
    try:
        responsible = message.text
        logger.info("Получен ответственный: '{}' для задачи '{}' от чата ID {}", responsible, task, message.chat.id)
        bot.send_message(message.chat.id,
                         "Введите дедлайн (в формате Год-Месяц-День Час:Минуты)(Пример:2023-05-26 13:00):",
                         reply_to_message_id=662)
        bot.register_next_step_handler(message, getdeadline, task, description, responsible)

    except Exception as e:
        logger.exception("Ошибка при получении ответственного для задачи '{}' от чата ID {}: {}", task, message.chat.id, e)


def getdeadline(message, task, description, responsible):
    try:
        deadline = datetime.strptime(message.text, '%Y-%m-%d %H:%M')
        chatid = message.chat.id
        logger.info("Получен дедлайн: '{}' для задачи '{}' от чата ID {}", deadline, task, chatid)
        bot.send_message(message.chat.id, "Введите дополнительную информацию:", reply_to_message_id=662)
        bot.register_next_step_handler(message, getadditional, task, description, responsible, deadline, chatid)
    
    except ValueError:
        logger.warning("Некорректный формат дедлайна для задачи '{}' от чата ID {}: {}", task, message.chat.id, message.text)
        bot.send_message(message.chat.id,
                         "Некорректный формат дедлайна. Пожалуйста, используйте YYYY-MM-DD HH:MM.",
                         reply_to_message_id=662)
        bot.send_message(message.chat.id,
                         "Пожалуйста, введите дедлайн в формате YYYY-MM-DD HH:MM:",
                         reply_to_message_id=662)

        bot.register_next_step_handler(message, getdeadline, task, description, responsible)


def getadditional(message, task, description, responsible, deadline, chatid):
    try:
        additional = message.text
        logger.info("Получена дополнительная информация: '{}' для задачи '{}' от чата ID {}", additional, task, chatid)
        bot.send_message(message.chat.id, "Введите время напоминания (в минутах до дедлайна):", reply_to_message_id=662)
        bot.register_next_step_handler(message, savetask, task, description, responsible, deadline, additional, chatid)

    except Exception as e:
        logger.exception("Ошибка при получении дополнительной информации для задачи '{}' от чата ID {}: {}", task, chatid, e)


def savetask(message, task, description, responsible, deadline, additional, chatid):
    try:
        remindertime = int(message.text)
        logger.info("Получено время напоминания: '{}' минут для задачи '{}' от чата ID {}", remindertime, task, chatid)
        addtask(task, description, responsible, deadline, additional, chatid, remindertime)
        logger.info("Задача '{}' успешно добавлена для чата ID {}", task, chatid)

    except ValueError:
        logger.warning("Некорректный формат времени напоминания для задачи '{}' от чата ID {}: {}", task, chatid, message.text)
        bot.send_message(message.chat.id, "Некорректный формат времени напоминания.")


@bot.message_handler(commands=['deletetask'])
def deletetaskhandler(message):
    try:
        logger.info("Получена команда /deletetask от чата ID {}", message.chat.id)
        bot.send_message(message.chat.id, "Введите ID задачи для удаления:", reply_to_message_id=662)
        bot.register_next_step_handler(message, processdelete)

    except Exception as e:
        logger.exception("Ошибка при обработке команды /deletetask для чата ID {}: {}", message.chat.id, e)


def processdelete(message):
    try:
        taskid = int(message.text)
        logger.info("Получен ID задачи для удаления: {} от чата ID {}", taskid, message.chat.id)
        deletetask(taskid, message.chat.id)
        logger.info("Задача с ID {} удалена для чата ID {}", taskid, message.chat.id)
    
    except ValueError:
        logger.warning("Некорректный ID задачи для удаления от чата ID {}: {}", message.chat.id, message.text)
        bot.send_message(message.chat.id, "ID должен быть числом.")


@bot.message_handler(commands=['updatetask'])
def updatetaskhandler(message):
    try:
        logger.info("Получена команда /updatetask от чата ID {}", message.chat.id)
        bot.send_message(message.chat.id, "Введите ID задачи для обновления:", reply_to_message_id=662)
        bot.register_next_step_handler(message, getupdateinfo)

    except Exception as e:
        logger.exception("Ошибка при обработке команды /updatetask для чата ID {}: {}", message.chat.id, e)


def getupdateinfo(message):
    try:
        taskid = int(message.text)
        logger.info("Получен ID задачи для обновления: {} от чата ID {}", taskid, message.chat.id)
        bot.send_message(message.chat.id, "Введите новую задачу:", reply_to_message_id=662)
        bot.register_next_step_handler(message, getnewtaskinfo, taskid)

    except ValueError:
        logger.warning("Некорректный ID задачи для обновления от чата ID {}: {}", message.chat.id, message.text)
        bot.send_message(message.chat.id, "ID должен быть числом.")


def getnewtaskinfo(message, taskid):
    newtask = message.text
    logger.info("Получена новая задача для обновления: '{}' для задачи с ID {} от чата ID {}", newtask, taskid, message.chat.id)
    bot.send_message(message.chat.id, "Введите новое описание:", reply_to_message_id=662)
    bot.register_next_step_handler(message, getnewdescriptioninfo, taskid, newtask)


def getnewdescriptioninfo(message, taskid, newtask):
    newdescription = message.text
    logger.info("Получено новое описание для обновления задачи с ID {}: '{}' от чата ID {}", taskid, newdescription, message.chat.id)
    bot.send_message(message.chat.id, "Введите нового ответственного:", reply_to_message_id=662)
    bot.register_next_step_handler(message, getnewresponsibleinfo, taskid, newtask, newdescription)


def getnewresponsibleinfo(message, taskid, newtask, newdescription):
    newresponsible = message.text
    logger.info("Получен новый ответственный для обновления задачи с ID {}: '{}' от чата ID {}", taskid, newresponsible, message.chat.id)
    bot.send_message(message.chat.id, "Введите новый дедлайн (Год-Месяц-День Час:Минуты):", reply_to_message_id=662)
    bot.register_next_step_handler(message, getnewdeadlineinfo, taskid, newtask, newdescription, newresponsible)


def getnewdeadlineinfo(message, taskid, newtask, newdescription,
                       newresponsible):
    try:
        newdeadline = datetime.strptime(message.text, '%Y-%m-%d %H:%M')
        logger.info("Получен новый дедлайн для обновления задачи с ID {}: '{}' от чата ID {}", taskid, newdeadline, message.chat.id)
        bot.send_message(message.chat.id, "Введите новую дополнительную информацию:", reply_to_message_id=662)
        bot.register_next_step_handler(message, getnewadditionalinfo, taskid, newtask, newdescription, newresponsible, newdeadline)

    except ValueError:
        logger.warning("Некорректный формат дедлайна для обновления задачи с ID {} от чата ID {}: {}", taskid, message.chat.id, message.text)
        bot.send_message(message.chat.id, "Некорректный формат дедлайна.")


def getnewadditionalinfo(message, taskid, newtask, newdescription,
                         newresponsible, newdeadline):
    newadditional = message.text
    logger.info("Получена новая дополнительная информация для обновления задачи с ID {}: '{}' от чата ID {}", taskid, newadditional, message.chat.id)
    bot.send_message(message.chat.id, "Введите новое время напоминания (в минутах):", reply_to_message_id=662)
    bot.register_next_step_handler(message, saveupdatedtask, taskid, newtask, newdescription, newresponsible, newdeadline, newadditional)


def saveupdatedtask(message, taskid, newtask, newdescription, newresponsible,
                    newdeadline, newadditional):
    try:
        newremindertime = int(message.text)
        logger.info("Время напоминания для обновления задачи с ID {} установлено: '{}' от чата ID {}", taskid, newremindertime, message.chat.id)
        updatetask(taskid, newtask, newdescription, newresponsible, newdeadline, newadditional, newremindertime)
        bot.send_message(message.chat.id, f"Задача {taskid} обновлена.")
    
    except ValueError:
        logger.warning("Некорректный формат времени напоминания для обновления задачи с ID {} от чата ID {}: {}", taskid, message.chat.id, message.text)
        bot.send_message(message.chat.id, "Некорректный формат времени напоминания.")


@bot.message_handler(commands=['viewtasks'])
def viewtaskshandler(message):
    logger.info("Запрос на просмотр задач от чата ID {}", message.chat.id)
    viewtasks(message.chat.id)


@bot.message_handler(commands=['searchtask'])
def searchtaskhandler(message):
    logger.info("Запрос на поиск задачи от чата ID {}", message.chat.id)
    bot.send_message(message.chat.id, "Введите ключевое слово для поиска задач:", reply_to_message_id=662)
    bot.register_next_step_handler(message, processsearch)


def processsearch(message):
    keyword = message.text
    logger.info("Запрос на поиск задач с ключевым словом '{}' от чата ID {}", keyword, message.chat.id)
    searchtasks(keyword, message.chat.id)


@bot.message_handler(commands=['clearcompleted'])
def clearcompletedhandler(message):
    logger.info("Запрос на удаление завершенных задач от чата ID {}", message.chat.id)
    clearcompletedtasks(message.chat.id)


@bot.message_handler(commands=['stopbot'])
def stopbothandler(message):
    logger.info("Запрос на остановку бота от чата ID {}", message.chat.id)
    stopbot(message.chat.id)


def stopbot(chatid):
    logger.info("Бот остановлен по запросу чата ID {}", chatid)
    bot.send_message(chatid, "Бот остановлен.")
    exit()


@bot.message_handler(commands=['adduser'])
def adduserhandler(message):
    logger.info("Запрос на добавление пользователя от чата ID {}", message.chat.id)
    bot.send_message(message.chat.id, "Введите ID задачи, к которой вы хотите привязать этот чат:", reply_to_message_id=662)
    bot.register_next_step_handler(message, processadduser)


def processadduser(message):
    try:
        taskid = int(message.text)
        logger.info("Привязка чата ID {} к задаче ID {}", message.chat.id, taskid)
        cursor.execute("INSERT INTO users (chatid, taskid) VALUES (?, ?)", (message.chat.id, taskid))
        conn.commit()
        bot.send_message(message.chat.id, f"Вы успешно привязаны к задаче {taskid}.")
        
    except ValueError:
        bot.send_message(message.chat.id, "ID задачи должен быть числом.")
        logger.warning("Не удалось привязать чат ID {} к задаче: неверный формат ID задачи", message.chat.id)


@bot.message_handler(commands=['removeuser'])
def removeuserhandler(message):
    logger.info("Запрос на удаление пользователя от чата ID {}", message.chat.id)
    bot.send_message(message.chat.id, "Введите ID задачи, от которой вы хотите отписаться:", reply_to_message_id=662)
    bot.register_next_step_handler(message, processremoveuser)


def processremoveuser(message):
    try:
        taskid = int(message.text)
        logger.info("Отписка чата ID {} от задачи ID {}", message.chat.id, taskid)
        cursor.execute("DELETE FROM users WHERE chatid=? AND taskid=?", (message.chat.id, taskid))
        conn.commit()
        
        bot.send_message(message.chat.id, f"Вы успешно отписаны от задачи {taskid}.")
    except ValueError:
        bot.send_message(message.chat.id, "ID задачи должен быть числом.")
        logger.warning("Не удалось отписать чат ID {} от задачи: неверный формат ID задачи", message.chat.id)


if __name__ == '__main__':
    try:
        threading.Thread(target=checkdeadlines, daemon=True).start()
        bot.polling(non_stop=True, interval=0)
    except Exception as e:
        logger.exception("Ошибка при запуске бота: {}", e)
