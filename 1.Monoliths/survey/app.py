#!/usr/bin/env python3

from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timezone
import json

import os,sys
import socket, platform

PORT = 5000
if len(sys.argv) > 1:
    PORT=sys.argv[1]

image = os.getenv('CONTAINER_IMAGE', '')

opsystem = platform.system()
#print(opsystem)
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
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class SurveyResponse(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    participant_id = db.Column(db.Integer, db.ForeignKey('participant.id'))
    question_id = db.Column(db.Integer)
    question_type = db.Column(db.String(20))
    response = db.Column(db.Text)
    submitted_at = db.Column(db.DateTime, default=datetime.utcnow)

# Load questions from JSON file
def load_questions():
    with open('survey_questions.json', 'r') as f:
        return json.load(f)['questions']

# Create Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = 'survey-secret-key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///survey.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

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

## -- START OF asciitext hack for wget/curl requests --------------------------------------------------

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
    print(ua)
    if 'curl/' in ua or 'wget/' in ua or 'httpie/' in ua:
        return ascii(request.base_url)
    return render_template('index.html')

@app.route('/start_survey', methods=['POST'])
def start_survey():
    name = request.form.get('name', 'Anonymous').strip()
    if not name:
        name = 'Anonymous'
    
    # Create new participant
    participant = Participant(name=name)
    db.session.add(participant)
    db.session.commit()
    
    session['participant_id'] = participant.id
    
    return jsonify({
        'success': True,
        'total_questions': len(load_questions())
    })

@app.route('/survey')
def survey():
    if 'participant_id' not in session:
        return redirect(url_for('index'))
    return render_template('survey.html')

@app.route('/get_questions')
def get_questions():
    questions = load_questions()
    return jsonify({'questions': questions})

@app.route('/total_questions')
def total_questions():
    questions = load_questions()
    return jsonify({'total_questions': len(questions)})

@app.route('/submit_response', methods=['POST'])
def submit_response():
    participant_id = session.get('participant_id')
    if not participant_id:
        return jsonify({'error': 'Not logged in'}), 401
    
    data = request.get_json()
    question_id = data.get('question_id')
    question_type = data.get('question_type')
    response = data.get('response')
    
    # Validate response
    if not response or str(response).strip() == '':
        return jsonify({'error': 'Response cannot be empty'}), 400
    
    # Check if participant already answered this question
    existing_response = SurveyResponse.query.filter_by(
        participant_id=participant_id,
        question_id=question_id
    ).first()
    
    if existing_response:
        # Update existing response
        existing_response.response = response
    else:
        # Create new response
        survey_response = SurveyResponse(
            participant_id=participant_id,
            question_id=question_id,
            question_type=question_type,
            response=response
        )
        db.session.add(survey_response)
    
    db.session.commit()
    
    return jsonify({'success': True})

@app.route('/submit_survey', methods=['POST'])
def submit_survey():
    participant_id = session.get('participant_id')
    if not participant_id:
        return jsonify({'error': 'Not logged in'}), 401
    
    # Check if all questions are answered
    questions = load_questions()
    answered_questions = SurveyResponse.query.filter_by(participant_id=participant_id).count()
    
    if answered_questions < len(questions):
        return jsonify({
            'success': False, 
            'message': f'Please answer all questions. You have answered {answered_questions} out of {len(questions)} questions.'
        })
    
    return jsonify({'success': True, 'message': 'Thank you for completing the survey!'})

@app.route('/results')
def results():
    return render_template('results.html')

@app.route('/api/results')
def api_results():
    questions = load_questions()
    results_data = {}
    
    for question in questions:
        question_id = question['id']
        question_type = question['type']
        question_text = question['question']
        
        # Get all responses for this question
        responses = SurveyResponse.query.filter_by(question_id=question_id).all()
        
        if question_type in ['sentiment', 'yesno']:
            # Count responses for each option
            response_counts = {}
            for response in responses:
                answer = response.response
                response_counts[answer] = response_counts.get(answer, 0) + 1
            
            results_data[question_id] = {
                'question': question_text,
                'type': question_type,
                'options': question.get('options', []),
                'responses': response_counts,
                'total_responses': len(responses)
            }
        elif question_type == 'text':
            # Collect all text responses
            text_responses = []
            for response in responses:
                if response.response.strip():  # Only include non-empty responses
                    text_responses.append(response.response)
            
            results_data[question_id] = {
                'question': question_text,
                'type': question_type,
                'responses': text_responses,
                'total_responses': len(text_responses)
            }
    
    return jsonify(results_data)

@app.route('/api/participant_count')
def api_participant_count():
    total_participants = Participant.query.count()
    return jsonify({'total_participants': total_participants})

@app.route('/debug_reset', methods=['GET'])
def debug_reset():
    """Debug route to reset everything"""
    SurveyResponse.query.delete()
    Participant.query.delete()
    db.session.commit()
    session.clear()
    return jsonify({'success': True, 'message': 'Survey reset complete'})

# Create database tables
with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=PORT)

