from bs4 import BeautifulSoup


def process_table_html(table_html):
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
        th[
            "style"
        ] = "border: 1px solid #ddd; padding: 8px; background-color: #f2f2f2;"
        header.append(th)
    new_table.append(header)

    # Process rows
    for row in soup.select('div[class*="row"]'):
        new_row = soup.new_tag("tr")

        if "subject-grade-row" in row.get("class", []):
            td = soup.new_tag("td")
            td.string = row.text.strip()
            td["colspan"] = "5"
            td[
                "style"
            ] = "border: 1px solid #ddd; padding: 8px; font-weight: bold; background-color: #e6e6e6;"
            new_row.append(td)
        elif "category-row" in row.get("class", []):
            td = soup.new_tag("td")
            td.string = row.text.strip()
            td["colspan"] = "5"
            td[
                "style"
            ] = "border: 1px solid #ddd; padding: 8px; font-style: italic; background-color: #f9f9f9;"
            new_row.append(td)
        elif "skill-row" in row.get("class", []):
            cells = [
                row.select_one(".skill-name-and-permacode span"),
                row.select_one(".permacode"),
                row.select_one(".skill-time"),
                row.select_one(".skill-questions"),
                row.select(".skill-improvement .score"),
            ]

            for i, cell in enumerate(cells):
                td = soup.new_tag("td")
                td["style"] = "border: 1px solid #ddd; padding: 8px;"
                if i == 4 and cell:  # Score Improvement
                    td.string = (
                        f"{cell[0].text} to {cell[1].text}"
                        if len(cell) == 2
                        else "N/A"
                    )
                elif cell:
                    td.string = cell.text.strip()
                else:
                    td.string = "N/A"
                new_row.append(td)

        new_table.append(new_row)

    return str(new_table)
