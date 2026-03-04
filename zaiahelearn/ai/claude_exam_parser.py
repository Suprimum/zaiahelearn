# services/claude_exam_parser.py

import base64, json, re
from anthropic import Anthropic
from decouple import config



client = Anthropic(api_key=config("ANTHROPIC_API_KEY"))










def extract_json_from_claude(response):

    # Join all text blocks Claude returned
    full_text = ""
    for block in response.content:
        if hasattr(block, "text"):
            full_text += block.text

    full_text = full_text.strip()

    # 1️Try to extract JSON inside ```json ... ```
    code_block_match = re.search(r"```json\s*(.*?)\s*```", full_text, re.DOTALL)

    if code_block_match:
        json_text = code_block_match.group(1)
    else:
        # 2️Fallback: try whole response
        json_text = full_text

    # 3️Remove stray backticks or spaces
    json_text = json_text.strip("` \n")

    # Try loading JSON safely
    try:
        return json.loads(json_text)
    except json.JSONDecodeError as e:
        print("❌ Claude JSON parse error:", e)
        print("RAW CLAUDE OUTPUT:\n", full_text)
        return []
    





def claude_questions_image_parser(image_file):

    # reset file pointer
    image_file.seek(0)

    encoded = base64.b64encode(image_file.read()).decode("utf-8")

    prompt = """
You are an expert exam parser.

From this image:

1. Detect the subject (math, physics, chemistry, biology, english, general)
2. Extract all MCQs
3. Detect if the question contains math formulas
4. Detect if the question references a diagram/figure
5. Infer the correct answer logically
6. Provide short reasoning
7. Provide confidence (0-1)

Return ONLY JSON list like:

[
{
"subject":"math",
"question":"...",
"A":"...",
"B":"...",
"C":"...",
"D":"...",
"answer":"A",
"explanation":"...",
"confidence":0.92,
"contains_math":true,
"contains_diagram":false
}
]
"""

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=4000,
        temperature=0,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": prompt
                    },
                    {
                        "type": "image",
                        "source":{
                            "type":"base64",
                            "data": encoded,
                            "media_type": image_file.content_type or "image/png"
                        },
                    }
                ]
            }
        ]
    )


    # Extract text safely from Claude response blocks
    
    return extract_json_from_claude(response)