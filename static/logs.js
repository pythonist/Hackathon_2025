// static/logs.js - Complete updated version
document.addEventListener('DOMContentLoaded', function() {
    const searchInput = document.getElementById('searchInput');
    const riskFilter = document.getElementById('riskFilter');
    const tableBody = document.getElementById('logsTableBody');
    
    if (!tableBody) return;
    
    const allRows = Array.from(tableBody.getElementsByTagName('tr'));
    
    if (searchInput) {
        searchInput.addEventListener('input', filterTable);
    }
    
    if (riskFilter) {
        riskFilter.addEventListener('change', filterTable);
    }
    
    function filterTable() {
        const searchTerm = searchInput ? searchInput.value.toLowerCase() : '';
        const selectedRisk = riskFilter ? riskFilter.value : 'all';
        
        allRows.forEach(row => {
            const phoneNumber = row.cells[1].textContent.toLowerCase();
            const riskLevel = row.getAttribute('data-risk');
            
            const matchesSearch = phoneNumber.includes(searchTerm);
            const matchesRisk = selectedRisk === 'all' || riskLevel === selectedRisk;
            
            if (matchesSearch && matchesRisk) {
                row.style.display = '';
                row.style.animation = 'fadeIn 0.3s ease-out';
            } else {
                row.style.display = 'none';
            }
        });
    }
    
    // Animate probability bars
    setTimeout(() => {
        document.querySelectorAll('.probability-fill').forEach(fill => {
            const width = fill.style.width;
            fill.style.width = '0';
            setTimeout(() => {
                fill.style.width = width;
            }, 100);
        });
    }, 200);
});

const style = document.createElement('style');
style.textContent = `
    @keyframes fadeIn {
        from {
            opacity: 0;
            transform: translateX(-10px);
        }
        to {
            opacity: 1;
            transform: translateX(0);
        }
    }
    
    .network-checks {
        display: flex;
        gap: 0.5rem;
        flex-wrap: wrap;
        justify-content: center;
    }
    
    .check-badge {
        padding: 0.25rem 0.5rem;
        border-radius: 4px;
        font-size: 0.7rem;
        font-weight: 600;
        display: inline-flex;
        align-items: center;
        gap: 0.25rem;
        white-space: nowrap;
    }
    
    .check-alert {
        background: rgba(239, 68, 68, 0.2);
        color: #ef4444;
        border: 1px solid #ef4444;
    }
    
    .check-warning {
        background: rgba(245, 158, 11, 0.2);
        color: #f59e0b;
        border: 1px solid #f59e0b;
    }
    
    .check-safe {
        background: rgba(16, 185, 129, 0.2);
        color: #10b981;
        border: 1px solid #10b981;
    }
    
    .camara-modal-section {
        background: linear-gradient(135deg, rgba(0, 217, 255, 0.05), rgba(74, 158, 255, 0.05));
        border: 1px solid #00d9ff;
        border-radius: 8px;
        padding: 1.5rem;
    }
    
    .camara-modal-section h3 {
        color: #00d9ff;
    }
    
    .rules-list-modal {
        display: flex;
        flex-direction: column;
        gap: 0.75rem;
    }
    
    .modal-rule-item {
        background: var(--bg-card);
        border-radius: 6px;
        padding: 1rem;
        border-left: 4px solid;
    }
    
    .modal-rule-item.severity-HIGH {
        border-color: #ef4444;
        background: rgba(239, 68, 68, 0.05);
    }
    
    .modal-rule-item.severity-MEDIUM {
        border-color: #f59e0b;
        background: rgba(245, 158, 11, 0.05);
    }
    
    .modal-rule-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 0.5rem;
    }
    
    .modal-rule-name {
        font-weight: 600;
        color: var(--text-primary);
    }
    
    .modal-rule-severity {
        padding: 0.25rem 0.5rem;
        border-radius: 4px;
        font-size: 0.7rem;
        font-weight: 600;
        text-transform: uppercase;
        background: #ef4444;
        color: white;
    }
    
    .modal-rule-description {
        color: var(--text-secondary);
        font-size: 0.85rem;
    }
`;
document.head.appendChild(style);

function showDetails(log) {
    // ========================================
    // BASIC TRANSACTION INFO
    // ========================================
    document.getElementById("modalPhone").textContent = log.phone_number || "N/A";
    document.getElementById("modalAmount").textContent = `$${(log.transaction_amount || 0).toFixed(2)}`;
    document.getElementById("modalTimestamp").textContent = log.timestamp || "N/A";
    document.getElementById("modalProbability").textContent = `${(log.fraud_probability * 100).toFixed(1)}%`;
    
    // Risk level with styling
    const riskLevelEl = document.getElementById("modalRiskLevel");
    riskLevelEl.textContent = log.risk_level || "N/A";
    riskLevelEl.className = `risk-badge ${(log.risk_level || '').toLowerCase().replace(' ', '-')}`;

    // ========================================
    // CAMARA NETWORK INTELLIGENCE DATA
    // ========================================
    if (log.camara_data) {
        const simSwap = log.camara_data.sim_swap || {};
        const location = log.camara_data.location || {};
        const roaming = log.camara_data.roaming || {};
        const deviceStatus = log.camara_data.device_status || {};
        
        // === SIM SWAP STATUS ===
        const simSwapEl = document.getElementById("modalSimSwap");
        if (simSwap.swapped) {
            simSwapEl.innerHTML = '<span style="color: #ef4444; font-weight: 600;">⚠️ DETECTED</span>';
        } else {
            simSwapEl.innerHTML = '<span style="color: #10b981; font-weight: 600;">✅ CLEAR</span>';
        }
        document.getElementById("modalSimSwapDate").textContent = simSwap.last_swap_date || "N/A";
        
        // === LOCATION VERIFICATION ===
        const locationVerifiedEl = document.getElementById("modalLocationVerified");
        if (location.verified) {
            locationVerifiedEl.innerHTML = '<span style="color: #10b981; font-weight: 600;">✅ VERIFIED</span>';
        } else {
            locationVerifiedEl.innerHTML = '<span style="color: #ef4444; font-weight: 600;">⚠️ MISMATCH</span>';
        }
        
        const distance = location.distance_meters || 0;
        document.getElementById("modalLocationDistance").textContent = 
            distance ? `${(distance / 1000).toFixed(1)} km` : "N/A";
        
        // === ROAMING STATUS (NEW) ===
        const roamingStatusEl = document.getElementById("modalRoamingStatus");
        if (roaming.roaming) {
            roamingStatusEl.innerHTML = '<span style="color: #ef4444; font-weight: 600;">🌍 ROAMING</span>';
        } else {
            roamingStatusEl.innerHTML = '<span style="color: #10b981; font-weight: 600;">🏠 HOME NETWORK</span>';
        }
        
        const currentNetwork = roaming.current_network || 'Unknown';
        const homeNetwork = roaming.home_network || 'Unknown';
        const roamingCountry = roaming.roaming_country || 'Unknown';
        document.getElementById("modalCurrentNetwork").textContent = 
            roaming.roaming ? `${currentNetwork} (${roamingCountry})` : homeNetwork;
        
        // === DEVICE STATUS (NEW) ===
        const deviceStatusEl = document.getElementById("modalDeviceStatus");
        const connectionStatus = deviceStatus.connection_status || 'UNKNOWN';
        
        if (connectionStatus === 'DATA') {
            deviceStatusEl.innerHTML = '<span style="color: #10b981; font-weight: 600;">🟢 DATA CONNECTED</span>';
        } else if (connectionStatus === 'SMS') {
            deviceStatusEl.innerHTML = '<span style="color: #f59e0b; font-weight: 600;">🟡 SMS ONLY</span>';
        } else if (connectionStatus === 'NOT_CONNECTED') {
            deviceStatusEl.innerHTML = '<span style="color: #ef4444; font-weight: 600;">🔴 OFFLINE</span>';
        } else {
            deviceStatusEl.innerHTML = '<span style="color: #9ca3af; font-weight: 600;">❓ UNKNOWN</span>';
        }
        
        const signalStrength = deviceStatus.signal_strength || 'Unknown';
        const networkType = deviceStatus.network_type || 'Unknown';
        const lastSeen = deviceStatus.last_seen || 'Unknown';
        
        if (connectionStatus !== 'NOT_CONNECTED') {
            document.getElementById("modalSignalStrength").textContent = `${signalStrength} (${networkType})`;
        } else {
            document.getElementById("modalSignalStrength").textContent = `No Signal - Last seen: ${lastSeen}`;
        }
        
    } else {
        // Fallback if no CAMARA data
        document.getElementById("modalSimSwap").textContent = "N/A";
        document.getElementById("modalSimSwapDate").textContent = "N/A";
        document.getElementById("modalLocationVerified").textContent = "N/A";
        document.getElementById("modalLocationDistance").textContent = "N/A";
        document.getElementById("modalRoamingStatus").textContent = "N/A";
        document.getElementById("modalCurrentNetwork").textContent = "N/A";
        document.getElementById("modalDeviceStatus").textContent = "N/A";
        document.getElementById("modalSignalStrength").textContent = "N/A";
    }

    // ========================================
    // CUSTOMER PROFILE
    // ========================================
    document.getElementById("modalVintage").textContent = log.customer_vintage || "N/A";
    document.getElementById("modalRiskRating").textContent = log.risk_rating || "N/A";
    document.getElementById("modalSegment").textContent = log.segment || "N/A";
    document.getElementById("modalOccupation").textContent = log.occupation || "N/A";
    document.getElementById("modalCountry").textContent = log.country || "N/A";
    document.getElementById("modalCity").textContent = log.city || "N/A";
    document.getElementById("modalGeoRestriction").textContent = log.geo_restriction || "N/A";
    document.getElementById("modalPepFlag").textContent = log.pep_flag || "N/A";

    // ========================================
    // TRANSACTION PATTERNS
    // ========================================
    document.getElementById("modalTxnCount").textContent = log.txn_count_1h || "N/A";
    document.getElementById("modalReversals").textContent = log.credit_reversals_7d || "N/A";

    // ========================================
    // TRIGGERED RULES SECTION
    // ========================================
    const triggeredRulesSection = document.getElementById("triggeredRulesSection");
    const triggeredRulesContainer = document.getElementById("modalTriggeredRules");
    
    if (log.explanation && log.explanation.triggered_rules && log.explanation.triggered_rules.length > 0) {
        triggeredRulesSection.style.display = 'block';
        
        const rulesHtml = log.explanation.triggered_rules.map(rule => `
            <div class="modal-rule-item severity-${rule.severity}">
                <div class="modal-rule-header">
                    <span class="modal-rule-name">${rule.rule}</span>
                    <span class="modal-rule-severity">${rule.severity}</span>
                </div>
                <div class="modal-rule-description">
                    <strong>Impact:</strong> ${rule.impact} | ${rule.description}
                </div>
            </div>
        `).join('');
        
        triggeredRulesContainer.innerHTML = rulesHtml;
    } else {
        triggeredRulesSection.style.display = 'none';
    }

    // ========================================
    // EXPLANATION
    // ========================================
    document.getElementById("modalExplanationSummary").textContent =
        (log.explanation && log.explanation.summary) || "No explanation provided.";

    if (log.explanation && log.explanation.factors && log.explanation.factors.length > 0) {
        const factorsHtml = `
            <strong>Key Detection Factors:</strong>
            <ul>${log.explanation.factors.map(f => `<li>${f}</li>`).join("")}</ul>
        `;
        document.getElementById("modalExplanationFactors").innerHTML = factorsHtml;
    } else {
        document.getElementById("modalExplanationFactors").innerHTML = "<em>No factors available</em>";
    }

    // ========================================
    // SHOW MODAL
    // ========================================
    const modal = document.getElementById("detailsModal");
    modal.style.display = "block";
}

function closeModal() {
    document.getElementById("detailsModal").style.display = "none";
}

// Close when clicking outside modal
window.onclick = function(event) {
    const modal = document.getElementById("detailsModal");
    if (event.target === modal) {
        modal.style.display = "none";
    }
};