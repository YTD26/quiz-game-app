// Admin Panel JavaScript

let questionCount = 0;

// Tab switching
document.querySelectorAll('.tab').forEach(tab => {
    tab.addEventListener('click', () => {
        // Update tabs
        document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
        tab.classList.add('active');
        
        // Update content
        document.querySelectorAll('.tab-content').forEach(content => content.classList.remove('active'));
        document.getElementById(`${tab.dataset.tab}-tab`).classList.add('active');
        
        // Load data for specific tabs
        if (tab.dataset.tab === 'manage') {
            loadQuizzes();
        } else if (tab.dataset.tab === 'start') {
            loadQuizzesForGame();
        }
    });
});

// Add initial question
addQuestion();

function addQuestion() {
    questionCount++;
    
    const questionDiv = document.createElement('div');
    questionDiv.className = 'question-item';
    questionDiv.id = `question-${questionCount}`;
    questionDiv.innerHTML = `
        <h4>Vraag ${questionCount}</h4>
        <div class="form-group">
            <label>Vraag</label>
            <input type="text" class="question-text" placeholder="Wat is...?" required>
        </div>
        <div class="form-group">
            <label>Tijdslimiet (seconden)</label>
            <input type="number" class="question-time" value="30" min="5" max="120" required>
        </div>
        <div class="form-group">
            <label>Antwoorden (kies 1 als correct)</label>
            <div class="answers-container">
                ${[1,2,3,4].map(i => `
                    <div class="answer-item">
                        <input type="text" class="answer-text" placeholder="Antwoord ${i}" required>
                        <label>
                            <input type="radio" name="correct-${questionCount}" class="answer-correct" ${i === 1 ? 'checked' : ''}>
                            Correct
                        </label>
                    </div>
                `).join('')}
            </div>
        </div>
        <button type="button" class="btn btn-danger" onclick="removeQuestion(${questionCount})">Verwijder Vraag</button>
        <hr>
    `;
    
    document.getElementById('questionsContainer').appendChild(questionDiv);
}

function removeQuestion(id) {
    const questionDiv = document.getElementById(`question-${id}`);
    if (questionDiv) {
        questionDiv.remove();
    }
}

// Create quiz form submission
document.getElementById('createQuizForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const title = document.getElementById('quizTitle').value;
    const description = document.getElementById('quizDescription').value;
    
    // Collect questions
    const questions = [];
    document.querySelectorAll('.question-item').forEach((questionDiv, index) => {
        const questionText = questionDiv.querySelector('.question-text').value;
        const timeLimit = parseInt(questionDiv.querySelector('.question-time').value);
        
        // Collect answers
        const answers = [];
        const answerItems = questionDiv.querySelectorAll('.answer-item');
        answerItems.forEach((answerDiv, answerIndex) => {
            const answerText = answerDiv.querySelector('.answer-text').value;
            const isCorrect = answerDiv.querySelector('.answer-correct').checked;
            
            answers.push({
                answer_text: answerText,
                is_correct: isCorrect,
                order: answerIndex
            });
        });
        
        questions.push({
            question_text: questionText,
            time_limit: timeLimit,
            order: index,
            answers: answers
        });
    });
    
    // Validate
    if (questions.length === 0) {
        showMessage('quizMessage', 'Voeg minimaal 1 vraag toe', 'error');
        return;
    }
    
    // Submit
    try {
        const response = await fetch('/api/admin/quiz', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                title: title,
                description: description,
                questions: questions
            })
        });
        
        if (response.ok) {
            const data = await response.json();
            showMessage('quizMessage', `Quiz "${data.title}" succesvol aangemaakt!`, 'success');
            
            // Reset form
            document.getElementById('createQuizForm').reset();
            document.getElementById('questionsContainer').innerHTML = '';
            questionCount = 0;
            addQuestion();
        } else {
            const error = await response.json();
            showMessage('quizMessage', error.detail || 'Fout bij aanmaken quiz', 'error');
        }
    } catch (error) {
        showMessage('quizMessage', 'Kan geen verbinding maken met server', 'error');
    }
});

async function loadQuizzes() {
    try {
        const response = await fetch('/api/admin/quiz');
        const quizzes = await response.json();
        
        const quizList = document.getElementById('quizList');
        quizList.innerHTML = '';
        
        if (quizzes.length === 0) {
            quizList.innerHTML = '<p>Nog geen quizzen aangemaakt</p>';
            return;
        }
        
        quizzes.forEach(quiz => {
            const quizDiv = document.createElement('div');
            quizDiv.className = 'quiz-item';
            quizDiv.innerHTML = `
                <div class="quiz-info">
                    <h3>${quiz.title}</h3>
                    <p class="quiz-meta">${quiz.question_count} vragen</p>
                </div>
                <div class="quiz-actions">
                    <button class="btn btn-primary" onclick="startGameWithQuiz(${quiz.id})">Start</button>
                    <button class="btn btn-danger" onclick="deleteQuiz(${quiz.id})">Verwijder</button>
                </div>
            `;
            quizList.appendChild(quizDiv);
        });
    } catch (error) {
        console.error('Error loading quizzes:', error);
    }
}

async function deleteQuiz(quizId) {
    if (!confirm('Weet je zeker dat je deze quiz wilt verwijderen?')) {
        return;
    }
    
    try {
        const response = await fetch(`/api/admin/quiz/${quizId}`, {
            method: 'DELETE'
        });
        
        if (response.ok) {
            loadQuizzes();
        } else {
            alert('Fout bij verwijderen quiz');
        }
    } catch (error) {
        alert('Kan geen verbinding maken met server');
    }
}

async function loadQuizzesForGame() {
    try {
        const response = await fetch('/api/admin/quiz');
        const quizzes = await response.json();
        
        const select = document.getElementById('gameQuizSelect');
        select.innerHTML = '<option value="">-- Kies een quiz --</option>';
        
        quizzes.forEach(quiz => {
            const option = document.createElement('option');
            option.value = quiz.id;
            option.textContent = `${quiz.title} (${quiz.question_count} vragen)`;
            select.appendChild(option);
        });
    } catch (error) {
        console.error('Error loading quizzes:', error);
    }
}

async function startNewGame() {
    const quizId = document.getElementById('gameQuizSelect').value;
    
    if (!quizId) {
        showMessage('gameStartMessage', 'Selecteer eerst een quiz', 'error');
        return;
    }
    
    try {
        const response = await fetch('/api/game/start', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({quiz_id: parseInt(quizId)})
        });
        
        if (response.ok) {
            const data = await response.json();
            showMessage('gameStartMessage', `Game gestart! Code: ${data.game_code}`, 'success');
            
            setTimeout(() => {
                window.location.href = `/host/${data.game_code}`;
            }, 1500);
        } else {
            const error = await response.json();
            showMessage('gameStartMessage', error.detail || 'Fout bij starten game', 'error');
        }
    } catch (error) {
        showMessage('gameStartMessage', 'Kan geen verbinding maken met server', 'error');
    }
}

function startGameWithQuiz(quizId) {
    document.getElementById('gameQuizSelect').value = quizId;
    document.querySelector('[data-tab="start"]').click();
}

function showMessage(elementId, message, type) {
    const messageDiv = document.getElementById(elementId);
    messageDiv.textContent = message;
    messageDiv.className = `alert alert-${type}`;
    messageDiv.style.display = 'block';
    
    setTimeout(() => {
        messageDiv.style.display = 'none';
    }, 5000);
}