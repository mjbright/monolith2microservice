#!/usr/bin/env python3

from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta, timezone
import json
import os, sys

import socket, platform

PORT = 5000
if len(sys.argv) > 1:
    PORT=sys.argv[1]

image = os.getenv('CONTAINER_IMAGE', '')

opsystem= platform.system()
#print(opsystem
match opsystem:
    case "Linux":
        serverhost=socket.gethostname()
        serverip=socket.gethostbyname(socket.gethostname())
    case "Darwin":
        serverhost=socket.gethostname()
        serverip=[(s.connect(('8.8.8.8', 53)), s.getsockname()[0], s.close()) for s in [socket.socket(socket.AF_INET, socket.SOCK_DGRAM)]][0][1]
    case _:
        print(f'Unknown OS type {opsystem}')
        sys.exit(1)

#print(f'serverhost={serverhost} serverip={serverip}')
#print(datetime.now(timezone.utc))

# Initialize extensions
db = SQLAlchemy()

# Models
class Participant(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    score = db.Column(db.Integer, default=0)
    total_questions = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'score': self.score,
            'total_questions': self.total_questions,
            'percentage': round((self.score / self.total_questions * 100), 2) if self.total_questions > 0 else 0
        }

# Simplified quiz session model
class QuizSession(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    current_question_index = db.Column(db.Integer, default=0)
    question_start_time = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)

# Track answers
class ParticipantAnswer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    participant_id = db.Column(db.Integer, db.ForeignKey('participant.id'))
    question_index = db.Column(db.Integer)
    answer_index = db.Column(db.Integer, nullable=True)
    is_correct = db.Column(db.Boolean, default=False)
    submitted_at = db.Column(db.DateTime, default=datetime.utcnow)

# Load questions from JSON file
def load_questions():
    with open('questions.json', 'r') as f:
        return json.load(f)['questions']

# Create Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = 'dev-secret-key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///quiz.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

# Get or create quiz session
def get_quiz_session():
    session_obj = QuizSession.query.first()
    if not session_obj:
        session_obj = QuizSession()
        db.session.add(session_obj)
        db.session.commit()
    return session_obj

## -- COLORS: --------------------------------------------------------------------------------
BLACK = "\033[0;30m"
RED = "\033[0;31m"
GREEN = "\033[0;32m"
BROWN = "\033[0;33m"
BLUE = "\033[0;34m"
PURPLE = "\033[0;35m"
CYAN = "\033[0;36m"
LIGHT_GRAY = "\033[0;37m"
DARK_GRAY = "\033[1;30m"
LIGHT_RED = "\033[1;31m"
LIGHT_GREEN = "\033[1;32m"
YELLOW = "\033[1;33m"
LIGHT_BLUE = "\033[1;34m"
LIGHT_PURPLE = "\033[1;35m"
LIGHT_CYAN = "\033[1;36m"
LIGHT_WHITE = "\033[1;37m"
BOLD = "\033[1m"
FAINT = "\033[2m"
ITALIC = "\033[3m"
UNDERLINE = "\033[4m"
BLINK = "\033[5m"
NEGATIVE = "\033[7m"
CROSSED = "\033[9m"
END = "\033[0m"
## -- COLORS: --------------------------------------------------------------------------------

## -- START OF asciitext hack for wget/curl requests --------------------------------------------------
def readfile(path, mode='r'):
    ifd = open(path, mode)
    #line1=ifd.readline()
    #for line in ifd.readlines(): print(line)
    ret=ifd.read()
    ifd.close()
    return ret

def ascii(url):
    #print(f'url={url}')
    ret = ''
    if not url.endswith(f':{PORT}/1'):
        ret = readfile('static/img/survey.txt')

    sourceip = request.environ.get('HTTP_X_REAL_IP', request.remote_addr)

    now = datetime.now(timezone.utc)
    statusline = f'[{now}] Request from {sourceip} to {serverhost}/{serverip}:{PORT}\n'
    if image != '':
        color=''
        end=''
        if 'v1' in image: color=CYAN
        if 'v2' in image: color=GREEN
        if 'v3' in image: color=RED
        if color != '':   end=END
        statusline = f'[{color}{image}{END}] {statusline}{end}'

    ret += statusline
    print(statusline)
    return ret

## -- END   OF asciitext hack for wget/curl requests --------------------------------------------------

@app.route('/1')
def statusLine():
    return ascii(request.base_url)

@app.route('/')
def index():
    ua = request.headers.get('User-Agent').lower()
    if 'curl/' in ua or 'wget/' in ua or 'httpie/' in ua:
        return ascii(request.base_url)
    return render_template('index.html')

@app.route('/start_quiz', methods=['POST'])
def start_quiz():
    name = request.form.get('name', 'Anonymous').strip()
    if not name:
        name = 'Anonymous'
    
    # Create new participant
    participant = Participant(name=name)
    db.session.add(participant)
    db.session.commit()
    
    session['participant_id'] = participant.id
    
    # Set total questions
    questions = load_questions()
    participant.total_questions = len(questions)
    db.session.commit()
    
    # Reset quiz session if this is the first participant
    quiz_session = get_quiz_session()
    participant_count = Participant.query.count()
    if participant_count == 1:  # Only reset if this is the first participant
        quiz_session.current_question_index = 0
        quiz_session.question_start_time = datetime.utcnow()
        quiz_session.is_active = True
        db.session.commit()
    
    return jsonify({
        'success': True,
        'total_questions': len(questions)
    })

@app.route('/quiz')
def quiz():
    if 'participant_id' not in session:
        return redirect(url_for('index'))
    return render_template('quiz.html')

@app.route('/get_question/<int:question_index>')
def get_question(question_index):
    questions = load_questions()
    if 0 <= question_index < len(questions):
        question = questions[question_index]
        return jsonify({
            'id': question_index,
            'question': question['question'],
            'options': question['options'],
            'correct_answer': question['correct_answer']
        })
    return jsonify({'error': 'Question not found'}), 404

@app.route('/total_questions')
def total_questions():
    questions = load_questions()
    return jsonify({'total_questions': len(questions)})

@app.route('/submit_answer', methods=['POST'])
def submit_answer():
    # Get participant_id from session
    participant_id = session.get('participant_id')
    if not participant_id:
        return jsonify({'error': 'Not logged in'}), 401
    
    data = request.get_json()
    question_index = data.get('question_id')
    answer_index = data.get('answer_index')
    
    questions = load_questions()
    
    if question_index < 0 or question_index >= len(questions):
        return jsonify({'error': 'Invalid question'}), 400
        
    current_question = questions[question_index]
    
    if answer_index is None:
        is_correct = False
    else:
        is_correct = answer_index == current_question['correct_answer']
    
    # Find participant
    participant = Participant.query.get(participant_id)
    if not participant:
        return jsonify({'error': 'Participant not found'}), 404
    
    # Update score
    if is_correct:
        participant.score += 1
    
    # Record answer
    existing_answer = ParticipantAnswer.query.filter_by(
        participant_id=participant.id,
        question_index=question_index
    ).first()
    
    if not existing_answer:
        answer_record = ParticipantAnswer(
            participant_id=participant.id,
            question_index=question_index,
            answer_index=answer_index,
            is_correct=is_correct
        )
        db.session.add(answer_record)
    
    db.session.commit()
    
    return jsonify({
        'correct': is_correct,
        'correct_answer': current_question['correct_answer'],
        'score': participant.score,
        'total_questions': len(questions)
    })

@app.route('/quiz_status')
def quiz_status():
    """Get current quiz status"""
    quiz_session = get_quiz_session()
    questions = load_questions()
    
    # Calculate time remaining
    time_remaining = 12
    print(f'time_remaining={time_remaining}')
    if quiz_session.question_start_time:
        elapsed = (datetime.utcnow() - quiz_session.question_start_time).total_seconds()
        print(f'time_remaining={time_remaining} = max(0, {time_remaining - elapsed}')
        time_remaining = max(0, time_remaining - elapsed)
    
    # Check if all participants have answered
    total_participants = Participant.query.count()
    answered_count = ParticipantAnswer.query.filter_by(
        question_index=quiz_session.current_question_index
    ).count()
    
    all_answered = total_participants > 0 and answered_count >= total_participants
    
    # NEW: Auto-submit for participants who haven't answered when time runs out
    if time_remaining <= 0 and not all_answered:
        # Find participants who haven't answered this question
        answered_participants = [pa.participant_id for pa in 
                               ParticipantAnswer.query.filter_by(question_index=quiz_session.current_question_index).all()]
        
        all_participants = Participant.query.all()
        for participant in all_participants:
            if participant.id not in answered_participants:
                # Auto-submit with no answer (timeout)
                timeout_answer = ParticipantAnswer(
                    participant_id=participant.id,
                    question_index=quiz_session.current_question_index,
                    answer_index=None,  # NULL means timeout
                    is_correct=False
                )
                db.session.add(timeout_answer)
        
        db.session.commit()
        
        # Update counts after auto-submission
        answered_count = ParticipantAnswer.query.filter_by(
            question_index=quiz_session.current_question_index
        ).count()
        all_answered = total_participants > 0 and answered_count >= total_participants
    
    # If everyone answered, force progression
    if all_answered:
        time_remaining = 0
    
    return jsonify({
        'current_question_index': quiz_session.current_question_index,
        'time_remaining': time_remaining,
        'all_answered': all_answered,
        'total_participants': total_participants,
        'answered_count': answered_count,
        'is_active': quiz_session.is_active
    })

@app.route('/next_question', methods=['POST'])
def next_question():
    """Move to next question"""
    quiz_session = get_quiz_session()
    questions = load_questions()
    
    if quiz_session.current_question_index < len(questions) - 1:
        quiz_session.current_question_index += 1
        quiz_session.question_start_time = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'success': True,
            'new_question_index': quiz_session.current_question_index
        })
    else:
        quiz_session.is_active = False
        db.session.commit()
        return jsonify({
            'success': True,
            'quiz_complete': True
        })

@app.route('/reset_quiz', methods=['POST'])
def reset_quiz():
    """Reset the entire quiz"""
    quiz_session = get_quiz_session()
    quiz_session.current_question_index = 0
    quiz_session.question_start_time = datetime.utcnow()
    quiz_session.is_active = True
    
    # Clear all data
    ParticipantAnswer.query.delete()
    Participant.query.delete()
    
    db.session.commit()
    return jsonify({'success': True})

@app.route('/debug_reset', methods=['GET'])
def debug_reset():
    """Debug route to reset everything"""
    quiz_session = get_quiz_session()
    quiz_session.current_question_index = 0
    quiz_session.question_start_time = datetime.utcnow()
    quiz_session.is_active = True
    
    ParticipantAnswer.query.delete()
    Participant.query.delete()
    
    db.session.commit()
    
    # Clear session
    session.clear()
    
    return jsonify({'success': True, 'message': 'Quiz reset complete'})

@app.route('/debug_status')
def debug_status():
    """Debug route to check status"""
    quiz_session = get_quiz_session()
    participants = Participant.query.all()
    current_answers = ParticipantAnswer.query.filter_by(question_index=quiz_session.current_question_index).all()
    
    return jsonify({
        'quiz_session': {
            'current_question': quiz_session.current_question_index,
            'start_time': quiz_session.question_start_time.isoformat() if quiz_session.question_start_time else None,
            'is_active': quiz_session.is_active
        },
        'participants': [{'id': p.id, 'name': p.name, 'score': p.score} for p in participants],
        'current_answers': [{'participant_id': a.participant_id, 'answer_index': a.answer_index} for a in current_answers],
        'session_participant_id': session.get('participant_id')
    })

@app.route('/leaderboard')
def leaderboard():
    participants = Participant.query.all()
    sorted_participants = sorted(
        participants, 
        key=lambda p: (p.score / p.total_questions * 100) if p.total_questions > 0 else 0, 
        reverse=True
    )[:3]
    
    return render_template('leaderboard.html', 
                         participants=[p.to_dict() for p in sorted_participants])

# Create database tables
with app.app_context():
    db.create_all()
    get_quiz_session()

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=PORT)
