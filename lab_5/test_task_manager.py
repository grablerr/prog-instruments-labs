import pytest
from unittest.mock import Mock
from task_manager import Task, TaskManager


def test_task_initialization():
    task = Task("Test Task", "Test Description")
    assert task.title == "Test Task"
    assert task.description == "Test Description"
    assert not task.completed


def test_mark_completed():
    task = Task("Test Task")
    task.mark_completed()
    assert task.completed


def test_task_string_representation():
    task = Task("Test Task", "Test Description")
    expected_str = "Задача: Test Task\nОписание: Test Description\nСтатус: В процессе"
    assert str(task) == expected_str
    task.mark_completed()
    expected_str_completed = "Задача: Test Task\nОписание: Test Description\nСтатус: Выполнено"
    assert str(task) == expected_str_completed


def test_add_task():
    manager = TaskManager()
    task = manager.add_task("New Task", "Task Description")
    assert len(manager.tasks) == 1
    assert manager.tasks[0] == task


def test_remove_task():
    manager = TaskManager()
    manager.add_task("Task to Remove")
    result = manager.remove_task("Task to Remove")
    assert result
    assert len(manager.tasks) == 0


def test_remove_task_not_found():
    manager = TaskManager()
    with pytest.raises(ValueError, match="Задача с заголовком 'Missing Task' не найдена."):
        manager.remove_task("Missing Task")


@pytest.mark.parametrize("title, description", [
    ("Task 1", "Description 1"),
    ("Task 2", ""),
    ("Task 3", "Description 3"),
])
def test_add_multiple_tasks(title, description):
    manager = TaskManager()
    task = manager.add_task(title, description)
    assert task.title == title
    assert task.description == description
    assert not task.completed


def test_mark_task_completed_with_mock():
    manager = TaskManager()
    mock_task = Mock(spec=Task)
    mock_task.title = "Mock Task"
    manager.tasks.append(mock_task)

    result = manager.mark_task_completed("Mock Task")
    assert result
    mock_task.mark_completed.assert_called_once()


def test_list_tasks():
    manager = TaskManager()
    manager.add_task("Task 1", "Description 1")
    manager.add_task("Task 2", "Description 2")
    result = manager.list_tasks()
    assert "Задача: Task 1" in result
    assert "Задача: Task 2" in result


def test_empty_task_title():
    manager = TaskManager()
    with pytest.raises(ValueError, match="Заголовок задачи не может быть пустым."):
        manager.add_task("")
