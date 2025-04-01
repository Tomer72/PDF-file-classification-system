from imports import *

class ExtractedInfo(BaseModel):
        
        course_name: str = Field(description="The name of the course")
        semester: str = Field(description="The semester of the test")
        year: str = Field(description="The year of the test")
        moed: str = Field(description="The moed of the test")
        degree: str = Field(description="The degree")


load_dotenv()
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
ORIGIN_PATH = os.environ.get("ORIGIN_PATH")
GOAL_PATH = os.environ.get("GOAL_PATH")
JSON_PATH = os.environ.get("JSON_PATH")
 
def object_type_recognizer(path):
    """Recognizes if the path is a file or a directory."""
    return Path(path).is_file()

def pdf_detector(pdf_path):
    """Checks if file is a valid PDF."""

    with open(pdf_path, "rb") as f:
        kind = filetype.guess(f.read(261))
    if kind:
        return kind.mime == "application/pdf"
    return magic.from_file(str(pdf_path), mime=True) == "application/pdf"

def pdf_suffix_adding(ORIGIN_PATH, GOAL_PATH):
    """ checking if the current file is actually a file and actually a pdf file, 
    and adding .pdf suffix in order to make sure the file will open without any problems"""

    path = Path(ORIGIN_PATH)
    goal = Path(GOAL_PATH)

    if not object_type_recognizer(path): 
        return None

    if not pdf_detector(path):
        not_pdf_dir = goal / "not_a_pdf"
        not_pdf_dir.mkdir(parents=True, exist_ok=True)
        path.replace(not_pdf_dir / path.name)
        print(f"Moved non-PDF: {path} -> {not_pdf_dir / path.name}")
        return None

    if path.suffix.lower() != ".pdf":
        new_path = path.with_suffix('.pdf')
        path.rename(new_path)
        print(f"Renamed: {path} -> {new_path}")
        return new_path
    return path

def extract_text_with_fitz(pdf_path, num_lines):
    """Extracts text from a PDF file using fitz."""

    text = ""
    try:
        with fitz.open(pdf_path) as doc:
            if doc.page_count > 0:
                first_page = doc[0]
                text = first_page.get_text()
                if num_lines:
                    return "".join(text.strip().splitlines()[:num_lines])  
                return text
            return ""
    except Exception as e:
        print(f"Error opening PDF with fitz: {e}")
        return ""

def extract_text_with_tesseract(pdf_path, num_lines):
    """Extracts text from a PDF file using Tesseract OCR and PIL."""

    full_text = ""
    try:
        doc = fitz.open(pdf_path)
        if doc.page_count > 0:
            page = doc.load_page(0)
            pix = page.get_pixmap(matrix=fitz.Matrix(300/72, 300/72))
            img_data = pix.tobytes("png")
            img = Image.open(io.BytesIO(img_data))
            enhancer = ImageEnhance.Contrast(img)
            img = enhancer.enhance(1.5)
            enhancer = ImageEnhance.Brightness(img)
            img = enhancer.enhance(1.2)
            img = img.convert('L')
            text = pytesseract.image_to_string(img, lang='heb')
            
            full_text += text + "\n"
            if num_lines:
                lines = full_text.strip().splitlines()
                return "".join(lines[:num_lines])
            return full_text
        return ""
    except Exception as e:
        print(f"Error implementing OCR with pytesseract: {e}")
        return full_text

def extract_text_from_pdf(pdf_path, num_lines):
    """Extracts text from a PDF file using fitz and Tesseract OCR."""

    text = extract_text_with_fitz(pdf_path, num_lines)
    if text.strip():
        print(f"Successfully parsed {pdf_path} with fitz")
        return text
    print(f"Error with fitz on {pdf_path}, trying Tesseract")
    text = extract_text_with_tesseract(pdf_path, num_lines)
    if text.strip():
        print(f"Successfully parsed {pdf_path} with Tesseract")
    return text    

def is_test(pdf_path):
    """Checks if the PDF file is actually a test."""

    text = extract_text_from_pdf(pdf_path, num_lines=60)
    keywords = ["מבחן", "מבחנים", "בחינה", "מועד", "סמסטר", "שנה", "תשע", "תשפ","נבחנים"]
    matches = [keywords for keyword in keywords if keyword in text]
    return len(matches) >= 2

def is_test_folder(folder_name: str):
    """Checks if the folder name contains the word 'מבחן' or 'בוחן'."""

    return bool(re.search(r"(מבח[ןנ]|בוח[ןנ])", folder_name))

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
    
    # Normalize the input course name
    normalized_input = normalize_course_name(course_name)
    print(f"Original course name: {course_name}")
    print(f"Normalized course name: {normalized_input}")
    
    # Try to find a match with a lower threshold
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
        
        # Check if the file is in the root, course folder, or test folder
        is_in_root = f.parent == source
        is_in_course_folder = f.parent.parent == source
        is_inside_test_folder = any(is_test_folder(part) for part in f.parts)

        if not (is_in_root or is_in_course_folder or is_inside_test_folder):
            print(f"Skipping: {f} (not in a course or test folder)")
            continue

        
        # Checking if the current file is a PDF file and adding the .pdf suffix
        print(f"Checking if file is PDF: {f}")
        updated_file = pdf_suffix_adding(f, GOAL_PATH)
        if not updated_file:
            print(f"Skipped non-PDF or moved: {f}")
            continue
        f = updated_file

        # Extracting fields from the PDF file
        print(f"Extracting text from PDF: {f}")
        time.sleep(1.5)

        
        if is_test(f):
            print(f"File identified as test: {f}")

            course_name, year, semester, moed, degree = field_ai_analysis(curr_path)

            print(f"Extracted info - Course: {course_name}, Year: {year}, Semester: {semester}, Moed: {moed}, Degree: {degree}")
            
            course_name = check_course_name(course_name, degree, JSON_PATH)
            print(f"Checked course name: {course_name}")

            # Checking if the year is valid
            try:
                year_int = int(year)
                if year_int < 2000 or year_int > 2025:
                    print(f"Invalid year: {year}")
                    year = "unknown"
            except ValueError:
                print(f"Failed to parse year as int: {year}")
                year = "unknown"
         
            # Moving the file to the goal path
            if course_name == "unknown" or year == "unknown" or semester == "unknown" or moed == "unknown" or degree == "unknown":
                not_a_test = goal / "not_a_test"
                not_a_test.mkdir(parents=True, exist_ok=True)
                f.replace(not_a_test / f.name)
                print(f"Moved to not_a_test: {f} (missing course name or year)")
                continue
            
            # Checking if the course name already exists using thefuzz, checking only directories
            
            temp_path = goal / degree
            temp_path.mkdir(parents=True, exist_ok=True)  # Create the degree directory if it doesn't exist
            files_arr = [file.name for file in temp_path.iterdir()]
                
            if files_arr:
                result = process.extractOne(course_name, files_arr, score_cutoff=85) # Only try to match if there are existing directories
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
            f.replace(new_path)
            print(f"Successfully moved test: {f} -> {new_path}")

        else:
            print(f"File not identified as test: {f}")
            continue

def text_ai_analysis(text: str):
    """Extracts fields from text using OpenAI's GPT-3.5 turbo model."""

    client = openai.OpenAI(api_key = OPENAI_API_KEY)

    response = client.chat.completions.create(
        model = "gpt-3.5-turbo",
        messages = [

            {"role": "system", "content": "You are an assistant that extracts metadata from exams."},
            {"role": "user", "content": f"""here are the first 30 lines of a scanned exam PDF:
             
             {text}

            Extract the following fields in JSON format:

           
            - course_name # Look out for the course name related to the degree, make sure the course name has ONLY hebrew letters and is a valid word in hebrew, make sure to get the full name of the course. e.g correct - "מבוא למדעי המחשב", incorrect - "מבוא למדעי המחשב והתכנות".

            - semester # Look for the semester, like "א" or "ב" WITHOUT the ending "׳" character. it may be "קיץ" or "ק" or "ח" or "חורף" or "אביב", notice that "קיץ" = "ג", "חורף" = "א", "אביב" = "ב", USE ONLY the "א","ב","קיץ" letters. Also notice that semester may be written as "סמ׳".            
            
            - year # Look for the year of the exam - Search for date. The year should be in the format "2022" and not "22".
            
            - moed # Look for the moed of the exam - like "א" or "ב". WITHOUT the ending "׳" character, notice that it may be "", and "" = "".
            
            - degree # Look for the department or faculty name, like "מדעי המחשב" or "הנדסת חשמל" if none found, decide by the context. 
            there is only ONE option for the degree name:  "תעשייה וניהול".

            The document is written in Hebrew. Return ONLY pure JSON without triple backticks or explanation.
            Ensure ALL values in the JSON are STRINGS. for example: the years should be "2022" and not 2022,
              the semster should be only "א"|"ב"|"ג"|"קיץ".
            While finding semster, make sure you extract the closests word or letter that comes right after the text "סמסטר" or "סמ׳".

            If a field is not found clearly in the text, set its value to "unknown".

            """} ],
            temperature = 0.0,
            max_tokens = 300
    )

    return response.choices[0].message.content

def field_ai_analysis(pdf_path: Path):
    """Returning the extracted info."""

    text = extract_text_from_pdf(pdf_path,60)
    extracted_info = text_ai_analysis(text)
    print(text)
    clean_response = re.sub(r"^```json\\s*|\\s*```$", "", extracted_info.strip(), flags=re.DOTALL)

    try:
        extracted_info = ExtractedInfo.model_validate_json(clean_response)

        return (
            extracted_info.course_name,
            extracted_info.year,
            extracted_info.semester,
            extracted_info.moed,
            extracted_info.degree
        )
    except Exception as e:
        print(f"Failed to parse: {e}")
        return "", "", "", "", ""

if __name__ == "__main__":
    file_classifier(ORIGIN_PATH, GOAL_PATH)

