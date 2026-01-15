/**
 * Pipeline Integration Module
 * Handles pushing candidates to hiring pipeline and managing pipeline status
 */

const PipelineManager = (() => {
    'use strict';

    // Configuration
    const API_ENDPOINTS = {
        pushSingle: (sessionId) => `/screening/sessions/${sessionId}/push-pipeline/`,
        bulkPush: (sessionId) => `/screening/sessions/${sessionId}/bulk-push-pipeline/`,
        statusUpdate: '/screening/pipeline/status-update/',
    };

    // State
    let selectedResults = [];
    let sessionId = null;

    /**
     * Initialize the pipeline manager
     */
    function init(session_id) {
        sessionId = session_id;
        attachEventListeners();
        console.log('PipelineManager initialized for session:', sessionId);
    }

    /**
     * Attach event listeners to UI elements
     */
    function attachEventListeners() {
        // Push to Pipeline button
        const pushBtn = document.querySelector('[data-action="push-to-pipeline"]');
        if (pushBtn) {
            pushBtn.addEventListener('click', handlePushClick);
        }

        // Bulk Push button
        const bulkPushBtn = document.querySelector('[data-action="bulk-push-pipeline"]');
        if (bulkPushBtn) {
            bulkPushBtn.addEventListener('click', handleBulkPushClick);
        }

        // Pipeline status update buttons
        document.querySelectorAll('[data-pipeline-status]').forEach(btn => {
            btn.addEventListener('click', handleStatusUpdate);
        });
    }

    /**
     * Handle single candidate push to pipeline
     */
    function handlePushClick(event) {
        event.preventDefault();
        const resultId = event.currentTarget.dataset.resultId;

        if (!resultId) {
            Notifications.error('Result ID not found');
            return;
        }

        showPipelineJobModal([resultId]);
    }

    /**
     * Handle bulk push to pipeline
     */
    function handleBulkPushClick(event) {
        event.preventDefault();

        // Get selected results
        const checkboxes = document.querySelectorAll('input[name="result_checkbox"]:checked');
        const resultIds = Array.from(checkboxes).map(cb => cb.value);

        if (resultIds.length === 0) {
            Notifications.warning('Please select at least one candidate');
            return;
        }

        showBulkPipelineModal(resultIds);
    }

    /**
     * Show modal for selecting job and push settings
     */
    function showPipelineJobModal(resultIds) {
        const modal = document.createElement('div');
        modal.className = 'fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50';
        modal.id = 'pipeline-job-modal';

        const content = `
            <div class="bg-white rounded-lg p-8 max-w-md w-full mx-4">
                <h3 class="text-lg font-bold mb-4">Push to Pipeline</h3>
                
                <div class="mb-4">
                    <label class="block text-sm font-medium mb-2">Select Job</label>
                    <select id="pipeline-job-select" class="form-select w-full rounded-md border-gray-300">
                        <option value="">-- Select a job --</option>
                    </select>
                </div>

                <div class="mb-4">
                    <label class="flex items-center">
                        <input type="checkbox" id="pipeline-include-notes" class="form-checkbox rounded" checked>
                        <span class="ml-2 text-sm">Include screening notes</span>
                    </label>
                </div>

                <div class="mb-6">
                    <label class="block text-sm font-medium mb-2">Message (optional)</label>
                    <textarea id="pipeline-message" 
                        class="form-textarea w-full rounded-md border-gray-300" 
                        rows="3" 
                        placeholder="Optional message..."></textarea>
                </div>

                <div class="flex gap-3 justify-end">
                    <button class="px-4 py-2 text-gray-700 border border-gray-300 rounded-md hover:bg-gray-50"
                        onclick="document.getElementById('pipeline-job-modal').remove()">
                        Cancel
                    </button>
                    <button class="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
                        onclick="PipelineManager.submitPush('${resultIds.join(',')}')">
                        Push to Pipeline
                    </button>
                </div>
            </div>
        `;

        modal.innerHTML = content;
        document.body.appendChild(modal);

        // Load available jobs
        loadAvailableJobs();

        // Close on background click
        modal.addEventListener('click', (e) => {
            if (e.target === modal) modal.remove();
        });
    }

    /**
     * Show modal for bulk push with strategy selection
     */
    function showBulkPipelineModal(resultIds) {
        const modal = document.createElement('div');
        modal.className = 'fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50';
        modal.id = 'bulk-pipeline-modal';

        const content = `
            <div class="bg-white rounded-lg p-8 max-w-lg w-full mx-4">
                <h3 class="text-lg font-bold mb-4">Bulk Push to Pipeline</h3>
                <p class="text-sm text-gray-600 mb-4">Selected: ${resultIds.length} candidate(s)</p>
                
                <div class="mb-4">
                    <label class="block text-sm font-medium mb-2">Target Jobs</label>
                    <select id="pipeline-jobs-select" class="form-select w-full rounded-md border-gray-300" multiple size="4">
                    </select>
                    <p class="text-xs text-gray-500 mt-1">Hold Ctrl/Cmd to select multiple</p>
                </div>

                <div class="mb-4">
                    <label class="block text-sm font-medium mb-2">Push Strategy</label>
                    <div class="space-y-2">
                        <label class="flex items-center">
                            <input type="radio" name="strategy" value="best_match" class="form-radio" checked>
                            <span class="ml-2 text-sm">Best Match Job (auto-select)</span>
                        </label>
                        <label class="flex items-center">
                            <input type="radio" name="strategy" value="all" class="form-radio">
                            <span class="ml-2 text-sm">All Selected Jobs</span>
                        </label>
                        <label class="flex items-center">
                            <input type="radio" name="strategy" value="filtered" class="form-radio">
                            <span class="ml-2 text-sm">Only Matching (70%+ score)</span>
                        </label>
                    </div>
                </div>

                <div class="mb-6">
                    <label class="flex items-center">
                        <input type="checkbox" id="pipeline-notify" class="form-checkbox rounded" checked>
                        <span class="ml-2 text-sm">Notify recruiters</span>
                    </label>
                </div>

                <div class="flex gap-3 justify-end">
                    <button class="px-4 py-2 text-gray-700 border border-gray-300 rounded-md hover:bg-gray-50"
                        onclick="document.getElementById('bulk-pipeline-modal').remove()">
                        Cancel
                    </button>
                    <button class="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
                        onclick="PipelineManager.submitBulkPush('${resultIds.join(',')}')">
                        Push All
                    </button>
                </div>
            </div>
        `;

        modal.innerHTML = content;
        document.body.appendChild(modal);

        // Load available jobs
        loadAvailableJobs('#pipeline-jobs-select');

        // Close on background click
        modal.addEventListener('click', (e) => {
            if (e.target === modal) modal.remove();
        });
    }

    /**
     * Load available jobs from server
     */
    function loadAvailableJobs(selector = '#pipeline-job-select') {
        // This would typically fetch from an API endpoint
        // For now, populate from data attributes if available
        const jobsData = document.querySelector('[data-available-jobs]');
        if (jobsData) {
            try {
                const jobs = JSON.parse(jobsData.dataset.availableJobs);
                const select = document.querySelector(selector);

                jobs.forEach(job => {
                    const option = document.createElement('option');
                    option.value = job.id;
                    option.textContent = job.title;
                    select.appendChild(option);
                });
            } catch (e) {
                console.error('Error loading jobs:', e);
            }
        }
    }

    /**
     * Submit single push request
     */
    function submitPush(resultIds) {
        const jobId = document.getElementById('pipeline-job-select').value;
        const includeNotes = document.getElementById('pipeline-include-notes').checked;
        const message = document.getElementById('pipeline-message').value;

        if (!jobId) {
            Notifications.error('Please select a job');
            return;
        }

        const data = {
            result_ids: resultIds.split(','),
            job_id: jobId,
            include_notes: includeNotes,
            message: message,
        };

        fetch(API_ENDPOINTS.pushSingle(sessionId), {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken'),
            },
            body: JSON.stringify(data),
        })
            .then(response => response.json())
            .then(result => {
                document.getElementById('pipeline-job-modal').remove();

                if (result.success) {
                    Notifications.success(result.message);
                    setTimeout(() => location.reload(), 1500);
                } else {
                    Notifications.error(result.message);
                }
            })
            .catch(error => {
                Notifications.error('Error pushing to pipeline: ' + error.message);
                console.error(error);
            });
    }

    /**
     * Submit bulk push request
     */
    function submitBulkPush(resultIds) {
        const jobSelect = document.getElementById('pipeline-jobs-select');
        const jobs = Array.from(jobSelect.selectedOptions).map(opt => opt.value);
        const strategy = document.querySelector('input[name="strategy"]:checked').value;
        const notify = document.getElementById('pipeline-notify').checked;

        if (jobs.length === 0) {
            Notifications.error('Please select at least one job');
            return;
        }

        const formData = new FormData();
        formData.append('result_ids', resultIds);
        jobs.forEach(jobId => formData.append('jobs', jobId));
        formData.append('strategy', strategy);
        formData.append('notify_recruiters', notify);
        formData.append('csrfmiddlewaretoken', getCookie('csrftoken'));

        fetch(API_ENDPOINTS.bulkPush(sessionId), {
            method: 'POST',
            headers: {
                'X-CSRFToken': getCookie('csrftoken'),
            },
            body: formData,
        })
            .then(response => {
                if (response.redirected) {
                    window.location = response.url;
                } else {
                    return response.json().then(data => {
                        if (data.success) {
                            Notifications.success('Candidates pushed to pipeline');
                            setTimeout(() => location.reload(), 1500);
                        } else {
                            Notifications.error(data.message || 'Error pushing candidates');
                        }
                    });
                }
            })
            .catch(error => {
                Notifications.error('Error: ' + error.message);
                console.error(error);
            });
    }

    /**
     * Handle pipeline status update
     */
    function handleStatusUpdate(event) {
        event.preventDefault();

        const resultId = event.currentTarget.dataset.resultId;
        const newStatus = event.currentTarget.dataset.pipelineStatus;

        if (!resultId || !newStatus) return;

        const notes = prompt(`Update notes (optional):`);

        const data = {
            result_id: resultId,
            status: newStatus,
            notes: notes || '',
        };

        fetch(API_ENDPOINTS.statusUpdate, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken'),
            },
            body: JSON.stringify(data),
        })
            .then(response => response.json())
            .then(result => {
                if (result.success) {
                    Notifications.success(result.message);
                    // Update UI to show new status
                    updateStatusUI(resultId, result.status);
                } else {
                    Notifications.error(result.message);
                }
            })
            .catch(error => {
                Notifications.error('Error updating status: ' + error.message);
                console.error(error);
            });
    }

    /**
     * Update UI to reflect status change
     */
    function updateStatusUI(resultId, newStatus) {
        const statusElement = document.querySelector(`[data-result-status="${resultId}"]`);
        if (statusElement) {
            statusElement.textContent = newStatus;
            statusElement.className = getStatusClass(newStatus);
        }
    }

    /**
     * Get CSS class for status badge
     */
    function getStatusClass(status) {
        const classes = {
            'Pending': 'inline-block px-3 py-1 rounded bg-yellow-100 text-yellow-800 text-sm',
            'Pushed to Pipeline': 'inline-block px-3 py-1 rounded bg-blue-100 text-blue-800 text-sm',
            'Hired': 'inline-block px-3 py-1 rounded bg-green-100 text-green-800 text-sm',
            'Rejected from Pipeline': 'inline-block px-3 py-1 rounded bg-red-100 text-red-800 text-sm',
            'Withdrawn': 'inline-block px-3 py-1 rounded bg-gray-100 text-gray-800 text-sm',
        };
        return classes[status] || 'inline-block px-3 py-1 rounded bg-gray-100 text-gray-800 text-sm';
    }

    /**
     * Get CSRF token
     */
    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }

    // Public API
    return {
        init,
        submitPush,
        submitBulkPush,
        handlePushClick,
        handleBulkPushClick,
        handleStatusUpdate,
    };
})();

// Initialize when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        const sessionId = document.querySelector('[data-session-id]')?.dataset.sessionId;
        if (sessionId) {
            PipelineManager.init(sessionId);
        }
    });
} else {
    const sessionId = document.querySelector('[data-session-id]')?.dataset.sessionId;
    if (sessionId) {
        PipelineManager.init(sessionId);
    }
}
