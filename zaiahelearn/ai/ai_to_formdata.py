# services/ai_to_formdata.py

from django.http import QueryDict

def build_question_formdata(ai_questions):
    """
    Convert AI JSON questions into a QueryDict compatible
    with save_question().
    """

    qd = QueryDict(mutable=True)

    for q in ai_questions:
        qd.appendlist("question_content_html[]", q["question"])
        qd.appendlist("correct_choice[]", q.get("answer","A"))
        qd.appendlist("difficulty[]", q.get("difficulty","medium"))

        qd.appendlist("option_A[]", q.get("A",""))
        qd.appendlist("option_B[]", q.get("B",""))
        qd.appendlist("option_C[]", q.get("C",""))
        qd.appendlist("option_D[]", q.get("D",""))

    return qd