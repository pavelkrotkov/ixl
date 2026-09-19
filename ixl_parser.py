from bs4 import BeautifulSoup

CELL_STYLE = "border: 1px solid #ddd; padding: 8px;"


def _cell(soup, tag, text, style, colspan=None):
    cell = soup.new_tag(tag)
    cell.string = text
    cell["style"] = style
    if colspan:
        cell["colspan"] = colspan
    return cell


def _skill_row(soup, row):
    rendered = soup.new_tag("tr")
    for selector in (
        ".skill-name-and-permacode span",
        ".permacode",
        ".skill-time",
        ".skill-questions",
    ):
        cell = row.select_one(selector)
        rendered.append(_cell(soup, "td", cell.get_text().strip() if cell else "N/A", CELL_STYLE))

    scores = row.select(".skill-improvement .score")
    improvement = (
        f"{scores[0].get_text()} to {scores[1].get_text()}" if len(scores) == 2 else "N/A"
    )
    rendered.append(_cell(soup, "td", improvement, CELL_STYLE))
    return rendered


def process_table_html(table_html: str) -> str:
    soup = BeautifulSoup(table_html, "html.parser")
    table = soup.new_tag("table")
    table["style"] = "border-collapse: collapse; width: 100%;"

    header = soup.new_tag("tr")
    for text in ("Subject/Category/Skill", "Code", "Time Spent", "#", "Score Improvement"):
        header.append(
            _cell(
                soup,
                "th",
                text,
                f"{CELL_STYLE} background-color: #f2f2f2;",
            )
        )
    table.append(header)

    for row in soup.select('div[class*="row"]'):
        classes = row.get("class")
        if not isinstance(classes, list):
            continue
        if "subject-grade-row" in classes:
            table.append(
                _cell_row(
                    soup,
                    row.get_text().strip(),
                    "font-weight: bold; background-color: #e6e6e6;",
                )
            )
        elif "category-row" in classes:
            table.append(
                _cell_row(
                    soup,
                    row.get_text().strip(),
                    "font-style: italic; background-color: #f9f9f9;",
                )
            )
        elif "skill-row" in classes:
            table.append(_skill_row(soup, row))

    return str(table)


def _cell_row(soup, text, style):
    row = soup.new_tag("tr")
    row.append(_cell(soup, "td", text, f"{CELL_STYLE} {style}", "5"))
    return row
