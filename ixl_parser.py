from bs4 import BeautifulSoup

HEADERS = [
    "Subject/Category/Skill",
    "Code",
    "Time Spent",
    "#",
    "Score Improvement",
]
SKILL_CELL_SELECTORS = [
    ".skill-name-and-permacode span",
    ".permacode",
    ".skill-time",
    ".skill-questions",
]
BASE_CELL_STYLE = "border: 1px solid #ddd; padding: 8px;"
HEADER_CELL_STYLE = f"{BASE_CELL_STYLE} background-color: #f2f2f2;"
SUBJECT_CELL_STYLE = f"{BASE_CELL_STYLE} font-weight: bold; background-color: #e6e6e6;"
CATEGORY_CELL_STYLE = f"{BASE_CELL_STYLE} font-style: italic; background-color: #f9f9f9;"


def process_table_html(table_html: str | None) -> str:
    """Convert raw IXL progress table markup into the compact HTML email table."""
    if not table_html:
        return ""

    soup = BeautifulSoup(table_html, "html.parser")

    # Create a new table
    new_table = soup.new_tag("table")
    new_table["style"] = "border-collapse: collapse; width: 100%;"

    # Add header row
    header = soup.new_tag("tr")
    num_cols = str(len(HEADERS))
    for h in HEADERS:
        th = soup.new_tag("th")
        th.string = h
        th["style"] = HEADER_CELL_STYLE
        header.append(th)
    new_table.append(header)

    # Process rows
    for row in soup.select(".subject-grade-row, .category-row, .skill-row"):
        row_classes = row.get("class")
        if not isinstance(row_classes, list):
            continue

        new_row = soup.new_tag("tr")

        if "subject-grade-row" in row_classes:
            td = soup.new_tag("td")
            td.string = row.get_text().strip()
            td["colspan"] = num_cols
            td["style"] = SUBJECT_CELL_STYLE
            new_row.append(td)
        elif "category-row" in row_classes:
            td = soup.new_tag("td")
            td.string = row.get_text().strip()
            td["colspan"] = num_cols
            td["style"] = CATEGORY_CELL_STYLE
            new_row.append(td)
        elif "skill-row" in row_classes:
            score_cells = row.select(".skill-improvement .score")
            plain_cells = [row.select_one(selector) for selector in SKILL_CELL_SELECTORS]

            for cell in plain_cells:
                td = soup.new_tag("td")
                td["style"] = BASE_CELL_STYLE
                td.string = cell.get_text().strip() if cell else "N/A"
                new_row.append(td)

            score_td = soup.new_tag("td")
            score_td["style"] = BASE_CELL_STYLE
            score_td.string = (
                f"{score_cells[0].get_text().strip()} to {score_cells[1].get_text().strip()}"
                if len(score_cells) >= 2
                else "N/A"
            )
            new_row.append(score_td)

        new_table.append(new_row)

    return str(new_table)
