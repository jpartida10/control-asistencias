import sqlite3

def get_connection():
    return sqlite3.connect("control_asistencias.db")
