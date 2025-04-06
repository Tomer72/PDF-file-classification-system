# ai_extraction.py
from pathlib import Path
import re
import openai
from models import ExtractedInfo
from pdf_processing import extract_text_from_pdf
from config import OPENAI_API_KEY

def text_ai_analysis(text: str):
    """Extracts fields from text using OpenAI's GPT-3.5 turbo model."""
    client = openai.OpenAI(api_key=OPENAI_API_KEY)
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are an assistant that extracts metadata from exams."},
            {"role": "user", "content": f"""here are the first 30 lines of a scanned exam PDF:
             
             {text}

            Extract the following fields in JSON format:

           
            - course_name # Look out for the course name related to the degree, make sure the course name has ONLY hebrew letters and is a valid word in hebrew, make sure to get the full name of the course. e.g correct - "מבוא למדעי המחשב", incorrect - "מבוא למדעי המחשב והתכנות".

            - semester # Look for the semester, like "א" or "ב" WITHOUT the ending "׳" character. it may be "קיץ" or "ק" or "ח" or "חורף" or "אביב", 
            notice that "קיץ" = "ג", "חורף" = "א", "אביב" = "ב" or "ק" = "קיץ" - classify "ק" or "ק׳" as "קיץ" USE ONLY the "א","ב","קיץ" letters. Also notice that semester may be written as "סמ׳".            
            
            - year # Look for the year of the exam - Search for date. The year should be in the format "2022" and not "22".
            
            - moed # Look for the moed of the exam - like "א" or "ב". WITHOUT the ending "׳" character, notice that it may be "", and "" = "".
            
            - degree # Look for the department or faculty name, like "מדעי המחשב" or "הנדסת חשמל" if none found, decide by the context. 
            there is only ONE option for the degree name:  "תעשייה וניהול".

            The document is written in Hebrew. Return ONLY pure JSON without triple backticks or explanation.
            Ensure ALL values in the JSON are STRINGS. for example: the years should be "2022" and not 2022,
              the semster should be only "א"|"ב"|"ג"|"קיץ".
            While finding semster, make sure you extract the closests word or letter that comes right after the text "סמסטר" or "סמ׳".

            If a field is not found clearly in the text, set its value to "unknown".

            """}
        ],
        temperature=0.0,
        max_tokens=300
    )
    return response.choices[0].message.content

def field_ai_analysis(pdf_path: Path):
    """Returning the extracted info."""
    text = extract_text_from_pdf(pdf_path, 60)
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