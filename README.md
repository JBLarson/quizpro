# QuizPro

QuizPro is a web app that lets you upload PowerPoint files, extracts the text, and uses AI to generate quizzes based on the content. Configure quiz style, tone, and difficulty, and get real-time feedback on your answers.

## Features
- Upload .pptx files and extract slide text
- Choose AI model (OpenAI, DeepSeek, etc.)
- Configure quiz tone, difficulty, and style
- Chat interface for Q&A
- Real-time answer evaluation and feedback

## Setup
- Clone this repo
- Create a virtual environment and activate it:
```bash
python -m venv venv
venv\Scripts\activate  # Windows
source venv/bin/activate  # macOS/Linux
```
- Install dependencies:
```bash
pip install -r reqs.txt
```
- Open `index.html` in your browser
- Enter your API key and upload a PowerPoint file to start

## Running Locally
1. Ensure your `.env` contains your `DATABASE_URL` (e.g. your Supabase connection URL).
2. Activate your virtual environment:
   ```bash
   venv\\Scripts\\activate   # Windows
   source venv/bin/activate  # macOS/Linux
   ```
3. Install dependencies:
   ```bash
   pip install -r reqs.txt
   ```
4. Initialize/migrate the database:
   ```bash
   flask db upgrade
   ```
5. Start the development server:
   ```bash
   flask run
   ```
6. Open `http://localhost:5000` in your browser.

## Supabase Admin User Setup
1. In your Supabase dashboard, navigate to **Authentication → Users**.
2. Click **Invite New User**, enter the admin email, and send the invite.
3. (Optional) Using the Supabase CLI:
   ```bash
   supabase auth admin create-user --project-ref YOUR_PROJECT_REF --email admin@example.com --password YourSecureP@ssw0rd
   ```
4. Assign the **admin** role via your project settings or SQL policies.

Once your admin accepts the invite, they can manage the database.

## Hackathon Submission Checklist
- [x] Project description (this file)
- [x] Source code (this repo)
- [x] Screenshot of the app
- [x] Demo video (2 min, with voiceover)

---

Built for the Artificial Intelligence Track Hackathon. 
