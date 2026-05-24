from bs4 import BeautifulSoup

from ixl_parser import process_table_html

FIXTURE_HTML = """
<div class="student-improvement-table">
    <div class="subject-grade-row">
        <span>Math - 5th grade</span>
    </div>
    <div class="category-row">
        <span>Multiplication and division</span>
    </div>
    <div class="skill-row">
        <div class="skill-name-and-permacode">
            <span>Multiply by 1-digit numbers</span>
        </div>
        <div class="permacode">ABC</div>
        <div class="skill-time">5 min</div>
        <div class="skill-questions">10</div>
        <div class="skill-improvement">
            <span class="score">50</span>
            <span class="score">80</span>
        </div>
    </div>
    <div class="skill-row">
        <div class="skill-name-and-permacode">
            <span>Divide by 1-digit numbers</span>
        </div>
        <div class="permacode">XYZ</div>
        <div class="skill-time">3 min</div>
        <div class="skill-questions">5</div>
        <div class="skill-improvement">
        </div>
    </div>
</div>
"""


def test_process_table_html_returns_table():
    result = process_table_html(FIXTURE_HTML)
    soup = BeautifulSoup(result, "html.parser")
    table = soup.find("table")
    assert table is not None


def test_process_table_html_includes_header_row():
    result = process_table_html(FIXTURE_HTML)
    soup = BeautifulSoup(result, "html.parser")
    header_cells = [th.get_text() for th in soup.find_all("th")]
    assert header_cells == [
        "Subject/Category/Skill",
        "Code",
        "Time Spent",
        "#",
        "Score Improvement",
    ]


def test_process_table_html_renders_subject_grade_row():
    result = process_table_html(FIXTURE_HTML)
    assert "Math - 5th grade" in result
    # Subject-grade rows span all 5 columns with bold styling
    soup = BeautifulSoup(result, "html.parser")
    subject_td = next(td for td in soup.find_all("td") if "Math - 5th grade" in td.get_text())
    assert subject_td.get("colspan") == "5"
    subject_style = subject_td.get("style", "")
    assert isinstance(subject_style, str)
    assert "font-weight: bold" in subject_style


def test_process_table_html_renders_category_row():
    result = process_table_html(FIXTURE_HTML)
    assert "Multiplication and division" in result
    soup = BeautifulSoup(result, "html.parser")
    category_td = next(
        td for td in soup.find_all("td") if "Multiplication and division" in td.get_text()
    )
    assert category_td.get("colspan") == "5"
    category_style = category_td.get("style", "")
    assert isinstance(category_style, str)
    assert "font-style: italic" in category_style


def test_process_table_html_renders_skill_row_with_score_improvement():
    result = process_table_html(FIXTURE_HTML)
    soup = BeautifulSoup(result, "html.parser")
    rows = soup.find_all("tr")
    # Locate the skill row with the multiply skill name
    multiply_row = next(tr for tr in rows if "Multiply by 1-digit numbers" in tr.get_text())
    cells = [td.get_text() for td in multiply_row.find_all("td")]
    assert cells == [
        "Multiply by 1-digit numbers",
        "ABC",
        "5 min",
        "10",
        "50 to 80",
    ]


def test_process_table_html_handles_missing_score_improvement():
    result = process_table_html(FIXTURE_HTML)
    soup = BeautifulSoup(result, "html.parser")
    rows = soup.find_all("tr")
    divide_row = next(tr for tr in rows if "Divide by 1-digit numbers" in tr.get_text())
    cells = [td.get_text() for td in divide_row.find_all("td")]
    # No scores -> last cell should be "N/A"
    assert cells[-1] == "N/A"


def test_process_table_html_empty_input_returns_empty_string():
    assert process_table_html("") == ""
    assert process_table_html(None) == ""


def test_process_table_html_markup_without_rows_returns_table_with_header_only():
    result = process_table_html("<div></div>")
    soup = BeautifulSoup(result, "html.parser")
    rows = soup.find_all("tr")
    assert len(rows) == 1
    assert rows[0].find_all("th")


def test_process_table_html_ignores_non_report_row_classes():
    result = process_table_html(
        """
        <div class="student-improvement-table">
            <div class="row-container">Container</div>
            <div class="narrow">Not a row</div>
        </div>
        """
    )
    soup = BeautifulSoup(result, "html.parser")
    rows = soup.find_all("tr")
    assert len(rows) == 1
    assert rows[0].find_all("th")


def test_process_table_html_strips_score_improvement_whitespace():
    result = process_table_html(
        """
        <div class="skill-row">
            <div class="skill-name-and-permacode"><span>Skill</span></div>
            <div class="permacode">ABC</div>
            <div class="skill-time">5 min</div>
            <div class="skill-questions">10</div>
            <div class="skill-improvement">
                <span class="score"> 50 </span>
                <span class="score"> 80 </span>
            </div>
        </div>
        """
    )
    assert "50 to 80" in result
    assert " 50 " not in result


def test_process_table_html_uses_first_two_scores_when_extra_scores_exist():
    result = process_table_html(
        """
        <div class="skill-row">
            <div class="skill-name-and-permacode"><span>Skill</span></div>
            <div class="permacode">ABC</div>
            <div class="skill-time">5 min</div>
            <div class="skill-questions">10</div>
            <div class="skill-improvement">
                <span class="score">10</span>
                <span class="score">20</span>
                <span class="score">30</span>
            </div>
        </div>
        """
    )

    assert "10 to 20" in result
    assert "30" not in result
