import re, json


def extract_response_and_json(full_output):
    # Cari blok JSON terakhir
    json_match = re.search(r"```json(.*?)```", full_output, re.DOTALL)

    if json_match:
        json_text = json_match.group(1).strip()
        try:
            json_data = json.loads(json_text)
        except json.JSONDecodeError:
            json_data = {}
        # Potong JSON dari output untuk ambil response text
        response_text = full_output.replace(json_match.group(0), "").strip()
    else:
        json_data = {}
        response_text = full_output.strip()

    return response_text, json_data