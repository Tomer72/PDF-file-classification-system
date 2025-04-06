# main.py
from pathlib import Path
import time
import re
import json
from fuzzywuzzy import process
from file_utils import object_type_recognizer, pdf_suffix_adding, safe_file_move
from pdf_processing import is_test, is_test_folder
from ai_extraction import field_ai_analysis
from config import ORIGIN_PATH, GOAL_PATH, JSON_PATH

def normalize_course_name(name: str) -> str:
    """Normalizes course name by removing special characters and extra spaces."""
    name = re.sub(r'[^\w\s]', '', name)
    name = ' '.join(name.split())
    return name

def check_course_name(course_name, degree, JSON_PATH):
    """Checking if the course name is valid and matches existing courses."""
    path = Path(JSON_PATH) / "courses.json"
    with open(path) as f:
        data = json.load(f)
    
    course_names = data[str(degree)]
    
    normalized_input = normalize_course_name(course_name)
    print(f"Original course name: {course_name}")
    print(f"Normalized course name: {normalized_input}")
    
    match_result = process.extractOne(normalized_input, course_names, score_cutoff=70)
    if match_result:
        best_match_name, score = match_result
        print(f"Found match: {best_match_name} with score: {score}")
        return best_match_name
    else:
        print(f"No match found for: {course_name}")
        return course_name

def file_classifier(ORIGIN_PATH, GOAL_PATH):
    """iterating over the files in the origin path and classifying them to the goal path"""
    source = Path(ORIGIN_PATH)
    goal = Path(GOAL_PATH)

    print(f"Starting scan of directory: {source}")
    print(f"Files will be moved to: {goal}")

    for f in source.rglob("*"):
        print(f"\nProcessing: {f}")
        curr_path = f

        if not f.is_file() or f.name == ".DS_Store":
            print(f"Skipping: {f} (not a file or .DS_Store)")
            continue
        
        is_in_root = f.parent == source
        is_in_course_folder = f.parent.parent == source
        is_inside_test_folder = any(is_test_folder(part) for part in f.parts)
        if not (is_in_root or is_in_course_folder or is_inside_test_folder):
            print(f"Skipping: {f} (not in a course or test folder)")
            continue

        print(f"Checking if file is PDF: {f}")
        updated_file = pdf_suffix_adding(f, GOAL_PATH)
        if not updated_file:
            print(f"Skipped non-PDF or moved: {f}")
            continue
        f = updated_file

        print(f"Extracting text from PDF: {f}")
        time.sleep(1.5)

        if is_test(f):
            print(f"File identified as test: {f}")
            course_name, year, semester, moed, degree = field_ai_analysis(f)
            print(f"Extracted info - Course: {course_name}, Year: {year}, Semester: {semester}, Moed: {moed}, Degree: {degree}")
            
            course_name = check_course_name(course_name, degree, JSON_PATH)
            print(f"Checked course name: {course_name}")

            try:
                year_int = int(year)
                if year_int < 2000 or year_int > 2025:
                    print(f"Invalid year: {year}")
                    year = "unknown"
            except ValueError:
                print(f"Failed to parse year as int: {year}")
                year = "unknown"
         
            if course_name == "unknown" or year == "unknown" or semester == "unknown" or moed == "unknown" or degree == "unknown":
                not_a_test = goal / "not_a_test"
                not_a_test.mkdir(parents=True, exist_ok=True)
                f.replace(not_a_test / f.name)
                print(f"Moved to not_a_test: {f} (missing course name or year)")
                continue
            
            temp_path = goal / degree
            temp_path.mkdir(parents=True, exist_ok=True)
            dirs_arr = [d.name for d in temp_path.iterdir() if d.is_dir()]
            if dirs_arr:
                result = process.extractOne(course_name, dirs_arr, score_cutoff=85)
                if result:
                    match, score = result
                    if score >= 85:
                        course_name = match
                        print(f"Matched existing course name: {course_name}")
                else:
                    print(f"No existing directories to match against for degree: {degree}")

            new_name = f"{year} סמסטר {semester} מועד {moed}.pdf"
            new_dir = goal / degree / course_name / "מבחנים" / year
            new_dir.mkdir(parents=True, exist_ok=True)
            new_path = new_dir / new_name
            final_path = safe_file_move(f, new_path)
            print(f"Successfully moved test: {f} -> {final_path}")
        else:
            print(f"File not identified as test: {f}")
            continue

if __name__ == "__main__":
    file_classifier(ORIGIN_PATH,GOAL_PATH)