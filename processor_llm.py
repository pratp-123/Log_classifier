from dotenv import load_dotenv
from groq import Groq
import json
import re
import os

load_dotenv()

groq = Groq()

def classify_with_llm(log_msg):
    """
    Generate a variant of the input sentence. For example,
    If input sentence is "User session timed out unexpectedly, user ID: 9250.",
    variant would be "Session timed out for user 9251"
    """
    # read model from env so you can swap without editing code
    model = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")

    prompt = f'''Classify the log message into one of these categories: 
    (1) Workflow Error, (2) Deprecation Warning.
    If you can't figure out a category, use "Unclassified".
    Put the category inside <category> </category> tags. 
    Log message: {log_msg}'''

    try:
        chat_completion = groq.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model=model,
            temperature=0.5
        )
    except groq.BadRequestError as e:
        # common cause: model has been decommissioned
        err_text = str(e)
        if "model_decommissioned" in err_text or "decommissioned" in err_text:
            raise RuntimeError(
                f"The model '{model}' is unavailable/decommissioned. "
                "Set a supported model via the GROQ_MODEL env var (or update your .env) "
                "and re-run. See https://console.groq.com/docs/deprecations for guidance."
            ) from e
        raise

    content = chat_completion.choices[0].message.content
    match = re.search(r'<category>(.*)<\/category>', content, flags=re.DOTALL)
    category = "Unclassified"
    if match:
        category = match.group(1).strip()

    return category


if __name__ == "__main__":
    print(classify_with_llm(
        "Case escalation for ticket ID 7324 failed because the assigned support agent is no longer active."))
    print(classify_with_llm(
        "The 'ReportGenerator' module will be retired in version 4.0. Please migrate to the 'AdvancedAnalyticsSuite' by Dec 2025"))
    print(classify_with_llm("System reboot initiated by user 12345."))