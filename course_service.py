from models import Course
import sqlite3

def add_course(connection, course):
    if not isinstance(course,Course):
        raise TypeError("course needs to be a Course type")
    cursor = connection.cursor()
    try:
        cursor.execute('''
            INSERT INTO courses(course_id, name,instructor,credits,capacity)
            VALUES(?,?,?,?,?)''',(
            course.course_id,
            course.name,
            course.instructor,
            course.credits,
            course.capacity)
            )
    except sqlite3.IntegrityError:
        raise ValueError("Course already exists")
    connection.commit()
    return True

def find_course(connection, course_id):
    course_id = Course.normalize_course_id(course_id)
    cursor = connection.cursor()
    cursor.execute('''
        SELECT course_id, name, credits, instructor, capacity From courses
        WHERE course_id = ?
        ''',
        (course_id,)
    )
    row = cursor.fetchone()
    if row is None:
        return None
    return Course(*row)


def delete_course(connection, course_id):
    cursor = connection.cursor()
    course_id = Course.normalize_course_id(course_id)
    try:
        cursor.execute('''
            DELETE FROM courses
            WHERE course_id = ?    
            ''',
            (course_id,)
        )
    except sqlite3.IntegrityError:
        raise ValueError("Cannot delete course with enrollment records")
    if cursor.rowcount == 0:
        return False
    connection.commit()
    return True        

def update_course(
    connection,
    course_id,
    name=None,
    credits=None,
    instructor=None,
    capacity=None
):
    course_id = Course.normalize_course_id(course_id)
    fields = []
    values = []
    if name is not None:
        name = Course.name_check(name)
        fields.append('name = ?')
        values.append(name)
    if credits is not None:
        credits = Course.credits_check(credits)
        fields.append('credits = ?')
        values.append(credits)
    if instructor is not None:
        instructor = Course.instructor_check(instructor)
        fields.append('instructor = ?')
        values.append(instructor)
    if capacity is not None:
        capacity = Course.capacity_check(capacity)
        fields.append('capacity = ?')
        values.append(capacity)

    if not fields:
        return find_course(connection, course_id) is not None
    values.append(course_id)
    cursor = connection.cursor()
    cursor.execute(f'''
        UPDATE courses
        SET {','.join(fields)}
        WHERE course_id = ?
        ''',
        values)
    if cursor.rowcount == 0:
            return False
    connection.commit()
    return True