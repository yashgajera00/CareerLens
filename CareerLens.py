from flask import Flask, render_template, request, session, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
import random
from datetime import datetime

app = Flask(__name__)
app.secret_key = "abc"

# ================= DATABASE CONFIG =================
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:@localhost/userdata'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# ================= DATABASE MODELS =================
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    email = db.Column(db.String(120), unique=True, nullable=False)
    userPassword = db.Column(db.String(100), nullable=False)
    bio = db.Column(db.Text, default='')
    skills = db.Column(db.Text, default='')
    interests = db.Column(db.Text, default='')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationship with assessments
    assessments = db.relationship('Assessment', backref='user', lazy=True)

class Assessment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    assessment_type = db.Column(db.String(50), nullable=False)
    score = db.Column(db.Integer, nullable=False)
    completed_at = db.Column(db.DateTime, default=datetime.utcnow)

class OTP(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), nullable=False)
    otp_code = db.Column(db.String(6), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    used = db.Column(db.Boolean, default=False)

class UserCareerField(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    career_field = db.Column(db.String(100), nullable=False)

class Question(db.Model):
    __tablename__ = 'questions'   # real table name

    id = db.Column(db.Integer, primary_key=True)
    career = db.Column(db.String(100), nullable=False)   
    skill = db.Column(db.String(50), nullable=False)
    question = db.Column(db.Text, nullable=False)        

    option_a = db.Column(db.String(200), nullable=False)
    option_b = db.Column(db.String(200), nullable=False)
    option_c = db.Column(db.String(200), nullable=False)
    option_d = db.Column(db.String(200), nullable=False)

    correct_option = db.Column(db.String(1), nullable=False)

class UserAnswer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=False)
    question_id = db.Column(db.Integer, nullable=False)
    selected_option = db.Column(db.String(1))
    is_correct = db.Column(db.Boolean)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


ALL_CAREERS = ["Software Engineer", "Data Scientist", "AI Engineer", "Cyber Security Expert",
    "Web Developer", "Mobile App Developer", "Cloud Engineer", "DevOps Engineer",
    "Game Developer", "Blockchain Developer",
    "UI/UX Designer", "Graphic Designer", "Product Designer",
    "Project Manager", "Business Analyst", "Product Manager",
    "Digital Marketer", "SEO Specialist", "Content Strategist",
    "Data Analyst", "Statistician", "Research Analyst",
    "Mechanical Engineer", "Civil Engineer", "Electrical Engineer",
    "Robotics Engineer", "Automation Engineer",
    "Entrepreneur", "Startup Founder", "Tech Consultant"]

# ================= HELPER FUNCTIONS =================
def login_required(f):
    """Decorator to check if user is logged in"""
    def wrapper(*args, **kwargs):
        if 'user_id' not in session:
            return redirect('/login')
        return f(*args, **kwargs)
    wrapper.__name__ = f.__name__
    return wrapper

def generate_sample_recommendations():
    """Generate sample career recommendations"""
    return [
        {
            'career_field': 'Software Engineering',
            'match_score': 85,
            'reasons': 'Strong analytical skills and technical aptitude'
        },
        {
            'career_field': 'Data Science',
            'match_score': 75,
            'reasons': 'Good with numbers and problem-solving'
        },
        {
            'career_field': 'Project Management',
            'match_score': 65,
            'reasons': 'Leadership skills and organizational abilities'
        }
    ]

def calculate_skill_distribution():
    """Calculate sample skill distribution"""
    return {
        'technical': random.randint(60, 90),
        'analytical': random.randint(50, 85),
        'communication': random.randint(40, 80),
        'leadership': random.randint(30, 75)
    }

# ================= OTP SENDER =================
def mailSender(receiver_email, subject, message):
    import smtplib
    from email.mime.text import MIMEText
    from email.mime.multipart import MIMEMultipart

    sender_email = 'gajerayash999@gmail.com'
    password = 'rpud ypzz mnyb foaa'   # Gmail app password

    try:
        # Create email object
        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = receiver_email
        msg['Subject'] = subject

        # UTF-8 message body
        body = MIMEText(message, 'plain', 'utf-8')
        msg.attach(body)

        # Send mail
        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.starttls()
            server.login(sender_email, password)
            server.send_message(msg)

        print("Mail sent successfully")
        return True

    except Exception as e:
        print("Failed to send mail:", e)
        return False



def otpSender(receiver_email, otp):
    subject = "CareerLens OTP Verification"
    message = f"Your CareerLens OTP is {otp}"
    return mailSender(receiver_email, subject, message)


# ================= ROUTES =================
@app.route('/')
def home():
    """Home page"""
    return render_template('home.html')

@app.route('/home-login')
@login_required
def homeLogin():
    user_id = session['user_id']
    user = db.session.get(User, user_id)

    assessments = Assessment.query.filter_by(user_id=user_id)\
        .order_by(Assessment.completed_at.desc()).limit(5).all()

    total_assessments = Assessment.query.filter_by(user_id=user_id).count()

    avg_score = 0
    if total_assessments > 0:
        total_score = db.session.query(db.func.sum(Assessment.score))\
            .filter_by(user_id=user_id).scalar()
        if total_score:
            avg_score = round(total_score / total_assessments)

    selected_fields = UserCareerField.query.filter_by(user_id=user_id).all()
    career_fields = [{"career_field": f.career_field} for f in selected_fields]

    is_unlocked = True if len(selected_fields) >= 1 else False

    # 🔥 Get modal result and remove from session (one time)
    last_result = session.pop('last_test_result', None)

    return render_template(
        'dashboard.html',
        user=user,
        total_assessments=total_assessments,
        avg_score=avg_score,
        career_fields=career_fields,
        assessments=assessments,
        is_unlocked=is_unlocked,
        ALL_CAREERS=ALL_CAREERS,
        last_result=last_result
    )


@app.route('/career-fields')
@login_required
def career_fields_page():
    return render_template(
        "career_fields.html",
        all_careers=ALL_CAREERS
    )


@app.route('/select-career-fields', methods=['POST'])
@login_required
def select_career_fields():
    user_id = session['user_id']
    selected = request.form.getlist('career_fields')

    if len(selected) < 1:
        return "Select at least one field", 400

    if len(selected) > 5:
        return "Select only 5 fields", 400

    # delete old
    UserCareerField.query.filter_by(user_id=user_id).delete()

    # insert new
    for field in selected:
        db.session.add(UserCareerField(user_id=user_id, career_field=field))

    db.session.commit()
    return redirect('/home-login')


@app.route('/profile')
@login_required
def profile():
    """User profile page"""
    user_id = session['user_id']
    user = User.query.get(user_id)
    
    if not user:
        session.clear()
        return redirect('/login')
    
    # Get assessment stats
    total_assessments = Assessment.query.filter_by(user_id=user_id).count()
    avg_score = 0
    if total_assessments > 0:
        total_score = db.session.query(db.func.sum(Assessment.score)).filter_by(user_id=user_id).scalar()
        if total_score:
            avg_score = round(total_score / total_assessments)
    
    return render_template('profile.html', 
                          user=user,
                          total_assessments=total_assessments,
                          avg_score=avg_score)

@app.route('/update-profile', methods=['POST'])
@login_required
def update_profile():
    """Update user profile"""
    user_id = session['user_id']
    user = User.query.get(user_id)
    
    if not user:
        session.clear()
        return redirect('/login')
    
    user.bio = request.form.get('bio', '')
    user.skills = request.form.get('skills', '')
    user.interests = request.form.get('interests', '')
    
    db.session.commit()
    
    return redirect('/profile')

@app.route('/assessment/<assessment_type>')
@login_required
def assessment(assessment_type):
    """Assessment page - handles both career and aptitude tests"""
    user_id = session['user_id']
    user = db.session.get(User, user_id)
    
    if not user:
        session.clear()
        return redirect('/login')
    
    if assessment_type == 'career':
        # Check if user has selected career fields
        selected_fields = UserCareerField.query.filter_by(user_id=user_id).all()
        
        if not selected_fields:
            flash("Please select career fields first!", "warning")
            return redirect('/home-login')
        
        # Store in session for career test
        session['selected_career_fields'] = [field.career_field for field in selected_fields]
        
        # Redirect directly to career test start
        return redirect('/assessment/career/start')
    
    elif assessment_type == 'aptitude':
        # Render aptitude test page
        assessment_names = {
            'aptitude': 'Aptitude Test',
            'career': 'Career Test'
        }
        assessment_name = assessment_names.get(assessment_type, 'Assessment')
        
        return render_template('assessment.html',
                              user=user,
                              assessment_type=assessment_type,
                              assessment_name=assessment_name)
    else:
        return redirect('/home-login')
    
@app.route('/assessment/career/start')
@login_required
def career_test_start_direct():
    """Direct start for career test"""
    return redirect('/assessment/career')

from sqlalchemy.sql import func

from sqlalchemy.sql import func

from sqlalchemy.sql import func
import random
from collections import defaultdict

TOTAL_QUESTIONS = 20
TOTAL_SKILLS = 4

@app.route('/assessment/career')
@login_required
def career_test_start():
    user_id = session.get('user_id')
    user = User.query.get(user_id)
    if not user:
        return "User not found"

    # Selected career fields
    selected_fields_db = UserCareerField.query.filter_by(user_id=user_id).all()
    selected_fields = [f.career_field.strip() for f in selected_fields_db]

    if not selected_fields:
        return "No career fields selected"

    num_fields = len(selected_fields)
    per_field = TOTAL_QUESTIONS // num_fields
    remaining_field = TOTAL_QUESTIONS % num_fields

    final_questions = []

    # Loop field-wise
    for field in selected_fields:
        # Field na badha questions
        field_questions = Question.query.filter(
            Question.career == field
        ).all()

        if not field_questions:
            continue

        # Skill wise grouping
        skill_groups = defaultdict(list)
        for q in field_questions:
            skill_groups[q.skill].append(q)

        skills = list(skill_groups.keys())[:TOTAL_SKILLS]  # only 4 skills

        per_skill = per_field // TOTAL_SKILLS
        skill_remaining = per_field % TOTAL_SKILLS

        selected_for_field = []

        # Har skill mathi equal questions
        for skill in skills:
            qs = skill_groups[skill]
            random.shuffle(qs)
            selected_for_field.extend(qs[:per_skill])

        # Skill remainder fill
        if skill_remaining > 0:
            leftover_pool = []
            for skill in skills:
                leftover_pool.extend(skill_groups[skill][per_skill:])
            random.shuffle(leftover_pool)
            selected_for_field.extend(leftover_pool[:skill_remaining])

        # Limit field questions
        random.shuffle(selected_for_field)
        final_questions.extend(selected_for_field[:per_field])

    # Global remaining fill
    if len(final_questions) < TOTAL_QUESTIONS:
        all_pool = Question.query.filter(
            Question.career.in_(selected_fields)
        ).all()

        used_ids = {q.id for q in final_questions}
        remaining = [q for q in all_pool if q.id not in used_ids]

        random.shuffle(remaining)
        final_questions.extend(remaining[:TOTAL_QUESTIONS - len(final_questions)])

    # Final shuffle
    random.shuffle(final_questions)

    # Session save
    session['career_test_questions'] = [q.id for q in final_questions]
    session['user_answers'] = {}
    session['current_question_index'] = 0

    first_question = final_questions[0]

    return render_template(
        "career_quiz.html",
        user=user,
        question=first_question,
        question_number=1,
        total_questions=len(final_questions)
    )





@app.route('/submit-assessment', methods=['POST'])
@login_required
def submit_assessment():
    user_id = session['user_id']
    assessment_type = request.form['assessment_type']
    score = int(request.form['score'])

    new_assessment = Assessment(
        user_id=user_id,
        assessment_type=assessment_type,
        score=score
    )
    db.session.add(new_assessment)
    db.session.commit()

    return redirect('/home-login')

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_server_error(e):
    return render_template('500.html'), 500

@app.route('/assessment/career/question/<int:question_num>')
@login_required
def career_question(question_num):
    user_id = session['user_id']
    user = User.query.get(user_id)

    if not user:
        session.clear()
        return redirect('/login')

    # Career test running hoy tyare j open thavu joie
    if 'career_test_questions' not in session:
        flash("No active test found!")
        return redirect('/home-login')

    question_index = question_num - 1

    if question_index < 0 or question_index >= len(session['career_test_questions']):
        flash("Invalid question number!")
        return redirect('/home-login')

    question_id = session['career_test_questions'][question_index]
    question = Question.query.get(question_id)

    user_answer = session.get('user_answers', {}).get(str(question_id))

    return render_template(
        'career_quiz.html',
        user=user,
        question=question,
        question_number=question_num,
        total_questions=len(session['career_test_questions']),
        user_answer=user_answer
    )


@app.route('/assessment/career/save-answer', methods=['POST'])
@login_required
def save_answer():
    current_q = int(request.form.get('current_question', 1))
    question_id = int(request.form.get('question_id'))
    user_answer = request.form.get('answer', '')

    if 'user_answers' not in session:
        session['user_answers'] = {}

    # Save answer
    session['user_answers'][str(question_id)] = user_answer
    session.modified = True

    total_questions = len(session.get('career_test_questions', []))
    next_question = current_q + 1

    # ❌ OLD CODE REMOVE KARO
    # if current_q >= total_questions:
    #     return redirect('/assessment/career/review')

    # Normal next question redirect
    if next_question <= total_questions:
        return redirect(f'/assessment/career/question/{next_question}')

    # Safety fallback (normally JS handle karse)
    return redirect(f'/assessment/career/question/{total_questions}')

@app.route('/assessment/career/review')
@login_required
def review_test():
    user_id = session['user_id']
    user = User.query.get(user_id)

    if not user:
        return redirect('/login')

    # Only last test review
    if 'last_test_questions' not in session or 'last_test_answers' not in session:
        flash("No review data found!")
        return redirect('/home-login')

    questions_data = []
    total_score = 0

    for i, q_id in enumerate(session['last_test_questions']):
        question = Question.query.get(q_id)
        user_answer = session['last_test_answers'].get(str(q_id))

        is_correct = False
        if user_answer:
            is_correct = (user_answer == question.correct_option)
            if is_correct:
                total_score += 5

        questions_data.append({
            'number': i + 1,
            'question': question,
            'user_answer': user_answer,
            'correct_answer': question.correct_option,
            'is_correct': is_correct
        })

    percentage = (total_score / 100) * 100

    return render_template(
        'test_review.html',
        user=user,
        questions=questions_data,
        total_score=total_score,
        percentage=percentage
    )



@app.route('/assessment/career/submit', methods=['POST'])
@login_required
def submit_career_test():

    user_id = session['user_id']
    user = User.query.get(user_id)

    total_score = 0
    total_questions = len(session.get('career_test_questions', []))

    if total_questions == 0:
        flash("No test data found!", "warning")
        return redirect('/home-login')

    # ===== FIELD & SKILL TRACKING =====
    field_data = {}
    skill_data = {}

    # Selected fields
    selected_fields = [f.career_field for f in UserCareerField.query.filter_by(user_id=user_id).all()]

    for field in selected_fields:
        field_data[field] = {'correct': 0, 'total': 0}

    # ===== MAIN LOOP =====
    for q_id in session['career_test_questions']:
        question = Question.query.get(q_id)
        user_answer = session.get('user_answers', {}).get(str(q_id), '')

        is_correct = False

        # FIELD tracking
        if question.career not in field_data:
            field_data[question.career] = {'correct': 0, 'total': 0}

        field_data[question.career]['total'] += 1

        # SKILL tracking
        if question.skill not in skill_data:
            skill_data[question.skill] = {'correct': 0, 'total': 0}

        skill_data[question.skill]['total'] += 1

        if user_answer and user_answer == question.correct_option:
            total_score += 5
            is_correct = True
            field_data[question.career]['correct'] += 1
            skill_data[question.skill]['correct'] += 1

        # SAVE ANSWER DB
        db.session.add(UserAnswer(
            user_id=user_id,
            question_id=q_id,
            selected_option=user_answer,
            is_correct=is_correct
        ))

    percentage = int((total_score / (total_questions * 5)) * 100)

    # SAVE assessment
    db.session.add(Assessment(
        user_id=user_id,
        assessment_type='career',
        score=percentage
    ))

    db.session.commit()

    # ===== CALCULATE FIELD SCORE =====
    field_scores = {
        f: int((d['correct']/d['total'])*100) if d['total']>0 else 0
        for f,d in field_data.items()
    }

    skill_scores = {
        s: int((d['correct']/d['total'])*100) if d['total']>0 else 0
        for s,d in skill_data.items()
    }

    # ===== STRONG & WEAK =====
    strong_fields = []
    weak_fields = []

    if field_scores:
        max_field = max(field_scores.values())
        min_field = min(field_scores.values())
        strong_fields = [f for f,v in field_scores.items() if v == max_field]
        weak_fields = [f for f,v in field_scores.items() if v == min_field]

    strong_skills = []
    weak_skills = []

    if skill_scores:
        max_skill = max(skill_scores.values())
        min_skill = min(skill_scores.values())
        strong_skills = [s for s,v in skill_scores.items() if v == max_skill]
        weak_skills = [s for s,v in skill_scores.items() if v == min_skill]

    # ===== EMAIL CONTENT =====
    subject = "CareerLens - Career Test Result & Analysis"

    message = f"""
Hello {user.name},

Your Career Test completed 🎉

Test Score: {percentage}%

=========================
STRONG FIELDS:
{', '.join(strong_fields)}

WEAK FIELDS:
{', '.join(weak_fields)}

STRONG SKILLS:
{', '.join(strong_skills)}

WEAK SKILLS:
{', '.join(weak_skills)}
=========================

⚠️ This score is from your last test, so consider it as your overall score. To view your overall score, log in to your CareerLens account.

Login to CareerLens for detailed reports.

Regards,
CareerLens Team
"""

    mailSender(user.email, subject, message)

    # session store
    session['last_test_result'] = {
        "score": percentage,
        "date": datetime.utcnow()
    }

    session['last_test_questions'] = session.get('career_test_questions')
    session['last_test_answers'] = session.get('user_answers')

    session.pop('career_test_questions', None)
    session.pop('user_answers', None)

    return redirect('/home-login')




@app.route('/assessment/career/submit-modal-data')
@login_required
def submit_modal_data():
    answered = 0
    unanswered = 0

    for q_id in session.get('career_test_questions', []):
        ans = session.get('user_answers', {}).get(str(q_id), '')
        if ans:
            answered += 1
        else:
            unanswered += 1

    # Simple string return (no JSON)
    return f"{answered}|{unanswered}"


# Add this function to CareerLens.py after the existing functions
def calculate_field_performance(user_id):
    """Calculate performance for each selected career field"""
    from sqlalchemy.sql import func
    
    # Get user's selected fields
    selected_fields = UserCareerField.query.filter_by(user_id=user_id).all()
    if not selected_fields:
        return {}
    
    field_performance = {}
    
    for field_obj in selected_fields:
        field = field_obj.career_field
        
        # Get all questions for this field
        field_questions = Question.query.filter_by(career=field).all()
        if not field_questions:
            continue
            
        # Get question IDs
        field_question_ids = [q.id for q in field_questions]
        
        # Get user's answers for these questions from session
        user_answers = session.get('user_answers', {})
        
        # Calculate score for this field
        correct_count = 0
        total_questions = len(field_question_ids)
        
        for q_id in field_question_ids:
            user_answer = user_answers.get(str(q_id), '')
            question = Question.query.get(q_id)
            
            if user_answer and user_answer == question.correct_option:
                correct_count += 1
        
        # Calculate percentage
        score_percentage = 0
        if total_questions > 0:
            score_percentage = round((correct_count / total_questions) * 100)
        
        field_performance[field] = {
            'score': score_percentage,
            'correct': correct_count,
            'total': total_questions,
            'questions': field_question_ids[:10]  # First 10 question IDs
        }
    
    return field_performance

# Add this function to calculate skill performance within each field
def calculate_field_skill_performance(user_id):
    """Calculate skill performance for each selected field"""
    # Get user's selected fields
    selected_fields = UserCareerField.query.filter_by(user_id=user_id).all()
    if not selected_fields:
        return {}
    
    field_skill_performance = {}
    
    for field_obj in selected_fields:
        field = field_obj.career_field
        
        # Get all questions for this field
        field_questions = Question.query.filter_by(career=field).all()
        if not field_questions:
            continue
        
        # Group questions by skill
        skill_performance = {}
        user_answers = session.get('user_answers', {})
        
        for question in field_questions:
            skill = question.skill
            if skill not in skill_performance:
                skill_performance[skill] = {
                    'correct': 0,
                    'total': 0,
                    'score': 0
                }
            
            user_answer = user_answers.get(str(question.id), '')
            skill_performance[skill]['total'] += 1
            
            if user_answer and user_answer == question.correct_option:
                skill_performance[skill]['correct'] += 1
        
        # Calculate percentages
        for skill in skill_performance:
            if skill_performance[skill]['total'] > 0:
                score = (skill_performance[skill]['correct'] / 
                        skill_performance[skill]['total']) * 100
                skill_performance[skill]['score'] = round(score)
        
        field_skill_performance[field] = skill_performance
    
    return field_skill_performance

@app.route('/reports')
@login_required
def reports():

    user_id = session['user_id']

    # ===== USER SELECTED FIELDS =====
    selected_fields_db = UserCareerField.query.filter_by(user_id=user_id).all()
    selected_fields = [f.career_field for f in selected_fields_db]

    # ===== TOTAL TEST & AVG SCORE =====
    assessments = Assessment.query.filter_by(user_id=user_id).all()
    total_tests = len(assessments)

    avg_score = 0
    if total_tests > 0:
        avg_score = int(sum(a.score for a in assessments) / total_tests)

    # ===== USER ANSWERS =====
    user_answers = UserAnswer.query.filter_by(user_id=user_id).all()

    # ===== FIELD DEFAULT =====
    field_data = {}
    for field in selected_fields:
        field_data[field] = {'correct': 0, 'total': 0}

    # ===== SKILL DEFAULT =====
    skill_data = {}

    # ===== PROCESS ANSWERS =====
    for ans in user_answers:
        question = Question.query.get(ans.question_id)

        # FIELD
        field = question.career
        if field in selected_fields:
            field_data[field]['total'] += 1
            if ans.is_correct:
                field_data[field]['correct'] += 1

        # SKILL
        skill = question.skill
        if skill not in skill_data:
            skill_data[skill] = {'correct': 0, 'total': 0}

        skill_data[skill]['total'] += 1
        if ans.is_correct:
            skill_data[skill]['correct'] += 1

    # ===== PERCENTAGE =====
    field_scores = {
        f: int((d['correct']/d['total'])*100) if d['total']>0 else 0
        for f,d in field_data.items()
    }

    skill_scores = {
        s: int((d['correct']/d['total'])*100) if d['total']>0 else 0
        for s,d in skill_data.items()
    }

    # ===== BEST & WEAK FIELD =====
    top_fields = []
    weak_fields = []

    if field_scores:
        max_score = max(field_scores.values())
        min_score = min(field_scores.values())

        top_fields = [f for f,s in field_scores.items() if s == max_score]
        weak_fields = [f for f,s in field_scores.items() if s == min_score]

    # ===== BEST & WEAK SKILL =====
    top_skills = []
    weak_skills = []

    if skill_scores:
        max_skill = max(skill_scores.values())
        min_skill = min(skill_scores.values())

        top_skills = [s for s,v in skill_scores.items() if v == max_skill]
        weak_skills = [s for s,v in skill_scores.items() if v == min_skill]

    return render_template(
        'reports.html',
        total_tests=total_tests,
        avg_score=avg_score,
        field_scores=field_scores,
        skill_scores=skill_scores,
        top_fields=top_fields,
        weak_fields=weak_fields,
        top_skills=top_skills,
        weak_skills=weak_skills
    )










@app.route('/resources')
@login_required
def resources():
    """Resources page"""
    user_id = session['user_id']
    user = User.query.get(user_id)
    
    if not user:
        session.clear()
        return redirect('/login')
    
    # Sample career fields based on user interests
    career_fields = []
    if user.interests:
        interests_list = [i.strip() for i in user.interests.split(',')]
        career_fields = interests_list[:3]
    
    return render_template('resources.html',
                          user=user,
                          career_fields=career_fields)

# ================= LOGIN =================
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # ===== SEND OTP =====
        if 'l_otp' not in request.form:
            email = request.form.get('l_email')
            password = request.form.get('l_password')

            user = User.query.filter_by(email=email).first()

            # ❌ Email not found
            if not user:
                return render_template('login.html', email_not_found=True)

            # ❌ Password wrong
            if user.userPassword != password:
                return render_template('login.html', password_wrong=True)

            # ✅ SEND OTP
            otp = random.randint(100000, 999999)
            session['login_otp'] = str(otp)
            session['login_email'] = email
            session['login_user_id'] = user.id

            otpSender(email, otp)

            return render_template('login.html', show_otp_modal=True)

        # ===== VERIFY OTP =====
        else:
            inputOtp = request.form.get('l_otp')

            if inputOtp == session.get('login_otp'):
                # Set user session
                session['user_id'] = session.get('login_user_id')
                session['user_email'] = session.get('login_email')
                
                # Get user name
                user = db.session.get(User, session['user_id'])
                if user:
                    session['user_name'] = user.name
                
                # Clear OTP session
                session.pop('login_otp', None)
                session.pop('login_email', None)
                session.pop('login_user_id', None)
                
                return redirect(url_for('homeLogin'))
            else:
                return render_template('login.html', show_otp_modal=True, otp_fail=True)

    return render_template('login.html')

# ================= REGISTRATION =================
@app.route('/registation', methods=['GET', 'POST'])
def registation():
    if request.method == 'POST':
        # ===== SEND OTP =====
        if 'r_otp' not in request.form:
            name = request.form.get('r_name')
            email = request.form.get('r_email')
            password = request.form.get('r_password')
            confirm_password = request.form.get('r_confirmPassword')

            # Check if passwords match
            if password != confirm_password:
                return render_template('registation.html',
                                       registation_fail=True,
                                       r_name=name,
                                       r_email=email)

            # Check if user already exists
            existing_user = User.query.filter_by(email=email).first()
            if existing_user:
                return render_template('registation.html', registation_fail=True)

            # ✅ SEND OTP
            otp = random.randint(100000, 999999)
            session['otp'] = str(otp)
            session['reg_name'] = name
            session['reg_email'] = email
            session['reg_password'] = password

            otpSender(email, otp)

            return render_template('registation.html', show_otp_modal=True)

        # ===== VERIFY OTP =====
        else:
            inputOtp = request.form.get('r_otp')

            if inputOtp == session.get('otp'):
                # SAVE USER TO DATABASE
                new_user = User(
                    name=session['reg_name'],
                    email=session['reg_email'],
                    userPassword=session['reg_password'],
                    created_at=datetime.utcnow()
                )
                db.session.add(new_user)
                db.session.commit()

                # Get the newly created user
                user = User.query.filter_by(email=session['reg_email']).first()
                
                # Clear registration session
                session.pop('otp', None)
                session.pop('reg_name', None)
                session.pop('reg_email', None)
                session.pop('reg_password', None)

                # Auto login after registration
                if user:
                    session['user_id'] = user.id
                    session['user_email'] = user.email
                    session['user_name'] = user.name
                
                return redirect(url_for('homeLogin'))
            else:
                return render_template('registation.html',
                                       show_otp_modal=True,
                                       otp_fail=True)

    return render_template('registation.html')

@app.route('/logout')
def logout():
    """Logout user"""
    session.clear()
    return redirect('/')        

# ================= INITIALIZE DATABASE =================
def create_tables():
    """Create database tables"""
    with app.app_context():
        db.create_all()
        print("✓ Database tables created successfully!")

# ================= RUN APP =================
if __name__ == "__main__":
    # Create database tables
    create_tables()
    
    # Run the application
    print("\n" + "="*50)
    print("CareerLens Application Starting...")
    print("="*50)
    print("Access the application at: http://localhost:5000")
    print("="*50 + "\n")
    
    app.run(debug=True, port=5000)