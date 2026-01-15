/**
 * Real-Time Progress Tracking Module
 * Handles polling for session progress updates and displays them in real-time
 */

class ProgressTracker {
    constructor(sessionId, options = {}) {
        this.sessionId = sessionId;
        this.pollInterval = options.pollInterval || 3000; // 3 seconds
        this.maxRetries = options.maxRetries || 5;
        this.retries = 0;
        this.isPolling = false;
        this.lastUpdateTime = null;

        // Callback functions
        this.onUpdate = options.onUpdate || (() => { });
        this.onComplete = options.onComplete || (() => { });
        this.onError = options.onError || (() => { });
        this.onStatsUpdate = options.onStatsUpdate || (() => { });

        // DOM elements
        this.progressContainer = options.progressContainer;
        this.statsContainer = options.statsContainer;
        this.errorContainer = options.errorContainer;

        this.setupEventListeners();
    }

    /**
     * Start polling for progress updates
     */
    startPolling() {
        if (this.isPolling) return;

        this.isPolling = true;
        this.retries = 0;
        this.pollProgress();
    }

    /**
     * Stop polling
     */
    stopPolling() {
        this.isPolling = false;
        if (this.pollTimer) {
            clearTimeout(this.pollTimer);
        }
    }

    /**
     * Poll for progress updates
     */
    async pollProgress() {
        if (!this.isPolling) return;

        try {
            const params = new URLSearchParams();
            if (this.lastUpdateTime) {
                params.append('since', this.lastUpdateTime);
            }

            const response = await fetch(
                `/screening/sessions/${this.sessionId}/progress-updates/?${params}`,
                {
                    headers: {
                        'X-Requested-With': 'XMLHttpRequest',
                    },
                    credentials: 'same-origin',
                }
            );

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }

            const data = await response.json();

            if (!data.success) {
                throw new Error(data.message || 'Unknown error');
            }

            // Process updates
            if (data.updates && data.updates.length > 0) {
                this.processUpdates(data.updates);
                this.lastUpdateTime = data.timestamp;
            }

            // Update session stats
            if (data.session) {
                this.updateStats(data.session);
            }

            // Reset retry counter on success
            this.retries = 0;

            // Check if we should stop polling (session complete)
            if (data.session && data.session.session_status === 'completed') {
                this.isPolling = false;
                this.onComplete(data.session);
            }

        } catch (error) {
            console.error('Progress polling error:', error);
            this.retries++;

            if (this.retries >= this.maxRetries) {
                this.isPolling = false;
                const errorMsg = `Failed to fetch progress after ${this.maxRetries} attempts`;
                this.onError(errorMsg);
                this.displayError(errorMsg);
                return;
            }

            // Exponential backoff on error
            const backoffDelay = Math.min(this.pollInterval * Math.pow(2, this.retries - 1), 30000);
            this.pollTimer = setTimeout(() => this.pollProgress(), backoffDelay);
            return;
        }

        // Schedule next poll
        if (this.isPolling) {
            this.pollTimer = setTimeout(() => this.pollProgress(), this.pollInterval);
        }
    }

    /**
     * Process and display progress updates
     */
    processUpdates(updates) {
        updates.forEach(update => {
            this.onUpdate(update);
            this.displayUpdate(update);
        });
    }

    /**
     * Display a single progress update
     */
    displayUpdate(update) {
        if (!this.progressContainer) return;

        const updateEl = document.createElement('div');
        updateEl.className = `progress-update progress-${update.status}`;
        updateEl.dataset.updateId = update.id;
        updateEl.innerHTML = `
            <div class="update-header">
                <span class="update-type" data-type="${update.type}">${this.formatUpdateType(update.type)}</span>
                <span class="update-time">${this.formatTime(update.timestamp)}</span>
            </div>
            <div class="update-content">
                <div class="update-title">${update.title}</div>
                ${update.message ? `<div class="update-message">${update.message}</div>` : ''}
                ${update.progress !== undefined && update.progress !== null ? `
                    <div class="progress-bar-container">
                        <div class="progress-bar" style="width: ${update.progress}%"></div>
                        <span class="progress-text">${update.progress}%</span>
                    </div>
                ` : ''}
                ${update.current && update.total ? `
                    <div class="progress-count">${update.current} / ${update.total}</div>
                ` : ''}
                ${update.error ? `<div class="update-error">${update.error}</div>` : ''}
            </div>
            <div class="update-status" data-status="${update.status}">${this.formatStatus(update.status)}</div>
        `;

        // Insert at the beginning of the container
        if (this.progressContainer.firstChild) {
            this.progressContainer.insertBefore(updateEl, this.progressContainer.firstChild);
        } else {
            this.progressContainer.appendChild(updateEl);
        }

        // Trigger animation
        requestAnimationFrame(() => {
            updateEl.classList.add('fade-in');
        });

        // Remove old updates (keep only last 20)
        const updateEls = this.progressContainer.querySelectorAll('.progress-update');
        if (updateEls.length > 20) {
            for (let i = 20; i < updateEls.length; i++) {
                updateEls[i].remove();
            }
        }
    }

    /**
     * Update session statistics
     */
    updateStats(stats) {
        if (!this.statsContainer) return;

        this.onStatsUpdate(stats);

        const statsHtml = `
            <div class="stat-item">
                <div class="stat-label">Total Resumes</div>
                <div class="stat-value">${stats.total_resumes}</div>
            </div>
            <div class="stat-item">
                <div class="stat-label">Processed</div>
                <div class="stat-value">${stats.processed_resumes}</div>
            </div>
            <div class="stat-item">
                <div class="stat-label">Results</div>
                <div class="stat-value">${stats.results_count}</div>
            </div>
            <div class="stat-item">
                <div class="stat-label">Status</div>
                <div class="stat-value">${stats.session_status}</div>
            </div>
        `;

        this.statsContainer.innerHTML = statsHtml;
    }

    /**
     * Display error message
     */
    displayError(message) {
        if (!this.errorContainer) {
            console.error('Error:', message);
            return;
        }

        const errorEl = document.createElement('div');
        errorEl.className = 'progress-error alert alert-danger';
        errorEl.innerHTML = `
            <strong>Error:</strong> ${message}
            <button type="button" class="btn-close" data-dismiss="alert"></button>
        `;

        this.errorContainer.appendChild(errorEl);

        // Auto-remove after 10 seconds
        setTimeout(() => {
            errorEl.classList.add('fade-out');
            setTimeout(() => errorEl.remove(), 300);
        }, 10000);
    }

    /**
     * Fetch current session stats immediately
     */
    async fetchStats() {
        try {
            const response = await fetch(
                `/screening/sessions/${this.sessionId}/stats/`,
                {
                    headers: {
                        'X-Requested-With': 'XMLHttpRequest',
                    },
                    credentials: 'same-origin',
                }
            );

            if (!response.ok) throw new Error(`HTTP ${response.status}`);

            const data = await response.json();

            if (data.success && data.stats) {
                this.updateStats(data.stats);
            }

            return data.stats;

        } catch (error) {
            console.error('Stats fetch error:', error);
        }
    }

    /**
     * Create a progress update manually
     */
    async createUpdate(updateData) {
        try {
            const csrfToken = this.getCookie('csrftoken');
            const response = await fetch(
                `/screening/sessions/${this.sessionId}/create-update/`,
                {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': csrfToken,
                        'X-Requested-With': 'XMLHttpRequest',
                    },
                    body: JSON.stringify(updateData),
                    credentials: 'same-origin',
                }
            );

            if (!response.ok) throw new Error(`HTTP ${response.status}`);

            const data = await response.json();
            return data;

        } catch (error) {
            console.error('Create update error:', error);
            throw error;
        }
    }

    /**
     * Format update type for display
     */
    formatUpdateType(type) {
        const typeMap = {
            'upload_started': 'Upload Started',
            'screening_started': 'Screening Started',
            'screening_progress': 'Screening Progress',
            'result_analyzed': 'Result Analyzed',
            'export_started': 'Export Started',
            'export_completed': 'Export Completed',
            'export_failed': 'Export Failed',
            'pipeline_push_started': 'Pipeline Push',
            'pipeline_push_completed': 'Pipeline Pushed',
            'error_occurred': 'Error',
        };
        return typeMap[type] || type;
    }

    /**
     * Format status for display
     */
    formatStatus(status) {
        const statusMap = {
            'running': '⏳ Running',
            'completed': '✓ Completed',
            'failed': '✗ Failed',
            'paused': '⏸ Paused',
        };
        return statusMap[status] || status;
    }

    /**
     * Format ISO timestamp for display
     */
    formatTime(isoString) {
        const date = new Date(isoString);
        const now = new Date();
        const diffSeconds = Math.floor((now - date) / 1000);

        if (diffSeconds < 60) return 'just now';
        if (diffSeconds < 3600) return `${Math.floor(diffSeconds / 60)}m ago`;
        if (diffSeconds < 86400) return `${Math.floor(diffSeconds / 3600)}h ago`;

        return date.toLocaleDateString();
    }

    /**
     * Get CSRF token from cookies
     */
    getCookie(name) {
        const value = `; ${document.cookie}`;
        const parts = value.split(`; ${name}=`);
        if (parts.length === 2) return parts.pop().split(';').shift();
    }

    /**
     * Setup DOM event listeners
     */
    setupEventListeners() {
        // Listen for error dismissal
        document.addEventListener('click', (e) => {
            if (e.target.classList.contains('btn-close')) {
                e.target.closest('.progress-error')?.remove();
            }
        });
    }
}

// Export for use in templates
if (typeof window !== 'undefined') {
    window.ProgressTracker = ProgressTracker;
}
