import subprocess
import platform
import re

DEBUG = False

def clean_sql_query(sql_query: str) -> str:
    """
    Очищает SQL запрос от повторяющихся пробелов и подстрок вида "\r\n" и "/r/n".
    """
    cleaned = sql_query
    # Заменяем все вхождения \r\n 
    cleaned = re.sub(r'\\r\\n', ' ', cleaned)
    # # Заменяем два и более подряд идущих перевода строк (LF или CRLF) на одинарный перевод строки "\n"
    # cleaned = re.sub(r'(\r\n|\n){2,}', '\n', cleaned)
    # Заменяем все последовательности пробелов (включая табы и новые строки) на один пробел
    cleaned = re.sub(r'\s+', ' ', cleaned)
    # Обрезаем пробелы в начале и конце
    cleaned = cleaned.strip()
    return cleaned

def format_sql_with_clickhouse_format(sql_query: str) -> str:
    """
    Форматирует SQL запрос с помощью утилиты clickhouse-format.

    :param sql_query: Текст SQL запроса
    :return: Отформатированный SQL запрос или сообщение об ошибке
    """
    if DEBUG:
        print(f"Запрос на входе:\n{sql_query}")
    try:
        # Очистка SQL запроса перед форматированием
        sql_query = clean_sql_query(sql_query)

        # Определяем команду в зависимости от ОС
        system_name = platform.system()
        if system_name == "Darwin":  # MacOS
            if DEBUG:
                print(f"system_name: {system_name}")            
            cmd = ["clickhouse", "format", "-n"]
        else:  # Linux и другие
            if DEBUG:
                print(f"system_name: {system_name}")
            cmd = ["clickhouse-format", "-n"]
        
        # Запускаем процесс clickhouse-format
        process = subprocess.Popen(
            cmd, 
            stdin=subprocess.PIPE, 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE,
            text=True
        )
        # Передаем запрос на форматирование и получаем результат
        stdout, stderr = process.communicate(input=sql_query)
        if process.returncode != 0:
            if DEBUG:
                print(f"Запрос на выходе:\n{stderr.strip()}")
            raise Exception(f"clickhouse-format error: {stderr.strip()}")
        if DEBUG:
            print(f"Запрос на выходе:\n{stdout.strip()}")
        return stdout.strip()
    except Exception as e:
        return f"Error: {str(e)}"
