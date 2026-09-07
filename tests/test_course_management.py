"""Run from the project directory: python -m unittest discover -s tests -v."""

import io
from pathlib import Path
import sqlite3
import tempfile
import unittest
from unittest.mock import patch

import course_service as cs
import enrollment_service as es
import main
import student_service as ss
from database import connect_database, create_tables
from models import Course, Enrollment, Student


class CourseManagementTests(unittest.TestCase):
    def setUp(self):
        self.db = connect_database(":memory:")
        self.addCleanup(self.db.close)
        create_tables(self.db)
        self.student = Student(" alice smith ", " ALICE@example.com ", "000001", "Computer Science")
        self.course = Course(" cs 101 ", " intro to python ", "3", " jane doe ", 1)
        ss.add_student(self.db, self.student)
        cs.add_course(self.db, self.course)

    def enroll(self, student=None, course=None, semester="Fall 2026"):
        return es.enroll_student(self.db, student or self.student, course or self.course, semester)

    def test_model_normalization(self):
        self.assertEqual((self.student.name, self.student.email), ("Alice Smith", "alice@example.com"))
        self.assertEqual((self.course.course_id, self.course.credits), ("CS101", 3))
        self.assertEqual(Enrollment.semester_check(" fall2026 "), "Fall 2026")

    def test_invalid_model_inputs(self):
        cases = [
            (Student.sid_chek, "123"), (Student.sid_chek, "１２３４５６"),
            (Student.email_check, "missing-at"), (Student.major_check, "Unknown Major"),
            (Course.credits_check, 0), (Course.credits_check, 7),
            (Course.credits_check, True), (Course.capacity_check, -1),
            (Course.normalize_course_id, "101CS"),
            (Enrollment.semester_check, "Winter 2026"), (Enrollment.grade_check, "Z"),
        ]
        for validator, value in cases:
            with self.subTest(validator=validator.__qualname__, value=value):
                with self.assertRaises(ValueError):
                    validator(value)

    def test_student_crud_and_duplicates(self):
        self.assertEqual(ss.find_student(self.db, "000001").email, "alice@example.com")
        with self.assertRaisesRegex(ValueError, "already exists"):
            ss.add_student(self.db, self.student)
        self.assertTrue(ss.update_student(self.db, "000001", name=" bob jones "))
        found = ss.find_student(self.db, "000001")
        self.assertEqual((found.name, found.email), ("Bob Jones", "alice@example.com"))
        self.assertTrue(ss.delete_student(self.db, "000001"))
        self.assertIsNone(ss.find_student(self.db, "000001"))
        self.assertFalse(ss.update_student(self.db, "000001", name="Nobody"))
        self.assertFalse(ss.delete_student(self.db, "000001"))

    def test_course_crud_and_duplicates(self):
        self.assertEqual(cs.find_course(self.db, "cs 101").name, "Intro To Python")
        with self.assertRaisesRegex(ValueError, "already exists"):
            cs.add_course(self.db, self.course)
        self.assertTrue(cs.update_course(self.db, "cs101", credits="4", capacity="2"))
        found = cs.find_course(self.db, "CS101")
        self.assertEqual((found.credits, found.capacity, found.instructor), (4, 2, "Jane Doe"))
        self.assertTrue(cs.delete_course(self.db, "cs101"))
        self.assertIsNone(cs.find_course(self.db, "CS101"))
        self.assertFalse(cs.update_course(self.db, "CS101", name="Missing"))
        self.assertFalse(cs.delete_course(self.db, "CS101"))

    def test_invalid_update_preserves_existing_data(self):
        with self.assertRaises(ValueError):
            cs.update_course(self.db, "CS101", name="Changed", credits=7)
        self.assertEqual(cs.find_course(self.db, "CS101").name, "Intro To Python")

    def test_schema_is_idempotent_and_foreign_keys_enabled(self):
        create_tables(self.db)
        self.assertEqual(self.db.execute("PRAGMA foreign_keys").fetchone()[0], 1)
        with self.assertRaises(sqlite3.IntegrityError):
            self.db.execute("INSERT INTO enrollments VALUES (?, ?, ?, ?, ?)",
                            ("999999", "CS101", "Fall 2026", "Enrolled", None))

    def test_enrollment_prevents_duplicate(self):
        self.assertTrue(self.enroll(semester="fall2026"))
        with self.assertRaisesRegex(ValueError, "Already enrolled"):
            self.enroll()
        records = es.get_student_enrollments(self.db, self.student)
        self.assertEqual(len(records), 1)
        self.assertEqual((records[0].semester, records[0].status, records[0].grade),
                         ("Fall 2026", "Enrolled", None))

    def test_capacity_is_per_semester(self):
        other = Student("Bob", "bob@example.com", "000002", "Mathematics")
        ss.add_student(self.db, other)
        self.enroll()
        with self.assertRaisesRegex(ValueError, "Course is full"):
            self.enroll(student=other)
        self.assertTrue(self.enroll(student=other, semester="Spring 2027"))

    def test_capacity_uses_current_database_value(self):
        # An object loaded before a capacity update must not permit overbooking.
        cs.update_course(self.db, "CS101", capacity=2)
        previously_loaded = cs.find_course(self.db, "CS101")
        cs.update_course(self.db, "CS101", capacity=1)
        self.enroll()
        other = Student("Bob", "bob@example.com", "000002", "Mathematics")
        ss.add_student(self.db, other)
        with self.assertRaisesRegex(ValueError, "Course is full"):
            self.enroll(student=other, course=previously_loaded)

    def test_drop_and_reenroll(self):
        self.assertFalse(es.drop_course(self.db, self.student, self.course, "Fall 2026"))
        self.enroll()
        self.assertTrue(es.drop_course(self.db, self.student, self.course, "Fall 2026"))
        self.assertFalse(es.drop_course(self.db, self.student, self.course, "Fall 2026"))
        self.assertEqual(es.get_course_roster(self.db, self.course, "Fall 2026"), [])
        self.assertTrue(self.enroll())
        records = es.get_student_enrollments(self.db, self.student)
        self.assertEqual(len(records), 1)
        self.assertEqual((records[0].status, records[0].grade), ("Enrolled", None))

    def test_completed_course_grade_and_transition_guards(self):
        self.enroll()
        self.assertTrue(es.update_grade(self.db, self.student, self.course, "Fall 2026", " ab "))
        record = es.get_student_enrollments(self.db, self.student)[0]
        self.assertEqual((record.status, record.grade), ("Completed", "AB"))
        with self.assertRaisesRegex(ValueError, "completed"):
            es.drop_course(self.db, self.student, self.course, "Fall 2026")
        with self.assertRaisesRegex(ValueError, "completed"):
            self.enroll()

    def test_grade_rejected_for_dropped_or_missing_enrollment(self):
        self.assertFalse(es.update_grade(self.db, self.student, self.course, "Fall 2026", "A"))
        self.enroll()
        es.drop_course(self.db, self.student, self.course, "Fall 2026")
        with self.assertRaisesRegex(ValueError, "dropped"):
            es.update_grade(self.db, self.student, self.course, "Fall 2026", "A")

    def test_enrollment_records_protect_student_and_course_from_deletion(self):
        self.enroll()
        with self.assertRaisesRegex(ValueError, "enrollment records"):
            ss.delete_student(self.db, self.student.sid)
        with self.assertRaisesRegex(ValueError, "enrollment records"):
            cs.delete_course(self.db, self.course.course_id)
        self.assertIsNotNone(ss.find_student(self.db, self.student.sid))
        self.assertIsNotNone(cs.find_course(self.db, self.course.course_id))

    def test_reports_filter_semester_and_active_status(self):
        self.enroll()
        self.enroll(semester="Spring 2027")
        es.drop_course(self.db, self.student, self.course, "Spring 2027")
        self.assertEqual(len(es.get_student_enrollments(self.db, self.student)), 2)
        self.assertEqual(len(es.get_course_enrollments(self.db, self.course, "Fall 2026")), 1)
        self.assertEqual([s.sid for s in es.get_course_roster(self.db, self.course, None)], ["000001"])
        self.assertEqual([c.course_id for c in es.get_student_courses(self.db, self.student, "Fall 2026")], ["CS101"])
        self.assertEqual(es.get_student_courses(self.db, self.student, "Spring 2027"), [])

    def test_gpa_is_credit_weighted_and_filters_semester(self):
        self.assertIsNone(es.calculate_gpa(self.db, self.student))
        self.enroll()
        self.assertIsNone(es.calculate_gpa(self.db, self.student))
        es.update_grade(self.db, self.student, self.course, "Fall 2026", "A")
        other = Course("MATH101", "Calculus", 4, "Teacher", 10)
        cs.add_course(self.db, other)
        self.enroll(course=other, semester="Spring 2027")
        es.update_grade(self.db, self.student, other, "Spring 2027", "B")
        self.enroll(semester="Fall 2027")  # Ungraded credits must be excluded.
        self.assertAlmostEqual(es.calculate_gpa(self.db, self.student), 24 / 7)
        self.assertEqual(es.calculate_gpa(self.db, self.student, "Fall 2026"), 4.0)
        self.assertIsNone(es.calculate_gpa(self.db, self.student, "Fall 2027"))

    def test_student_menu_recovers_after_invalid_input(self):
        answers = ["1", "Bob", "invalid-email", "000002", "Mathematics",
                   "1", "Bob", "bob@example.com", "000002", "Mathematics", "0"]
        with patch("builtins.input", side_effect=answers), patch("sys.stdout", new_callable=io.StringIO) as output:
            main.student_menu(self.db)
        self.assertIn("Failed to add student", output.getvalue())
        self.assertIn("Student added", output.getvalue())
        self.assertEqual(ss.find_student(self.db, "000002").name, "Bob")

    def test_main_menu_exit_closes_connection(self):
        with patch("main.connect_database", return_value=self.db), \
             patch("builtins.input", side_effect=["invalid", "1", "0", "2", "0", "3", "0", "4", "0", "0"]), \
             patch("sys.stdout", new_callable=io.StringIO) as output:
            main.main()
        self.assertIn("Invalid command", output.getvalue())
        with self.assertRaises(sqlite3.ProgrammingError):
            self.db.execute("SELECT 1")

    def test_file_database_persists_after_reopening(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "nested" / "test.db"
            connection = connect_database(path)
            try:
                create_tables(connection)
                ss.add_student(connection, self.student)
            finally:
                connection.close()
            connection = connect_database(path)
            try:
                self.assertEqual(ss.find_student(connection, "000001").email, "alice@example.com")
            finally:
                connection.close()


if __name__ == "__main__":
    unittest.main()
