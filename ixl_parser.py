from bs4 import BeautifulSoup


def process_table_html(table_html: str | None) -> str:
    if not table_html:
        return ""

    soup = BeautifulSoup(table_html, "html.parser")

    # Create a new table
    new_table = soup.new_tag("table")
    new_table["style"] = "border-collapse: collapse; width: 100%;"

    # Add header row
    header = soup.new_tag("tr")
    headers = [
        "Subject/Category/Skill",
        "Code",
        "Time Spent",
        "#",
        "Score Improvement",
    ]
    for h in headers:
        th = soup.new_tag("th")
        th.string = h
        th["style"] = "border: 1px solid #ddd; padding: 8px; background-color: #f2f2f2;"
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
            td["colspan"] = "5"
            td["style"] = (
                "border: 1px solid #ddd; padding: 8px; font-weight: bold; background-color: #e6e6e6;"
            )
            new_row.append(td)
        elif "category-row" in row_classes:
            td = soup.new_tag("td")
            td.string = row.get_text().strip()
            td["colspan"] = "5"
            td["style"] = (
                "border: 1px solid #ddd; padding: 8px; font-style: italic; background-color: #f9f9f9;"
            )
            new_row.append(td)
        elif "skill-row" in row_classes:
            score_cells = row.select(".skill-improvement .score")
            plain_cells = [
                row.select_one(".skill-name-and-permacode span"),
                row.select_one(".permacode"),
                row.select_one(".skill-time"),
                row.select_one(".skill-questions"),
            ]

            for cell in plain_cells:
                td = soup.new_tag("td")
                td["style"] = "border: 1px solid #ddd; padding: 8px;"
                td.string = cell.get_text().strip() if cell else "N/A"
                new_row.append(td)

            score_td = soup.new_tag("td")
            score_td["style"] = "border: 1px solid #ddd; padding: 8px;"
            score_td.string = (
                f"{score_cells[0].get_text().strip()} to {score_cells[1].get_text().strip()}"
                if len(score_cells) == 2
                else "N/A"
            )
            new_row.append(score_td)

        new_table.append(new_row)

    return str(new_table)
