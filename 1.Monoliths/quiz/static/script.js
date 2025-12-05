class QuizApp {
    constructor() {
        this.currentQuestionIndex = 0;
        this.totalQuestions = 0;
        this.score = 0;
        this.selectedAnswer = null;
        this.answerSubmitted = false;
        this.syncInterval = null;
        this.init();
    }

    init() {
        console.log('QuizApp initialized');
        this.bindEvents();
        
        if (window.location.pathname === '/quiz') {
            this.initializeQuiz();
        }
    }

    bindEvents() {
        const startForm = document.getElementById('start-quiz-form');
        if (startForm) {
            startForm.addEventListener('submit', (e) => this.handleStartQuiz(e));
        }

        const nextBtn = document.getElementById('next-question');
        if (nextBtn) {
            nextBtn.addEventListener('click', () => this.nextQuestion());
        }

        const submitBtn = document.getElementById('submit-answer');
        if (submitBtn) {
            submitBtn.addEventListener('click', () => this.submitSelectedAnswer());
        }
    }

    async handleStartQuiz(e) {
        e.preventDefault();
        
        const formData = new FormData(e.target);
        const name = formData.get('name') || 'Anonymous';

        try {
            const response = await fetch('/start_quiz', {
                method: 'POST',
                body: formData
            });

            const data = await response.json();

            if (data.success) {
                window.location.href = '/quiz';
            } else {
                this.showError('Failed to start quiz. Please try again.');
            }
        } catch (error) {
            console.error('Error starting quiz:', error);
            this.showError('Network error. Please try again.');
        }
    }

    async initializeQuiz() {
        console.log('Initializing quiz...');
        try {
            const response = await fetch('/total_questions');
            const data = await response.json();
            
            this.totalQuestions = data.total_questions;
            this.score = 0;
            this.answerSubmitted = false;
            
            console.log('Total questions:', this.totalQuestions);
            
            if (this.totalQuestions > 0) {
                this.startSync();
            } else {
                this.showError('No questions available.');
            }
        } catch (error) {
            console.error('Error initializing quiz:', error);
            this.showError('Failed to initialize quiz. Please try refreshing the page.');
        }
    }

    startSync() {
        if (this.syncInterval) {
            clearInterval(this.syncInterval);
        }
        
        this.syncInterval = setInterval(() => {
            this.syncWithServer();
        }, 1000);
        
        this.syncWithServer();
    }

    async syncWithServer() {
        try {
            const response = await fetch('/quiz_status');
            const status = await response.json();
            
            console.log('Server status:', status);
            
            await this.updateFromServer(status);
            
        } catch (error) {
            console.error('Error syncing with server:', error);
        }
    }

    async updateFromServer(status) {
        const serverQuestionIndex = status.current_question_index;
        const timeRemaining = Math.floor(status.time_remaining);
        const allAnswered = status.all_answered;
        
        console.log(`Update: Q${serverQuestionIndex}, Time:${timeRemaining}s, AllAnswered:${allAnswered}`);
        
        this.updateTimer(timeRemaining);
        this.updateNextButton(allAnswered, timeRemaining);
        
        // NEW: Handle timeout case - if time is up and we haven't submitted, show timeout result
        if (timeRemaining <= 0 && !this.answerSubmitted && this.currentQuestionData) {
            console.log('Time ran out - showing timeout result');
            this.showTimeoutResult();
        }
        
        if (serverQuestionIndex !== this.currentQuestionIndex || !this.currentQuestionData) {
            this.currentQuestionIndex = serverQuestionIndex;
            this.answerSubmitted = false;
            this.selectedAnswer = null;
            await this.loadQuestion(serverQuestionIndex);
        }
        
        this.updateParticipantCount(status);
    }

    updateTimer(timeRemaining) {
        const timeLeftElement = document.getElementById('time-left');
        const timerElement = document.getElementById('timer');
        
        if (timeLeftElement) {
            timeLeftElement.textContent = timeRemaining;
            
            if (timeRemaining <= 0) {
                timerElement.className = 'timer time-up';
            } else if (timeRemaining <= 12) {
                timerElement.className = 'timer warning';
            } else {
                timerElement.className = 'timer';
            }
        }
    }

    updateNextButton(allAnswered, timeRemaining) {
        const nextBtn = document.getElementById('next-question');
        if (!nextBtn) return;

        const shouldEnable = allAnswered || timeRemaining <= 0;
        
        console.log(`Next button - shouldEnable: ${shouldEnable}`);
        
        nextBtn.disabled = !shouldEnable;
        
        if (shouldEnable) {
            nextBtn.className = 'btn btn-ready';
        } else {
            nextBtn.className = 'btn btn-secondary';
        }
        
        nextBtn.textContent = this.currentQuestionIndex === this.totalQuestions - 1 ? 'Finish Quiz' : 'Next Question';
    }

    async loadQuestion(questionIndex) {
        console.log('Loading question:', questionIndex);
        
        try {
            const response = await fetch(`/get_question/${questionIndex}`);
            const question = await response.json();
            
            if (question.error) {
                throw new Error(question.error);
            }

            this.currentQuestionData = question;
            this.displayQuestion(question);
            
        } catch (error) {
            console.error('Error loading question:', error);
        }
    }

    displayQuestion(question) {
        const questionText = document.getElementById('question-text');
        const optionsContainer = document.getElementById('options-container');
        const progressText = document.getElementById('progress-text');
        const progressFill = document.getElementById('progress-fill');
        const submitBtn = document.getElementById('submit-answer');

        progressText.textContent = `Question ${this.currentQuestionIndex + 1} of ${this.totalQuestions}`;
        progressFill.style.width = `${((this.currentQuestionIndex + 1) / this.totalQuestions) * 100}%`;

        questionText.textContent = question.question;

        optionsContainer.innerHTML = '';
        question.options.forEach((option, index) => {
            const button = document.createElement('button');
            button.className = 'option-btn';
            button.textContent = option;
            button.addEventListener('click', () => this.selectAnswer(index, button));
            optionsContainer.appendChild(button);
        });

        if (!this.answerSubmitted) {
            submitBtn.disabled = false;
            submitBtn.textContent = 'Submit Answer';
            submitBtn.className = 'btn btn-primary';
        } else {
            submitBtn.disabled = true;
            submitBtn.textContent = 'Submitted';
        }

        document.getElementById('question-container').style.display = 'block';
        document.getElementById('result-container').style.display = 'none';
        document.getElementById('quiz-complete').style.display = 'none';
    }

    selectAnswer(answerIndex, button) {
        if (this.answerSubmitted) return;
        
        const optionButtons = document.querySelectorAll('.option-btn');
        optionButtons.forEach(btn => {
            btn.classList.remove('selected');
        });

        button.classList.add('selected');
        this.selectedAnswer = answerIndex;

        const submitBtn = document.getElementById('submit-answer');
        submitBtn.disabled = false;
    }

    async submitSelectedAnswer() {
        if (this.selectedAnswer === null || this.answerSubmitted) {
            return;
        }

        const optionButtons = document.querySelectorAll('.option-btn');
        const submitBtn = document.getElementById('submit-answer');
        
        optionButtons.forEach(btn => {
            btn.disabled = true;
        });
        submitBtn.disabled = true;
        submitBtn.textContent = 'Submitting...';

        try {
            const response = await fetch('/submit_answer', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    question_id: this.currentQuestionIndex,
                    answer_index: this.selectedAnswer
                })
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const result = await response.json();
            
            if (result.error) {
                throw new Error(result.error);
            }
            
            this.answerSubmitted = true;
            this.score = result.score;
            
            this.showResult(result, this.selectedAnswer);
            
            setTimeout(() => this.syncWithServer(), 100);
            
        } catch (error) {
            console.error('Error submitting answer:', error);
            this.showError(`Failed to submit answer: ${error.message}`);
            
            // Re-enable interface on error
            optionButtons.forEach(btn => {
                btn.disabled = false;
            });
            submitBtn.disabled = false;
            submitBtn.textContent = 'Submit Answer';
            submitBtn.className = 'btn btn-primary';
        }
    }

    // NEW: Handle timeout case
    showTimeoutResult() {
        if (this.answerSubmitted) return; // Don't show timeout if already submitted
        
        console.log('Showing timeout result');
        this.answerSubmitted = true;
        
        const questionContainer = document.getElementById('question-container');
        const resultContainer = document.getElementById('result-container');
        const resultTitle = document.getElementById('result-title');
        const resultMessage = document.getElementById('result-message');
        const currentScore = document.getElementById('current-score');

        // Highlight correct answer
        const optionButtons = document.querySelectorAll('.option-btn');
        optionButtons.forEach((btn, index) => {
            if (index === this.currentQuestionData.correct_answer) {
                btn.classList.add('correct');
            }
        });

        // Show timeout message
        resultTitle.textContent = 'Time\'s Up! ⏰';
        resultTitle.style.color = '#e53e3e';
        resultMessage.textContent = 'You ran out of time! The correct answer has been highlighted.';

        // Update display
        currentScore.textContent = this.score;

        questionContainer.style.display = 'none';
        resultContainer.style.display = 'block';
        
        // Disable submit button
        const submitBtn = document.getElementById('submit-answer');
        submitBtn.disabled = true;
        submitBtn.textContent = 'Time\'s Up';
        submitBtn.className = 'btn btn-secondary';
    }

    updateParticipantCount(status) {
        const total = status.total_participants || 0;
        const answered = status.answered_count || 0;
        
        const participantDisplay = document.getElementById('participant-count');
        if (participantDisplay) {
            participantDisplay.textContent = `Participants: ${answered}/${total}`;
        }
    }

    showResult(result, selectedAnswer) {
        const questionContainer = document.getElementById('question-container');
        const resultContainer = document.getElementById('result-container');
        const resultTitle = document.getElementById('result-title');
        const resultMessage = document.getElementById('result-message');
        const currentScore = document.getElementById('current-score');

        const optionButtons = document.querySelectorAll('.option-btn');
        optionButtons.forEach((btn, index) => {
            if (index === result.correct_answer) {
                btn.classList.add('correct');
            }
            if (selectedAnswer !== null && index === selectedAnswer && !result.correct) {
                btn.classList.add('incorrect');
            }
        });

        currentScore.textContent = this.score;

        if (result.correct) {
            resultTitle.textContent = 'Correct! 🎉';
            resultTitle.style.color = '#48bb78';
            resultMessage.textContent = 'Well done! You got it right.';
        } else {
            resultTitle.textContent = 'Incorrect 😞';
            resultTitle.style.color = '#f56565';
            const correctAnswer = document.querySelectorAll('.option-btn')[result.correct_answer].textContent;
            resultMessage.textContent = `The correct answer is: ${correctAnswer}`;
        }

        questionContainer.style.display = 'none';
        resultContainer.style.display = 'block';
    }

    async nextQuestion() {
        try {
            const response = await fetch('/next_question', {
                method: 'POST'
            });

            const result = await response.json();
            
            if (result.quiz_complete) {
                this.completeQuiz();
            }
            
        } catch (error) {
            console.error('Error moving to next question:', error);
        }
    }

    completeQuiz() {
        const finalScore = document.getElementById('final-score');
        finalScore.textContent = `${this.score} out of ${this.totalQuestions}`;
        
        document.getElementById('question-container').style.display = 'none';
        document.getElementById('result-container').style.display = 'none';
        document.getElementById('quiz-complete').style.display = 'block';
        
        if (this.syncInterval) {
            clearInterval(this.syncInterval);
        }
    }

    showError(message) {
        const errorDiv = document.getElementById('error-message');
        if (errorDiv) {
            errorDiv.textContent = message;
            errorDiv.style.display = 'block';
        } else {
            alert(message);
        }
    }
}

document.addEventListener('DOMContentLoaded', function() {
    new QuizApp();
});
