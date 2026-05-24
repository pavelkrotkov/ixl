from math_academy_parser import format_activity_html, parse_activity_html

SAMPLE_ACTIVITY_HTML = """
<table id="tasksFrame">
  <tr>
    <td class="dateHeader">
      Monday, May 5
      <span class="dateTotalXP">85 XP</span>
    </td>
  </tr>
  <tr class="taskRow">
    <td class="taskTypeColumn">Lesson</td>
    <td>
      <div class="taskName">Adding Fractions</div>
    </td>
    <td class="taskCompletedColumn">Completed</td>
    <td><span class="taskPoints">40 XP</span></td>
  </tr>
  <tr class="taskRow">
    <td class="taskTypeColumn">Review</td>
    <td>
      <div class="taskName">Multiplication Drill</div>
    </td>
    <td class="taskCompletedColumn">Completed</td>
    <td><span class="completedTaskPoints">45 XP</span></td>
  </tr>
  <tr>
    <td class="dateHeader">
      Sunday, May 4
      <span class="dateTotalXP">30 XP</span>
    </td>
  </tr>
  <tr class="taskRow">
    <td class="taskTypeColumn">Quiz</td>
    <td>
      <div class="taskName">Decimals Quiz</div>
    </td>
    <td class="taskCompletedColumn">Completed</td>
    <td><span class="taskPoints">30 XP</span></td>
  </tr>
  <tr>
    <td class="dateHeader">
      Saturday, May 3
      <span class="dateTotalXP">99 XP</span>
    </td>
  </tr>
  <tr class="taskRow">
    <td class="taskTypeColumn">Lesson</td>
    <td>
      <div class="taskName">Should not appear</div>
    </td>
    <td class="taskCompletedColumn">Completed</td>
    <td><span class="taskPoints">99 XP</span></td>
  </tr>
</table>
"""


def test_parse_activity_html_extracts_dates_and_tasks():
    parsed = parse_activity_html(SAMPLE_ACTIVITY_HTML)

    # Two date headers (third stops parsing) + three task rows (two on day one, one on day two).
    assert len(parsed) == 5

    assert parsed[0] == {"type": "date", "date": "Monday, May 5", "xp": "85 XP"}
    assert parsed[1] == {
        "type": "task",
        "task_type": "Lesson",
        "task_name": "Adding Fractions",
        "completion": "Completed",
        "points": "40 XP",
    }
    assert parsed[2] == {
        "type": "task",
        "task_type": "Review",
        "task_name": "Multiplication Drill",
        "completion": "Completed",
        "points": "45 XP",
    }
    assert parsed[3] == {"type": "date", "date": "Sunday, May 4", "xp": "30 XP"}
    assert parsed[4] == {
        "type": "task",
        "task_type": "Quiz",
        "task_name": "Decimals Quiz",
        "completion": "Completed",
        "points": "30 XP",
    }


def test_parse_activity_html_stops_after_second_date_header():
    parsed = parse_activity_html(SAMPLE_ACTIVITY_HTML)
    task_names = [item.get("task_name") for item in parsed if item["type"] == "task"]
    assert "Should not appear" not in task_names


def test_parse_activity_html_empty_input():
    assert parse_activity_html("") == []


def test_parse_activity_html_none_input():
    assert parse_activity_html(None) == []


def test_format_activity_html_renders_date_and_task_rows():
    parsed_data = [
        {"type": "date", "date": "Monday, May 5", "xp": "85 XP"},
        {
            "type": "task",
            "task_type": "Lesson",
            "task_name": "Adding Fractions",
            "completion": "Completed",
            "points": "40 XP",
        },
    ]

    html = format_activity_html(parsed_data)

    assert html.startswith("<table")
    assert html.endswith("</table>")
    # Header row.
    assert "<th>Type</th>" in html
    assert "<th>Name</th>" in html
    assert "<th>Completion</th>" in html
    assert "<th>Points</th>" in html
    # Date row.
    assert "<strong>Monday, May 5 - 85 XP</strong>" in html
    assert "colspan='4'" in html
    # Task row.
    assert "<td>Lesson</td>" in html
    assert "<td>Adding Fractions</td>" in html
    assert "<td>Completed</td>" in html
    assert "<td>40 XP</td>" in html


def test_format_activity_html_escapes_dynamic_content():
    html = format_activity_html(
        [
            {
                "type": "date",
                "date": "Monday <script>",
                "xp": "85 & 90 XP",
            },
            {
                "type": "task",
                "task_type": "Lesson",
                "task_name": "Angles <img src=x onerror=alert(1)>",
                "completion": "Done & checked",
                "points": "40 < 50",
            },
        ]
    )

    assert "Monday &lt;script&gt; - 85 &amp; 90 XP" in html
    assert "Angles &lt;img src=x onerror=alert(1)&gt;" in html
    assert "Done &amp; checked" in html
    assert "40 &lt; 50" in html
    assert "<script>" not in html
    assert "<img" not in html


def test_format_activity_html_empty_input_returns_table_shell():
    html = format_activity_html([])
    assert html.startswith("<table")
    assert html.endswith("</table>")
    assert "<th>Type</th>" in html


def test_round_trip_parse_then_format():
    parsed = parse_activity_html(SAMPLE_ACTIVITY_HTML)
    html = format_activity_html(parsed)
    assert "Adding Fractions" in html
    assert "Decimals Quiz" in html
    assert "Monday, May 5 - 85 XP" in html
    assert "Sunday, May 4 - 30 XP" in html
    assert "Should not appear" not in html
