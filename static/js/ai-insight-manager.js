/**
 * AI Insights Management Module
 * Handles generation, retrieval, and feedback for AI-generated insights
 */

class AIInsightManager {
    constructor(options = {}) {
        this.sessionId = options.sessionId;
        this.onInsightGenerated = options.onInsightGenerated || (() => { });
        this.onBatchComplete = options.onBatchComplete || (() => { });
        this.onError = options.onError || (() => { });
        this.insightsContainer = options.insightsContainer;
    }

    /**
     * Generate a single insight for a result
     */
    async generateInsight(resultId, insightType) {
        try {
            const csrfToken = this.getCookie('csrftoken');

            const response = await fetch(
                `/screening/sessions/${this.sessionId}/generate-insight/`,
                {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': csrfToken,
                        'X-Requested-With': 'XMLHttpRequest',
                    },
                    body: JSON.stringify({
                        result_id: resultId,
                        insight_type: insightType,
                    }),
                    credentials: 'same-origin',
                }
            );

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }

            const data = await response.json();

            if (!data.success) {
                throw new Error(data.message || 'Failed to generate insight');
            }

            this.onInsightGenerated({
                resultId: resultId,
                insightType: insightType,
                insight: data,
            });

            return data;

        } catch (error) {
            console.error('Insight generation error:', error);
            this.onError(error.message);
            throw error;
        }
    }

    /**
     * Generate insights for multiple results
     */
    async batchGenerateInsights(resultIds, insightTypes) {
        try {
            const csrfToken = this.getCookie('csrftoken');

            const response = await fetch(
                `/screening/sessions/${this.sessionId}/batch-insights/`,
                {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': csrfToken,
                        'X-Requested-With': 'XMLHttpRequest',
                    },
                    body: JSON.stringify({
                        result_ids: resultIds,
                        insight_types: insightTypes,
                    }),
                    credentials: 'same-origin',
                }
            );

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }

            const data = await response.json();

            if (!data.success) {
                throw new Error(data.message || 'Batch generation failed');
            }

            this.onBatchComplete({
                created: data.insights_created,
                errors: data.errors,
                total: data.total_created,
            });

            return data;

        } catch (error) {
            console.error('Batch insight error:', error);
            this.onError(error.message);
            throw error;
        }
    }

    /**
     * Retrieve insights for a result
     */
    async getInsights(resultId, insightType = null) {
        try {
            const params = new URLSearchParams();
            if (insightType) {
                params.append('type', insightType);
            }

            const response = await fetch(
                `/screening/results/${resultId}/insights/?${params}`,
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
                throw new Error(data.message || 'Failed to retrieve insights');
            }

            return data.insights;

        } catch (error) {
            console.error('Retrieve insights error:', error);
            throw error;
        }
    }

    /**
     * Approve an insight
     */
    async approveInsight(insightId) {
        try {
            const csrfToken = this.getCookie('csrftoken');

            const response = await fetch(
                `/screening/insights/${insightId}/approve/`,
                {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': csrfToken,
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
                throw new Error(data.message || 'Failed to approve insight');
            }

            return data;

        } catch (error) {
            console.error('Approve insight error:', error);
            this.onError(error.message);
            throw error;
        }
    }

    /**
     * Submit feedback on an insight
     */
    async submitFeedback(insightId, rating, comment = '') {
        try {
            const csrfToken = this.getCookie('csrftoken');

            const response = await fetch(
                `/screening/insights/${insightId}/feedback/`,
                {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': csrfToken,
                        'X-Requested-With': 'XMLHttpRequest',
                    },
                    body: JSON.stringify({
                        insight_id: insightId,
                        rating: rating,
                        comment: comment,
                    }),
                    credentials: 'same-origin',
                }
            );

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }

            const data = await response.json();

            if (!data.success) {
                throw new Error(data.message || 'Failed to submit feedback');
            }

            return data;

        } catch (error) {
            console.error('Feedback error:', error);
            this.onError(error.message);
            throw error;
        }
    }

    /**
     * Display insight content
     */
    displayInsight(insight) {
        if (!this.insightsContainer) return;

        const insightEl = document.createElement('div');
        insightEl.className = `insight-card insight-${insight.type}`;
        insightEl.dataset.insightId = insight.id;

        let contentHtml = '';

        // Render content based on type
        if (insight.type === 'interview_questions') {
            const questions = insight.content.questions || [];
            contentHtml = `
                <div class="insight-questions">
                    ${questions.map((q, idx) => `
                        <div class="question-item">
                            <div class="question-number">Q${idx + 1}.</div>
                            <div class="question-text">${q.question || q}</div>
                            ${q.category ? `<span class="question-category">${q.category}</span>` : ''}
                        </div>
                    `).join('')}
                </div>
            `;
        } else if (insight.type === 'ai_notes') {
            const notes = insight.content.notes || [];
            contentHtml = `
                <div class="insight-notes">
                    ${notes.map(n => `
                        <div class="note-item">
                            <strong>${n.title || 'Note'}:</strong> ${n.content || n}
                        </div>
                    `).join('')}
                    ${insight.content.summary ? `<p class="note-summary">${insight.content.summary}</p>` : ''}
                </div>
            `;
        } else if (insight.type === 'rejection_reasons') {
            const reasons = insight.content.reasons || [];
            contentHtml = `
                <div class="insight-reasons">
                    ${reasons.map(r => `
                        <div class="reason-item">
                            <strong>${r.title || 'Reason'}:</strong> ${r.description || r}
                            ${r.severity ? `<span class="severity-${r.severity}">${r.severity}</span>` : ''}
                        </div>
                    `).join('')}
                    ${insight.content.recommendation ? `<p class="reason-recommendation">${insight.content.recommendation}</p>` : ''}
                </div>
            `;
        } else if (insight.type === 'resume_parsing') {
            const parsed = insight.content.parsed_data || {};
            contentHtml = `
                <div class="insight-parsing">
                    ${parsed.name ? `<p><strong>Name:</strong> ${parsed.name}</p>` : ''}
                    ${parsed.email ? `<p><strong>Email:</strong> ${parsed.email}</p>` : ''}
                    ${parsed.phone ? `<p><strong>Phone:</strong> ${parsed.phone}</p>` : ''}
                    ${parsed.skills ? `<p><strong>Skills:</strong> ${Array.isArray(parsed.skills) ? parsed.skills.join(', ') : parsed.skills}</p>` : ''}
                    ${parsed.summary ? `<p><strong>Summary:</strong> ${parsed.summary}</p>` : ''}
                </div>
            `;
        }

        insightEl.innerHTML = `
            <div class="insight-header">
                <h4 class="insight-title">${insight.title}</h4>
                <span class="insight-type-badge">${this.formatType(insight.type)}</span>
                <span class="insight-confidence">${Math.round(insight.confidence * 100)}%</span>
            </div>
            <div class="insight-content">
                ${contentHtml}
            </div>
            <div class="insight-footer">
                <div class="insight-actions">
                    <button class="btn btn-sm btn-primary approve-insight" data-insight-id="${insight.id}">
                        ${insight.is_approved ? '✓ Approved' : 'Approve'}
                    </button>
                    <button class="btn btn-sm btn-secondary feedback-insight" data-insight-id="${insight.id}">
                        Feedback
                    </button>
                </div>
                <span class="insight-timestamp">${new Date(insight.created_at).toLocaleDateString()}</span>
            </div>
        `;

        this.insightsContainer.appendChild(insightEl);

        // Attach event listeners
        insightEl.querySelector('.approve-insight').addEventListener('click', () => {
            this.approveInsight(insight.id).catch(e => console.error(e));
        });

        insightEl.querySelector('.feedback-insight').addEventListener('click', () => {
            this.showFeedbackModal(insight.id);
        });
    }

    /**
     * Show feedback submission modal
     */
    showFeedbackModal(insightId) {
        const modal = document.createElement('div');
        modal.className = 'modal fade';
        modal.id = `feedback-modal-${insightId}`;
        modal.innerHTML = `
            <div class="modal-dialog">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title">Submit Feedback</h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                    </div>
                    <div class="modal-body">
                        <div class="mb-3">
                            <label class="form-label">Rating</label>
                            <select class="form-select feedback-rating">
                                <option value="">-- Select --</option>
                                <option value="helpful">Helpful</option>
                                <option value="partially_helpful">Partially Helpful</option>
                                <option value="not_helpful">Not Helpful</option>
                                <option value="incorrect">Incorrect</option>
                            </select>
                        </div>
                        <div class="mb-3">
                            <label class="form-label">Comment (optional)</label>
                            <textarea class="form-control feedback-comment" rows="3"></textarea>
                        </div>
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Close</button>
                        <button type="button" class="btn btn-primary submit-feedback">Submit</button>
                    </div>
                </div>
            </div>
        `;

        document.body.appendChild(modal);

        const bootstrapModal = new bootstrap.Modal(modal);
        bootstrapModal.show();

        modal.querySelector('.submit-feedback').addEventListener('click', async () => {
            const rating = modal.querySelector('.feedback-rating').value;
            const comment = modal.querySelector('.feedback-comment').value;

            if (!rating) {
                alert('Please select a rating');
                return;
            }

            try {
                await this.submitFeedback(insightId, rating, comment);
                bootstrapModal.hide();
                modal.remove();
                alert('Thank you for your feedback!');
            } catch (error) {
                console.error('Feedback submission error:', error);
            }
        });
    }

    /**
     * Format insight type for display
     */
    formatType(type) {
        const typeMap = {
            'interview_questions': 'Interview Questions',
            'ai_notes': 'AI Notes',
            'rejection_reasons': 'Rejection Analysis',
            'resume_parsing': 'Resume Parsing',
        };
        return typeMap[type] || type;
    }

    /**
     * Get CSRF token from cookies
     */
    getCookie(name) {
        const value = `; ${document.cookie}`;
        const parts = value.split(`; ${name}=`);
        if (parts.length === 2) return parts.pop().split(';').shift();
    }
}

// Export for use
if (typeof window !== 'undefined') {
    window.AIInsightManager = AIInsightManager;
}
