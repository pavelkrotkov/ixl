from bs4 import BeautifulSoup

CELL_STYLE = "border: 1px solid #ddd; padding: 8px;"
HEADER_STYLE = f"{CELL_STYLE} background-color: #f2f2f2;"
SUBJECT_STYLE = f"{CELL_STYLE} font-weight: bold; background-color: #e6e6e6;"
CATEGORY_STYLE = f"{CELL_STYLE} font-style: italic; background-color: #f9f9f9;"
HEADERS = (
    "Subject/Category/Skill",
    "Code",
    "Time Spent",
    "#",
    "Score Improvement",
)
SKILL_SELECTORS = (
    ".skill-name-and-permacode span",
    ".permacode",
    ".skill-time",
    ".skill-questions",
)


def _cell(soup, tag, text, style, colspan=None):
    cell = soup.new_tag(tag)
    cell.string = text
    cell["style"] = style
    if colspan:
        cell["colspan"] = colspan
    return cell


def _cell_row(soup, text, style):
    row = soup.new_tag("tr")
    row.append(_cell(soup, "td", text, style, "5"))
    return row


def _skill_row(soup, row):
    rendered = soup.new_tag("tr")
    for selector in SKILL_SELECTORS:
        cell = row.select_one(selector)
        text = cell.get_text().strip() if cell else "N/A"
        rendered.append(_cell(soup, "td", text, CELL_STYLE))

    scores = row.select(".skill-improvement .score")
    improvement = "N/A"
    if len(scores) == 2:
        improvement = f"{scores[0].get_text()} to {scores[1].get_text()}"
    rendered.append(_cell(soup, "td", improvement, CELL_STYLE))
    return rendered


def process_table_html(table_html: str) -> str:
    soup = BeautifulSoup(table_html, "html.parser")
    table = soup.new_tag("table")
    table["style"] = "border-collapse: collapse; width: 100%;"

    header = soup.new_tag("tr")
    for text in HEADERS:
        header.append(_cell(soup, "th", text, HEADER_STYLE))
    table.append(header)

    for row in soup.select('div[class*="row"]'):
        classes = row.get("class")
        if not isinstance(classes, list):
            continue
        if "subject-grade-row" in classes:
            table.append(_cell_row(soup, row.get_text().strip(), SUBJECT_STYLE))
        elif "category-row" in classes:
            table.append(_cell_row(soup, row.get_text().strip(), CATEGORY_STYLE))
        elif "skill-row" in classes:
            table.append(_skill_row(soup, row))

    return str(table)
