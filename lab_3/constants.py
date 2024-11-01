VAR = "6"
CSV_PATH = f"prog-instruments-labs\\lab_3\\{VAR}.csv"
JSON_PATH = "prog-instruments-labs\\result.json"
REGULARS = {
    "telephone": r"^\+7-\([0-9]{3}\)-[0-9]{3}-[0-9]{2}-[0-9]{2}+$",
    "http_status_message": r"^\d{3}( [a-zA-Z]+)+$",
    "inn": r"^\d{12}$",
    "identifier": r"^\d{2}-\d{2}\/\d{2}$",
    "ip_v4": r"^(25[0-5]|2[0-4][0-9]|1[0-9]{2}|[1-9]?[0-9])(\.(25[0-5]|2[0-4][0-9]|1[0-9]{2}|[1-9]?[0-9])){3}$",
    "latitude": r"^[+-]?(90\.0+|[0-8]?\d\.\d+)$",
    "blood_type": r"^(A|B|AB|O)(\+|\u2212)$",
    "isbn": r"^(\d{3}-)?\d{1}-\d{5}-\d{3}-\d{1}$",
    "uuid": r"^[a-z0-9]{8}-([a-f0-9]{4}-){3}[a-z0-9]{12}$",
    "date": r"^(19|20)\d{2}-(0[1-9]|1[0-2])-(0[1-9]|[12]\d|3[01])$"
}