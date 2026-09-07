from models import Student
import sqlite3

def add_student(connection, student):
    if not isinstance(student,Student):
        raise TypeError('Only accept Student type')
    cursor = connection.cursor()
    try:
        cursor.execute("""
            INSERT INTO students(sid, name, email, major)
            VALUES(?,?,?,?)
            """,(
            student.sid,
            student.name,
            student.email,
            student.major)
        )
    except sqlite3.IntegrityError:
        raise ValueError("Student already exists")
    connection.commit()
    return True

def find_student(connection, sid):
    cursor = connection.cursor()
    sid = Student.sid_chek(sid)
    cursor.execute('''
        SELECT name, email, sid, major FROM students
        WHERE sid = ?
        ''',
        (sid,)
    )
    row = cursor.fetchone()
    if row is None:
        return None
    return Student(*row)

def delete_student(connection, sid):
    cursor = connection.cursor()
    try:
        cursor.execute('''
            DELETE FROM students
            WHERE sid = ?
            ''',
            (sid,)
        )
    except sqlite3.IntegrityError:
        raise ValueError('Cannot delete student with enrollment records')
    if cursor.rowcount == 0:
        return False
    connection.commit()
    return True

def update_student(connection, sid, name=None, email=None, major=None):
    fields = []
    values = []
    sid = Student.sid_chek(sid)
    if name is not  None:
        name = Student.name_check(name)
        fields.append('name = ?')
        values.append(name)
    if email is not  None:
        email = Student.email_check(email)
        fields.append('email = ?')
        values.append(email)
    if major is not None:
        major = Student.major_check(major)
        fields.append('major = ?')
        values.append(major)
    
    if not fields:
        return find_student(connection,sid) is not None
    values.append(sid)

    cursor = connection.cursor()
    cursor.execute(f'''
        UPDATE students
        SET {','.join(fields)}
        WHERE sid = ?
    ''', values)

    if cursor.rowcount == 0:
        return False
    connection.commit()
    return True


    
    