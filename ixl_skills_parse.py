#!/usr/bin/env python3

import requests
import pandas as pd
from bs4 import BeautifulSoup


def fetch_ixl_content():
    # Headers to mimic browser request
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }

    url = "https://www.ixl.com/science/earth-science"

    try:
        print("hi")
        response = requests.get(url, headers=headers)
        response.raise_for_status()  # Raise an exception for bad status codes
        print(response.status_code)

        # Parse HTML
        soup = BeautifulSoup(response.text, "html.parser")

        skills = []
        skill_categories = soup.find_all("div", class_="skill-tree-category")

        for category in skill_categories:
            grade = category.find(
                "span", class_="skill-tree-skills-header"
            ).text.strip()
            skill_nodes = category.find_all("li", class_="skill-tree-skill-node")

            for node in skill_nodes:
                skill_number = node.find(
                    "span", class_="skill-tree-skill-number"
                ).text.strip()
                skill_name = node.find(
                    "span", class_="skill-tree-skill-name"
                ).text.strip()
                skill_link = node.find("a", class_="skill-tree-skill-link")
                permacode = skill_link["data-permacode"] if skill_link else None

                skills.append(
                    {
                        "grade": grade,
                        "skill_number": skill_number,
                        "skill_name": skill_name,
                        "permacode": permacode,
                    }
                )

        # Create DataFrame
        df = pd.DataFrame(skills)

        # Pivot the DataFrame
        pivot_df = df.pivot(
            index=["skill_number", "skill_name"], columns="grade", values="permacode"
        )

        return pivot_df

    except requests.exceptions.RequestException as e:
        print(f"Error fetching content: {e}")
        return None


if __name__ == "__main__":
    print("hi")
    # Fetch and display results
    result_df = fetch_ixl_content()
    if result_df is not None:
        print(result_df)
