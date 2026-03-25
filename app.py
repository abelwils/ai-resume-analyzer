from flask import Flask, render_template, request, Response
import PyPDF2
import spacy

app = Flask(__name__)

nlp = spacy.load("en_core_web_sm")

history = []
latest_resume = ""


def extract_text(file):
    text = ""
    try:
        reader = PyPDF2.PdfReader(file)
        for page in reader.pages:
            t = page.extract_text()
            if t:
                text += t
    except:
        pass
    return text.lower()


def analyze_resume_ai(text):
    score = 0
    ats_score = 0
    suggestions = []

    doc = nlp(text)

    skills_db = [
        "python", "java", "html", "css", "javascript", "sql", "flask",
        "teaching", "classroom", "curriculum", "student", "education",
        "management", "leadership", "communication", "teamwork", "marketing",
        "analysis", "design"
    ]

    found_skills = list(set([token.text for token in doc if token.text in skills_db]))

    score += len(found_skills) * 3
    ats_score += len(found_skills) * 4

    for sec in ["experience", "education", "skills"]:
        if sec in text:
            ats_score += 10
        else:
            suggestions.append(f"Add '{sec}' section.")

    if "%" in text or "improved" in text:
        score += 15
        ats_score += 15
    else:
        suggestions.append("Add measurable achievements.")

    if any(w in text for w in ["developed", "managed", "led"]):
        score += 10
    else:
        suggestions.append("Use action verbs.")

    if len(list(doc.sents)) > 5:
        score += 10
    else:
        suggestions.append("Add more descriptions.")

    if "teacher" in text:
        field = "Education"
    elif "python" in text:
        field = "Technology"
    else:
        field = "General"

    if field == "Technology" and "github" not in text:
        suggestions.append("Add GitHub portfolio.")

    if field == "Education":
        suggestions.append("Add student performance results.")

    if len(text.split()) < 200:
        suggestions.append("Resume too short.")

    final_score = min(score, 100)
    ats_score = min(ats_score, 100)

    if final_score < 40:
        summary = "Needs improvement."
    elif final_score < 70:
        summary = "Average resume."
    else:
        summary = "Strong resume."

    if not suggestions:
        suggestions.append("Good resume. Customize for jobs.")

    return final_score, ats_score, found_skills, suggestions, summary, field


def rewrite_resume(text):
    improved = []
    sentences = text.split(".")

    for s in sentences:
        s = s.strip()
        if len(s) > 20:
            improved.append("✔️ " + s.capitalize() + ".")

    if not improved:
        improved.append("Add more content.")

    return improved


@app.route('/', methods=['GET', 'POST'])
def index():
    global latest_resume

    if request.method == 'POST':
        file = request.files.get('resume')

        if not file:
            return render_template('index.html')

        text = extract_text(file)

        score, ats_score, skills, suggestions, summary, field = analyze_resume_ai(text)

        improved_resume = rewrite_resume(text)

        latest_resume = "\n".join(improved_resume)

        history.append({
            "score": score,
            "field": field
        })

        return render_template(
            'index.html',
            score=score,
            ats_score=ats_score,
            skills=skills,
            suggestions=suggestions,
            summary=summary,
            field=field,
            improved_resume=improved_resume
        )

    return render_template('index.html')


@app.route('/download')
def download():
    return Response(
        latest_resume,
        mimetype="text/plain",
        headers={"Content-Disposition": "attachment;filename=resume.txt"}
    )


@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html', history=history)


if __name__ == '__main__':
    app.run(debug=True)