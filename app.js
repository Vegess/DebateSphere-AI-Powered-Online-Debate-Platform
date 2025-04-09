// DOM Elements
const microphoneSelect = document.getElementById('microphone-select');
const startRecordingBtn = document.getElementById('start-recording');
const stopRecordingBtn = document.getElementById('stop-recording');
const textInput = document.getElementById('text-input');
const analyzeTextBtn = document.getElementById('analyze-text');
const loadingElement = document.getElementById('loading');
const transcriptContainer = document.getElementById('transcript-container');
const transcriptElement = document.getElementById('transcript');
const claimsContainer = document.getElementById('claims-container');
const claimsList = document.getElementById('claims-list');
const verificationContainer = document.getElementById('verification-container');
const verificationResults = document.getElementById('verification-results');
const sourcesContainer = document.getElementById('sources-container');
const sourcesList = document.getElementById('sources-list');

// Variables
let mediaRecorder;
let audioChunks = [];
let isRecording = false;

// Initialize the application
document.addEventListener('DOMContentLoaded', () => {
    // Populate microphone selection
    populateMicrophoneSelect();
    
    // Add event listeners
    startRecordingBtn.addEventListener('click', startRecording);
    stopRecordingBtn.addEventListener('click', stopRecording);
    analyzeTextBtn.addEventListener('click', analyzeText);
});

// Function to populate microphone selection dropdown
async function populateMicrophoneSelect() {
    try {
        const devices = await navigator.mediaDevices.enumerateDevices();
        const audioInputs = devices.filter(device => device.kind === 'audioinput');
        
        microphoneSelect.innerHTML = '';
        
        audioInputs.forEach(device => {
            const option = document.createElement('option');
            option.value = device.deviceId;
            option.text = device.label || `Microphone ${microphoneSelect.length + 1}`;
            microphoneSelect.appendChild(option);
        });
        
        // Enable/disable recording buttons based on microphone availability
        if (audioInputs.length > 0) {
            startRecordingBtn.disabled = false;
        } else {
            startRecordingBtn.disabled = true;
            microphoneSelect.innerHTML = '<option value="">No microphones found</option>';
        }
    } catch (error) {
        console.error('Error accessing microphone devices:', error);
        microphoneSelect.innerHTML = '<option value="">Error accessing microphones</option>';
        startRecordingBtn.disabled = true;
    }
}

// Function to start recording
async function startRecording() {
    try {
        const stream = await navigator.mediaDevices.getUserMedia({
            audio: {
                deviceId: microphoneSelect.value ? { exact: microphoneSelect.value } : undefined
            }
        });
        
        mediaRecorder = new MediaRecorder(stream);
        audioChunks = [];
        
        mediaRecorder.ondataavailable = (event) => {
            audioChunks.push(event.data);
        };
        
        mediaRecorder.onstop = () => {
            const audioBlob = new Blob(audioChunks, { type: 'audio/wav' });
            sendAudioToServer(audioBlob);
        };
        
        mediaRecorder.start();
        isRecording = true;
        
        // Update UI
        startRecordingBtn.disabled = true;
        stopRecordingBtn.disabled = false;
        microphoneSelect.disabled = true;
        
        // Show recording indicator
        startRecordingBtn.innerHTML = '<i class="fas fa-microphone"></i> Recording...';
        startRecordingBtn.classList.add('recording');
    } catch (error) {
        console.error('Error starting recording:', error);
        alert('Error starting recording. Please check your microphone permissions.');
    }
}

// Function to stop recording
function stopRecording() {
    if (mediaRecorder && mediaRecorder.state !== 'inactive') {
        mediaRecorder.stop();
        isRecording = false;
        
        // Update UI
        startRecordingBtn.disabled = false;
        stopRecordingBtn.disabled = true;
        microphoneSelect.disabled = false;
        
        // Reset recording indicator
        startRecordingBtn.innerHTML = '<i class="fas fa-microphone"></i> Start Recording';
        startRecordingBtn.classList.remove('recording');
    }
}

// Function to send audio to server
function sendAudioToServer(audioBlob) {
    const formData = new FormData();
    formData.append('audio', audioBlob, 'recording.wav');
    
    // Show loading indicator
    loadingElement.classList.remove('hidden');
    transcriptContainer.classList.add('hidden');
    claimsContainer.classList.add('hidden');
    verificationContainer.classList.add('hidden');
    sourcesContainer.classList.add('hidden');
    
    fetch('http://127.0.0.1:5000/api/voice-to-text', {
        method: 'POST',
        body: formData
    })
    .then(response => {
        if (!response.ok) {
            throw new Error('Network response was not ok');
        }
        return response.json();
    })
    .then(data => {
        // Hide loading indicator
        loadingElement.classList.add('hidden');
        
        if (data.error) {
            alert(`Error: ${data.error}`);
            return;
        }
        
        // Display transcribed text
        transcriptElement.textContent = data.text;
        transcriptContainer.classList.remove('hidden');
        
        // Analyze the transcribed text
        analyzeClaims(data.text);
    })
    .catch(error => {
        console.error('Error:', error);
        loadingElement.classList.add('hidden');
        alert(`Error: ${error.message}. Please try again.`);
    });
}

// Function to analyze text
function analyzeText() {
    const text = textInput.value.trim();
    
    if (text === '') {
        alert('Please enter some text to analyze.');
        return;
    }
    
    analyzeClaims(text);
}

// Function to analyze claims
function analyzeClaims(text) {
    // Show loading indicator
    loadingElement.classList.remove('hidden');
    claimsContainer.classList.add('hidden');
    verificationContainer.classList.add('hidden');
    sourcesContainer.classList.add('hidden');
    
    fetch('http://127.0.0.1:5000/api/analyze/claims', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ text: text })
    })
    .then(response => {
        if (!response.ok) {
            throw new Error('Network response was not ok');
        }
        return response.json();
    })
    .then(data => {
        // Hide loading indicator
        loadingElement.classList.add('hidden');
        
        if (data.error) {
            alert(`Error: ${data.error}`);
            return;
        }
        
        // Display claims
        displayClaims(data.claims);
        
        // Display verification results
        displayVerificationResults(data.claims);
        
        // Display sources
        displaySources(data.claims);
    })
    .catch(error => {
        console.error('Error:', error);
        loadingElement.classList.add('hidden');
        alert(`Error: ${error.message}. Please try again.`);
    });
}

// Function to display claims
function displayClaims(claims) {
    if (!claims || claims.length === 0) {
        claimsList.innerHTML = '<p>No claims found in the text.</p>';
        claimsContainer.classList.remove('hidden');
        return;
    }
    
    let html = `<p>Found ${claims.length} claims in the text.</p>`;
    
    claims.forEach((claim, index) => {
        html += `
            <div class="claim-item">
                <div class="claim-text">${claim.claim}</div>
                <div class="claim-percentage">Claim #${index + 1} (${claim.percentage.toFixed(0)}%)</div>
            </div>
        `;
    });
    
    claimsList.innerHTML = html;
    claimsContainer.classList.remove('hidden');
}

// Function to display verification results
function displayVerificationResults(claims) {
    if (!claims || claims.length === 0) {
        verificationResults.innerHTML = '<p>No verification results available.</p>';
        verificationContainer.classList.remove('hidden');
        return;
    }
    
    let html = '';
    
    claims.forEach((claim, index) => {
        const verification = claim.verification;
        const statusClass = `status-${verification.verified}`;
        
        html += `
            <div class="claim-item">
                <div class="claim-text">${claim.claim}</div>
                <div class="verification-status ${statusClass}">${verification.verified.toUpperCase()}</div>
                <div class="confidence">
                    <p>Confidence: ${(verification.confidence * 100).toFixed(0)}%</p>
                    <div class="confidence-bar">
                        <div class="confidence-level" style="width: ${verification.confidence * 100}%"></div>
                    </div>
                </div>
                <div class="explanation">
                    <h4>Explanation</h4>
                    <p>${verification.explanation}</p>
                </div>
                <div class="reason">
                    <h4>Detailed Reason</h4>
                    <p>${verification.reason}</p>
                </div>
                ${verification.related_facts && verification.related_facts.length > 0 ? `
                    <div class="related-facts">
                        <h4>Related Facts</h4>
                        <ul>
                            ${verification.related_facts.map(fact => `<li>${fact}</li>`).join('')}
                        </ul>
                    </div>
                ` : ''}
                ${verification.counter_arguments && verification.counter_arguments.length > 0 ? `
                    <div class="counter-arguments">
                        <h4>Counter Arguments</h4>
                        <ul>
                            ${verification.counter_arguments.map(arg => `<li>${arg}</li>`).join('')}
                        </ul>
                    </div>
                ` : ''}
            </div>
        `;
    });
    
    verificationResults.innerHTML = html;
    verificationContainer.classList.remove('hidden');
}

// Function to display sources
function displaySources(claims) {
    if (!claims || claims.length === 0) {
        sourcesList.innerHTML = '<p>No sources available.</p>';
        sourcesContainer.classList.remove('hidden');
        return;
    }
    
    // Collect all unique sources
    const allSources = new Set();
    
    claims.forEach(claim => {
        const verification = claim.verification;
        if (verification.sources && verification.sources.length > 0) {
            verification.sources.forEach(source => {
                if (typeof source === 'string') {
                    allSources.add(source);
                } else if (source.url) {
                    allSources.add(`<a href="${source.url}" target="_blank">${source.title || source.url}</a>`);
                }
            });
        }
    });
    
    if (allSources.size === 0) {
        sourcesList.innerHTML = '<p>No sources available.</p>';
    } else {
        let html = '<ul>';
        allSources.forEach(source => {
            html += `<li>${source}</li>`;
        });
        html += '</ul>';
        sourcesList.innerHTML = html;
    }
    
    sourcesContainer.classList.remove('hidden');
} 