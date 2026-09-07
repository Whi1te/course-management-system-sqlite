# Course Management SQLite

A command-line course management application built with Python and SQLite. It supports student and course management, enrollment, course withdrawal, grade entry, and GPA reports. Records are stored in a local database and remain available after the application exits.

## Requirements

- Python 3.10 or later (the menus use `match` / `case` syntax).
- Python standard library only; no third-party packages or separate database server are required.
- Keep `majors.json` in the project directory. The application reads the list of available majors at startup.

## Getting Started

Open a terminal in the project directory and run:

```powershell
python main.py
```

On first launch, the application automatically creates `data/course_management.db` and the required tables. The database path is relative to the project files.

Enter a number and press Enter to select an option from the main menu:

```text
1. Student Management
2. Course Management
3. Enrollment Management
4. View Reports
0. Exit
```

Enter `0` in a submenu to return to the main menu, or `0` in the main menu to exit.

## Features

| Module | Features |
| --- | --- |
| Student Management | Add, find by student ID, update, and delete students |
| Course Management | Add, find by course ID, update, and delete courses |
| Enrollment Management | Enroll students, drop courses, and enter or update grades |
| Reports | View active course rosters, view a student's active courses, and calculate GPA for one semester or all semesters |

When updating a student or course, enter `0` in a field to keep its current value. When viewing reports, enter `0` at the semester prompt to include all semesters.

## Evolution from V1

The first version of this project used Python lists for in-memory data
management and JSON serialization for persistence. This version replaces
that persistence layer with SQLite while preserving the core domain models
and application features.

| Area | V1 — JSON | V2 — SQLite |
| --- | --- | --- |
| Persistence | JSON file | SQLite database |
| Runtime data | Python lists of objects | Database-backed records |
| Saving | Explicit serialization and save on exit | Changes committed directly to the database |
| Loading | Deserialize JSON and rebuild objects at startup | Query records as needed |
| Relationships | Enrollment stored student/course IDs in JSON and manually reconstructed objects | Foreign keys connect enrollments to students and courses |
| Duplicate enrollment | Checked in Python logic | Application logic plus composite database primary key |
| Referential integrity | Application manually checked enrollment references before deletion | SQLite foreign key constraints prevent invalid deletion |
| Capacity checking | Counted Enrollment objects in memory | SQL `COUNT(*)` over current database records |
| Updates | Mutated in-memory objects | SQL `UPDATE` statements |
| Data integrity | Primarily enforced by Python validation | Python validation plus database constraints |

## Input Rules

| Field | Rules and examples |
| --- | --- |
| Student ID | Exactly six ASCII digits, such as `000001`; leading zeros are preserved |
| Student name, course name, instructor name | Must not be empty; surrounding whitespace is removed and names are converted to title case |
| Email | Surrounding whitespace is removed and text is converted to lowercase; basic validation requires an `@` with nonempty text on both sides |
| Major | Must appear in `majors.json` |
| Course ID | English letters followed by digits, such as `CS101`; `cs 101` is normalized to `CS101` |
| Credits | Enter an integer from `1` to `6` |
| Capacity | Enter an integer greater than `0` |
| Semester | `Spring`, `Summer`, or `Fall` followed by a four-digit year, such as `Fall 2026`; `fall2026` is also accepted |
| Grade | One of `A`, `AB`, `B`, `BC`, `C`, `D`, or `F`; input is case-insensitive |

The default majors are `Computer Science`, `Data Science`, `Mathematics`, `Statistics`, `Economics`, and `Undeclared`. Edit `majors.json` and restart the application to change the list. Use title case for new entries, consistent with the existing names, and retain majors used by existing student records.

## Example Workflow

This example assumes that the student ID and course ID below do not already exist in the database.

1. Select `1` from the main menu, then `1` to add a student. Enter these values in order:

   ```text
   Alice Smith
   alice@example.com
   000001
   Computer Science
   ```

2. Enter `0` to return to the main menu. Select `2`, then `1` to add a course. Enter these values in order:

   ```text
   CS101
   Introduction to Python
   3
   Jane Doe
   30
   ```

3. Return to the main menu. Select `3`, then `1` to enroll the student. Enter student ID `000001`, course ID `CS101`, and semester `Fall 2026`.
4. In Enrollment Management, select `3` to update the grade. Enter the same student ID, course ID, and semester, followed by grade `A`.
5. Return to the main menu. Select `4`, then `3` to calculate GPA. Enter semester `Fall 2026`, followed by student ID `000001`. The application displays `GPA: 4.00`.

## Enrollment and Grading Rules

- Create the student and course before enrolling.
- Each student, course, and semester combination has one enrollment record. Duplicate enrollment is rejected.
- Capacity is checked per course and semester, counting only records with `Enrolled` status. Enrollment uses the latest course capacity from the database.
- Dropping a course changes its status to `Dropped`, preserves the record, and frees a seat. If space is available, enrolling again restores the existing record to `Enrolled`.
- Entering a valid grade automatically changes the status to `Completed`. Grades for completed courses can be updated, but those courses cannot be dropped or enrolled in again in the same semester.
- Grades cannot be assigned directly to dropped enrollments.
- Students and courses with enrollment records cannot be deleted, including records for dropped or completed courses.
- Course rosters and student course reports show only `Enrolled` records. Completed and dropped records are excluded.

## GPA Calculation

GPA is weighted by course credits and includes only records with `Completed` status and an assigned grade:

```text
GPA = sum(grade points * course credits) / sum(credits for included courses)
```

| Grade | Grade points |
| --- | --- |
| A | 4.0 |
| AB | 3.5 |
| B | 3.0 |
| BC | 2.5 |
| C | 2.0 |
| D | 1.0 |
| F | 0.0 |

For example, an A in a three-credit course and a B in a four-credit course produce a GPA of `(3 * 4.0 + 4 * 3.0) / 7`, approximately `3.43`. If no grades qualify, the application displays `No completed graded courses found`.

The calculation uses the current credits in the course table, so changing course credits affects GPA calculations for historical grades. Reports across all semesters include each completed, graded enrollment, including the same course taken in different semesters.

## Project Structure

```text
course-management-system-sqlite/
├── main.py                       # Command-line menus and user interaction
├── models.py                     # Student, course, and enrollment models and validation
├── database.py                   # Database connection and table creation
├── student_service.py            # Student CRUD operations
├── course_service.py             # Course CRUD operations
├── enrollment_service.py         # Enrollment, withdrawal, grades, reports, and GPA
├── majors.json                   # Available majors
├── data/
│   └── course_management.db       # Local SQLite database, created automatically
├── tests/
│   └── test_course_management.py  # Automated unittest tests
└── README.md
```

The database contains three tables:

| Table | Main fields | Primary key |
| --- | --- | --- |
| `students` | `sid`, `name`, `email`, `major` | `sid` |
| `courses` | `course_id`, `name`, `credits`, `instructor`, `capacity` | `course_id` |
| `enrollments` | `student_id`, `course_id`, `semester`, `status`, `grade` | Combination of student ID, course ID, and semester |

Database connections enable foreign key constraints, linking enrollments to students and courses. To back up the data, exit the application and copy `data/course_management.db`.

## Running Tests

Run the following command from the project root:

```powershell
python -m unittest discover -s tests -v
```

The 18 tests cover input validation, student and course CRUD operations, duplicate enrollment, capacity and capacity updates, dropping and re-enrolling, grade and status restrictions, report filtering, GPA, foreign key constraints, persistence, and menu interaction.

To run only the capacity update test:

```powershell
python -m unittest discover -s tests -p test_course_management.py -k test_capacity_uses_current_database_value -v
```

Tests use isolated in-memory and temporary databases without modifying `data/course_management.db`. The persistence test requires access to the system temporary directory.

## Common Messages

| Message | Cause and suggested action |
| --- | --- |
| `Student already exists` / `Course already exists` | The student ID or course ID is already in use; find or update the existing record |
| `Invalid major` | Choose a major listed in `majors.json` |
| `Invalid semester` | Use a semester such as `Fall 2026` |
| `Course is full` | Active enrollment for that semester has reached the course capacity |
| `Already enrolled` | The student is already enrolled in that course for that semester |
| `Cannot delete ... with enrollment records` | Related enrollment records exist, and foreign key constraints prevent deletion |
| Missing `majors.json` at startup | Restore a valid majors list in the same directory as `models.py` |
