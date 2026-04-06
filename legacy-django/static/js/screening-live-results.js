/**
 * Screening Live Results Updater
 * Updates screening results in real-time as they complete via WebSocket
 */

class ScreeningLiveResultsUpdater {
    constructor(screeningId, options = {}) {
        this.screeningId = screeningId;
        this.wsManager = options.wsManager || new WebSocketManager();
        this.resultsContainerId = options.resultsContainerId || 'screening-results-preview';
        this.autoUpdate = options.autoUpdate !== false;
        this.pollInterval = options.pollInterval || 5000; // Fallback poll interval
        this.pollTimer = null;

        this.handlers = {
            result_update: (data) => this.handleResultUpdate(data),
            screening_state: (data) => this.handleScreeningState(data),
            screening_complete: (data) => this.handleScreeningComplete(data),
            screening_error: (data) => this.handleScreeningError(data)
        };
    }

    /**
     * Start monitoring screening results
     */
    start() {
        const endpoint = `/ws/screening/${this.screeningId}/`;
        this.wsManager.connect(endpoint, `screening_results_${this.screeningId}`, this.handlers);
        console.log(`[Live Results] Started monitoring for ${this.screeningId}`);

        // Fallback: poll for updates every 5 seconds if WebSocket fails
        this.startPolling();
    }

    /**
     * Stop monitoring
     */
    stop() {
        this.wsManager.disconnect(`screening_results_${this.screeningId}`);
        this.stopPolling();
        console.log(`[Live Results] Stopped monitoring for ${this.screeningId}`);
    }

    /**
     * Start polling for result updates (fallback)
     */
    startPolling() {
        this.stopPolling();
        this.pollTimer = setInterval(() => {
            this.fetchLatestResults();
        }, this.pollInterval);
    }

    /**
     * Stop polling
     */
    stopPolling() {
        if (this.pollTimer) {
            clearInterval(this.pollTimer);
            this.pollTimer = null;
        }
    }

    /**
     * Handle result update from WebSocket
     */
    handleResultUpdate(data) {
        console.log('[Result Update]:', data);
        const result = data.result;

        if (result) {
            this.updateResultInUI(result);
        }
    }

    /**
     * Handle screening completion
     */
    handleScreeningComplete(data) {
        console.log('[Screening Complete]:', data);
        this.stopPolling(); // Stop polling when done
        this.fetchLatestResults(); // Final refresh
        window.dispatchEvent(new CustomEvent('screening_results_complete', { detail: data }));
    }

    /**
     * Handle screening error
     */
    handleScreeningError(data) {
        console.error('[Screening Error]:', data.message);
        window.dispatchEvent(new CustomEvent('screening_results_error', { detail: data }));
    }

    /**
     * Handle initial screening state
     */
    handleScreeningState(data) {
        console.log('[Screening State]:', data.data);
        // Initial state received
    }

    /**
     * Fetch latest results from API
     */
    async fetchLatestResults() {
        try {
            const response = await fetch(`/screening/api/sessions/${this.screeningId}/results/?limit=10`);
            if (!response.ok) {
                console.error('Failed to fetch results:', response.status);
                return;
            }

            const data = await response.json();
            if (data.success && data.results) {
                this.renderResults(data.results, data);

                // Dispatch event for other components
                window.dispatchEvent(new CustomEvent('screening_results_fetched', {
                    detail: data
                }));
            }
        } catch (error) {
            console.error('[Live Results] Fetch error:', error);
        }
    }

    /**
     * Update a single result in the UI
     */
    updateResultInUI(result) {
        const resultElement = document.querySelector(`[data-result-id="${result.id}"]`);

        if (resultElement) {
            // Update match score
            const scoreElement = resultElement.querySelector('.match-score-value');
            if (scoreElement) {
                scoreElement.textContent = `${result.match_score}%`;

                // Update color based on score
                const scoreContainer = resultElement.querySelector('.match-score-container');
                if (scoreContainer) {
                    scoreContainer.classList.remove('score-low', 'score-medium', 'score-high');
                    if (result.match_score >= 80) {
                        scoreContainer.classList.add('score-high');
                    } else if (result.match_score >= 60) {
                        scoreContainer.classList.add('score-medium');
                    } else {
                        scoreContainer.classList.add('score-low');
                    }
                }
            }

            // Update progress bar
            const progressBar = resultElement.querySelector('.match-progress-bar');
            if (progressBar) {
                progressBar.style.width = `${result.match_score}%`;
            }

            // Update status
            const statusElement = resultElement.querySelector('.result-status');
            if (statusElement && result.status) {
                statusElement.textContent = result.status.charAt(0).toUpperCase() + result.status.slice(1);
                statusElement.className = `result-status status-${result.status}`;
            }

            // Add animation
            resultElement.classList.add('result-updated');
            setTimeout(() => resultElement.classList.remove('result-updated'), 500);
        } else {
            console.log(`[Live Results] Element not found for result ${result.id}, refreshing all results`);
            this.fetchLatestResults();
        }
    }

    /**
     * Render all results
     */
    renderResults(results, metadata) {
        const container = document.getElementById(this.resultsContainerId);
        if (!container) return;

        // Update each result row
        results.forEach(result => {
            const resultElement = container.querySelector(`[data-result-id="${result.id}"]`);
            if (resultElement) {
                this.updateResultInUI(result);
            }
        });

        // Update session stats if available
        if (metadata.session_status) {
            this.updateSessionStats(metadata);
        }
    }

    /**
     * Update session statistics display
     */
    updateSessionStats(metadata) {
        // Update average score
        const avgScoreElement = document.querySelector('[data-stat="average-score"]');
        if (avgScoreElement && metadata.average_match_score !== null) {
            avgScoreElement.textContent = `${Math.round(metadata.average_match_score)}%`;
        }

        // Update processed resumes count
        const processedElement = document.querySelector('[data-stat="processed-resumes"]');
        if (processedElement) {
            processedElement.textContent = metadata.processed_resumes || 0;
        }

        // Update progress bar
        const progressBar = document.querySelector('[data-stat="session-progress-bar"]');
        if (progressBar && metadata.total_resumes > 0) {
            const progress = (metadata.processed_resumes / metadata.total_resumes) * 100;
            progressBar.style.width = `${progress}%`;
            progressBar.setAttribute('aria-valuenow', progress);
        }

        // Update session status
        const statusElement = document.querySelector('[data-stat="session-status"]');
        if (statusElement) {
            statusElement.textContent = metadata.session_status.charAt(0).toUpperCase() + metadata.session_status.slice(1);
            statusElement.className = `session-status status-${metadata.session_status}`;
        }
    }
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', function () {
    const screeningId = document.querySelector('[data-screening-id]')?.dataset.screeningId;
    if (!screeningId) return;

    // Check if we're on a screening detail page
    const resultsContainer = document.getElementById('screening-results-preview');
    if (!resultsContainer) return;

    // Initialize live results updater
    const updater = new ScreeningLiveResultsUpdater(screeningId, {
        resultsContainerId: 'screening-results-preview'
    });

    updater.start();

    // Make available globally for manual control
    window.screeningLiveResultsUpdater = updater;

    // Listen for completion event
    window.addEventListener('screening_complete', function () {
        console.log('[Live Results] Screening completed, stopping updates');
        updater.stop();

        // Refresh page to show final results
        setTimeout(() => location.reload(), 2000);
    });
});
