class Task:

    def __init__(self, title, description=""):
        if not title.strip():
            raise ValueError("Заголовок задачи не может быть пустым.")
        self.title = title
        self.description = description
        self.completed = False

    def mark_completed(self):
        self.completed = True

    def __str__(self):
        status = "Выполнено" if self.completed else "В процессе"
        return f"Задача: {self.title}\nОписание: {self.description}\nСтатус: {status}"


class TaskManager:

    def __init__(self):
        self.tasks = []

    def add_task(self, title, description=""):
        if not title.strip():
            raise ValueError("Заголовок задачи не может быть пустым.")
        task = Task(title, description)
        self.tasks.append(task)
        return task

    def remove_task(self, title):
        for task in self.tasks:
            if task.title == title:
                self.tasks.remove(task)
                return True
        raise ValueError(f"Задача с заголовком '{title}' не найдена.")

    def mark_task_completed(self, title):
        for task in self.tasks:
            if task.title == title:
                task.mark_completed()
                return True
        raise ValueError(f"Задача с заголовком '{title}' не найдена.")

    def list_tasks(self):
        if not self.tasks:
            return "Нет задач."
        return "\n\n".join(str(task) for task in self.tasks)

    def find_task(self, title):
        for task in self.tasks:
            if task.title == title:
                return task
        return None

if __name__ == "__main__":
    manager = TaskManager()

    manager.add_task("Купить продукты", "Молоко, хлеб, яйца")
    manager.add_task("Сделать зарядку", "20 минут утренней зарядки")

    manager.mark_task_completed("Купить продукты")

    print("Все задачи:")
    print(manager.list_tasks())

    manager.remove_task("Сделать зарядку")

    print("\nПосле удаления задачи:")
    print(manager.list_tasks())