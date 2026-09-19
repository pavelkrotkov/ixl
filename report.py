from ixl_parser import process_table_html
from math_academy_parser import format_activity_html, parse_activity_html
from progress import IXLStudentProgress, MathAcademyStudentProgress


def build_report(
    ixl_data: list[IXLStudentProgress],
    math_academy_data: list[MathAcademyStudentProgress],
) -> str:
    html = ["<html><body>"]

    if ixl_data:
        html.append("<h2>IXL</h2>")
        for student in ixl_data:
            html.append(f"<h3>{student.student_name} {student.stats}</h3>")
            if student.progress_table:
                html.append(process_table_html(student.progress_table))

    if math_academy_data:
        html.append("<h2>Math Academy</h2>")
        for student in math_academy_data:
            html.append(
                f"<h3>{student.student_name}: today {student.daily_xp_earned}/"
                f"{student.daily_xp_goal} XP, this week {student.weekly_xp} XP</h3>"
            )
            html.append(format_activity_html(parse_activity_html(student.activity_html)))

    html.append("</body></html>")
    return "".join(html)
