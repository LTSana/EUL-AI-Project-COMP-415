/**
 * main.js - TTS Frontend Logic
 * Rebuilt for Shadcn Zinc aesthetic and full functionality
 */

// ==================== DOM ELEMENTS ====================
const elements = {
    textInput: document.getElementById('text-input'),
    charCount: document.getElementById('char-count'),
    voiceSelect: document.getElementById('voice-select'),
    synthesizeBtn: document.getElementById('synthesize-btn'),
    clearBtn: document.getElementById('clear-btn'),
    statusSection: document.getElementById('status-section'),
    statusMessage: document.getElementById('status-message'),
    loadingSpinner: document.getElementById('loading-spinner'),
    audioSection: document.getElementById('audio-section'),
    audioPlayer: document.getElementById('audio-player'),
    audioInfo: document.getElementById('audio-info'),
    downloadBtn: document.getElementById('download-btn'),
    exampleBtns: document.querySelectorAll('.btn-example')
};

// ==================== STATE ====================
let isGenerating = false;
let currentAudioUrl = null;

// ==================== INITIALIZATION ====================
document.addEventListener('DOMContentLoaded', () => {
    loadVoices();
    setupEventListeners();
});

// ==================== CORE FUNCTIONS ====================

/**
 * Fetch available voices from the backend
 */
async function loadVoices() {
    try {
        const response = await fetch('/api/voices');
        const data = await response.json();
        
        if (data.success) {
            elements.voiceSelect.innerHTML = data.voices.map(voice => 
                `<option value="${voice.id || ''}">${voice.name}</option>`
            ).join('');
        }
    } catch (error) {
        console.error('Failed to load voices:', error);
        showStatus('Could not load voices. Using system default.', 'error');
    }
}

/**
 * Handle the TTS Synthesis request
 */
async function handleSynthesize() {
    const text = elements.textInput.value.trim();
    
    if (!text) {
        showStatus('Please enter text to synthesize.', 'error');
        return;
    }

    if (isGenerating) return;

    // UI Loading State
    setLoading(true);
    hideStatus();
    elements.audioSection.style.display = 'none';

    try {
        const response = await fetch('/api/synthesize', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                text: text,
                // Ensures empty string is sent as null to avoid the .npz error
                voice_preset: elements.voiceSelect.value || null
            })
        });

        const data = await response.json();

        if (!data.success) {
            throw new Error(data.error || 'Synthesis failed');
        }

        // Handle the backend-generated audio URL
        currentAudioUrl = data.audio_url;
        displayResult(data);
        showStatus('Synthesis complete', 'success');

    } catch (error) {
        console.error('Synthesis Error:', error);
        showStatus(error.message, 'error');
    } finally {
        setLoading(false);
    }
}

/**
 * Update the UI with the result from the backend
 */
function displayResult(data) {
    elements.audioPlayer.src = data.audio_url;
    elements.audioSection.style.display = 'block';
    
    const date = new Date(data.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    
    elements.audioInfo.innerHTML = `
        <div style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 10px; font-size: 0.75rem; color: hsl(var(--muted-foreground)); margin-top: 1rem;">
            <div><strong>ID:</strong> ${data.audio_id.substring(0, 8)}</div>
            <div><strong>Duration:</strong> ~${data.estimated_duration}s</div>
            <div><strong>Time:</strong> ${date}</div>
            <div><strong>Format:</strong> WAV</div>
        </div>
    `;

    elements.audioPlayer.play().catch(() => console.log("Autoplay prevented by browser"));
}

// ==================== EVENT LISTENERS ====================

function setupEventListeners() {
    // 1. Main Synthesis Action
    elements.synthesizeBtn.addEventListener('click', handleSynthesize);

    // 2. Quick Examples Implementation
    elements.exampleBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            const exampleText = btn.getAttribute('data-text');
            if (exampleText) {
                elements.textInput.value = exampleText;
                elements.charCount.textContent = exampleText.length;
                hideStatus();
                elements.audioSection.style.display = 'none';
                elements.textInput.focus();
            }
        });
    });

    // 3. Text Area Inputs
    elements.textInput.addEventListener('input', () => {
        const length = elements.textInput.value.length;
        elements.charCount.textContent = length;
    });

    // 4. Reset Button
    elements.clearBtn.addEventListener('click', () => {
        elements.textInput.value = '';
        elements.charCount.textContent = '0';
        elements.audioSection.style.display = 'none';
        elements.audioPlayer.src = '';
        hideStatus();
    });

    // 5. Download Action
    elements.downloadBtn.addEventListener('click', () => {
        if (!currentAudioUrl) return;
        const a = document.createElement('a');
        a.href = currentAudioUrl;
        a.download = `speech-${Date.now()}.wav`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
    });
}

// ==================== UI UTILITIES ====================

/**
 * Manages the loading state across the UI
 */
function setLoading(loading) {
    isGenerating = loading;
    const btn = elements.synthesizeBtn;
    const spinnerArea = elements.loadingSpinner;

    if (loading) {
        btn.disabled = true;
        // Shadcn Zinc Style Inline Spinner
        btn.innerHTML = `
            <span style="display: inline-block; width: 12px; height: 12px; border: 2px solid currentColor; border-radius: 50%; border-top-color: transparent; animation: spin 0.6s linear infinite; margin-right: 8px;"></span>
            Generating...
        `;
        if (spinnerArea) spinnerArea.style.display = 'block';
    } else {
        btn.disabled = false;
        btn.textContent = 'Generate Speech';
        if (spinnerArea) spinnerArea.style.display = 'none';
    }
}

/**
 * Displays status notifications
 */
function showStatus(msg, type) {
    elements.statusSection.style.display = 'block';
    elements.statusMessage.textContent = msg;
    
    // Reset classes
    elements.statusMessage.className = 'status-message';
    if (type === 'error') {
        elements.statusMessage.classList.add('status-error');
    }
}

function hideStatus() {
    elements.statusSection.style.display = 'none';
}