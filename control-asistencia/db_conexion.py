import pyodbc

def get_connection():
    server = "localhost"  # instancia
    database = "ControlAsistenciasDB"
    username = "sa"
    driver = "{ODBC Driver 17 for SQL Server}"

    conn = pyodbc.connect(
        f"DRIVER={driver};SERVER={server};DATABASE={database};UID={username};Trusted_Connection=yes"
    )
    return conn
