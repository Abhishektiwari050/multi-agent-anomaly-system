/* ----------------------------------------------------
   Aura Clinical System - Single-Page Dashboard Logic
   Matches backend API routes and chart visualizations
   ---------------------------------------------------- */

document.addEventListener('DOMContentLoaded', () => {
    // API Endpoint resolution
    const apiBaseUrl = window.location.origin;
    document.getElementById('api-endpoint-url').textContent = apiBaseUrl;

    // DOM Elements
    const runScanForm = document.getElementById('new-scan-form');
    const patientGroupNameInput = document.getElementById('patient-group-name');
    const groupNameError = document.getElementById('group-name-error');
    const customSizeInput = document.getElementById('custom-size');
    const customContaminationInput = document.getElementById('custom-contamination');
    const randomSeedInput = document.getElementById('random-seed');
    const deadlineInput = document.getElementById('deadline');
    
    // Panels
    const welcomePanel = document.getElementById('welcome-panel');
    const progressPanel = document.getElementById('progress-panel');
    const resultsPanel = document.getElementById('results-panel');
    
    // Connection Status
    const statusDot = document.getElementById('status-dot');
    const statusText = document.getElementById('status-text');
    
    // Steppers and Progress
    const runningTaskDesc = document.getElementById('running-task-desc');
    const runningTaskId = document.getElementById('running-task-id');
    const progressCircle = document.getElementById('progress-circle');
    const progressTextPct = document.getElementById('progress-text-pct');
    const step1 = document.getElementById('step-1');
    const step2 = document.getElementById('step-2');
    const step3 = document.getElementById('step-3');
    const step4 = document.getElementById('step-4');

    // Result Text Fields
    const resultTimestamp = document.getElementById('result-timestamp');
    const resultTitle = document.getElementById('result-title');
    const resultTaskId = document.getElementById('result-task-id');
    const resultAlertBadge = document.getElementById('result-alert-badge');
    const valTotalRecords = document.getElementById('val-total-records');
    const valAnomaliesDetected = document.getElementById('val-anomalies-detected');
    const valAvgScore = document.getElementById('val-avg-score');
    const valExecutionTime = document.getElementById('val-execution-time');
    const clinicalAlertsContainer = document.getElementById('clinical-alerts-container');
    
    // Legend indicators
    const legendHigh = document.getElementById('legend-high');
    const legendMedium = document.getElementById('legend-medium');
    const legendLow = document.getElementById('legend-low');

    // Chart Globals
    let scatterChartInstance = null;
    let donutChartInstance = null;
    
    // Polling Intervals
    let pollingIntervalId = null;

    // Preset Selection Helpers
    setupPresets('size-presets', customSizeInput);
    setupPresets('contamination-presets', customContaminationInput);
    
    // Initialize Lucide Icons
    lucide.createIcons();

    // Check Broker Status
    checkSystemHealth();
    setInterval(checkSystemHealth, 15000); // Poll health every 15 seconds

    // Load History list on load
    loadHistory();
    document.getElementById('refresh-history-btn').addEventListener('click', loadHistory);

    // Form Submission
    runScanForm.addEventListener('submit', (e) => {
        e.preventDefault();
        
        // Reset Validation
        runScanForm.querySelector('.form-group').classList.remove('has-error');
        
        const groupName = patientGroupNameInput.value.trim();
        if (!groupName) {
            runScanForm.querySelector('.form-group').classList.add('has-error');
            return;
        }

        const requestBody = {
            total_records: parseInt(customSizeInput.value) || 7000,
            contamination: parseFloat(customContaminationInput.value) || 0.05,
            random_seed: parseInt(randomSeedInput.value) || 42,
            deadline_minutes: parseInt(deadlineInput.value) || 5,
            description: groupName
        };

        submitAnalysisTask(requestBody);
    });

    // Preset Toggle Handler
    function setupPresets(containerId, hiddenInput) {
        const container = document.getElementById(containerId);
        const buttons = container.querySelectorAll('.preset-btn');
        
        buttons.forEach(btn => {
            btn.addEventListener('click', () => {
                buttons.forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
                hiddenInput.value = btn.getAttribute('data-value');
            });
        });
    }

    // Health Check endpoint poller
    function checkSystemHealth() {
        fetch(`${apiBaseUrl}/health`)
            .then(res => res.json())
            .then(data => {
                if (data.status === 'ok') {
                    statusDot.className = 'dot online pulse';
                    statusText.textContent = 'Broker Connected';
                } else {
                    statusDot.className = 'dot offline pulse';
                    statusText.textContent = 'Broker Degraded';
                }
            })
            .catch(err => {
                statusDot.className = 'dot offline pulse';
                statusText.textContent = 'API Server Offline';
            });
    }

    // Submit Task
    function submitAnalysisTask(body) {
        // Switch to progress panel
        showPanel(progressPanel);
        
        // Initialize circular progress bar & steps
        updateProgressCircle(0);
        runningTaskDesc.textContent = body.description;
        runningTaskId.textContent = 'Dispatching to Planner (Agent A)...';
        resetStepper();
        
        // Disable submission button while running
        document.getElementById('run-scan-btn').disabled = true;
        document.getElementById('run-scan-btn').style.opacity = 0.5;

        fetch(`${apiBaseUrl}/tasks/analyze`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(body)
        })
        .then(res => {
            if (!res.ok) throw new Error('API dispatch failed');
            return res.json();
        })
        .then(data => {
            runningTaskId.textContent = data.task_id;
            // Begin polling task status
            startPollingTask(data.task_id);
        })
        .catch(err => {
            console.error(err);
            runningTaskId.textContent = 'Error: Dispatch Failed';
            updateStepState(step1, 'failed', 'Error dispatching task to queue.');
            document.getElementById('run-scan-btn').disabled = false;
            document.getElementById('run-scan-btn').style.opacity = 1;
        });
    }

    // Reset Stepper Elements
    function resetStepper() {
        [step1, step2, step3, step4].forEach(step => {
            step.className = 'step';
            const num = step.querySelector('.step-num');
            if (step === step1) {
                num.innerHTML = '<i data-lucide="loader-2" class="spin"></i>';
            } else {
                num.textContent = step.id.split('-')[1];
            }
        });
        lucide.createIcons();
    }

    function updateStepState(stepElement, state, customText = '') {
        const numElement = stepElement.querySelector('.step-num');
        const descElement = stepElement.querySelector('.step-content p');
        
        stepElement.className = `step ${state}`;
        
        if (state === 'active') {
            numElement.innerHTML = '<i data-lucide="loader-2" class="spin"></i>';
            if (customText) descElement.textContent = customText;
        } else if (state === 'completed') {
            numElement.innerHTML = '<i data-lucide="check"></i>';
            if (customText) descElement.textContent = customText;
        } else if (state === 'failed') {
            numElement.innerHTML = '<i data-lucide="x"></i>';
            if (customText) descElement.textContent = customText;
        }
        lucide.createIcons();
    }

    // Circular Progress Update (Stroke Dash offset calculation)
    function updateProgressCircle(pct) {
        progressTextPct.textContent = `${pct}%`;
        const radius = 45;
        const circumference = 2 * Math.PI * radius; // ~282.7
        const offset = circumference - (pct / 100) * circumference;
        progressCircle.style.strokeDashoffset = offset;
    }

    // Poll Task Status
    function startPollingTask(taskId) {
        if (pollingIntervalId) clearInterval(pollingIntervalId);
        
        pollingIntervalId = setInterval(() => {
            fetch(`${apiBaseUrl}/tasks/${taskId}/status`)
                .then(res => {
                    if (res.status === 404) return { status: 'DISPATCHED', progress_pct: 0 };
                    return res.json();
                })
                .then(task => {
                    const pct = task.progress_pct || 0;
                    const status = task.status;
                    const subtask = task.current_sub_task || '';
                    
                    updateProgressCircle(pct);
                    
                    // Stepper coordination logic
                    if (pct < 25) {
                        updateStepState(step1, 'active', 'Planner is enqueuing message parameters...');
                    } else if (pct >= 25 && pct < 50) {
                        updateStepState(step1, 'completed', 'Enqueued successfully.');
                        updateStepState(step2, 'active', 'Ingesting and simulating patient vital metrics...');
                    } else if (pct >= 50 && pct < 75) {
                        updateStepState(step1, 'completed');
                        updateStepState(step2, 'completed', 'Simulated metrics generated.');
                        updateStepState(step3, 'active', 'Training Isolation Forest algorithm...');
                    } else if (pct >= 75 && pct < 100) {
                        updateStepState(step1, 'completed');
                        updateStepState(step2, 'completed');
                        updateStepState(step3, 'completed', 'Models trained. Multivariate anomalies detected.');
                        updateStepState(step4, 'active', 'Verifying safety thresholds and compiling files...');
                    } else if (pct === 100 && status === 'COMPLETED') {
                        updateStepState(step1, 'completed');
                        updateStepState(step2, 'completed');
                        updateStepState(step3, 'completed');
                        updateStepState(step4, 'completed', 'Alarm thresholds resolved and verified.');
                        
                        // Done Polling
                        clearInterval(pollingIntervalId);
                        loadHistory();
                        
                        // Enable submission button
                        document.getElementById('run-scan-btn').disabled = false;
                        document.getElementById('run-scan-btn').style.opacity = 1;
                        
                        // Wait 1s and show result
                        setTimeout(() => {
                            viewTaskResult(taskId);
                        }, 1000);
                    }
                    
                    if (status === 'FAILED') {
                        clearInterval(pollingIntervalId);
                        updateStepState(step4, 'failed', task.error || 'Task calculation failed.');
                        document.getElementById('run-scan-btn').disabled = false;
                        document.getElementById('run-scan-btn').style.opacity = 1;
                    }
                })
                .catch(err => {
                    console.error('Error polling task:', err);
                });
        }, 1200);
    }

    // Load Tasks list
    function loadHistory() {
        const listContainer = document.getElementById('history-list-container');
        
        fetch(`${apiBaseUrl}/tasks`)
            .then(res => res.json())
            .then(tasks => {
                listContainer.innerHTML = '';
                
                const taskEntries = Object.entries(tasks);
                if (taskEntries.length === 0) {
                    listContainer.innerHTML = '<div class="loading-placeholder">No scans run yet.</div>';
                    return;
                }
                
                // Sort tasks by last updated (newest first)
                taskEntries.sort((a, b) => {
                    return new Date(b[1].last_updated) - new Date(a[1].last_updated);
                });
                
                taskEntries.forEach(([taskId, task]) => {
                    const card = document.createElement('div');
                    card.className = 'history-card';
                    card.setAttribute('data-id', taskId);
                    
                    const timeString = new Date(task.last_updated).toLocaleString();
                    const anomalyCount = task.result_summary ? task.result_summary.anomalies_detected : (task.anomalies_so_far || 0);
                    
                    card.innerHTML = `
                        <div class="history-card-header">
                            <h3>${task.description || 'Unnamed Group'}</h3>
                            <span class="badge-status ${task.status.toLowerCase()}">${task.status}</span>
                        </div>
                        <div class="history-card-meta">
                            <span>Vitals: ${task.total_records || task.records_processed || 0}</span>
                            <span>Anomalies: ${anomalyCount}</span>
                        </div>
                        <div class="history-card-meta">
                            <span>${timeString}</span>
                        </div>
                    `;
                    
                    card.addEventListener('click', () => {
                        // Remove active class from all card elements
                        document.querySelectorAll('.history-card').forEach(c => c.classList.remove('active'));
                        card.classList.add('active');
                        viewTaskResult(taskId);
                    });
                    
                    listContainer.appendChild(card);
                });
            })
            .catch(err => {
                listContainer.innerHTML = '<div class="loading-placeholder color-danger">Error loading history records.</div>';
                console.error(err);
            });
    }

    // Load and Display Task Results
    function viewTaskResult(taskId) {
        fetch(`${apiBaseUrl}/tasks/${taskId}/status`)
            .then(res => res.json())
            .then(task => {
                showPanel(resultsPanel);
                
                // Set Header Details
                const dateText = new Date(task.last_updated).toLocaleString();
                resultTimestamp.textContent = dateText;
                resultTitle.textContent = task.description || 'Scan Results';
                resultTaskId.textContent = taskId;
                
                const summary = task.result_summary;
                if (!summary) {
                    // Task failed or is incomplete
                    valTotalRecords.textContent = task.records_processed || '0';
                    valAnomaliesDetected.textContent = 'N/A';
                    valAvgScore.textContent = '0.00';
                    valExecutionTime.textContent = 'N/A';
                    resultAlertBadge.className = 'badge warning';
                    resultAlertBadge.textContent = task.status;
                    clinicalAlertsContainer.innerHTML = `<div class="loading-placeholder">Task ended with status: ${task.status}. ${task.error || ''}</div>`;
                    return;
                }
                
                // Renders completed diagnostic metrics
                valTotalRecords.textContent = summary.total_records.toLocaleString();
                valAnomaliesDetected.textContent = summary.anomalies_detected;
                valAvgScore.textContent = summary.avg_anomaly_score.toFixed(3);
                valExecutionTime.textContent = `${task.execution_time_ms} ms`;
                
                // Set Clinical Alert Severity levels
                const highCount = summary.high_severity || 0;
                legendHigh.textContent = highCount;
                legendMedium.textContent = summary.medium_severity || 0;
                legendLow.textContent = summary.low_severity || 0;
                
                if (highCount >= 5) {
                    resultAlertBadge.className = 'badge critical';
                    resultAlertBadge.textContent = 'CRITICAL EMERGENCY';
                    document.querySelector('.metric-card.danger-glow').classList.add('active');
                } else if (highCount >= 2) {
                    resultAlertBadge.className = 'badge warning';
                    resultAlertBadge.textContent = 'VITAL ALERT REVIEW';
                    document.querySelector('.metric-card.danger-glow').classList.remove('active');
                } else {
                    resultAlertBadge.className = 'badge normal';
                    resultAlertBadge.textContent = 'Vitals Healthy';
                    document.querySelector('.metric-card.danger-glow').classList.remove('active');
                }
                
                // Renders clinical alert list
                renderPatientAlerts(summary.top_anomalous_records || []);
                
                // Build Charts
                renderVitalsCharts(summary);
            })
            .catch(err => {
                console.error(err);
            });
    }

    // Render Patient Cards inside alert box
    function renderPatientAlerts(records) {
        clinicalAlertsContainer.innerHTML = '';
        
        if (records.length === 0) {
            clinicalAlertsContainer.innerHTML = '<div class="loading-placeholder">No anomalous records found. Vitals are optimal.</div>';
            return;
        }
        
        records.forEach(rec => {
            const card = document.createElement('div');
            const severityClass = rec.severity.toLowerCase(); // 'high', 'medium', 'low'
            card.className = `patient-card severity-${severityClass}`;
            
            const v = rec.vitals;
            
            // Evaluates abnormal flags
            const isHrAbnormal = v.heart_rate > 100 || v.heart_rate < 60;
            const isO2Abnormal = v.oxygen_saturation < 95;
            const isBpAbnormal = v.systolic_bp > 140 || v.systolic_bp < 90 || v.diastolic_bp > 90 || v.diastolic_bp < 60;
            const isTempAbnormal = v.temperature > 37.5 || v.temperature < 36.0;
            
            // Generates recommendations
            const recommendation = getClinicalRecommendation(v);
            
            card.innerHTML = `
                <div class="patient-header">
                    <div class="patient-title-box">
                        <i data-lucide="user" class="patient-icon"></i>
                        <h4>Patient Record #${rec.record_id}</h4>
                    </div>
                    <span class="score-badge">Isolation Score: ${rec.score.toFixed(3)}</span>
                </div>
                <div class="vitals-grid-cards">
                    <div class="vital-metric ${isHrAbnormal ? 'anomaly-v' : ''}">
                        <span class="label">Heart Rate</span>
                        <span class="val">${Math.round(v.heart_rate)} bpm</span>
                    </div>
                    <div class="vital-metric ${isO2Abnormal ? 'anomaly-v' : ''}">
                        <span class="label">Oxygen (SpO2)</span>
                        <span class="val">${v.oxygen_saturation.toFixed(1)}%</span>
                    </div>
                    <div class="vital-metric ${isBpAbnormal ? 'anomaly-v' : ''}">
                        <span class="label">Blood Pressure</span>
                        <span class="val">${Math.round(v.systolic_bp)}/${Math.round(v.diastolic_bp)}</span>
                    </div>
                    <div class="vital-metric ${isTempAbnormal ? 'anomaly-v' : ''}">
                        <span class="label">Temp</span>
                        <span class="val">${v.temperature.toFixed(1)} °C</span>
                    </div>
                </div>
                <div class="recommendation-box">
                    <i data-lucide="shield-alert"></i>
                    <p>${recommendation}</p>
                </div>
            `;
            clinicalAlertsContainer.appendChild(card);
        });
        lucide.createIcons();
    }

    // Dynamic Clinical Recommendation Engine
    function getClinicalRecommendation(v) {
        if (v.oxygen_saturation < 90) {
            return 'CRITICAL: Severe clinical hypoxia detected. Administer high-flow supplemental oxygen immediately. Check patient airway responsiveness and alert critical care response team.';
        }
        if (v.heart_rate > 150) {
            return 'CRITICAL: Extreme tachycardia detected. Evaluate hemodynamics. Risk of arrhythmias. Prepare ECG monitoring and notify cardiologist immediately.';
        }
        if (v.temperature > 39.5) {
            return 'WARNING: High hyperthermia/pyrexia. Administer cooling therapy and antipyretics. Assess for acute systemic infections or septic shock conditions.';
        }
        if (v.oxygen_saturation < 95) {
            return 'WARNING: Sub-clinical hypoxia. Monitor breathing patterns and prepare low-flow nasal cannula. Assess arterial oxygenation status.';
        }
        if (v.heart_rate > 100) {
            return 'ALERT: Tachycardia observed. Patient may be experiencing cardiovascular stress, pain, or fever. Assess mental state and fluid balance.';
        }
        if (v.heart_rate < 55) {
            return 'ALERT: Bradycardia observed. Review active medication lists (e.g. beta-blockers) and assess patient perfusion.';
        }
        if (v.systolic_bp > 150) {
            return 'ALERT: Elevated systolic blood pressure (hypertension). Verify patient compliance with cardiovascular therapy and reduce stress triggers.';
        }
        return 'Standard vitals deviation. Monitor clinical logs at regular intervals. Review baseline thresholds.';
    }

    // Draw Chart.js graphs
    function renderVitalsCharts(summary) {
        // Destroy existing scatter chart
        if (scatterChartInstance) {
            scatterChartInstance.destroy();
        }
        
        // Destroy existing donut chart
        if (donutChartInstance) {
            donutChartInstance.destroy();
        }
        
        // 1. Scatter Chart: Heart Rate vs SpO2
        const records = summary.top_anomalous_records || [];
        const scatterData = records.map(rec => ({
            x: rec.vitals.heart_rate,
            y: rec.vitals.oxygen_saturation,
            label: `Patient #${rec.record_id} (${rec.severity})`
        }));
        
        const ctxScatter = document.getElementById('anomalies-scatter-chart').getContext('2d');
        
        // Render reference healthy region & anomaly points
        scatterChartInstance = new Chart(ctxScatter, {
            type: 'scatter',
            data: {
                datasets: [
                    {
                        label: 'Clinical Anomaly Records',
                        data: scatterData,
                        backgroundColor: '#EF4444',
                        borderColor: 'rgba(239, 68, 68, 0.8)',
                        pointRadius: 6,
                        pointHoverRadius: 8
                    },
                    {
                        label: 'Optimal Clinical Baseline',
                        data: [{x: 80, y: 98.5}], // Single center point representing normal baseline
                        backgroundColor: '#10B981',
                        borderColor: 'rgba(16, 185, 129, 0.8)',
                        pointRadius: 10,
                        pointStyle: 'crossRot',
                        borderWidth: 3
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        labels: { color: '#94A3B8', font: { family: 'Plus Jakarta Sans' } }
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                if (context.datasetIndex === 0) {
                                    const pt = scatterData[context.dataIndex];
                                    return `${pt.label}: HR=${Math.round(pt.x)} bpm, SpO2=${pt.y.toFixed(1)}%`;
                                }
                                return 'Healthy Vital Baseline Central Target (HR: 80, SpO2: 98.5)';
                            }
                        }
                    }
                },
                scales: {
                    x: {
                        title: { display: true, text: 'Heart Rate (bpm)', color: '#94A3B8' },
                        grid: { color: 'rgba(255,255,255,0.03)' },
                        ticks: { color: '#94A3B8' },
                        min: 30,
                        max: 220
                    },
                    y: {
                        title: { display: true, text: 'Oxygen Saturation (SpO2 %)', color: '#94A3B8' },
                        grid: { color: 'rgba(255,255,255,0.03)' },
                        ticks: { color: '#94A3B8' },
                        min: 50,
                        max: 102
                    }
                }
            }
        });
        
        // 2. Donut Chart: Severity Breakdown
        const ctxDonut = document.getElementById('severity-donut-chart').getContext('2d');
        const highVal = summary.high_severity || 0;
        const medVal = summary.medium_severity || 0;
        const lowVal = summary.low_severity || 0;
        
        donutChartInstance = new Chart(ctxDonut, {
            type: 'doughnut',
            data: {
                labels: ['High', 'Medium', 'Low'],
                datasets: [{
                    data: [highVal, medVal, lowVal],
                    backgroundColor: ['#EF4444', '#F59E0B', '#10B981'],
                    borderColor: '#0B0F19',
                    borderWidth: 2,
                    hoverOffset: 4
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                cutout: '70%',
                plugins: {
                    legend: {
                        display: false // We use our own custom Legend list underneath
                    }
                }
            }
        });
    }

    // Toggle active panel view
    function showPanel(panelElement) {
        [welcomePanel, progressPanel, resultsPanel].forEach(panel => {
            panel.classList.remove('active');
        });
        panelElement.classList.add('active');
    }
});
