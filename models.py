import json
from pathlib import Path
import re

SID_LENGTH = 6

def to_int(value, field_name = 'value'):
    if isinstance(value, bool):
        raise ValueError(f"Invalid {field_name}")
    try:
        value = int(value)
    except (TypeError,ValueError):
        raise ValueError(f"Invalid {field_name}")
    if not value > 0:
        raise ValueError(f"Invalid {field_name}")
    return value

AVAILABLE_MAJOR = set()
path = Path(__file__).parent / "majors.json"

if path.exists():
    with path.open('r', encoding= 'utf-8') as f:
        AVAILABLE_MAJOR = set(json.load(f))
else:
    raise FileNotFoundError(f'Cannot find {path}')
    
class Student:

    def __init__(self, name, email, sid, major):        
        self.name = name
        self.email = email
        self.sid = sid
        self.major = major

    @property
    def name(self):
        return self._name
    @staticmethod
    def name_check(value):
        if not isinstance(value, str):
            raise TypeError("Name must be a string")
        value = value.strip().title()
        if not value:
            raise ValueError('Invalid name')
        return value
    @name.setter
    def name(self,value):
        self._name = self.name_check(value)

    @property
    def major(self):
        return self._major
    @staticmethod
    def major_check(value):
        if not isinstance(value, str):
            raise TypeError("Major must be a string")
        value = value.strip().title()
        if value not in AVAILABLE_MAJOR:
            raise ValueError('Invalid major')
        return value
    @major.setter
    def major(self, value):
        self._major = self.major_check(value)

    @property
    def email(self):
        return self._email
    @staticmethod
    def email_check(value):
        if not isinstance(value, str):
            raise TypeError('Email needs to be a string')
        value = value.strip().lower()
        if '@' not in value:
            raise ValueError('Invalid email')
        local, domain = value.rsplit('@',1)
        if not local or not domain:
            raise ValueError('Invalid email')
        return value
    @email.setter
    def email(self, value):
        self._email = self.email_check(value)


    @property
    def sid(self):
        return self._sid
    @staticmethod
    def sid_chek(value):
        if not isinstance(value, str):
            raise ValueError("Invalid ID")
        value = value.strip()
        #avoid special characters,make sure ID is all digit
        if not value.isascii() or not value.isdigit():
            raise ValueError("Invalid ID")
                
        if len(value) != SID_LENGTH:
            raise ValueError(f"Student ID must contain exactly {SID_LENGTH} digits")
        return value
    @sid.setter
    def sid(self, value):          
        self._sid = self.sid_chek(value)

    def __str__(self):
        return f"Name: {self.name} \n Sid: {self.sid} \n Email: {self.email} \n Major: {self.major}"

    def __repr__(self):
        return (f"Student(Name={self.name!r}, Email={self.email!r}, "
                f"Sid={self.sid!r}, Major={self.major!r})")

class Course:
    def __init__(self, course_id, name, credits, instructor, capacity):
        self.course_id = course_id
        self.name = name
        self.instructor = instructor
        self.credits = credits
        self.capacity = capacity

    @property
    def name(self):
        return self._name
    @staticmethod
    def name_check(value):
        if not isinstance(value,str):
                raise TypeError('course name must be string')
        value = value.strip().title()
        if not value:
                raise ValueError('Invalid name')
        return value
    @name.setter
    def name(self,value):
        self._name = self.name_check(value)

    @property
    def instructor(self):
        return self._instructor
    @staticmethod
    def instructor_check(value):
        if not isinstance(value,str):
            raise TypeError("Instructor needs to be a string")
        value = value.strip().title()
        if not value:
            raise ValueError('Invalid instructor')
        return value
    @instructor.setter
    def instructor(self,value):
        self._instructor= self.instructor_check(value)

    @property
    def credits(self):
        return self._credits
    @staticmethod
    def credits_check(value):
        value = to_int(value, 'credits')
        if value > 6:
            raise ValueError('Invalid credits')
        return value
    @credits.setter
    def credits(self,value):
        self._credits = self.credits_check(value)

    @property
    def capacity(self):
        return self._capacity
    @staticmethod
    def capacity_check(value):
        value = to_int(value, 'capacity')
        return value
    @capacity.setter
    def capacity(self,value):
        self._capacity = self.capacity_check(value)

    @property
    def course_id(self):
        return self._course_id
    @staticmethod
    def normalize_course_id(value):
        if not isinstance(value, str):
            raise TypeError('course id must be a string')
        value = value.strip()
        valid_id = re.fullmatch(r"([A-Za-z]+)\s*(\d+)", value)
        if not valid_id:
            raise ValueError('Invalid course id')
        letters,numbers = valid_id.groups()
        return letters.upper()+numbers

    @course_id.setter
    def course_id(self,value):
        self._course_id = self.normalize_course_id(value)
        


    def __str__(self):
        return f"{self.course_id} - {self.name} ({self.credits} credits)"

    def __repr__(self):
        return (f"Course(course_id={self.course_id!r}, name={self.name!r}, credits={self.credits}, "
                f"instructor={self.instructor!r}, capacity={self.capacity!r})")


class Enrollment:
    COURSE_SEMESTER = ['Summer', 'Fall', 'Spring']
    GRADE_RANGE = ['A','AB','B','BC', 'C','D','F']
    STATUS = ['Completed', 'Enrolled', 'Dropped']

    def __init__(self, student, course, semester,status = 'Enrolled', grade=None):
        if not isinstance(student,Student):
            raise TypeError('Need a student object')
        if not isinstance(course,Course):
            raise TypeError('Need a course object')
        self.student = student
        self.course = course
        self.semester = self.semester_check(semester)
        self.status = status
        self.grade = grade
                
    @staticmethod
    def semester_check(value):
        if not isinstance(value,str):
            raise TypeError("Semester needs to be a string")
        value = value.strip()
        semester_pattern = re.fullmatch(rf"([A-Za-z]+)\s*(\d{{4}})",value)
        if not semester_pattern:
            raise ValueError('Invalid semester')
        prefix,year = semester_pattern.groups()
        if prefix.title() not in Enrollment.COURSE_SEMESTER:
            raise ValueError('Invalid semester')
        value = prefix.title() + ' ' + year
        return value
        


    @property
    def sid(self):
        return self.student.sid
    @property
    def course_id(self):
        return self.course.course_id
    @property
    def grade(self):
        return self._grade
    @staticmethod
    def grade_check(value):
        if not isinstance(value, str):
            raise TypeError("Grade needs to be a string")
        value = value.strip().upper()
        if value not in Enrollment.GRADE_RANGE:
            raise ValueError("Invalid grade")
        return value
    
    @grade.setter
    def grade(self, value):
        if value is None:
            self._grade = None
            return
        if self.status != "Completed":
            raise ValueError("Only completed courses can have a grade")

        self._grade = self.grade_check(value)

    @property
    def status(self):
        return self._status
    @status.setter
    def status(self,value):
        if not isinstance(value,str):
            raise TypeError("Status needs to be a string")
        value = value.strip().title()
        if value not in self.STATUS:
            raise ValueError('Invalid status')
        if value in ['Dropped','Enrolled']:
            self._grade = None
        self._status = value

    def __str__(self):
        return f'student_id={self.sid},course_id={self.course_id},semester={self.semester},status={self.status},grade={self.grade}'

    def __repr__(self):
        return (f"Enrollment(student_id={self.sid!r},course_id={self.course_id!r},"
                f"semester={self.semester!r},status={self.status!r},grade={self.grade!r})")


    