/**
 * HireSight Screening Results UI
 * Handles inline actions, expandable rows, and bulk operations
 */

/**
 * Build a path that includes the current locale prefix (if any).
 * Helps prevent redirect loops when i18n URL patterns require the language slug.
 */
function buildScreeningUrl(path) {
    let normalized = path.startsWith('/') ? path : `/${path}`;
    normalized = normalized.replace(/\/+/g, '/');

    const localeMatch = window.location.pathname.match(/^\/([a-z]{2}(?:-[a-z]{2})?)(?:\/|$)/i);
    const localePrefix = localeMatch ? localeMatch[1] : '';

    if (localePrefix && !normalized.startsWith(`/${localePrefix}/`)) {
        return `/${localePrefix}${normalized}`;
    }

    return normalized;
}

/**
 * Filter and sort results
 */
const ResultsFilter = {
    /**
     * Apply score range filter
     */
    filterByScore: function (minScore, maxScore) {
        const rows = document.querySelectorAll('.result-row');
        rows.forEach(row => {
            const scoreText = row.querySelector('.match-score');
            if (scoreText) {
                const score = parseInt(scoreText.textContent);
                const show = score >= minScore && score <= maxScore;
                row.style.display = show ? '' : 'none';
            }
        });
    },

    /**
     * Apply experience filter
     */
    filterByExperience: function (minYears, maxYears) {
        const rows = document.querySelectorAll('.result-row');
        rows.forEach(row => {
            const expText = row.querySelector('[data-experience]');
            if (expText) {
                const years = parseInt(expText.dataset.experience);
                const show = years >= minYears && years <= maxYears;
                row.style.display = show ? '' : 'none';
            }
        });
    },

    /**
     * Search candidates
     */
    search: function (query) {
        const rows = document.querySelectorAll('.result-row');
        const lowerQuery = query.toLowerCase();

        rows.forEach(row => {
            const name = row.querySelector('[data-candidate-name]');
            const email = row.querySelector('[data-candidate-email]');

            if (name && email) {
                const nameMatch = name.textContent.toLowerCase().includes(lowerQuery);
                const emailMatch = email.textContent.toLowerCase().includes(lowerQuery);
                const show = nameMatch || emailMatch || query === '';
                row.style.display = show ? '' : 'none';
            }
        });
    }
};

/**
 * Experience visualization
 */
const ExperienceVisualization = {
    /**
     * Create experience bar
     */
    createBar: function (years) {
        const percentage = Math.min((years / 20) * 100, 100);
        return `<div class="w-16 h-2 bg-gray-200 rounded-full overflow-hidden">
                    <div class="h-full bg-blue-500 rounded-full" style="width: ${percentage}%"></div>
                </div>`;
    },

    /**
     * Get experience level label
     */
    getLevel: function (years) {
        if (years < 2) return 'Entry Level';
        if (years < 5) return 'Junior';
        if (years < 8) return 'Mid-level';
        if (years < 12) return 'Senior';
        return 'Lead/Principal';
    }
};

/**
 * Skill match visualization
 */
const SkillVisualization = {
    /**
     * Create matched skills list
     */
    createMatchedList: function (skills) {
        if (!skills || skills.length === 0) return '<span class="text-gray-400">No matched skills</span>';

        return skills.map(skill =>
            `<span class="inline-block px-2 py-1 bg-green-100 text-green-800 text-xs rounded-lg mr-1 mb-1">${skill}</span>`
        ).join('');
    },

    /**
     * Create missing skills list
     */
    createGapsList: function (skills) {
        if (!skills || skills.length === 0) return '<span class="text-gray-400">No missing skills</span>';

        return skills.map(skill =>
            `<span class="inline-block px-2 py-1 bg-red-100 text-red-800 text-xs rounded-lg mr-1 mb-1">${skill}</span>`
        ).join('');
    },

    /**
     * Calculate skill match percentage
     */
    calculateMatchPercent: function (matched, required) {
        if (required === 0) return 100;
        return Math.round((matched.length / required) * 100);
    }
};

/**
 * Result detail modal management
 */
const ResultModal = {
    /**
     * Open result detail in modal
     */
    open: function (resultId) {
        // This would open a modal with detailed candidate information
        console.log('Opening result modal for:', resultId);
    },

    /**
     * Close modal
     */
    close: function () {
        const modal = document.querySelector('[role="dialog"]');
        if (modal) {
            modal.remove();
        }
    }
};

/**
 * Comparison utilities
 */
const Comparison = {
    /**
     * Compare two candidates side-by-side
     */
    compare: function (resultId1, resultId2) {
        const row1 = document.querySelector(`.result-row[data-result-id="${resultId1}"]`);
        const row2 = document.querySelector(`.result-row[data-result-id="${resultId2}"]`);

        if (row1 && row2) {
            console.log('Comparing candidates:', resultId1, resultId2);
            // Implementation would open comparison view
        }
    },

    /**
     * Get result data for comparison
     */
    getResultData: function (resultId) {
        const row = document.querySelector(`.result-row[data-result-id="${resultId}"]`);
        if (!row) return null;

        return {
            id: resultId,
            name: row.querySelector('[data-candidate-name]')?.textContent,
            email: row.querySelector('[data-candidate-email]')?.textContent,
            score: parseInt(row.querySelector('.match-score')?.textContent || 0),
            experience: parseInt(row.querySelector('[data-experience]')?.dataset.experience || 0),
            status: row.querySelector('[data-status]')?.textContent.trim()
        };
    }
};

/**
 * Notification system
 */
const Notifications = {
    /**
     * Show toast notification
     */
    show: function (message, type = 'info', duration = 3000) {
        const notification = document.createElement('div');
        const bgColor = {
            success: 'bg-green-500',
            error: 'bg-red-500',
            warning: 'bg-yellow-500',
            info: 'bg-blue-500'
        }[type] || 'bg-blue-500';

        notification.className = `fixed top-4 right-4 px-6 py-4 ${bgColor} text-white rounded-lg shadow-lg z-50 animate-pulse`;
        notification.innerHTML = `<div class="flex items-center">${message}</div>`;
        document.body.appendChild(notification);

        setTimeout(() => {
            notification.style.opacity = '0';
            notification.style.transition = 'opacity 0.3s';
            setTimeout(() => notification.remove(), 300);
        }, duration);
    },

    /**
     * Show error notification
     */
    error: function (message) {
        this.show(message, 'error');
    },

    /**
     * Show success notification
     */
    success: function (message) {
        this.show(message, 'success');
    },

    /**
     * Show info notification
     */
    info: function (message) {
        this.show(message, 'info');
    }
};

/**
 * AJAX utilities for results operations
 */
const ResultsAPI = {
    /**
     * Get CSRF token from page
     */
    getCsrfToken: function () {
        return document.querySelector('[name=csrfmiddlewaretoken]')?.value || '';
    },

    /**
     * Add note to result
     */
    addNote: function (resultId, noteText) {
        return fetch(buildScreeningUrl(`/screening/result/${resultId}/note/`), {
            method: 'POST',
            headers: {
                'X-CSRFToken': this.getCsrfToken(),
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ note: noteText })
        }).then(r => r.json());
    },

    /**
     * Toggle shortlist status
     */
    toggleShortlist: function (resultId, shortlist) {
        return fetch(buildScreeningUrl(`/screening/result/${resultId}/shortlist-toggle/`), {
            method: 'POST',
            headers: {
                'X-CSRFToken': this.getCsrfToken(),
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ shortlist: shortlist })
        }).then(r => r.json());
    },

    /**
     * Bulk shortlist operation
     */
    bulkShortlist: function (resultIds, shortlist) {
        return fetch(buildScreeningUrl('/screening/bulk-shortlist/'), {
            method: 'POST',
            headers: {
                'X-CSRFToken': this.getCsrfToken(),
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                result_ids: resultIds,
                shortlist: shortlist
            })
        }).then(r => r.json());
    },

    /**
     * Get interview questions
     */
    getInterviewQuestions: function (resultId) {
        return fetch(buildScreeningUrl(`/screening/result/${resultId}/interview-questions/`), {
            method: 'GET',
            headers: {
                'X-CSRFToken': this.getCsrfToken(),
                'Accept': 'application/json'
            }
        }).then(r => r.json());
    }
};

/**
 * Sorting utilities
 */
const Sorting = {
    /**
     * Sort results by score
     */
    byScore: function (ascending = false) {
        const rows = Array.from(document.querySelectorAll('.result-row'));
        rows.sort((a, b) => {
            const scoreA = parseInt(a.querySelector('.match-score')?.textContent || 0);
            const scoreB = parseInt(b.querySelector('.match-score')?.textContent || 0);
            return ascending ? scoreA - scoreB : scoreB - scoreA;
        });
        this.updateTableOrder(rows);
    },

    /**
     * Sort by experience
     */
    byExperience: function (ascending = false) {
        const rows = Array.from(document.querySelectorAll('.result-row'));
        rows.sort((a, b) => {
            const expA = parseInt(a.querySelector('[data-experience]')?.dataset.experience || 0);
            const expB = parseInt(b.querySelector('[data-experience]')?.dataset.experience || 0);
            return ascending ? expA - expB : expB - expA;
        });
        this.updateTableOrder(rows);
    },

    /**
     * Sort by name
     */
    byName: function (ascending = true) {
        const rows = Array.from(document.querySelectorAll('.result-row'));
        rows.sort((a, b) => {
            const nameA = a.querySelector('[data-candidate-name]')?.textContent || '';
            const nameB = b.querySelector('[data-candidate-name]')?.textContent || '';
            return ascending ? nameA.localeCompare(nameB) : nameB.localeCompare(nameA);
        });
        this.updateTableOrder(rows);
    },

    /**
     * Update table row order
     */
    updateTableOrder: function (rows) {
        const tbody = document.querySelector('tbody');
        if (tbody) {
            rows.forEach(row => {
                tbody.appendChild(row);
            });
        }
    }
};

/**
 * Export utilities
 */
const Export = {
    /**
     * Export selected results to CSV
     */
    toCSV: function (resultIds) {
        const csvContent = "data:text/csv;charset=utf-8,";
        // Implementation would generate CSV
        console.log('Exporting to CSV:', resultIds);
    },

    /**
     * Export to Excel
     */
    toExcel: function (resultIds) {
        // Implementation would generate Excel file
        console.log('Exporting to Excel:', resultIds);
    },

    /**
     * Export to PDF
     */
    toPDF: function (resultIds) {
        // Implementation would generate PDF
        console.log('Exporting to PDF:', resultIds);
    }
};

/**
 * Initialize results list features
 */
function initializeResultsList(sessionId) {
    // This function is called from the main page script
    console.log('Results list initialized for session:', sessionId);
}

// Export for use in other scripts
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        ResultsFilter,
        ExperienceVisualization,
        SkillVisualization,
        ResultModal,
        Comparison,
        Notifications,
        ResultsAPI,
        Sorting,
        Export
    };
}
