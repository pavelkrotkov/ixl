from bs4 import BeautifulSoup


def parse_activity_html(activity_html):
    soup = BeautifulSoup(activity_html, "html.parser")
    parsed_data = []
    date_count = 0

    for tr in soup.find_all("tr"):
        if tr.get("class", []) == []:
            date_td = tr.find("td", class_="dateHeader")
            if date_td:
                date_count += 1
                if date_count >= 3:
                    break  # Stop parsing after the second date row
                xp_span = date_td.find("span", class_="dateTotalXP")
                xp = xp_span.get_text(strip=True) if xp_span else ""

                # Remove the XP span from the date_td to get the date
                if xp_span:
                    xp_span.extract()
                date = date_td.get_text(strip=True)
                parsed_data.append({"type": "date", "date": date, "xp": xp})
        elif date_count < 3:  # Only parse task rows before the third date row
            task_type_td = tr.find("td", class_="taskTypeColumn")
            task_name_div = tr.find("div", class_="taskName")
            completion_td = tr.find("td", class_="taskCompletedColumn")
            points_span = tr.find("span", class_="taskPoints") or tr.find(
                "span", class_="completedTaskPoints"
            )

            parsed_data.append(
                {
                    "type": "task",
                    "task_type": (
                        task_type_td.get_text(strip=True) if task_type_td else ""
                    ),
                    "task_name": (
                        task_name_div.get_text(strip=True) if task_name_div else ""
                    ),
                    "completion": (
                        completion_td.get_text(strip=True) if completion_td else ""
                    ),
                    "points": (
                        points_span.get_text(strip=True) if points_span else ""
                    ),
                }
            )

    return parsed_data


def format_activity_html(parsed_data):
    html = "<table border='1' style='border-collapse: collapse; width: 100%;'>"
    html += "<tr style='background-color: #f2f2f2;'><th>Type</th><th>Name</th><th>Completion</th><th>Points</th></tr>"

    for item in parsed_data:
        if item["type"] == "date":
            html += "<tr style='background-color: #e6e6e6;'>"
            html += f"<td colspan='4'><strong>{item['date']} - {item['xp']}</strong></td></tr>"
        else:
            html += f"<tr><td>{item['task_type']}</td><td>{item['task_name']}</td><td>{item['completion']}</td><td>{item['points']}</td></tr>"

    html += "</table>"
    return html
