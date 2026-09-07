import sqlite3
from pathlib import Path

DB_FILE = Path(__file__).parent / "data" / "course_management.db"

def connect_database(path=DB_FILE):
    path = Path(path)
    path.parent.mkdir(parents= True, exist_ok= True)

    connection = sqlite3.connect(path)
    connection.execute("PRAGMA foreign_keys = ON")
    return connection

def create_tables(connection):
    cursor = connection.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS students(
        sid TEXT PRIMARY KEY NOT NULL,
        name TEXT NOT NULL,
        email TEXT NOT NULL,
        major TEXT NOT NULL
        )
""")
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS courses(
        course_id TEXT PRIMARY KEY NOT NULL,
        name TEXT NOT NULL,
        credits INTEGER NOT NULL CHECK(credits > 0 AND credits <= 6),
        instructor TEXT NOT NULL,
        capacity INTEGER NOT NULL CHECK(capacity > 0)
        )
''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS enrollments(
        student_id TEXT NOT NULL,
        course_id TEXT NOT NULL,
        semester TEXT NOT NULL,
        status TEXT NOT NULL,
        grade TEXT,
        PRIMARY KEY (student_id, course_id, semester),
        
        FOREIGN KEY (student_id)
            REFERENCES students(sid),

        FOREIGN KEY (course_id)
            REFERENCES courses(course_id)
        )
''')
    connection.commit()