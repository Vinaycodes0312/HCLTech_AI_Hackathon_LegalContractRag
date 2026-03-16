// Bussiness Contract Search System - Frontend JavaScript

const API_BASE = '/api';

// DOM Elements
const fileInput = document.getElementById('fileInput');
const uploadBtn = document.getElementById('uploadBtn');
const uploadStatus = document.getElementById('uploadStatus');
const contractsList = document.getElementById('contractsList');
const questionInput = document.getElementById('questionInput');
const askBtn = document.getElementById('askBtn');
const topKInput = document.getElementById('topK');
const answerSection = document.getElementById('answerSection');
const answerContent = document.getElementById('answerContent');
const sourcesContent = document.getElementById('sourcesContent');
const sourcesList = document.getElementById('sourcesList');
const loadingIndicator = document.getElementById('loadingIndicator');
const refreshBtn = document.getElementById('refreshBtn');
const clearBtn = document.getElementById('clearBtn');
const contractCount = document.getElementById('contractCount');
const docCount = document.getElementById('docCount');
const sampleButtons = document.querySelectorAll('.sample-btn');

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    loadStats();
    loadContracts();
    setupEventListeners();
    checkAPIHealth();
});

async function checkAPIHealth() {
    try {
        const response = await fetch(`${API_BASE}/health`);
        const data = await response.json();
        
        if (!data.status === 'healthy') {
            showWarning('System is not fully operational. Please check server logs.');
        }
    } catch (error) {
        showWarning('Cannot connect to server. Please ensure the server is running.');
    }
}

function showWarning(message) {
    const warningDiv = document.createElement('div');
    warningDiv.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        background: #fef3c7;
        border-left: 4px solid #f59e0b;
        padding: 15px 20px;
        border-radius: 8px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        z-index: 1000;
        max-width: 400px;
    `;
    warningDiv.innerHTML = `<strong>⚠️ Warning:</strong> ${message}`;
    document.body.appendChild(warningDiv);
    
    setTimeout(() => warningDiv.remove(), 8000);
}

function setupEventListeners() {
    // File selection display
    fileInput.addEventListener('change', displaySelectedFiles);
    
    // Upload
    uploadBtn.addEventListener('click', uploadFiles);
    
    // Ask question
    askBtn.addEventListener('click', askQuestion);
    questionInput.addEventListener('keydown', (e) => {
        if (e.ctrlKey && e.key === 'Enter') {
            askQuestion();
        }
    });
    
    // Sample questions
    sampleButtons.forEach(btn => {
        btn.addEventListener('click', () => {
            questionInput.value = btn.dataset.question;
            askQuestion();
        });
    });
    
    // Actions
    refreshBtn.addEventListener('click', () => {
        loadStats();
        loadContracts();
    });
    
    clearBtn.addEventListener('click', clearIndex);
}

// Display selected files
function displaySelectedFiles() {
    const files = Array.from(fileInput.files);
    const selectedFilesDiv = document.getElementById('selectedFiles');
    const fileLabel = document.getElementById('fileLabel');
    
    if (files.length === 0) {
        selectedFilesDiv.innerHTML = '';
        fileLabel.textContent = 'Choose PDF Files (Multiple)';
        return;
    }
    
    fileLabel.textContent = `${files.length} file(s) selected`;
    
    const filesList = files.map((file, index) => {
        const size = (file.size / 1024).toFixed(1);
        return `
            <div class="selected-file-item">
                <span class="file-icon">📄</span>
                <span class="file-name">${file.name}</span>
                <span class="file-size">${size} KB</span>
            </div>
        `;
    }).join('');
    
    selectedFilesDiv.innerHTML = `<div class="selected-files-list">${filesList}</div>`;
}

// Upload multiple files sequentially
async function uploadFiles() {
    const files = Array.from(fileInput.files);
    
    if (files.length === 0) {
        showStatus('Please select PDF file(s)', 'error');
        return;
    }
    
    // Validate all files are PDFs
    const invalidFiles = files.filter(f => !f.name.endsWith('.pdf'));
    if (invalidFiles.length > 0) {
        showStatus(`Only PDF files are supported. Invalid: ${invalidFiles.map(f => f.name).join(', ')}`, 'error');
        return;
    }
    
    const progressDiv = document.getElementById('uploadProgress');
    uploadBtn.disabled = true;
    uploadBtn.textContent = `Processing 0/${files.length}...`;
    
    let successCount = 0;
    let failedCount = 0;
    const results = [];
    
    try {
        for (let i = 0; i < files.length; i++) {
            const file = files[i];
            
            // Update progress
            uploadBtn.textContent = `Processing ${i + 1}/${files.length}...`;
            showStatus(`Processing: ${file.name} (${i + 1}/${files.length})`, 'info');
            
            // Show current file progress
            progressDiv.innerHTML = `
                <div class="progress-item">
                    <div class="progress-file">📄 ${file.name}</div>
                    <div class="progress-bar-container">
                        <div class="progress-bar-fill" style="width: ${((i + 1) / files.length * 100)}%"></div>
                    </div>
                    <div class="progress-text">${i + 1} / ${files.length}</div>
                </div>
            `;
            
            try {
                const formData = new FormData();
                formData.append('file', file);
                
                const response = await fetch(`${API_BASE}/upload`, {
                    method: 'POST',
                    body: formData
                });
                
                const data = await response.json();
                
                if (response.ok) {
                    successCount++;
                    results.push({
                        file: file.name,
                        status: 'success',
                        message: data.message,
                        stats: data.stats
                    });
                    
                    // Update progress with success
                    progressDiv.innerHTML += `<div class="progress-result success">✓ ${file.name} - Processed successfully</div>`;
                } else {
                    failedCount++;
                    results.push({
                        file: file.name,
                        status: 'error',
                        message: data.detail
                    });
                    
                    // Update progress with error
                    progressDiv.innerHTML += `<div class="progress-result error">✗ ${file.name} - ${data.detail}</div>`;
                }
                
            } catch (error) {
                failedCount++;
                results.push({
                    file: file.name,
                    status: 'error',
                    message: error.message
                });
                
                progressDiv.innerHTML += `<div class="progress-result error">✗ ${file.name} - ${error.message}</div>`;
            }
        }
        
        // Final status
        const totalProcessed = successCount + failedCount;
        if (successCount === files.length) {
            showStatus(`✓ All ${files.length} file(s) uploaded and processed successfully!`, 'success');
        } else if (successCount > 0) {
            showStatus(`⚠ Processed ${successCount} of ${files.length} files (${failedCount} failed)`, 'warning');
        } else {
            showStatus(`✗ All ${files.length} file(s) failed to process`, 'error');
        }
        
        // Clear file input and refresh
        fileInput.value = '';
        displaySelectedFiles();
        loadContracts();
        loadStats();
        
        // Clear progress after 10 seconds
        setTimeout(() => {
            progressDiv.innerHTML = '';
        }, 10000);
        
    } catch (error) {
        showStatus(`✗ Upload failed: ${error.message}`, 'error');
    } finally {
        uploadBtn.disabled = false;
        uploadBtn.textContent = 'Upload & Process All';
    }
}

// Legacy single file upload (kept for compatibility)
async function uploadFile() {
    const file = fileInput.files[0];
    
    if (!file) {
        showStatus('Please select a PDF file', 'error');
        return;
    }
    
    if (!file.name.endsWith('.pdf')) {
        showStatus('Only PDF files are supported', 'error');
        return;
    }
    
    const formData = new FormData();
    formData.append('file', file);
    
    try {
        uploadBtn.disabled = true;
        uploadBtn.textContent = 'Uploading...';
        showStatus('Uploading and processing...', 'info');
        
        const response = await fetch(`${API_BASE}/upload`, {
            method: 'POST',
            body: formData
        });
        
        const data = await response.json();
        
        if (response.ok) {
            showStatus(`✓ ${data.message}`, 'success');
            fileInput.value = '';
            loadContracts();
            loadStats();
        } else {
            showStatus(`✗ ${data.detail}`, 'error');
        }
        
    } catch (error) {
        showStatus(`✗ Upload failed: ${error.message}`, 'error');
    } finally {
        uploadBtn.disabled = false;
        uploadBtn.textContent = 'Upload & Process';
    }
}

async function askQuestion() {
    const question = questionInput.value.trim();
    
    if (!question) {
        return;
    }
    
    const topK = parseInt(topKInput.value) || 5;
    
    try {
        // Show loading with progress messages
        loadingIndicator.classList.remove('hidden');
        answerSection.classList.add('hidden');
        askBtn.disabled = true;
        askBtn.querySelector('.btn-text').textContent = 'Processing...';
        
        const loadingMessage = document.getElementById('loadingMessage');
        const loadingSubtext = document.getElementById('loadingSubtext');
        
        // Update loading message over time
        loadingMessage.textContent = 'Searching contracts...';
        loadingSubtext.textContent = 'Finding relevant information...';
        
        const messageTimer = setTimeout(() => {
            loadingMessage.textContent = 'Generating answer...';
            loadingSubtext.textContent = 'AI is analyzing the contracts...';
        }, 2000);
        
        const slowTimer = setTimeout(() => {
            loadingSubtext.textContent = '⏳ Taking longer than usual - this is normal for complex questions';
        }, 10000);
        
        const endpoint = `${API_BASE}/query`;
        const payload = { question, top_k: topK };
        
        const response = await fetch(endpoint, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(payload)
        });
        
        clearTimeout(messageTimer);
        clearTimeout(slowTimer);
        
        const data = await response.json();
        
        if (response.ok && data.success !== false) {
            displayAnswer(data);
        } else {
            const errorMsg = data.detail || data.error || 'An error occurred while processing your request';
            displayError(errorMsg);
        }
        
    } catch (error) {
        displayError(`Failed to process question: ${error.message}`);
    } finally {
        loadingIndicator.classList.add('hidden');
        askBtn.disabled = false;
        askBtn.querySelector('.btn-text').textContent = 'Ask Question';
    }
}

function displayAnswer(data) {
    // Format and display answer
    answerContent.innerHTML = formatAnswer(data.answer);
    
    // Display sources if available
    if (data.sources && data.sources.length > 0) {
        displaySources(data.sources);
        sourcesContent.classList.remove('hidden');
    } else {
        sourcesContent.classList.add('hidden');
    }
    
    answerSection.classList.remove('hidden');
    answerSection.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
}

function formatAnswer(answer) {
    // Convert markdown-like formatting to HTML
    answer = answer.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
    answer = answer.replace(/\n/g, '<br>');
    return answer;
}

function displaySources(sources) {
    sourcesList.innerHTML = '';
    
    sources.forEach(source => {
        const sourceItem = document.createElement('div');
        sourceItem.className = 'source-item';
        sourceItem.innerHTML = `
            <div class="source-contract">${source.contract}</div>
            <div class="source-page">Page ${source.page}</div>
        `;
        sourcesList.appendChild(sourceItem);
    });
}

function displayError(message) {
    answerContent.innerHTML = `
        <div style="color: var(--danger-color); padding: 20px; background: #fee2e2; border-radius: 8px; border-left: 4px solid var(--danger-color);">
            <strong style="font-size: 1.2em;">⚠️ Error:</strong><br><br>
            ${message}
        </div>
    `;
    sourcesContent.classList.add('hidden');
    answerSection.classList.remove('hidden');
}

async function loadContracts() {
    try {
        const response = await fetch(`${API_BASE}/contracts`);
        const data = await response.json();
        
        if (data.contracts && data.contracts.length > 0) {
            contractsList.innerHTML = '';
            data.contracts.forEach(contract => {
                const item = document.createElement('div');
                item.className = 'contract-item';
                
                const sizeKB = (contract.size / 1024).toFixed(1);
                
                item.innerHTML = `
                    <div>
                        <div class="contract-name">${contract.name}</div>
                        <div class="contract-size">${sizeKB} KB</div>
                    </div>
                `;
                contractsList.appendChild(item);
            });
        } else {
            contractsList.innerHTML = '<p class="empty-message">No contracts uploaded yet</p>';
        }
        
    } catch (error) {
        console.error('Failed to load contracts:', error);
    }
}

async function loadStats() {
    try {
        const response = await fetch(`${API_BASE}/stats`);
        const data = await response.json();
        
        contractCount.textContent = data.contracts_uploaded || 0;
        docCount.textContent = data.vector_store?.total_documents || 0;
        
    } catch (error) {
        console.error('Failed to load stats:', error);
    }
}

async function clearIndex() {
    if (!confirm('Are you sure you want to clear the entire index? This cannot be undone.')) {
        return;
    }
    
    try {
        const response = await fetch(`${API_BASE}/clear`, {
            method: 'DELETE'
        });
        
        const data = await response.json();
        
        if (response.ok) {
            alert('✓ Index cleared successfully');
            loadStats();
            answerSection.classList.add('hidden');
        } else {
            alert(`✗ Failed to clear index: ${data.detail}`);
        }
        
    } catch (error) {
        alert(`✗ Error: ${error.message}`);
    }
}

function showStatus(message, type) {
    uploadStatus.textContent = message;
    uploadStatus.className = 'status-message';
    
    if (type === 'success') {
        uploadStatus.classList.add('status-success');
    } else if (type === 'error') {
        uploadStatus.classList.add('status-error');
    } else if (type === 'warning') {
        uploadStatus.classList.add('status-warning');
    } else {
        uploadStatus.classList.add('status-info');
    }
    
    // Clear after 5 seconds
    setTimeout(() => {
        uploadStatus.textContent = '';
        uploadStatus.className = 'status-message';
    }, 5000);
}
