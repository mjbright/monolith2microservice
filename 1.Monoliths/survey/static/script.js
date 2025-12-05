class SurveyApp {
    constructor() {
        this.currentQuestionIndex = 0;
        this.totalQuestions = 0;
        this.questions = [];
        this.responses = {};
        this.init();
    }

    init() {
        console.log('SurveyApp initialized');
        this.bindEvents();
        
        if (window.location.pathname === '/survey') {
            this.initializeSurvey();
        }
    }

    bindEvents() {
        const startForm = document.getElementById('start-survey-form');
        if (startForm) {
            startForm.addEventListener('submit', (e) => this.handleStartSurvey(e));
        }

        const prevBtn = document.getElementById('prev-question');
        if (prevBtn) {
            prevBtn.addEventListener('click', () => this.previousQuestion());
        }

        const nextBtn = document.getElementById('next-question');
        if (nextBtn) {
            nextBtn.addEventListener('click', () => this.nextQuestion());
        }

        const submitBtn = document.getElementById('submit-survey');
        if (submitBtn) {
            submitBtn.addEventListener('click', () => this.submitSurvey());
        }
    }

    async handleStartSurvey(e) {
        e.preventDefault();
        
        const formData = new FormData(e.target);
        const name = formData.get('name') || 'Anonymous';

        try {
            const response = await fetch('/start_survey', {
                method: 'POST',
                body: formData
            });

            const data = await response.json();

            if (data.success) {
                window.location.href = '/survey';
            } else {
                this.showError('Failed to start survey. Please try again.');
            }
        } catch (error) {
            console.error('Error starting survey:', error);
            this.showError('Network error. Please try again.');
        }
    }

    async initializeSurvey() {
        console.log('Initializing survey...');
        try {
            const response = await fetch('/get_questions');
            const data = await response.json();
            
            this.questions = data.questions;
            this.totalQuestions = this.questions.length;
            
            console.log('Total questions:', this.totalQuestions);
            
            if (this.totalQuestions > 0) {
                this.displayQuestion(0);
            } else {
                this.showError('No questions available.');
            }
        } catch (error) {
            console.error('Error initializing survey:', error);
            this.showError('Failed to initialize survey. Please try refreshing the page.');
        }
    }

    displayQuestion(questionIndex) {
        if (questionIndex < 0 || questionIndex >= this.totalQuestions) {
            return;
        }

        const question = this.questions[questionIndex];
        const questionText = document.getElementById('question-text');
        const optionsContainer = document.getElementById('options-container');
        const textInputContainer = document.getElementById('text-input-container');
        const progressText = document.getElementById('progress-text');
        const progressFill = document.getElementById('progress-fill');
        const prevBtn = document.getElementById('prev-question');
        const nextBtn = document.getElementById('next-question');
        const submitBtn = document.getElementById('submit-survey');

        // Update progress
        progressText.textContent = `Question ${questionIndex + 1} of ${this.totalQuestions}`;
        progressFill.style.width = `${((questionIndex + 1) / this.totalQuestions) * 100}%`;

        // Display question
        questionText.textContent = question.question;

        // Handle different question types
        if (question.type === 'text') {
            // Show text input
            optionsContainer.style.display = 'none';
            textInputContainer.style.display = 'block';
            
            // Set current response if exists
            const textResponse = document.getElementById('text-response');
            textResponse.value = this.responses[question.id] || '';
        } else {
            // Show options
            optionsContainer.style.display = 'grid';
            textInputContainer.style.display = 'none';
            
            // Display options
            optionsContainer.innerHTML = '';
            question.options.forEach((option, index) => {
                const button = document.createElement('button');
                button.className = 'option-btn';
                button.textContent = option;
                if (this.responses[question.id] === option) {
                    button.classList.add('selected');
                }
                button.addEventListener('click', () => this.selectOption(question.id, option, button));
                optionsContainer.appendChild(button);
            });
        }

        // Update navigation buttons
        prevBtn.disabled = questionIndex === 0;
        
        if (questionIndex === this.totalQuestions - 1) {
            nextBtn.style.display = 'none';
            submitBtn.style.display = 'inline-block';
        } else {
            nextBtn.style.display = 'inline-block';
            submitBtn.style.display = 'none';
        }

        this.currentQuestionIndex = questionIndex;
    }

    selectOption(questionId, option, button) {
        const optionButtons = document.querySelectorAll('.option-btn');
        optionButtons.forEach(btn => {
            btn.classList.remove('selected');
        });

        button.classList.add('selected');
        this.responses[questionId] = option;
        
        // Save response immediately
        this.saveResponse(questionId, 'option', option);
    }

    async saveResponse(questionId, questionType, response) {
        try {
            const question = this.questions.find(q => q.id === questionId);
            const responseData = {
                question_id: questionId,
                question_type: question.type,
                response: response
            };

            const saveResponse = await fetch('/submit_response', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(responseData)
            });

            const result = await saveResponse.json();
            if (!result.success) {
                console.error('Failed to save response:', result.error);
            }
        } catch (error) {
            console.error('Error saving response:', error);
        }
    }

    previousQuestion() {
        this.saveCurrentResponse();
        this.displayQuestion(this.currentQuestionIndex - 1);
    }

    async nextQuestion() {
        if (await this.saveCurrentResponse()) {
            this.displayQuestion(this.currentQuestionIndex + 1);
        }
    }

    async saveCurrentResponse() {
        const currentQuestion = this.questions[this.currentQuestionIndex];
        
        if (currentQuestion.type === 'text') {
            const textResponse = document.getElementById('text-response').value.trim();
            if (!textResponse) {
                this.showError('Please enter your response before continuing.');
                return false;
            }
            this.responses[currentQuestion.id] = textResponse;
            await this.saveResponse(currentQuestion.id, 'text', textResponse);
        } else {
            if (!this.responses[currentQuestion.id]) {
                this.showError('Please select an option before continuing.');
                return false;
            }
            // Response already saved when option was selected
        }
        
        return true;
    }

    async submitSurvey() {
        if (await this.saveCurrentResponse()) {
            try {
                const response = await fetch('/submit_survey', {
                    method: 'POST'
                });

                const result = await response.json();
                
                if (result.success) {
                    this.showCompletion(result.message);
                } else {
                    this.showError(result.message);
                }
            } catch (error) {
                console.error('Error submitting survey:', error);
                this.showError('Failed to submit survey. Please try again.');
            }
        }
    }

    showCompletion(message) {
        const surveyContent = document.getElementById('survey-content');
        const completionMessage = document.getElementById('completion-message');
        
        completionMessage.textContent = message;
        document.getElementById('question-container').style.display = 'none';
        document.getElementById('survey-complete').style.display = 'block';
    }

    showError(message) {
        const errorDiv = document.getElementById('error-message');
        if (errorDiv) {
            errorDiv.textContent = message;
            errorDiv.style.display = 'block';
            setTimeout(() => {
                errorDiv.style.display = 'none';
            }, 5000);
        } else {
            alert(message);
        }
    }
}

// Results page functionality
async function loadSurveyResults() {
    try {
        const response = await fetch('/api/results');
        const results = await response.json();
        
        const loadingMessage = document.getElementById('loading-message');
        const chartsContainer = document.getElementById('charts-container');
        const noDataMessage = document.getElementById('no-data-message');
        
        if (Object.keys(results).length === 0) {
            loadingMessage.style.display = 'none';
            noDataMessage.style.display = 'block';
            return;
        }
        
        loadingMessage.style.display = 'none';
        chartsContainer.style.display = 'block';
        chartsContainer.innerHTML = '';
        
        // Create charts for each question
        for (const questionId in results) {
            const questionData = results[questionId];
            const chartItem = document.createElement('div');
            chartItem.className = 'chart-item';
            
            if (questionData.type === 'text') {
                // Display text responses
                chartItem.innerHTML = `
                    <h3 class="chart-title">${questionData.question}</h3>
                    <div class="text-responses">
                        ${questionData.responses.length > 0 ? 
                          questionData.responses.map(response => 
                            `<div class="text-response-item">${response}</div>`
                          ).join('') :
                          '<p>No text responses yet.</p>'
                        }
                    </div>
                    <p><strong>Total responses:</strong> ${questionData.total_responses}</p>
                `;
            } else {
                // Create chart for sentiment/yesno questions
                chartItem.innerHTML = `
                    <h3 class="chart-title">${questionData.question}</h3>
                    <div class="chart-container">
                        <canvas id="chart-${questionId}"></canvas>
                    </div>
                    <p><strong>Total responses:</strong> ${questionData.total_responses}</p>
                `;
            }
            
            chartsContainer.appendChild(chartItem);
            
            // Create chart if not text type
            if (questionData.type !== 'text') {
                createPieChart(questionId, questionData);
            }
        }
    } catch (error) {
        console.error('Error loading results:', error);
        document.getElementById('loading-message').textContent = 'Error loading results. Please try again.';
    }
}

function createPieChart(questionId, questionData) {
    const ctx = document.getElementById(`chart-${questionId}`).getContext('2d');
    
    // Prepare data for chart
    const labels = questionData.options || Object.keys(questionData.responses);
    const data = labels.map(label => questionData.responses[label] || 0);
    
    // Define colors based on question type
    let backgroundColors;
    if (questionData.type === 'sentiment') {
        backgroundColors = [
            '#48bb78', // perfect - green
            '#68d391', // good - light green
            '#ecc94b', // ok - yellow
            '#ed8936', // poor - orange
            '#e53e3e'  // very poor - red
        ];
    } else {
        backgroundColors = [
            '#48bb78', // yes - green
            '#e53e3e', // no - red
            '#a0aec0'  // don't know - gray
        ];
    }
    
    new Chart(ctx, {
        type: 'pie',
        data: {
            labels: labels,
            datasets: [{
                data: data,
                backgroundColor: backgroundColors,
                borderColor: '#fff',
                borderWidth: 2
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: {
                        padding: 20,
                        usePointStyle: true
                    }
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            const label = context.label || '';
                            const value = context.raw || 0;
                            const total = context.dataset.data.reduce((a, b) => a + b, 0);
                            const percentage = total > 0 ? ((value / total) * 100).toFixed(1) : 0;
                            return `${label}: ${value} (${percentage}%)`;
                        }
                    }
                }
            }
        }
    });
}

async function loadParticipantCount() {
    try {
        const response = await fetch('/api/participant_count');
        const data = await response.json();
        document.getElementById('total-participants').textContent = data.total_participants;
    } catch (error) {
        console.error('Error loading participant count:', error);
    }
}

// Initialize the app when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    new SurveyApp();
});
