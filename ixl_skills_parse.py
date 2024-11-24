from typing import Union
import requests
import pandas as pd
from bs4 import BeautifulSoup


def get_codes_from_ixl(url: str) -> Union[pd.DataFrame, None]:
    """
    Fetches Earth Science skills data from the IXL website and returns it in a DataFrame.
    If any errors occur during the request or parsing, prints an error message and returns None.

    Returns:
        A DataFrame containing the skills data, or None if an error occurred.
    """
    # Headers to mimic browser request
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }

    try:
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

        return df

    except requests.exceptions.RequestException as e:
        print(f"Error fetching content: {e}")
        return None


def earch_science_skills_data() -> Union[pd.DataFrame, None]:
    # Define the URL of the Earth Science section on the IXL website
    url = "https://www.ixl.com/science/earth-science"

    # Fetch the data from the URL and store it in a DataFrame
    df = get_codes_from_ixl(url)

    # Define a mapping from the grade names to their corresponding numeric values
    grade_map = {
        "Kindergarten skills": 0,
        "First-grade skills": 1,
        "Second-grade skills": 2,
        "Second-grade skills": 2,
        "Third-grade skills": 3,
        "Fourth-grade skills": 4,
        "Fifth-grade skills": 5,
        "Sixth-grade skills": 6,
        "Seventh-grade skills": 7,
        "Eighth-grade skills": 8,
    }

    # Map the grade names in the DataFrame to their corresponding numeric values
    df.grade = df.grade.map(grade_map)

    # Extract the skill number from the skill_number column and store it in a new column called 'skill'
    df["skill"] = df["skill_number"].str.split(".").str[0]

    # Filter the DataFrame to only include rows with a grade of 6 or higher, and pivot the DataFrame to create a new DataFrame
    # where each row corresponds to a unique skill, and each column corresponds to a grade
    pivot_df = df.query("grade >=6").pivot(
        # index=['skill_name'],
        index=["skill", "skill_name"],
        columns="grade",
        values="permacode",
    )

    # Fill any missing values in the pivot DataFrame with an empty string
    return pivot_df.fillna("")


def algebra2_skills_data() -> Union[pd.DataFrame, None]:
    url = "https://www.ixl.com/math/algebra-2"
    df = get_codes_from_ixl(url)

    return df.set_index(["grade", "skill_number", "skill_name"])
