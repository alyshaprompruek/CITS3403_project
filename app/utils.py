import requests
from bs4 import BeautifulSoup
import json

def parse_gemini_response(gemini_data):
    """
    Parse the response from Gemini API to extract summary and links.

    Args:
        gemini_data (dict): The JSON response from Gemini API

    Returns:
        tuple: A tuple containing the summary (str) and a list of links (list of dicts).
               Returns ("", []) on error.
    """
    summary = ""
    links = []

    try:
        if 'candidates' in gemini_data and gemini_data['candidates']:
            first_candidate = gemini_data['candidates'][0]
            if 'content' in first_candidate and 'parts' in first_candidate['content']:
                for part in first_candidate['content']['parts']:
                    if 'text' in part:
                        ai_response_text = part['text']
                        paragraphs = ai_response_text.split('\n\n')
                        if paragraphs:
                            summary = paragraphs[0].strip()

                        lines = ai_response_text.split('\n')
                        for line in lines:
                            line = line.strip()
                            if line.startswith("Link Name:"):
                                name_part = line.replace("Link Name:", "", 1).strip()
                                url = ""

                                if "[" in name_part and "]" in name_part:
                                    url_start = name_part.find("[")
                                    url_end = name_part.find("]")
                                    if url_start < url_end:
                                        url = name_part[url_start+1:url_end].strip()
                                        name = name_part[:url_start].strip()
                                    else:
                                        name = name_part
                                else:
                                    name = name_part

                                links.append({"name": name, "url": url})

        return summary, links

    except Exception:
        return "", []

def fetch_unit_details_and_summary(unit_code, gemini_api_key):
    """
    Fetches UWA unit details and generates a summary and relevant links using the Gemini API.

    Args:
        unit_code (str): The UWA unit code (e.g., CITS1001).
        gemini_api_key (str): Your Google Cloud Gemini API key.

    Returns:
        tuple: A tuple containing the summary (str) and a list of links (list of dicts).
               Returns ("", []) on error.
    """
    url = f"https://handbooks.uwa.edu.au/unitdetails?code={unit_code}"
    try:
        response = requests.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        description = soup.find(string="Description").find_next('p').text if soup.find(string="Description") else ""
        outcomes = soup.find(string="Outcomes").find_next('p').text if soup.find(string="Outcomes") else ""
        unit_text = f"Description: {description}\nOutcomes: {outcomes}"

        gemini_api_url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent"
        headers = {
            "Content-Type": "application/json",
        }

        prompt = (
            "Please provide a brief summary of this university unit in the first paragraph.\n"
            "Then, list 2-3 *actual* publicly accessible study resources with real working links in this format:\n"
            "Link Name: Descriptive Title [https://example.com/resource]\n\n"
            f"{unit_text}"
        )

        payload = {
            "contents": [{
                "parts": [{"text": prompt}]
            }],
            "safetySettings": [
                {
                    "category": "HARM_CATEGORY_HARASSMENT",
                    "threshold": "BLOCK_MEDIUM_AND_ABOVE"
                },
                {
                    "category": "HARM_CATEGORY_HATE_SPEECH",
                    "threshold": "BLOCK_MEDIUM_AND_ABOVE"
                },
                {
                    "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
                    "threshold": "BLOCK_MEDIUM_AND_ABOVE"
                },
                {
                    "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
                    "threshold": "BLOCK_MEDIUM_AND_ABOVE"
                }
            ]
        }

        gemini_api_url_with_key = f"{gemini_api_url}?key={gemini_api_key}"
        gemini_response = requests.post(gemini_api_url_with_key, json=payload, headers=headers)
        gemini_response.raise_for_status()

        gemini_data = gemini_response.json()
        return parse_gemini_response(gemini_data)

    except Exception:
        return "", []
