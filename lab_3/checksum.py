import json
import hashlib
import csv
import re
from constants import VAR, CSV_PATH, JSON_PATH, REGULARS
from typing import List

"""
В этом модуле обитают функции, необходимые для автоматизированной проверки результатов ваших трудов.
"""


def calculate_checksum(row_numbers: List[int]) -> str:
    """
    Вычисляет md5 хеш от списка целочисленных значений.

    ВНИМАНИЕ, ВАЖНО! Чтобы сумма получилась корректной, считать, что первая строка с данными csv-файла имеет номер 0
    Другими словами: В исходном csv 1я строка - заголовки столбцов, 2я и остальные - данные.
    Соответственно, считаем что у 2 строки файла номер 0, у 3й - номер 1 и так далее.

    Надеюсь, я расписал это максимально подробно.
    Хотя что-то мне подсказывает, что обязательно найдется человек, у которого с этим возникнут проблемы.
    Которому я отвечу, что все написано в докстринге ¯\_(ツ)_/¯

    :param row_numbers: список целочисленных номеров строк csv-файла, на которых были найдены ошибки валидации
    :return: md5 хеш для проверки через github action
    """
    row_numbers.sort()
    return hashlib.md5(json.dumps(row_numbers).encode('utf-8')).hexdigest()


def serialize_result(variant: int, checksum: str) -> None:
    """
    Метод для сериализации результатов лабораторной пишите сами.
    Вам нужно заполнить данными - номером варианта и контрольной суммой - файл, лежащий в папке с лабораторной.
    Файл называется, очевидно, result.json.

    ВНИМАНИЕ, ВАЖНО! На json натравлен github action, который проверяет корректность выполнения лабораторной.
    Так что не перемещайте, не переименовывайте и не изменяйте его структуру, если планируете успешно сдать лабу.

    :param variant: номер вашего варианта
    :param checksum: контрольная сумма, вычисленная через calculate_checksum()
    """
    try:
        with open(JSON_PATH, 'w', encoding='utf-16') as file:
            result = {
                "variant": VAR,
                "checksum": checksum
            }
            file.write(json.dumps(result))
    except Exception as exc:
        print(f"Serializing error: {exc}\n")


def read_csv(file_path: str):
    data = []
    try:
        with open(file_path, mode='r', encoding='utf-16') as file:
            reader = csv.DictReader(file, delimiter=';')
            for row in reader:
                data.append(row)
        return data
    except Exception as exc:
        print(f"Reading .csv error: {exc}\n")


def validate_data(data, regulars):
    try:
        validated_data = []
        for row in data:
            is_valid = True
            for key, pattern in regulars.items():
                if key in row and not re.match(pattern, row[key]):
                    is_valid = False
                    break
            validated_data.append(is_valid)
        return validated_data
    except Exception as exc:
        print(f"Error in data validating: {exc}\n")


def get_invalid_rows(data, regulars):
    try:
        validated_data = validate_data(data, regulars)
        invalid_rows = [index + 2 for index, is_valid in enumerate(
            validated_data) if not is_valid]
        return invalid_rows
    except Exception as exc:
        print(f"Error in getting invalid rows: {exc}\n")


if __name__ == "__main__":
    data = read_csv(CSV_PATH)
    invalid_indeces = get_invalid_rows(data, REGULARS)
    checksum = calculate_checksum(invalid_indeces)
    serialize_result(VAR, checksum)
