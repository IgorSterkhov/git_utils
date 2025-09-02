import subprocess

DEBUG = True

def format_sql_with_clickhouse_format(sql_query: str) -> str:
    """
    Форматирует SQL запрос с помощью утилиты clickhouse-format.

    :param sql_query: Текст SQL запроса
    :return: Отформатированный SQL запрос или сообщение об ошибке
    """
    if DEBUG:
        print(f"Запрос на входе:\n{sql_query}")
    try:
        # Запускаем процесс clickhouse-format
        process = subprocess.Popen(
            ['clickhouse-format'], 
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
