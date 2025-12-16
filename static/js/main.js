/**
 * Main JavaScript for TTS Application
 * Handles user interactions and API calls
 */

// ==================== DOM ELEMENTS ====================

const textInput = document.getElementById('text-input');
const charCount = document.getElementById('char-count');
const voiceSelect = document.getElementById('voice-select');
const synthesizeBtn = document.getElementById('synthesize-btn');
const clearBtn = document.getElementById('clear-btn');
const statusSection = document.getElementById('status-section');
const statusMessage = document.getElementById('status-message');
const loadingSpinner = document.getElementById('loading-spinner');
const audioSection = document.getElementById('audio-section');
const audioPlayer = document.getElementById('audio-player');
const audioInfo = document.getElementById('audio-info');
const downloadBtn = document.getElementById('download-btn');
const exampleButtons = document.querySelectorAll('.btn-example');

// ==================== STATE ====================

let currentAudioUrl = null;
let isGenerating = false;

// ==================== EVENT LISTENERS ====================

// Character counter
if (textInput) {
    textInput.addEventListener('input', () => {
        const count = textInput.value.length;
        charCount.textContent = count;
        
        // Visual feedback when approaching limit
        if (count > 450) {
            charCount.style.color = 'var(--error-color)';
        } else if (count > 400) {
            charCount.style.color = 'var(--warning-color)';
        } else {
            charCount.style.color = '#666';
        }
    });
}

// Synthesize button
if (synthesizeBtn) {
    synthesizeBtn.addEventListener('click', handleSynthesize);
}

// Clear button
if (clearBtn) {
    clearBtn.addEventListener('click', () => {
        textInput.value = '';
        charCount.textContent = '0';
        charCount.style.color = '#666';
        hideStatus();
        hideAudio();
    });
}

// Download button
if (downloadBtn) {
    downloadBtn.addEventListener('click', handleDownload);
}

// Example buttons
exampleButtons.forEach(btn => {
    btn.addEventListener('click', () => {
        const exampleText = btn.getAttribute('data-text');
        textInput.value = exampleText;
        charCount.textContent = exampleText.length;
        
        // Update char counter color
        const count = exampleText.length;
        if (count > 450) {
            charCount.style.color = 'var(--error-color)';
        } else if (count > 400) {
            charCount.style.color = 'var(--warning-color)';
        } else {
            charCount.style.color = '#666';
        }
        
        textInput.focus();
        textInput.scrollIntoView({ behavior: 'smooth', block: 'center' });
    });
});

// Enter key to synthesize (with Ctrl/Cmd)
if (textInput) {
    textInput.addEventListener('keydown', (e) => {
        if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
            e.preventDefault();
            if (!isGenerating) {
                handleSynthesize();
            }
        }
    });
}

// ==================== CORE FUNCTIONS ====================

/**
 * Handle text synthesis
 */
async function handleSynthesize() {
    if (isGenerating) {
        return; // Prevent multiple simultaneous requests
    }
    
    const text = textInput.value.trim();
    
    // Validation
    if (!text) {
        showStatus('Please enter some text to synthesize.', 'error');
        textInput.focus();
        return;
    }
    
    if (text.length < 3) {
        showStatus('Text is too short (minimum 3 characters).', 'error');
        textInput.focus();
        return;
    }
    
    if (text.length > 500) {
        showStatus('Text is too long (maximum 500 characters).', 'error');
        textInput.focus();
        return;
    }
    
    // Start generation
    isGenerating = true;
    synthesizeBtn.disabled = true;
    synthesizeBtn.textContent = '⏳ Generating...';
    showLoading();
    hideAudio();
    
    try {
        // Get selected voice
        const voicePreset = voiceSelect.value || null;
        
        // Make API request
        const response = await fetch('/api/synthesize', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                text: text,
                voice_preset: voicePreset
            })
        });
        
        const data = await response.json();
        
        if (!response.ok || !data.success) {
            throw new Error(data.error || 'Synthesis failed');
        }
        
        // Success - show audio player
        currentAudioUrl = data.audio_url;
        displayAudio(data);
        showStatus('✓ Speech generated successfully!', 'success');
        
    } catch (error) {
        console.error('Synthesis error:', error);
        showStatus(`Error: ${error.message}`, 'error');
        hideAudio();
        
    } finally {
        // Re-enable button
        isGenerating = false;
        synthesizeBtn.disabled = false;
        synthesizeBtn.textContent = '🎤 Generate Speech';
        hideLoading();
    }
}

/**
 * Display audio player with generated speech
 */
function displayAudio(data) {
    // Set audio source
    audioPlayer.src = data.audio_url;
    
    // Show audio section
    audioSection.style.display = 'block';
    
    // Display info
    const truncatedText = data.text.length > 100 
        ? data.text.substring(0, 100) + '...' 
        : data.text;
    
    const timestamp = new Date(data.timestamp);
    const timeString = timestamp.toLocaleTimeString();
    
    const infoHtml = `
        <p><strong>Text:</strong> "${truncatedText}"</p>
        <p><strong>Estimated Duration:</strong> ~${data.estimated_duration} seconds</p>
        <p><strong>Generated:</strong> ${timeString}</p>
    `;
    audioInfo.innerHTML = infoHtml;
    
    // Auto-play (user must have interacted with page first)
    audioPlayer.play().catch(err => {
        console.log('Auto-play prevented:', err.message);
        // Browsers block auto-play without user interaction
    });
    
    // Scroll to audio section
    audioSection.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
}

/**
 * Handle audio download
 */
function handleDownload() {
    if (!currentAudioUrl) {
        showStatus('No audio to download.', 'error');
        return;
    }
    
    try {
        // Create download link
        const link = document.createElement('a');
        link.href = currentAudioUrl;
        link.download = `speech_${Date.now()}.wav`;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        
        showStatus('Download started!', 'success');
        
    } catch (error) {
        console.error('Download error:', error);
        showStatus('Download failed. Please try again.', 'error');
    }
}

/**
 * Show status message
 */
function showStatus(message, type = 'success') {
    statusSection.style.display = 'block';
    statusMessage.textContent = message;
    statusMessage.className = 'status-message';
    
    if (type === 'success') {
        statusMessage.classList.add('status-success');
    } else if (type === 'error') {
        statusMessage.classList.add('status-error');
    } else if (type === 'warning') {
        statusMessage.classList.add('status-warning');
    }
    
    // Auto-hide success messages after 5 seconds
    if (type === 'success') {
        setTimeout(() => {
            hideStatus();
        }, 5000);
    }
    
    // Scroll to status message
    statusSection.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
}

/**
 * Hide status message
 */
function hideStatus() {
    statusSection.style.display = 'none';
    statusMessage.textContent = '';
    statusMessage.className = 'status-message';
}

/**
 * Show loading spinner
 */
function showLoading() {
    loadingSpinner.style.display = 'block';
}

/**
 * Hide loading spinner
 */
function hideLoading() {
    loadingSpinner.style.display = 'none';
}

/**
 * Hide audio section
 */
function hideAudio() {
    audioSection.style.display = 'none';
    if (audioPlayer) {
        audioPlayer.pause();
        audioPlayer.src = '';
    }
    currentAudioUrl = null;
}

// ==================== UTILITY FUNCTIONS ====================

/**
 * Test API connection on page load
 */
async function testConnection() {
    try {
        const response = await fetch('/health');
        const data = await response.json();
        
        if (data.status === 'healthy') {
            console.log('✓ Connected to TTS server');
            console.log(`Model: ${data.model}`);
            console.log(`Device: ${data.device}`);
        }
    } catch (error) {
        console.error('Connection test failed:', error);
        showStatus('Warning: Could not connect to server. Please refresh the page.', 'warning');
    }
}

/**
 * Format file size in human-readable format
 */
function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

/**
 * Debounce function for performance
 */
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// ==================== INITIALIZATION ====================

// Test connection when page loads
document.addEventListener('DOMContentLoaded', () => {
    testConnection();
    console.log('TTS Application initialized');
    
    // Set focus on text input for better UX
    if (textInput) {
        textInput.focus();
    }
});

// Handle page visibility (pause audio when tab is hidden)
document.addEventListener('visibilitychange', () => {
    if (document.hidden && audioPlayer && !audioPlayer.paused) {
        audioPlayer.pause();
    }
});

// Handle audio player events
if (audioPlayer) {
    audioPlayer.addEventListener('ended', () => {
        console.log('Audio playback completed');
    });
    
    audioPlayer.addEventListener('error', (e) => {
        console.error('Audio playback error:', e);
        const error = audioPlayer.error;
        let errorMsg = 'Error playing audio. ';
        if (error) {
            switch(error.code) {
                case error.MEDIA_ERR_ABORTED:
                    errorMsg += 'Playback aborted.';
                    break;
                case error.MEDIA_ERR_NETWORK:
                    errorMsg += 'Network error.';
                    break;
                case error.MEDIA_ERR_DECODE:
                    errorMsg += 'Decode error - audio file may be corrupted.';
                    break;
                case error.MEDIA_ERR_SRC_NOT_SUPPORTED:
                    errorMsg += 'Audio format not supported.';
                    break;
                default:
                    errorMsg += `Error code: ${error.code}`;
            }
        }
        showStatus(errorMsg, 'error');
    });
    
    audioPlayer.addEventListener('loadedmetadata', () => {
        console.log(`Audio loaded: ${audioPlayer.duration.toFixed(2)}s`);
    });
}

// Prevent form submission if wrapped in form
if (textInput && textInput.form) {
    textInput.form.addEventListener('submit', (e) => {
        e.preventDefault();
        if (!isGenerating) {
            handleSynthesize();
        }
    });
}

// Handle browser back/forward buttons
window.addEventListener('popstate', () => {
    // Clean up audio when navigating
    hideAudio();
});

// Export functions for testing (if needed)
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        handleSynthesize,
        showStatus,
        hideStatus,
        formatFileSize
    };
}