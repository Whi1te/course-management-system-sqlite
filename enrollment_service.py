from models import Enrollment, Student, Course
from student_service import find_student
from course_service import find_course

def _validate_normalize_enrollment_args(student, course, semester):
    if not isinstance(student, Student):
        raise TypeError("student needs to be a Student type")
    if not isinstance(course, Course):
        raise TypeError("course needs to be a Course type")
    semester = Enrollment.semester_check(semester)
    return semester

def enroll_student(connection, student, course, semester):
    semester = _validate_normalize_enrollment_args(student,course,semester)
    #get the most recent course, in case course capactity updated after create the instance
    course = find_course(connection, course.course_id)
    if course is None:
        raise ValueError("Course not found")
    
    enrollment = Enrollment(student, course, semester)
    cursor = connection.cursor()

    cursor.execute("""
        SELECT status
        FROM enrollments
        WHERE student_id = ?
          AND course_id = ?
          AND semester = ?
    """, (
        student.sid,
        course.course_id,
        semester
    ))

    row = cursor.fetchone()

    if row is not None:
        status = row[0]

        if status == "Enrolled":
            raise ValueError("Already enrolled")

        if status == "Completed":
            raise ValueError("Course already completed")

    cursor.execute("""
        SELECT COUNT(*)
        FROM enrollments
        WHERE course_id = ?
          AND semester = ?
          AND status = ?
    """, (
        course.course_id,
        semester,
        "Enrolled"
    ))

    count = cursor.fetchone()[0]

    if count >= course.capacity:
        raise ValueError("Course is full")

    if row is not None and row[0] == "Dropped":
        cursor.execute("""
            UPDATE enrollments
            SET status = ?, grade = ?
            WHERE student_id = ?
              AND course_id = ?
              AND semester = ?
        """, (
            "Enrolled",
            None,
            student.sid,
            course.course_id,
            semester
        ))
        connection.commit()
        return True
        
    cursor.execute('''
        INSERT INTO enrollments(student_id,course_id,semester,status,grade)
        VALUES(?,?,?,?,?)''',(
        enrollment.sid,
        enrollment.course_id,
        enrollment.semester,
        enrollment.status,
        enrollment.grade)
    )

    connection.commit()
    return True
        
def drop_course(connection, student, course, semester):
    semester = _validate_normalize_enrollment_args(student,course,semester)
    cursor = connection.cursor()
    cursor.execute('''
        SELECT status FROM enrollments
        WHERE student_id = ? AND course_id = ? AND semester = ?
        ''',
        (student.sid, course.course_id, semester)
    )
    row = cursor.fetchone()
    if row is None:
        return False
    status = row[0]
    if status == "Completed":
        raise ValueError("Cannot drop a completed course")
    if status == "Dropped":
        return False
    
    cursor.execute("""
        UPDATE enrollments
        SET status = ?
        WHERE student_id = ?
        AND course_id = ?
        AND semester = ?
    """, (
        "Dropped",
        student.sid,
        course.course_id,
        semester
    ))

    connection.commit()
    return True

def update_grade(connection, student, course, semester, grade):
    semester = _validate_normalize_enrollment_args(student,course,semester)
    if grade is None:
        raise ValueError("Grade cannot be none")
    grade = Enrollment.grade_check(grade)
    cursor = connection.cursor()
    cursor.execute('''
        SELECT status FROM enrollments
        WHERE student_id = ? AND course_id = ? AND semester = ?
        ''',(student.sid, course.course_id,semester)
    )
    row = cursor.fetchone()
    if row is None:
        return False
    if row[0] == 'Dropped':
        raise ValueError("Course is dropped")

    cursor.execute('''
        UPDATE enrollments
        SET status = ?, grade = ?
        WHERE student_id = ? AND course_id = ? AND semester = ?    
        ''', 
        ("Completed", grade,student.sid, course.course_id, semester)
    )
    count = cursor.rowcount
    if count == 0:
        return False
    connection.commit()
    return True

def get_student_enrollments(connection, student, semester=None):
    if not isinstance(student, Student):
        raise TypeError("student needs to be a Student type")
    cursor = connection.cursor()
    if semester is not None:
        semester = Enrollment.semester_check(semester)
        cursor.execute('''
            SELECT student_id, course_id, semester, status, grade FROM enrollments
            WHERE student_id = ? AND semester =?
            ''',
            (student.sid,semester)
        ) 
    else:
        cursor.execute('''
            SELECT student_id, course_id, semester, status, grade FROM enrollments
            WHERE student_id = ?
            ''',
            (student.sid,)
        )
    rows = cursor.fetchall()
    student_enrollments = []
    for row in rows:
        course = find_course(connection,row[1])
        if course is None:
            raise ValueError("Course not found")
        student_enrollments.append(Enrollment(student,course,row[2],row[3],row[4]))
        
    return student_enrollments

def get_course_enrollments(connection, course, semester=None):
    if not isinstance(course, Course):
        raise TypeError("course needs to be a Course type")
    cursor = connection.cursor()
    if semester is not None:
        semester = Enrollment.semester_check(semester)
        cursor.execute('''
            SELECT student_id, course_id, semester, status, grade FROM enrollments
            WHERE course_id = ? AND semester =?
            ''',
            (course.course_id,semester)
        ) 
    else:
        cursor.execute('''
            SELECT student_id, course_id, semester, status, grade FROM enrollments
            WHERE course_id = ?
            ''',
            (course.course_id,)
        )
    rows = cursor.fetchall()
    course_enrollments = []
    for row in rows:
        student = find_student(connection,row[0])
        if student is None:
            raise ValueError("Student not found")
        course_enrollments.append(Enrollment(student,course,row[2],row[3],row[4]))
    return course_enrollments

def get_course_roster(connection, course, semester):
    enrollment_list = get_course_enrollments(connection,course,semester)
    student_in_course = [enrollment.student for enrollment in enrollment_list if enrollment.status == 'Enrolled']
    return student_in_course

def get_student_courses(connection, student,semester):
    enrollment_list = get_student_enrollments(connection,student,semester)
    student_courses = [enrollment.course for enrollment in enrollment_list if enrollment.status == 'Enrolled']
    return student_courses

GRADE_POINTS = {
    "A": 4.0,
    "AB": 3.5,
    "B": 3.0,
    "BC": 2.5,
    "C": 2.0,
    "D": 1.0,
    "F": 0.0
}
def calculate_gpa(connection, student, semester=None):
    enrollment_list = get_student_enrollments(connection,student,semester)
    total = 0
    all_credits =  0
    for enrollment in enrollment_list:
        if enrollment.grade is None:
            continue
        if enrollment.status == 'Completed':
            total += GRADE_POINTS[enrollment.grade] * enrollment.course.credits
            all_credits += enrollment.course.credits
    if all_credits == 0:
        return None
    return total/all_credits
