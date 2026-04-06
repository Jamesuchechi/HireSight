/**
 * HireSight Screening Analytics Charts
 * Chart.js initialization and rendering for analytics dashboard
 */

// Color schemes matching HireSight branding
const colors = {
    primary: '#6366f1',
    secondary: '#ec4899',
    success: '#10b981',
    warning: '#f59e0b',
    danger: '#ef4444',
    info: '#3b82f6',
    purple: '#a855f7',
};

// Chart color gradients for score distribution
const scoreColors = [
    '#ef4444', // 0-59: Red (poor)
    '#f59e0b', // 60-69: Orange (fair)
    '#eab308', // 70-79: Yellow (good)
    '#3b82f6', // 80-89: Blue (very good)
    '#10b981', // 90-100: Green (excellent)
];

/**
 * Initialize all charts
 */
function initializeCharts(data) {
    // Score Distribution Chart
    if (document.getElementById('scoreDistributionChart')) {
        createScoreDistributionChart(data.scoreDistribution);
    }

    // Processing Status Pie Chart
    if (document.getElementById('statusPieChart')) {
        createStatusPieChart(data.statusPie);
    }

    // Experience Distribution Chart
    if (document.getElementById('experienceChart')) {
        createExperienceChart(data.experienceDistribution);
    }

    // Top Skills Chart
    if (document.getElementById('topSkillsChart')) {
        createTopSkillsChart(data.topSkills);
    }
}

/**
 * Create Score Distribution Histogram
 */
function createScoreDistributionChart(data) {
    const ctx = document.getElementById('scoreDistributionChart').getContext('2d');

    const labels = Object.keys(data);
    const values = Object.values(data);

    new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [
                {
                    label: 'Number of Candidates',
                    data: values,
                    backgroundColor: scoreColors,
                    borderColor: scoreColors,
                    borderWidth: 2,
                    borderRadius: 8,
                    barThickness: 40,
                },
            ],
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                legend: {
                    display: false,
                },
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        stepSize: 1,
                        callback: function (value) {
                            return value.toFixed(0);
                        },
                    },
                    grid: {
                        color: 'rgba(0, 0, 0, 0.05)',
                    },
                },
                x: {
                    grid: {
                        display: false,
                    },
                },
            },
        },
    });
}

/**
 * Create Processing Status Pie Chart
 */
function createStatusPieChart(data) {
    const ctx = document.getElementById('statusPieChart').getContext('2d');

    const labels = ['Completed', 'Failed', 'Pending'];
    const values = [data.completed, data.failed, data.pending];

    // Only show non-zero values
    const filteredLabels = [];
    const filteredValues = [];
    const filteredColors = [];
    const pieColors = ['#10b981', '#ef4444', '#f59e0b'];

    values.forEach((val, idx) => {
        if (val > 0) {
            filteredLabels.push(labels[idx]);
            filteredValues.push(val);
            filteredColors.push(pieColors[idx]);
        }
    });

    new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: filteredLabels,
            datasets: [
                {
                    data: filteredValues,
                    backgroundColor: filteredColors,
                    borderColor: '#fff',
                    borderWidth: 3,
                },
            ],
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: {
                        padding: 20,
                        font: {
                            size: 14,
                        },
                        boxWidth: 12,
                    },
                },
            },
        },
    });
}

/**
 * Create Experience Distribution Bar Chart
 */
function createExperienceChart(data) {
    const ctx = document.getElementById('experienceChart').getContext('2d');

    const labels = Object.keys(data);
    const values = Object.values(data);

    new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels.map(label => label + ' years'),
            datasets: [
                {
                    label: 'Number of Candidates',
                    data: values,
                    backgroundColor: colors.info,
                    borderColor: colors.primary,
                    borderWidth: 2,
                    borderRadius: 8,
                    barThickness: 40,
                },
            ],
        },
        options: {
            indexAxis: 'y', // Horizontal bar chart
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                legend: {
                    display: true,
                    position: 'top',
                },
            },
            scales: {
                x: {
                    beginAtZero: true,
                    ticks: {
                        stepSize: 1,
                    },
                    grid: {
                        color: 'rgba(0, 0, 0, 0.05)',
                    },
                },
                y: {
                    grid: {
                        display: false,
                    },
                },
            },
        },
    });
}

/**
 * Create Top Matched Skills Bar Chart
 */
function createTopSkillsChart(data) {
    const ctx = document.getElementById('topSkillsChart').getContext('2d');

    const labels = Object.keys(data);
    const values = Object.values(data);

    if (labels.length === 0) {
        // If no skills, show empty state
        ctx.fillStyle = '#6b7280';
        ctx.font = '14px sans-serif';
        ctx.textAlign = 'center';
        ctx.fillText('No skills data available', ctx.canvas.width / 2, ctx.canvas.height / 2);
        return;
    }

    new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [
                {
                    label: 'Times Matched',
                    data: values,
                    backgroundColor: colors.success,
                    borderColor: colors.success,
                    borderWidth: 2,
                    borderRadius: 8,
                    barThickness: 40,
                },
            ],
        },
        options: {
            indexAxis: 'y', // Horizontal bar chart
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                legend: {
                    display: true,
                    position: 'top',
                },
            },
            scales: {
                x: {
                    beginAtZero: true,
                    ticks: {
                        stepSize: 1,
                    },
                    grid: {
                        color: 'rgba(0, 0, 0, 0.05)',
                    },
                },
                y: {
                    grid: {
                        display: false,
                    },
                },
            },
        },
    });
}

/**
 * Format large numbers with commas
 */
function formatNumber(num) {
    return num.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ',');
}

/**
 * Export chart as image (bonus feature)
 */
function exportChartAsImage(chartId) {
    const canvas = document.getElementById(chartId);
    const image = canvas.toDataURL('image/png');
    const link = document.createElement('a');
    link.href = image;
    link.download = `${chartId}-${new Date().toISOString().split('T')[0]}.png`;
    link.click();
}
