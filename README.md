# CareerVoice AI Counselor

An AI-powered voice career counselor designed to help Nigerian secondary-school students discover suitable careers, university courses, admission pathways, and personalized action plans.

CareerVoice AI uses conversational AI to understand a student's interests, strengths, subjects, academic stream, career goals, and preferences, then provides personalized guidance.

---

## Key Features

* Voice-based AI counseling
* Conversational career guidance
* Student profile analysis
* Personalized career recommendations
* Nigerian university recommendations
* WAEC subject requirement guidance
* JAMB/UTME admission guidance
* Admission readiness analysis
* Personalized action plans
* Career and university search
* Support for Science, Art/Humanities, and Commercial students

---

## How CareerVoice AI Works

```text
Student
   |
   v
Voice / Text Conversation
   |
   v
AI Profile Analysis
   |
   +-- Academic Stream
   +-- Subjects
   +-- Interests
   +-- Strengths
   +-- Skills
   +-- Personality
   +-- Career Goals
   |
   v
Career Matching Engine
   |
   +-- Career Recommendations
   +-- University Recommendations
   +-- Admission Requirements
   +-- Action Plan
   |
   v
Personalized Guidance
```

---

## Supported Student Streams

CareerVoice AI is designed for students across the major Nigerian secondary-school academic streams.

### Science

Examples include students interested in:

* Medicine
* Pharmacy
* Nursing
* Engineering
* Computer Science
* Biochemistry
* Microbiology
* Medical Laboratory Science
* Physiotherapy
* Radiography
* Other science-related careers

### Art / Humanities

Examples include students interested in:

* Law
* Mass Communication
* Journalism
* Political Science
* History
* International Relations
* English
* Literature
* Sociology
* Education
* Other humanities and social-science careers

### Commercial

Examples include students interested in:

* Accounting
* Banking and Finance
* Economics
* Business Administration
* Marketing
* Entrepreneurship
* Insurance
* Finance
* Other business-related careers

---

## Project Architecture

```text
CareerVoice_AI COUNSELOR/
|
+-- backend/
|   +-- main.py
|   +-- profile_analyzer.py
|   +-- career_engine.py
|   +-- career_knowledge.py
|   +-- university_engine.py
|   +-- admission_engine.py
|   +-- action_plan.py
|   +-- __init__.py
|
+-- data/
|   +-- careers.json
|   +-- universities.json
|
+-- frontend/
|   +-- index.html
|   +-- app.js
|   +-- CSS files
|
+-- .env.example
+-- .gitignore
+-- README.md
+-- requirements.txt
```

---

## Technology Stack

### Backend

* Python
* FastAPI
* Uvicorn
* Google Gemini API

### Frontend

* HTML
* CSS
* JavaScript
* Browser Web APIs

### AI

* Google Gemini
* Natural-language profile analysis
* Career matching
* Conversational guidance

### Data

* JSON-based career knowledge base
* Nigerian university information
* WAEC/JAMB subject requirements

---

## Installation

### 1. Clone the repository

```bash
git clone https://github.com/joshua-AI121/CareerVoice-AI-Counselor.git
cd CareerVoice-AI-Counselor
```

### 2. Create a virtual environment

```bash
python -m venv .venv
```

### 3. Activate the virtual environment

For Windows PowerShell:

```powershell
.venv\Scripts\Activate.ps1
```

If PowerShell blocks activation, run:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned
```

Then activate again:

```powershell
.venv\Scripts\Activate.ps1
```

### 4. Install dependencies

```powershell
pip install -r requirements.txt
```

---

## Gemini API Configuration

Create a `.env` file in the project root:

```text
GEMINI_API_KEY=your_gemini_api_key_here
```

Important: Never upload your real API key to GitHub.

The `.gitignore` file is configured to prevent `.env` from being committed.

---

## Running the Application

Start the FastAPI backend:

```powershell
uvicorn backend.main:app --reload
```

The backend will normally run at:

```text
http://127.0.0.1:8000
```

Open the API documentation:

```text
http://127.0.0.1:8000/docs
```

Open the CareerVoice AI application:

```text
http://127.0.0.1:8000/app/
```

---

## API Endpoints

The backend currently provides endpoints for:

| Endpoint                | Method | Purpose                     |
| ----------------------- | ------ | --------------------------- |
| `/`                     | GET    | API information             |
| `/app/`                 | GET    | CareerVoice AI application  |
| `/info`                 | GET    | Application information     |
| `/session`              | POST   | Create a counseling session |
| `/ask`                  | POST   | Send a question/message     |
| `/session/{session_id}` | GET    | Retrieve session profile    |
| `/profile/update`       | POST   | Update student profile      |
| `/careers`              | GET    | List careers                |
| `/careers/{career_id}`  | GET    | Get career information      |
| `/universities`         | GET    | List universities           |
| `/universities/search`  | GET    | Search universities         |
| `/admission`            | GET    | Admission guidance          |
| `/action-plan`          | GET    | Generate action plan        |

---

## Recommendation System

CareerVoice AI combines information from the student's profile with the project's career and university knowledge bases.

The system considers information such as:

* Academic stream
* Subjects
* Favorite subjects
* Strongest subjects
* Interests
* Skills
* Strengths
* Personality
* Work preferences
* Career interests
* Career goals
* Preferred location
* University preferences
* Budget preferences

This information is used to generate personalized recommendations.

---

## University Recommendations

CareerVoice AI can recommend Nigerian universities based on factors such as:

* Relevant courses
* Student career interests
* Academic stream
* Course requirements
* Location preferences
* University preferences

The recommendation system is designed to help students explore possible university pathways rather than simply providing a single generic recommendation.

---

## Admission Guidance

The admission engine considers academic requirements associated with recommended courses.

This can include:

* WAEC subject requirements
* Required O'Level credits
* JAMB/UTME subject combinations
* Course-specific requirements
* Missing subjects
* Weak subject areas
* Admission preparation guidance

Students should always confirm admission requirements against the current official JAMB brochure and the university's current admission information because requirements can change.

---

## Personalized Action Plans

CareerVoice AI can generate practical next steps for students.

An action plan may include:

1. Subjects to strengthen
2. Career exploration activities
3. Relevant skills to develop
4. University research
5. JAMB preparation
6. WAEC preparation
7. Course requirement checks
8. Longer-term career development

---

## Example Conversation

### Student

> I'm a Science student. I enjoy Biology and Chemistry, and I like helping people. I'm interested in healthcare careers.

### CareerVoice AI

The system analyzes the student's profile and can identify relevant healthcare-related career pathways and universities that may match the student's interests and academic background.

The same system can also analyze Art/Humanities and Commercial student profiles.

---

## Data Honesty

CareerVoice AI is designed to provide useful guidance while avoiding unsupported claims.

Admission requirements and subject combinations can change over time.

Students should verify important admission information with:

* JAMB
* WAEC
* The relevant university
* Other official admission sources

CareerVoice AI should be treated as a guidance tool and not as a replacement for official admission information.

---

## Future Development

Planned improvements include:

* Improved voice-to-voice interaction
* Better speech recognition
* More advanced career matching
* Larger Nigerian university database
* More comprehensive admission requirements
* Better JAMB preparation guidance
* Student progress tracking
* Improved recommendation explanations
* Parent/guardian guidance
* Counselor dashboard
* Student career reports
* Mobile-friendly experience

---

## Project Purpose

CareerVoice AI was created to make career guidance more accessible to Nigerian students.

Many students have difficulty connecting:

```text
Subjects
   |
   v
Interests
   |
   v
Career
   |
   v
University Course
   |
   v
University
   |
   v
Admission Requirements
   |
   v
Action Plan
```

CareerVoice AI aims to connect these stages into one conversational experience.

---

## Disclaimer

CareerVoice AI provides educational and career guidance.

It does not guarantee admission, employment, examination results, or university acceptance.

Students should verify current requirements and admission decisions with official sources before making important academic decisions.

---

## License

This project is currently provided for educational and development purposes.

---

## Author

**Joshua AI**

GitHub: https://github.com/joshua-AI121

---

If you find this project interesting, consider giving the repository a star on GitHub.
