// static/analytics.js - FIXED VERSION
document.addEventListener('DOMContentLoaded', function() {
    loadHeatmap();
    loadFraudMap();
    loadVelocityChecks();
    loadBehaviorTimeline();
});

// ============================================
// 1. FRAUD HEATMAP - Enhanced with Fraud Rate
// ============================================
function loadHeatmap() {
    fetch('/api/fraud-heatmap')
        .then(response => response.json())
        .then(data => {
            const container = document.getElementById('heatmapContainer');
            
            const heatmapHTML = `
                <div class="heatmap-container">
                    ${Array.from({length: 24}, (_, hour) => {
                        const hourData = data.hourly_fraud[hour] || {total: 0, high_risk: 0, fraud_rate: 0};
                        const fraudRate = hourData.fraud_rate || 0;
                        const color = getHeatColor(fraudRate);
                        const textColor = fraudRate > 50 ? '#ffffff' : '#1a1f29';
                        
                        return `
                            <div class="heatmap-cell" 
                                 style="background: ${color}; color: ${textColor};" 
                                 title="Hour ${hour}:00\nTotal: ${hourData.total} transactions\nHigh Risk: ${hourData.high_risk}\nFraud Rate: ${fraudRate}%"
                                 onclick="showHourDetails(${hour}, ${JSON.stringify(hourData).replace(/"/g, '&quot;')})">
                                ${hour}h
                                <br>
                                <small style="font-size: 0.6rem;">${fraudRate.toFixed(0)}%</small>
                            </div>
                        `;
                    }).join('')}
                </div>
            `;
            
            container.innerHTML = heatmapHTML;
        })
        .catch(error => {
            console.error('Error loading heatmap:', error);
            document.getElementById('heatmapContainer').innerHTML = 
                '<p style="color: var(--text-secondary); text-align: center; padding: 2rem;">Error loading heatmap data</p>';
        });
}

function getHeatColor(fraudRate) {
    // Gradient based on fraud rate percentage
    if (fraudRate === 0) return '#1a1f29'; // No data
    if (fraudRate <= 20) return '#10b981'; // Low - Green
    if (fraudRate <= 50) return '#f59e0b'; // Medium - Orange
    return '#ef4444'; // High - Red
}

function showHourDetails(hour, hourData) {
    const modal = `
        <div style="background: rgba(0,0,0,0.8); position: fixed; top: 0; left: 0; width: 100%; height: 100%; z-index: 9999; display: flex; align-items: center; justify-content: center;" onclick="this.remove()">
            <div style="background: var(--bg-card); padding: 2rem; border-radius: 12px; max-width: 500px; border: 1px solid var(--border-color);" onclick="event.stopPropagation()">
                <h3 style="margin-top: 0; color: var(--primary-color);">Hour ${hour}:00 - ${hour + 1}:00 Analysis</h3>
                <div style="display: grid; gap: 1rem; margin-top: 1.5rem;">
                    <div style="background: var(--bg-dark); padding: 1rem; border-radius: 8px;">
                        <div style="color: var(--text-secondary); font-size: 0.9rem;">Total Transactions</div>
                        <div style="font-size: 2rem; font-weight: bold; color: var(--primary-color);">${hourData.total}</div>
                    </div>
                    <div style="background: rgba(239, 68, 68, 0.1); padding: 1rem; border-radius: 8px; border-left: 4px solid var(--danger-color);">
                        <div style="color: var(--text-secondary); font-size: 0.9rem;">High Risk Detected</div>
                        <div style="font-size: 2rem; font-weight: bold; color: var(--danger-color);">${hourData.high_risk}</div>
                    </div>
                    <div style="background: var(--bg-dark); padding: 1rem; border-radius: 8px;">
                        <div style="color: var(--text-secondary); font-size: 0.9rem;">Fraud Rate</div>
                        <div style="font-size: 2rem; font-weight: bold; color: ${hourData.fraud_rate > 50 ? 'var(--danger-color)' : 'var(--warning-color)'};">${hourData.fraud_rate.toFixed(1)}%</div>
                    </div>
                </div>
                <button onclick="this.closest('div').parentElement.remove()" style="margin-top: 1.5rem; width: 100%; padding: 0.75rem; background: var(--primary-color); color: white; border: none; border-radius: 6px; cursor: pointer;">Close</button>
            </div>
        </div>
    `;
    document.body.insertAdjacentHTML('beforeend', modal);
}

// ============================================
// 2. GEOGRAPHIC FRAUD MAP - Real Coordinates
// ============================================
function loadFraudMap() {
    fetch('/api/fraud-geographic')
        .then(response => response.json())
        .then(data => {
            const map = L.map('fraudMap').setView([20, 0], 2);
            
            L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
                attribution: '© OpenStreetMap contributors',
                maxZoom: 18
            }).addTo(map);
            
            // Add markers for fraud clusters
            data.clusters.forEach(cluster => {
                const color = cluster.risk_level === 'High' ? '#ef4444' : 
                             cluster.risk_level === 'Medium' ? '#f59e0b' : '#10b981';
                
                const circle = L.circleMarker([cluster.lat, cluster.lon], {
                    radius: Math.min(Math.max(cluster.count * 3, 8), 40),
                    fillColor: color,
                    color: color,
                    weight: 2,
                    opacity: 0.8,
                    fillOpacity: 0.6
                }).addTo(map);
                
                circle.bindPopup(`
                    <div style="font-family: Arial; padding: 0.5rem;">
                        <strong style="font-size: 1.1rem;">${cluster.location}</strong><br>
                        <div style="margin-top: 0.5rem; padding-top: 0.5rem; border-top: 1px solid #e5e7eb;">
                            <strong>Transactions:</strong> ${cluster.count}<br>
                            <strong>Risk Level:</strong> <span style="color: ${color}; font-weight: bold;">${cluster.risk_level}</span><br>
                            <strong>Fraud Rate:</strong> ${cluster.risk_rate}%<br>
                            <strong>Total Amount:</strong> $${cluster.total_amount.toFixed(2)}
                        </div>
                    </div>
                `);
            });
            
            // Auto-fit bounds if clusters exist
            if (data.clusters.length > 0) {
                const bounds = L.latLngBounds(data.clusters.map(c => [c.lat, c.lon]));
                map.fitBounds(bounds, {padding: [50, 50]});
            }
        })
        .catch(error => {
            console.error('Error loading fraud map:', error);
            document.getElementById('fraudMap').innerHTML = 
                '<p style="padding: 2rem; text-align: center; color: var(--text-secondary);">Error loading map</p>';
        });
}

// ============================================
// 3. VELOCITY CHECKS - Enhanced Display
// ============================================
function loadVelocityChecks() {
    fetch('/api/velocity-checks')
        .then(response => response.json())
        .then(data => {
            const container = document.getElementById('velocityChecks');
            
            if (data.anomalies.length === 0) {
                container.innerHTML = `
                    <div style="text-align: center; padding: 2rem; color: var(--text-secondary);">
                        <i class="bi bi-check-circle" style="font-size: 3rem; color: var(--success-color);"></i>
                        <p style="margin-top: 1rem;">No velocity anomalies detected</p>
                        <p style="font-size: 0.85rem; margin-top: 0.5rem;">All transaction patterns are within normal ranges</p>
                    </div>
                `;
                return;
            }
            
            const anomaliesHTML = data.anomalies.map(anomaly => `
                <div class="velocity-alert" style="border-left-color: ${anomaly.severity === 'HIGH' ? 'var(--danger-color)' : 'var(--warning-color)'};">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem;">
                        <strong style="color: ${anomaly.severity === 'HIGH' ? 'var(--danger-color)' : 'var(--warning-color)'};">
                            <i class="bi bi-exclamation-triangle"></i> ${anomaly.severity} Severity Alert
                        </strong>
                        <span class="severity-badge severity-${anomaly.severity}">${anomaly.severity}</span>
                    </div>
                    <div class="velocity-item">
                        <span><i class="bi bi-telephone"></i> Phone:</span>
                        <strong>${anomaly.phone}</strong>
                    </div>
                    <div class="velocity-item">
                        <span><i class="bi bi-lightning"></i> Rapid Transactions:</span>
                        <strong style="color: var(--danger-color);">${anomaly.transaction_count} in ${anomaly.time_window}</strong>
                    </div>
                    <div class="velocity-item">
                        <span><i class="bi bi-geo"></i> Different Locations:</span>
                        <strong>${anomaly.location_count}</strong>
                    </div>
                    <div class="velocity-item">
                        <span><i class="bi bi-currency-dollar"></i> Total Amount:</span>
                        <strong>$${anomaly.total_amount.toFixed(2)}</strong>
                    </div>
                    <div class="velocity-item">
                        <span><i class="bi bi-exclamation-octagon"></i> High Risk Count:</span>
                        <strong style="color: var(--danger-color);">${anomaly.high_risk_count}</strong>
                    </div>
                    <button class="btn-details" onclick="window.location.href='/investigation/${anomaly.phone}'" 
                            style="margin-top: 0.75rem; width: 100%;">
                        <i class="bi bi-search"></i> Investigate This Pattern
                    </button>
                </div>
            `).join('');
            
            container.innerHTML = anomaliesHTML;
        })
        .catch(error => {
            console.error('Error loading velocity checks:', error);
            document.getElementById('velocityChecks').innerHTML = 
                '<p style="color: var(--text-secondary); text-align: center; padding: 2rem;">Error loading velocity data</p>';
        });
}

// ============================================
// 4. NETWORK BEHAVIOR TIMELINE - Enhanced
// ============================================
function loadBehaviorTimeline() {
    fetch('/api/network-behavior')
        .then(response => response.json())
        .then(data => {
            const container = document.getElementById('behaviorTimeline');
            
            if (data.events.length === 0) {
                container.innerHTML = `
                    <div style="text-align: center; padding: 2rem; color: var(--text-secondary);">
                        <i class="bi bi-info-circle" style="font-size: 2rem;"></i>
                        <p style="margin-top: 1rem;">No network behavior events detected</p>
                        <p style="font-size: 0.85rem; margin-top: 0.5rem;">All network activities are normal</p>
                    </div>
                `;
                return;
            }
            
            const eventsHTML = data.events.map(event => {
                const markerClass = `marker-${event.type.toLowerCase().replace(/ /g, '-')}`;
                const icon = event.type === 'SIM Swap' ? 'bi-sim' :
                           event.type === 'Location Change' ? 'bi-geo-alt' :
                           event.type === 'Roaming' ? 'bi-globe' :
                           event.type === 'Device Offline' ? 'bi-phone-x' : 'bi-activity';
                
                const severityColor = event.severity === 'CRITICAL' ? '#991b1b' :
                                     event.severity === 'HIGH' ? 'var(--danger-color)' :
                                     'var(--warning-color)';
                
                return `
                    <div class="timeline-event">
                        <div class="timeline-marker ${markerClass}"></div>
                        <div class="event-content">
                            <div class="event-header">
                                <div class="event-type">
                                    <i class="bi ${icon}"></i>
                                    ${event.type}
                                    <span class="severity-badge severity-${event.severity}" style="margin-left: 0.5rem;">${event.severity}</span>
                                </div>
                                <div class="event-time"><i class="bi bi-clock"></i> ${event.timestamp}</div>
                            </div>
                            <div class="event-details" style="margin-top: 0.5rem;">
                                <strong style="color: var(--text-primary);"><i class="bi bi-telephone"></i> Phone:</strong> ${event.phone}<br>
                                <strong style="color: var(--text-primary);"><i class="bi bi-info-circle"></i> Details:</strong> ${event.details}
                            </div>
                            <div style="margin-top: 0.5rem; padding-top: 0.5rem; border-top: 1px solid var(--border-color);">
                                <span style="font-size: 0.85rem; color: var(--text-secondary);">Risk Level:</span>
                                <span class="risk-badge ${event.risk_level.toLowerCase().replace(' ', '-')}" style="margin-left: 0.5rem;">${event.risk_level}</span>
                            </div>
                        </div>
                    </div>
                `;
            }).join('');
            
            container.innerHTML = eventsHTML;
        })
        .catch(error => {
            console.error('Error loading behavior timeline:', error);
            document.getElementById('behaviorTimeline').innerHTML = 
                '<p style="color: var(--text-secondary); text-align: center; padding: 2rem;">Error loading timeline</p>';
        });
}

// ============================================
// EXPORT FUNCTIONS
// ============================================
function exportHeatmap() {
    alert('Heatmap export feature: Save as PNG/PDF\n\nImplementation: Use html2canvas library to capture the heatmap visualization and download as image.');
}

function exportMap() {
    alert('Map export feature: Save geographic view\n\nImplementation: Use Leaflet\'s built-in screenshot functionality or html2canvas.');
}

// Auto-refresh every 30 seconds
setInterval(() => {
    console.log('🔄 Refreshing analytics data...');
    loadVelocityChecks();
    loadBehaviorTimeline();
    loadHeatmap();
}, 30000);

console.log('✅ Advanced Analytics Dashboard loaded successfully');