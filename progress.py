from dataclasses import dataclass


@dataclass
class IXLStudentProgress:
    student_name: str
    stats: str
    progress_table: str | None = None


@dataclass
class MathAcademyStudentProgress:
    student_id: str
    student_name: str
    daily_xp_earned: str
    daily_xp_goal: str
    weekly_xp: str
    activity_html: str | None
