from ixl_parser import process_table_html
from progress import IXLStudentProgress, MathAcademyStudentProgress
from report import build_report

IXL_TABLE = """
<div class="subject-grade-row">Math 7</div>
<div class="category-row">Fractions</div>
<div class="skill-row">
  <div class="skill-name-and-permacode"><span>Add fractions</span></div>
  <span class="permacode">ABC</span>
  <span class="skill-time">12 min</span>
  <span class="skill-questions">8</span>
  <div class="skill-improvement"><span class="score">80</span><span class="score">90</span></div>
</div>
"""

ACTIVITY = """
<table>
  <tr><td class="dateHeader">Monday<span class="dateTotalXP">25 XP</span></td></tr>
  <tr class="taskRow">
    <td class="taskTypeColumn">Lesson</td>
    <td><div class="taskName">Ratios</div></td>
    <td class="taskCompletedColumn">Completed</td>
    <td><span class="taskPoints">25 XP</span></td>
  </tr>
</table>
"""


def test_process_table_html_without_browser():
    html = process_table_html(IXL_TABLE)

    assert "Math 7" in html
    assert "Fractions" in html
    assert "Add fractions" in html
    assert "80 to 90" in html


def test_build_report_from_typed_progress():
    html = build_report(
        [IXLStudentProgress("Maya", "answered 8 questions", process_table_html(IXL_TABLE))],
        [MathAcademyStudentProgress("1", "Luca", "25", "30", "100", ACTIVITY)],
    )

    assert "<h2>IXL</h2>" in html
    assert "Maya answered 8 questions" in html
    assert "Add fractions" in html
    assert "<h2>Math Academy</h2>" in html
    assert "Luca: today 25/30 XP, this week 100 XP" in html
    assert "Ratios" in html
