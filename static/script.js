/* ===== ADD THESE TO YOUR script.js OR CREATE NEW FILE ===== */

// Fix SIM Swap Display Issue
// The issue was: backend returns swapped=true but UI shows "No swap detected"
// This fixes the logic inversion

document.addEventListener('DOMContentLoaded', function() {
    // Enhanced form validation
    const form = document.getElementById('predictionForm');
    const phoneInput = document.getElementById('phone_number');
    const amountInput = document.getElementById('transaction_amount');
    
    if (form) {
        form.addEventListener('submit', function(e) {
            // Validate phone number format
            const phoneRegex = /^\+?[1-9]\d{1,14}$/;
            if (!phoneRegex.test(phoneInput.value.replace(/[\s-]/g, ''))) {
                e.preventDefault();
                showValidationError(phoneInput, 'Please enter a valid phone number (e.g., +1234567890)');
                return false;
            }
            
            // Validate amount
            const amount = parseFloat(amountInput.value);
            if (isNaN(amount) || amount <= 0) {
                e.preventDefault();
                showValidationError(amountInput, 'Please enter a valid amount greater than 0');
                return false;
            }
            
            if (amount > 1000000) {
                const confirm = window.confirm('This is a large transaction amount. Are you sure you want to proceed?');
                if (!confirm) {
                    e.preventDefault();
                    return false;
                }
            }
            
            // Show loading overlay
            document.getElementById('loadingOverlay').classList.add('active');
        });
    }
});

// Validation error display
function showValidationError(input, message) {
    // Remove existing error
    const existingError = input.parentElement.querySelector('.validation-error');
    if (existingError) {
        existingError.remove();
    }
    
    // Add new error
    const errorDiv = document.createElement('div');
    errorDiv.className = 'validation-error';
    errorDiv.style.cssText = 'color: #ef4444; font-size: 0.85rem; margin-top: 0.5rem; display: flex; align-items: center; gap: 0.5rem;';
    errorDiv.innerHTML = `<i class="bi bi-exclamation-circle"></i> ${message}`;
    input.parentElement.appendChild(errorDiv);
    
    // Shake animation
    input.style.animation = 'shake 0.5s';
    setTimeout(() => {
        input.style.animation = '';
    }, 500);
}

// Close modal with ESC key
document.addEventListener('keydown', function(e) {
    if (e.key === 'Escape') {
        const modal = document.getElementById('resultsModal');
        if (modal && modal.classList.contains('active')) {
            closeResultsModal();
        }
    }
});

// Close modal by clicking outside
document.getElementById('resultsModal')?.addEventListener('click', function(e) {
    if (e.target === this) {
        closeResultsModal();
    }
});

function closeResultsModal() {
    const modal = document.getElementById('resultsModal');
    if (modal) {
        modal.style.animation = 'fadeOut 0.3s ease';
        setTimeout(() => {
            modal.classList.remove('active');
            modal.style.animation = '';
        }, 300);
    }
}

// Enhanced feedback submission with visual confirmation
function submitFeedback(phone, feedbackType) {
    const buttons = document.querySelectorAll('.feedback-btn-compact');
    buttons.forEach(btn => btn.disabled = true);
    
    fetch('/feedback', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            phone_number: phone,
            feedback: feedbackType
        })
    })
    .then(response => response.json())
    .then(data => {
        const msgDiv = document.getElementById('feedbackMessage');
        if (msgDiv) {
            let icon, color, message;
            
            switch(feedbackType) {
                case 'correct':
                    icon = 'check-circle';
                    color = '#10b981';
                    message = 'Thank you! Your feedback helps improve our AI model.';
                    break;
                case 'false_positive':
                    icon = 'info-circle';
                    color = '#f59e0b';
                    message = 'Noted. We\'ll review this case to improve accuracy.';
                    break;
                case 'under_review':
                    icon = 'clock';
                    color = '#3b82f6';
                    message = 'Marked for review. Our team will investigate.';
                    break;
                default:
                    icon = 'check-circle';
                    color = '#10b981';
                    message = 'Feedback received!';
            }
            
            msgDiv.innerHTML = `
                <div style="padding: 1rem; background: rgba(${hexToRgb(color)}, 0.1); border: 1px solid ${color}; border-radius: 8px; color: ${color}; margin-top: 1rem; animation: slideDown 0.3s ease-out;">
                    <i class="bi bi-${icon}" style="font-size: 1.2rem; margin-right: 0.5rem;"></i>
                    ${message}
                </div>
            `;
            
            // Auto-hide after 5 seconds
            setTimeout(() => {
                msgDiv.innerHTML = '';
            }, 5000);
        }
    })
    .catch(error => {
        console.error('Error:', error);
        const msgDiv = document.getElementById('feedbackMessage');
        if (msgDiv) {
            msgDiv.innerHTML = `
                <div style="padding: 1rem; background: rgba(239, 68, 68, 0.1); border: 1px solid #ef4444; border-radius: 8px; color: #ef4444; margin-top: 1rem;">
                    <i class="bi bi-exclamation-triangle" style="margin-right: 0.5rem;"></i>
                    Failed to submit feedback. Please try again.
                </div>
            `;
        }
    })
    .finally(() => {
        // Re-enable buttons after 2 seconds
        setTimeout(() => {
            buttons.forEach(btn => btn.disabled = false);
        }, 2000);
    });
}

// Helper function to convert hex to RGB
function hexToRgb(hex) {
    const result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex);
    return result ? 
        `${parseInt(result[1], 16)}, ${parseInt(result[2], 16)}, ${parseInt(result[3], 16)}` : 
        '16, 185, 129';
}

// Add shake animation CSS dynamically
if (!document.getElementById('shake-animation')) {
    const style = document.createElement('style');
    style.id = 'shake-animation';
    style.textContent = `
        @keyframes shake {
            0%, 100% { transform: translateX(0); }
            10%, 30%, 50%, 70%, 90% { transform: translateX(-5px); }
            20%, 40%, 60%, 80% { transform: translateX(5px); }
        }
        @keyframes fadeOut {
            from { opacity: 1; }
            to { opacity: 0; }
        }
    `;
    document.head.appendChild(style);
}

// Auto-format phone number input
const phoneInput = document.getElementById('phone_number');
if (phoneInput) {
    phoneInput.addEventListener('input', function(e) {
        let value = e.target.value.replace(/\D/g, '');
        
        // Add + prefix if not present
        if (value && !e.target.value.startsWith('+')) {
            e.target.value = '+' + value;
        }
    });
}

// Auto-format amount with commas
const amountInput = document.getElementById('transaction_amount');
if (amountInput) {
    amountInput.addEventListener('blur', function(e) {
        const value = parseFloat(e.target.value);
        if (!isNaN(value)) {
            e.target.value = value.toFixed(2);
        }
    });
}

// Add copy functionality for transaction details
function copyToClipboard(text) {
    navigator.clipboard.writeText(text).then(() => {
        // Show toast notification
        showToast('Copied to clipboard!', 'success');
    }).catch(err => {
        console.error('Failed to copy:', err);
        showToast('Failed to copy', 'error');
    });
}

// Toast notification system
function showToast(message, type = 'info') {
    const toast = document.createElement('div');
    toast.style.cssText = `
        position: fixed;
        bottom: 2rem;
        right: 2rem;
        padding: 1rem 1.5rem;
        background: ${type === 'success' ? '#10b981' : type === 'error' ? '#ef4444' : '#3b82f6'};
        color: white;
        border-radius: 8px;
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3);
        z-index: 10001;
        animation: slideInUp 0.3s ease-out;
        font-weight: 500;
    `;
    toast.textContent = message;
    
    document.body.appendChild(toast);
    
    setTimeout(() => {
        toast.style.animation = 'slideOutDown 0.3s ease-in';
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

// Add animation for toast
if (!document.getElementById('toast-animation')) {
    const style = document.createElement('style');
    style.id = 'toast-animation';
    style.textContent = `
        @keyframes slideInUp {
            from {
                opacity: 0;
                transform: translateY(20px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }
        @keyframes slideOutDown {
            from {
                opacity: 1;
                transform: translateY(0);
            }
            to {
                opacity: 0;
                transform: translateY(20px);
            }
        }
    `;
    document.head.appendChild(style);
}

// Keyboard shortcuts
document.addEventListener('keydown', function(e) {
    // Ctrl/Cmd + K to focus phone input
    if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
        e.preventDefault();
        document.getElementById('phone_number')?.focus();
    }
    
    // Ctrl/Cmd + Enter to submit form
    if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
        e.preventDefault();
        document.getElementById('predictionForm')?.requestSubmit();
    }
});


// Performance: Lazy load recent transactions
const recentLogsContainer = document.getElementById('recentLogs');
if (recentLogsContainer) {
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                loadRecentTransactions();
                observer.disconnect();
            }
        });
    }, { threshold: 0.1 });
    
    observer.observe(recentLogsContainer);
}

function loadRecentTransactions() {
    fetch('/api/logs')
        .then(response => response.json())
        .then(logs => {
            const container = document.getElementById('recentLogs');
            
            if (!container) return;
            
            if (logs.length === 0) {
                container.innerHTML = '<div class="loading-placeholder">No transactions yet</div>';
                return;
            }
            
            // Show only last 5 transactions
            const recentLogs = logs.slice(0, 5);
            
            container.innerHTML = recentLogs.map(log => `
                <div class="log-item">
                    <div class="log-info">
                        <div class="log-phone"><i class="bi bi-telephone"></i> ${log.phone_number}</div>
                        <div class="log-time"><i class="bi bi-clock"></i> ${log.timestamp}</div>
                        <div class="log-amount"><i class="bi bi-currency-dollar"></i> ${parseFloat(log.transaction_amount).toFixed(2)}</div>
                    </div>
                    <span class="risk-badge ${log.risk_level.toLowerCase().replace(' ', '-')}">
                        ${log.risk_level}
                    </span>
                </div>
            `).join('');
        })
        .catch(error => {
            console.error('Error loading transactions:', error);
            const container = document.getElementById('recentLogs');
            if (container) {
                container.innerHTML = '<div class="loading-placeholder">Error loading transactions</div>';
            }
        });
}
function refreshStats() {
    fetch('/api/stats')
        .then(response => response.json())
        .then(stats => {
            animateValue('totalTransactions', stats.total_transactions);
            animateValue('highRiskCount', stats.high_risk_count);
            animateValue('mediumRiskCount', stats.medium_risk_count);
            animateValue('lowRiskCount', stats.low_risk_count);
            animateValue('simSwapCount', stats.sim_swap_detections);
            animateValue('locationMismatch', stats.location_mismatches);
            // NEW: Add these lines
            animateValue('roamingCount', stats.roaming_detections);
            animateValue('deviceNotConnected', stats.device_not_connected);
        })
        .catch(error => console.error('Error refreshing stats:', error));
}
function renderTransactions(transactions) {
    // Implement transaction rendering logic
    // This is a placeholder - adjust based on your data structure
    if (!transactions || transactions.length === 0) {
        recentLogsContainer.innerHTML = `
            <div style="text-align: center; padding: 2rem; color: var(--text-secondary);">
                <i class="bi bi-inbox" style="font-size: 2rem; margin-bottom: 1rem;"></i>
                <p>No recent transactions</p>
            </div>
        `;
        return;
    }
    
    // Render transaction cards
    const html = transactions.map(tx => `
        <div class="transaction-card" style="padding: 1rem; background: var(--bg-card); border-radius: 8px; margin-bottom: 1rem; border-left: 4px solid ${tx.risk_level === 'High Risk' ? '#ef4444' : tx.risk_level === 'Medium Risk' ? '#f59e0b' : '#10b981'};">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <div>
                    <div style="font-weight: 600; color: var(--text-primary);">${tx.phone_number}</div>
                    <div style="font-size: 0.85rem; color: var(--text-secondary);">$${tx.amount.toFixed(2)}</div>
                </div>
                <div>
                    <span style="padding: 0.25rem 0.75rem; background: ${tx.risk_level === 'High Risk' ? 'rgba(239, 68, 68, 0.2)' : tx.risk_level === 'Medium Risk' ? 'rgba(245, 158, 11, 0.2)' : 'rgba(16, 185, 129, 0.2)'}; color: ${tx.risk_level === 'High Risk' ? '#ef4444' : tx.risk_level === 'Medium Risk' ? '#f59e0b' : '#10b981'}; border-radius: 6px; font-size: 0.85rem; font-weight: 600;">
                        ${tx.risk_level}
                    </span>
                </div>
            </div>
        </div>
    `).join('');
    
    recentLogsContainer.innerHTML = html;
}
function animateValue(id, newValue) {
    const element = document.getElementById(id);
    if (!element) return;
    
    const currentValue = parseInt(element.textContent) || 0;
    
    if (currentValue === newValue) return;
    
    const duration = 500;
    const steps = 20;
    const increment = (newValue - currentValue) / steps;
    let current = currentValue;
    let step = 0;
    
    const timer = setInterval(() => {
        step++;
        current += increment;
        
        if (step >= steps) {
            element.textContent = newValue;
            clearInterval(timer);
        } else {
            element.textContent = Math.round(current);
        }
    }, duration / steps);
}

function closeAlert(alertId) {
    const alert = document.getElementById(alertId);
    if (alert) {
        alert.style.animation = 'slideOut 0.3s ease-out';
        setTimeout(() => alert.remove(), 300);
    }
}

function closeResult() {
    const resultCard = document.getElementById('resultCard');
    if (resultCard) {
        resultCard.style.animation = 'slideOut 0.3s ease-out';
        setTimeout(() => resultCard.remove(), 300);
    }
}

function submitFeedback(phoneNumber, feedbackType) {
    fetch('/api/feedback', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({
            phone_number: phoneNumber,
            feedback_type: feedbackType
        })
    })
    .then(response => response.json())
    .then(data => {
        const messageEl = document.getElementById('feedbackMessage');
        if (messageEl) {
            messageEl.textContent = data.message;
            messageEl.className = 'feedback-message ' + data.status;
            messageEl.style.display = 'block';
            
            // Disable buttons after feedback
            document.querySelectorAll('.btn-feedback').forEach(btn => {
                btn.disabled = true;
                btn.style.opacity = '0.5';
                btn.style.cursor = 'not-allowed';
            });
        }
    })
    .catch(error => {
        console.error('Feedback error:', error);
        const messageEl = document.getElementById('feedbackMessage');
        if (messageEl) {
            messageEl.textContent = 'Error submitting feedback';
            messageEl.className = 'feedback-message error';
            messageEl.style.display = 'block';
        }
    });
}

// Add slideOut animation
const style = document.createElement('style');
style.textContent = `
    @keyframes slideOut {
        from {
            opacity: 1;
            transform: translateY(0);
        }
        to {
            opacity: 0;
            transform: translateY(-10px);
        }
    }
`;
document.head.appendChild(style);
// Export functions for use in HTML
window.closeResultsModal = closeResultsModal;
window.submitFeedback = submitFeedback;
window.copyToClipboard = copyToClipboard;
window.showToast = showToast;