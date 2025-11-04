// static/llm_explanation.js
// Functions to populate and display LLM-powered explanations

/**
 * Main function to display LLM explanation in the UI
 * Call this after prediction result is received
 */
function displayLLMExplanation(llmData, transactionData) {
    if (!llmData) {
        console.log('No LLM explanation data available');
        return;
    }
    
    // Show the LLM explanation section
    const section = document.getElementById('llmExplanation');
    if (section) {
        section.style.display = 'block';
    }
    
    // Populate each section
    populateExecutiveSummary(llmData);
    populateDetailedAnalysis(llmData);
    populateBehavioralInsights(llmData, transactionData);
    populateRiskFactors(llmData);
    populateNetworkIntelligence(llmData, transactionData);
    populateRecommendations(llmData);
    populateCustomerTimeline(llmData);
}

/**
 * Populate Executive Summary
 */
function populateExecutiveSummary(llmData) {
    const summaryEl = document.getElementById('executiveSummary');
    if (summaryEl && llmData.executive_summary) {
        summaryEl.textContent = llmData.executive_summary;
    }
}

/**
 * Populate Detailed Analysis
 */
function populateDetailedAnalysis(llmData) {
    const contentEl = document.getElementById('detailedAnalysisContent');
    if (!contentEl || !llmData.detailed_analysis) return;
    
    // Convert text to paragraphs with proper formatting
    const analysis = llmData.detailed_analysis;
    
    // Split by double newlines or markdown-style bold headers
    const sections = analysis.split(/\*\*|\n\n/).filter(s => s.trim());
    
    let html = '';
    sections.forEach(section => {
        const trimmed = section.trim();
        if (trimmed) {
            if (trimmed.includes(':') && trimmed.length < 100) {
                // Likely a header
                html += `<h5 style="color: var(--primary-color); margin-top: 1.5rem; margin-bottom: 0.75rem;">${trimmed}</h5>`;
            } else {
                // Regular paragraph
                html += `<p style="color: var(--text-secondary); line-height: 1.8; margin-bottom: 1rem;">${trimmed}</p>`;
            }
        }
    });
    
    contentEl.innerHTML = html || '<p style="color: var(--text-secondary);">Detailed analysis is being generated...</p>';
}

/**
 * Populate Behavioral Insights
 */
function populateBehavioralInsights(llmData, transactionData) {
    const contentEl = document.getElementById('behavioralInsightsContent');
    if (!contentEl) return;
    
    let html = '';
    
    // Add LLM-generated insights
    if (llmData.behavioral_insights) {
        const insights = llmData.behavioral_insights;
        const sections = insights.split(/\*\*|\n\n/).filter(s => s.trim());
        
        sections.forEach(section => {
            const trimmed = section.trim();
            if (trimmed) {
                if (trimmed.includes(':') && trimmed.length < 100) {
                    html += `<h5 style="color: var(--primary-color); margin-top: 1.5rem; margin-bottom: 0.75rem;">${trimmed}</h5>`;
                } else {
                    html += `<p style="color: var(--text-secondary); line-height: 1.8; margin-bottom: 1rem;">${trimmed}</p>`;
                }
            }
        });
    }
    
    // Add customer profile statistics
    if (llmData.customer_profile) {
        const profile = llmData.customer_profile;
        
        html += `
            <div style="background: var(--bg-dark); padding: 1.5rem; border-radius: 8px; margin-top: 2rem;">
                <h5 style="color: var(--text-primary); margin-bottom: 1rem;">
                    <i class="bi bi-person-badge"></i> Customer Profile Summary
                </h5>
                <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1rem;">
                    <div class="profile-stat">
                        <div style="color: var(--text-secondary); font-size: 0.85rem;">Total Transactions</div>
                        <div style="color: var(--text-primary); font-size: 1.5rem; font-weight: 600;">${profile.total_transactions || 0}</div>
                    </div>
                    <div class="profile-stat">
                        <div style="color: var(--text-secondary); font-size: 0.85rem;">Average Amount</div>
                        <div style="color: var(--text-primary); font-size: 1.5rem; font-weight: 600;">$${(profile.average_amount || 0).toFixed(2)}</div>
                    </div>
                    <div class="profile-stat">
                        <div style="color: var(--text-secondary); font-size: 0.85rem;">Activity Level</div>
                        <div style="color: var(--text-primary); font-size: 1.5rem; font-weight: 600;">${profile.velocity_pattern || 'Unknown'}</div>
                    </div>
                    <div class="profile-stat">
                        <div style="color: var(--text-secondary); font-size: 0.85rem;">Customer Since</div>
                        <div style="color: var(--text-primary); font-size: 1.5rem; font-weight: 600;">${profile.days_as_customer || 0} days</div>
                    </div>
                </div>
            </div>
        `;
    }
    
    contentEl.innerHTML = html || '<p style="color: var(--text-secondary);">No behavioral insights available</p>';
}

/**
 * Populate Risk Factors
 */
function populateRiskFactors(llmData) {
    const contentEl = document.getElementById('riskFactorsContent');
    if (!contentEl) return;
    
    const riskFactors = llmData.risk_factors || [];
    
    if (riskFactors.length === 0) {
        contentEl.innerHTML = `
            <div style="text-align: center; padding: 2rem; color: var(--text-secondary);">
                <i class="bi bi-check-circle" style="font-size: 3rem; color: var(--success-color);"></i>
                <p style="margin-top: 1rem;">No significant risk factors detected</p>
            </div>
        `;
        return;
    }
    
    let html = '<div class="risk-factor-grid">';
    
    riskFactors.forEach(factor => {
        html += `
            <div class="risk-factor-item severity-${factor.severity}">
                <div class="risk-factor-header">
                    <span class="risk-factor-title">${factor.factor}</span>
                    <span class="severity-badge ${factor.severity}">${factor.severity}</span>
                </div>
                <div class="risk-factor-description">${factor.explanation}</div>
            </div>
        `;
    });
    
    html += '</div>';
    contentEl.innerHTML = html;
}

/**
 * Populate Network Intelligence Breakdown
 */
function populateNetworkIntelligence(llmData, transactionData) {
    const contentEl = document.getElementById('networkIntelContent');
    if (!contentEl || !transactionData.camara_data) return;
    
    const camara = transactionData.camara_data;
    
    let html = '<div class="network-intel-grid">';
    
    // SIM Swap Card
    const simSwap = camara.sim_swap || {};
    html += `
        <div class="intel-card">
            <div class="intel-card-header">
                <i class="bi bi-sim"></i> SIM Swap Detection
            </div>
            <div class="intel-status">
                <div class="status-indicator ${simSwap.swapped ? 'danger' : 'safe'}"></div>
                <strong>${simSwap.swapped ? 'DETECTED' : 'Clear'}</strong>
            </div>
            <div class="intel-details">
                ${simSwap.swapped ? 
                    `⚠️ SIM card was changed ${simSwap.last_swap_date}. This is a critical fraud indicator suggesting potential account takeover.` :
                    `✅ No SIM swap activity detected in monitoring period. Device maintains original SIM configuration.`
                }
            </div>
        </div>
    `;
    
    // Location Verification Card
    const location = camara.location || {};
    html += `
        <div class="intel-card">
            <div class="intel-card-header">
                <i class="bi bi-geo-alt"></i> Location Verification
            </div>
            <div class="intel-status">
                <div class="status-indicator ${location.verified ? 'safe' : 'danger'}"></div>
                <strong>${location.verified ? 'Verified' : 'Mismatch'}</strong>
            </div>
            <div class="intel-details">
                ${location.verified ?
                    `✅ Device location matches KYC registered address within acceptable radius.` :
                    `⚠️ Device is ${(location.distance_meters / 1000).toFixed(1)} km from registered address. Possible VPN, proxy, or unauthorized access.`
                }
            </div>
        </div>
    `;
    
    // Roaming Status Card
    const roaming = camara.roaming || {};
    html += `
        <div class="intel-card">
            <div class="intel-card-header">
                <i class="bi bi-globe"></i> Roaming Status
            </div>
            <div class="intel-status">
                <div class="status-indicator ${roaming.roaming ? 'warning' : 'safe'}"></div>
                <strong>${roaming.roaming ? 'Roaming' : 'Home Network'}</strong>
            </div>
            <div class="intel-details">
                ${roaming.roaming ?
                    `📡 Device is roaming on ${roaming.current_network} in ${roaming.roaming_country}. Verify if customer has notified bank of international travel.` :
                    `✅ Device is on home network (${roaming.current_network}). Normal domestic usage pattern.`
                }
            </div>
        </div>
    `;
    
    // Device Status Card
    const deviceStatus = camara.device_status || {};
    html += `
        <div class="intel-card">
            <div class="intel-card-header">
                <i class="bi bi-phone"></i> Device Connectivity
            </div>
            <div class="intel-status">
                <div class="status-indicator ${deviceStatus.connection_status === 'DATA' ? 'safe' : deviceStatus.connection_status === 'SMS' ? 'warning' : 'danger'}"></div>
                <strong>${deviceStatus.connection_status || 'Unknown'}</strong>
            </div>
            <div class="intel-details">
                ${deviceStatus.connection_status === 'DATA' ?
                    `✅ Device is actively connected with data service. Signal: ${deviceStatus.signal_strength}.` :
                deviceStatus.connection_status === 'SMS' ?
                    `⚠️ Device has SMS-only connectivity. Limited data service may indicate network issues or basic phone.` :
                deviceStatus.connection_status === 'NOT_CONNECTED' ?
                    `🚨 Device is offline (last seen: ${deviceStatus.last_seen}). Transaction may be from compromised credentials on different device.` :
                    `Status unknown`
                }
            </div>
        </div>
    `;
    
    html += '</div>';
    
    // Add explanation of CAMARA APIs
    html += `
        <div style="margin-top: 2rem; padding: 1.5rem; background: rgba(74, 158, 255, 0.1); border-radius: 8px; border-left: 4px solid var(--primary-color);">
            <h5 style="color: var(--primary-color); margin-bottom: 1rem;">
                <i class="bi bi-info-circle"></i> What are CAMARA Network APIs?
            </h5>
            <p style="color: var(--text-secondary); line-height: 1.8;">
                CAMARA (Network-as-Code) APIs provide real-time intelligence directly from mobile network operators. 
                Unlike traditional fraud detection that relies only on transaction data, these APIs access network-level 
                information including SIM card status, device location, connectivity state, and roaming activity. 
                This provides an additional layer of security that's extremely difficult for fraudsters to bypass.
            </p>
        </div>
    `;
    
    contentEl.innerHTML = html;
}

/**
 * Populate Recommendations
 */
function populateRecommendations(llmData) {
    const contentEl = document.getElementById('recommendationsContent');
    if (!contentEl || !llmData.recommendation) return;
    
    const rec = llmData.recommendation;
    const actionClass = rec.action === 'BLOCK TRANSACTION' ? 'reject' :
                       rec.action === 'REQUIRE ADDITIONAL VERIFICATION' ? 'step-up' : 'approve';
    
    let html = `
        <div class="recommendation-action ${actionClass}">
            <div class="action-header">${rec.action}</div>
            ${rec.urgency ? `<div class="urgency-badge">${rec.urgency}</div>` : ''}
        </div>
    `;
    
    if (rec.next_steps && rec.next_steps.length > 0) {
        html += `
            <div class="next-steps">
                <h5>Recommended Next Steps:</h5>
                <ol>
                    ${rec.next_steps.map(step => `<li>${step}</li>`).join('')}
                </ol>
            </div>
        `;
    }
    
    if (rec.additional_info_needed && rec.additional_info_needed.length > 0) {
        html += `
            <div class="next-steps" style="margin-top: 1.5rem;">
                <h5>Additional Information Needed:</h5>
                <ul style="list-style: none; padding-left: 0;">
                    ${rec.additional_info_needed.map(info => `
                        <li style="padding: 0.5rem 0; border-bottom: 1px solid var(--border-color);">
                            <i class="bi bi-check-square" style="color: var(--primary-color); margin-right: 0.5rem;"></i>
                            ${info}
                        </li>
                    `).join('')}
                </ul>
            </div>
        `;
    }
    
    contentEl.innerHTML = html;
}

/**
 * Populate Customer Transaction Timeline
 */
function populateCustomerTimeline(llmData) {
    const timelineEl = document.getElementById('customerTimelineViz');
    if (!timelineEl) return;
    
    const recentTxns = llmData.customer_profile?.recent_transactions || 
                      llmData.historical_context?.recent_transactions || [];
    
    if (recentTxns.length === 0) {
        timelineEl.innerHTML = `
            <div style="text-align: center; padding: 2rem; color: var(--text-secondary);">
                <i class="bi bi-inbox" style="font-size: 2rem;"></i>
                <p style="margin-top: 0.5rem;">No recent transaction history available</p>
            </div>
        `;
        return;
    }
    
    let html = '<div style="position: relative; padding-left: 2rem;">';
    html += '<div style="position: absolute; left: 0; top: 0; bottom: 0; width: 2px; background: var(--border-color);"></div>';
    
    recentTxns.forEach((txn, index) => {
        const riskColor = txn.risk === 'High Risk' ? 'var(--danger-color)' :
                         txn.risk === 'Medium Risk' ? 'var(--warning-color)' : 'var(--success-color)';
        
        html += `
            <div style="position: relative; margin-bottom: 1.5rem; padding-left: 1rem;">
                <div style="position: absolute; left: -2.5rem; width: 12px; height: 12px; border-radius: 50%; background: ${riskColor}; border: 3px solid var(--bg-card);"></div>
                <div style="background: var(--bg-dark); padding: 1rem; border-radius: 8px; border-left: 3px solid ${riskColor};">
                    <div style="display: flex; justify-content: space-between; margin-bottom: 0.5rem;">
                        <strong style="color: var(--text-primary);">$${txn.amount.toFixed(2)}</strong>
                        <span style="color: var(--text-secondary); font-size: 0.85rem;">${txn.time}</span>
                    </div>
                    <div style="display: flex; align-items: center; gap: 0.5rem;">
                        <span style="padding: 0.25rem 0.75rem; background: ${riskColor}20; color: ${riskColor}; border-radius: 12px; font-size: 0.75rem; font-weight: 600;">
                            ${txn.risk}
                        </span>
                    </div>
                </div>
            </div>
        `;
    });
    
    html += '</div>';
    timelineEl.innerHTML = html;
}

/**
 * Load LLM explanation for existing transaction (investigation page)
 */
async function loadLLMExplanationForPhone(phoneNumber) {
    try {
        const response = await fetch(`/api/get-llm-explanation/${phoneNumber}`);
        const data = await response.json();
        
        if (data.success && data.explanation) {
            displayLLMExplanation(data.explanation, {
                camara_data: data.explanation.camara_intelligence || {}
            });
        } else {
            console.error('Failed to load LLM explanation:', data.error);
        }
    } catch (error) {
        console.error('Error loading LLM explanation:', error);
    }
}

/**
 * Export this for use in other scripts
 */
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        displayLLMExplanation,
        loadLLMExplanationForPhone
    };
}