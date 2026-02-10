from flask import Flask, render_template, request, session, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
import random
from datetime import datetime
from sqlalchemy.sql import func
from collections import defaultdict

app = Flask(__name__)
app.secret_key = "abc"

app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:@localhost/userdata'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    email = db.Column(db.String(120), unique=True, nullable=False)
    userPassword = db.Column(db.String(100), nullable=False)
    bio = db.Column(db.Text, default='')
    skills = db.Column(db.Text, default='')
    interests = db.Column(db.Text, default='')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    assessments = db.relationship('Assessment', backref='user', lazy=True)

class Assessment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    assessment_type = db.Column(db.String(50), nullable=False)
    score = db.Column(db.Integer, nullable=False)
    completed_at = db.Column(db.DateTime, default=datetime.utcnow)

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

def login_required(f):
    """Decorator to check if user is logged in"""
    def wrapper(*args, **kwargs):
        if 'user_id' not in session:
            return redirect('/login')
        return f(*args, **kwargs)
    wrapper.__name__ = f.__name__
    return wrapper

def mailSender(receiver_email, subject, message):
    import smtplib
    from email.mime.text import MIMEText
    from email.mime.multipart import MIMEMultipart

    sender_email = 'gajerayash999@gmail.com'
    password = 'rpud ypzz mnyb foaa'   # Gmail app password

    try:
        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = receiver_email
        msg['Subject'] = subject

        body = MIMEText(message, 'plain', 'utf-8')
        msg.attach(body)

        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.starttls()
            server.login(sender_email, password)
            server.send_message(msg)

        return True

    except Exception as e:
        return False



def otpSender(receiver_email, otp):
    subject = "CareerLens OTP Verification"
    message = f"Your CareerLens OTP is {otp}"
    return mailSender(receiver_email, subject, message)


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

@app.route('/select-career-fields', methods=['POST'])
@login_required
def select_career_fields():
    user_id = session['user_id']
    selected = request.form.getlist('career_fields')

    if len(selected) < 1:
        return "Select at least one field", 400

    if len(selected) > 5:
        return "Select only 5 fields", 400

    UserCareerField.query.filter_by(user_id=user_id).delete()

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
    
    # Get basic stats
    total_assessments = Assessment.query.filter_by(user_id=user_id).count()
    avg_score = 0
    if total_assessments > 0:
        total_score = db.session.query(db.func.sum(Assessment.score)).filter_by(user_id=user_id).scalar()
        if total_score:
            avg_score = round(total_score / total_assessments)
    
    # Get field performance data
    selected_fields_db = UserCareerField.query.filter_by(user_id=user_id).all()
    selected_fields = [f.career_field for f in selected_fields_db]
    
    # Get user answers
    user_answers = UserAnswer.query.filter_by(user_id=user_id).all()
    
    # Calculate field scores
    field_data = {}
    for field in selected_fields:
        field_data[field] = {'correct': 0, 'total': 0}
    
    skill_data = {}
    
    for ans in user_answers:
        question = Question.query.get(ans.question_id)
        if not question:
            continue
            
        field = question.career
        if field in selected_fields:
            field_data[field]['total'] += 1
            if ans.is_correct:
                field_data[field]['correct'] += 1
        
        skill = question.skill
        if skill not in skill_data:
            skill_data[skill] = {'correct': 0, 'total': 0}
        
        skill_data[skill]['total'] += 1
        if ans.is_correct:
            skill_data[skill]['correct'] += 1
    
    # Calculate scores
    field_scores = {
        f: int((d['correct']/d['total'])*100) if d['total']>0 else 0
        for f,d in field_data.items()
    }
    
    skill_scores = {
        s: int((d['correct']/d['total'])*100) if d['total']>0 else 0
        for s,d in skill_data.items()
    }
    
    # Get top and weak fields
    top_fields = []
    weak_fields = []
    top_field_score = 0
    weak_field_score = 0
    
    if field_scores:
        max_score = max(field_scores.values()) if field_scores.values() else 0
        min_score = min(field_scores.values()) if field_scores.values() else 0
        
        top_fields = [f for f,s in field_scores.items() if s == max_score]
        weak_fields = [f for f,s in field_scores.items() if s == min_score]
        top_field_score = max_score
        weak_field_score = min_score
    
    # Get top and weak skills
    top_skills = []
    weak_skills = []
    
    if skill_scores:
        max_skill = max(skill_scores.values()) if skill_scores.values() else 0
        min_skill = min(skill_scores.values()) if skill_scores.values() else 0
        
        top_skills = [s for s,v in skill_scores.items() if v == max_skill]
        weak_skills = [s for s,v in skill_scores.items() if v == min_skill]
    
    # Limit to 5 skills each
    top_skills = top_skills[:5]
    weak_skills = weak_skills[:5]
    
    return render_template('profile.html', 
                          user=user,
                          total_assessments=total_assessments,
                          avg_score=avg_score,
                          top_fields=top_fields,
                          weak_fields=weak_fields,
                          top_skills=top_skills,
                          weak_skills=weak_skills,
                          top_field_score=top_field_score,
                          weak_field_score=weak_field_score)
    
@app.route('/assessment/career/start')
@login_required
def career_test_start_direct():
    """Direct start for career test"""
    return redirect('/assessment/career')

TOTAL_QUESTIONS = 20
TOTAL_SKILLS = 4

@app.route('/assessment/career')
@login_required
def career_test_start():
    user_id = session.get('user_id')
    user = User.query.get(user_id)
    if not user:
        return "User not found"

    selected_fields_db = UserCareerField.query.filter_by(user_id=user_id).all()
    selected_fields = [f.career_field.strip() for f in selected_fields_db]

    if not selected_fields:
        return "No career fields selected"

    num_fields = len(selected_fields)
    per_field = TOTAL_QUESTIONS // num_fields
    remaining_field = TOTAL_QUESTIONS % num_fields

    final_questions = []

    for field in selected_fields:
        field_questions = Question.query.filter(
            Question.career == field
        ).all()

        if not field_questions:
            continue

        skill_groups = defaultdict(list)
        for q in field_questions:
            skill_groups[q.skill].append(q)

        skills = list(skill_groups.keys())[:TOTAL_SKILLS]  # only 4 skills

        per_skill = per_field // TOTAL_SKILLS
        skill_remaining = per_field % TOTAL_SKILLS

        selected_for_field = []

        for skill in skills:
            qs = skill_groups[skill]
            random.shuffle(qs)
            selected_for_field.extend(qs[:per_skill])

        if skill_remaining > 0:
            leftover_pool = []
            for skill in skills:
                leftover_pool.extend(skill_groups[skill][per_skill:])
            random.shuffle(leftover_pool)
            selected_for_field.extend(leftover_pool[:skill_remaining])

        random.shuffle(selected_for_field)
        final_questions.extend(selected_for_field[:per_field])

    if len(final_questions) < TOTAL_QUESTIONS:
        all_pool = Question.query.filter(
            Question.career.in_(selected_fields)
        ).all()

        used_ids = {q.id for q in final_questions}
        remaining = [q for q in all_pool if q.id not in used_ids]

        random.shuffle(remaining)
        final_questions.extend(remaining[:TOTAL_QUESTIONS - len(final_questions)])

    random.shuffle(final_questions)

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

@app.route('/assessment/career/question/<int:question_num>')
@login_required
def career_question(question_num):
    user_id = session['user_id']
    user = User.query.get(user_id)

    if not user:
        session.clear()
        return redirect('/login')

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

    session['user_answers'][str(question_id)] = user_answer
    session.modified = True

    total_questions = len(session.get('career_test_questions', []))
    next_question = current_q + 1


    if next_question <= total_questions:
        return redirect(f'/assessment/career/question/{next_question}')

    return redirect(f'/assessment/career/question/{total_questions}')

@app.route('/assessment/career/review')
@login_required
def review_test():
    user_id = session['user_id']
    user = User.query.get(user_id)

    if not user:
        return redirect('/login')

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

    field_data = {}
    skill_data = {}

    selected_fields = [f.career_field for f in UserCareerField.query.filter_by(user_id=user_id).all()]

    for field in selected_fields:
        field_data[field] = {'correct': 0, 'total': 0}

    for q_id in session['career_test_questions']:
        question = Question.query.get(q_id)
        user_answer = session.get('user_answers', {}).get(str(q_id), '')

        is_correct = False

        if question.career not in field_data:
            field_data[question.career] = {'correct': 0, 'total': 0}

        field_data[question.career]['total'] += 1

        if question.skill not in skill_data:
            skill_data[question.skill] = {'correct': 0, 'total': 0}

        skill_data[question.skill]['total'] += 1

        if user_answer and user_answer == question.correct_option:
            total_score += 5
            is_correct = True
            field_data[question.career]['correct'] += 1
            skill_data[question.skill]['correct'] += 1

        db.session.add(UserAnswer(
            user_id=user_id,
            question_id=q_id,
            selected_option=user_answer,
            is_correct=is_correct
        ))

    percentage = int((total_score / (total_questions * 5)) * 100)

    db.session.add(Assessment(
        user_id=user_id,
        assessment_type='career',
        score=percentage
    ))

    db.session.commit()

    field_scores = {
        f: int((d['correct']/d['total'])*100) if d['total']>0 else 0
        for f,d in field_data.items()
    }

    skill_scores = {
        s: int((d['correct']/d['total'])*100) if d['total']>0 else 0
        for s,d in skill_data.items()
    }

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

    return f"{answered}|{unanswered}"


def calculate_field_performance(user_id):
    """Calculate performance for each selected career field"""
        
    selected_fields = UserCareerField.query.filter_by(user_id=user_id).all()
    if not selected_fields:
        return {}
    
    field_performance = {}
    
    for field_obj in selected_fields:
        field = field_obj.career_field
        
        field_questions = Question.query.filter_by(career=field).all()
        if not field_questions:
            continue
            
        field_question_ids = [q.id for q in field_questions]
        
        user_answers = session.get('user_answers', {})
        
        correct_count = 0
        total_questions = len(field_question_ids)
        
        for q_id in field_question_ids:
            user_answer = user_answers.get(str(q_id), '')
            question = Question.query.get(q_id)
            
            if user_answer and user_answer == question.correct_option:
                correct_count += 1
        
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

def calculate_field_skill_performance(user_id):
    """Calculate skill performance for each selected field"""
    selected_fields = UserCareerField.query.filter_by(user_id=user_id).all()
    if not selected_fields:
        return {}
    
    field_skill_performance = {}
    
    for field_obj in selected_fields:
        field = field_obj.career_field
        
        field_questions = Question.query.filter_by(career=field).all()
        if not field_questions:
            continue
        
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

    selected_fields_db = UserCareerField.query.filter_by(user_id=user_id).all()
    selected_fields = [f.career_field for f in selected_fields_db]

    assessments = Assessment.query.filter_by(user_id=user_id).all()
    total_tests = len(assessments)

    avg_score = 0
    if total_tests > 0:
        avg_score = int(sum(a.score for a in assessments) / total_tests)

    user_answers = UserAnswer.query.filter_by(user_id=user_id).all()

    field_data = {}
    for field in selected_fields:
        field_data[field] = {'correct': 0, 'total': 0}

    skill_data = {}

    for ans in user_answers:
        question = Question.query.get(ans.question_id)

        field = question.career
        if field in selected_fields:
            field_data[field]['total'] += 1
            if ans.is_correct:
                field_data[field]['correct'] += 1

        skill = question.skill
        if skill not in skill_data:
            skill_data[skill] = {'correct': 0, 'total': 0}

        skill_data[skill]['total'] += 1
        if ans.is_correct:
            skill_data[skill]['correct'] += 1

    field_scores = {
        f: int((d['correct']/d['total'])*100) if d['total']>0 else 0
        for f,d in field_data.items()
    }

    skill_scores = {
        s: int((d['correct']/d['total'])*100) if d['total']>0 else 0
        for s,d in skill_data.items()
    }

    top_fields = []
    weak_fields = []
    top_field_score = 0
    weak_field_score = 0

    if field_scores:

        # 60+ fields only for best
        eligible_fields = {f: s for f, s in field_scores.items() if s >= 60}

        if eligible_fields:
            max_score = max(eligible_fields.values())
            top_fields = [f for f, s in eligible_fields.items() if s == max_score]
            top_field_score = max_score

        # Improvement fields = <60
        improvement_fields = {f: s for f, s in field_scores.items() if s < 60}

        if improvement_fields:
            min_score = min(improvement_fields.values())
            weak_fields = [f for f, s in improvement_fields.items() if s == min_score]
            weak_field_score = min_score

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
        top_field_score=top_field_score,
        weak_field_score=weak_field_score,
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
    
    career_fields = []
    if user.interests:
        interests_list = [i.strip() for i in user.interests.split(',')]
        career_fields = interests_list[:3]
    
    return render_template('resources.html',
                          user=user,
                          career_fields=career_fields)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        if 'l_otp' not in request.form:
            email = request.form.get('l_email')
            password = request.form.get('l_password')

            user = User.query.filter_by(email=email).first()

            if not user:
                return render_template('login.html', email_not_found=True)

            if user.userPassword != password:
                return render_template('login.html', password_wrong=True)

            otp = random.randint(100000, 999999)
            print(otp)
            session['login_otp'] = str(otp)
            session['login_email'] = email
            session['login_user_id'] = user.id

            otpSender(email, otp)

            return render_template('login.html', show_otp_modal=True)

        else:
            inputOtp = request.form.get('l_otp')

            if inputOtp == session.get('login_otp'):
                session['user_id'] = session.get('login_user_id')
                session['user_email'] = session.get('login_email')
                
                user = db.session.get(User, session['user_id'])
                if user:
                    session['user_name'] = user.name
                
                session.pop('login_otp', None)
                session.pop('login_email', None)
                session.pop('login_user_id', None)
                
                return redirect(url_for('homeLogin'))
            else:
                return render_template('login.html', show_otp_modal=True, otp_fail=True)

    return render_template('login.html')

@app.route('/registation', methods=['GET', 'POST'])
def registation():
    if request.method == 'POST':
        if 'r_otp' not in request.form:
            name = request.form.get('r_name')
            email = request.form.get('r_email')
            password = request.form.get('r_password')
            confirm_password = request.form.get('r_confirmPassword')

            if password != confirm_password:
                return render_template('registation.html',
                                       registation_fail=True,
                                       r_name=name,
                                       r_email=email)

            existing_user = User.query.filter_by(email=email).first()
            if existing_user:
                return render_template('registation.html', registation_fail=True)

            otp = random.randint(100000, 999999)
            session['otp'] = str(otp)
            session['reg_name'] = name
            session['reg_email'] = email
            session['reg_password'] = password

            otpSender(email, otp)

            return render_template('registation.html', show_otp_modal=True)

        else:
            inputOtp = request.form.get('r_otp')

            if inputOtp == session.get('otp'):
                new_user = User(
                    name=session['reg_name'],
                    email=session['reg_email'],
                    userPassword=session['reg_password'],
                    created_at=datetime.utcnow()
                )
                db.session.add(new_user)
                db.session.commit()

                user = User.query.filter_by(email=session['reg_email']).first()
                
                session.pop('otp', None)
                session.pop('reg_name', None)
                session.pop('reg_email', None)
                session.pop('reg_password', None)

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

def create_tables():
    """Create database tables"""
    with app.app_context():
        db.create_all()

if __name__ == "__main__":
    create_tables()
    
    
    app.run(debug=True, port=5000)