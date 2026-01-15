// Company Profile Benefits Chips Management
// Handles add/remove functionality for employee benefits

document.addEventListener('DOMContentLoaded', function () {
    // DOM Elements
    const benefitsContainer = document.getElementById('benefits-chips-container');
    const benefitsInput = document.getElementById('id_benefits_json');
    const addBenefitBtn = document.getElementById('add-benefit-btn');
    const newBenefitInput = document.getElementById('new-benefit-input');

    // Existing benefits data from template
    const existingBenefits = JSON.parse(document.getElementById('existing-benefits-data').textContent);

    // Initialize benefits chips
    function initBenefits() {
        // Clear existing chips
        benefitsContainer.innerHTML = '';

        // Add existing benefits as chips
        existingBenefits.forEach(benefit => {
            addBenefitChip(benefit);
        });

        // Update hidden input
        updateBenefitsInput();
    }

    // Add a benefit chip to the container
    function addBenefitChip(benefitText) {
        if (!benefitText || benefitText.trim() === '') return;

        const chipId = 'benefit-' + Date.now();

        const chipElement = document.createElement('div');
        chipElement.className = 'benefit-chip';
        chipElement.id = chipId;
        chipElement.innerHTML = `
            <span class="benefit-text">${escapeHtml(benefitText)}</span>
            <button type="button" class="remove-benefit-btn" data-chip-id="${chipId}">
                <svg width="16" height="16" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
                </svg>
            </button>
        `;

        benefitsContainer.appendChild(chipElement);

        // Add event listener to remove button
        chipElement.querySelector('.remove-benefit-btn').addEventListener('click', function () {
            removeBenefitChip(chipId);
        });
    }

    // Remove a benefit chip
    function removeBenefitChip(chipId) {
        const chipElement = document.getElementById(chipId);
        if (chipElement) {
            chipElement.remove();
            updateBenefitsInput();
        }
    }

    // Update the hidden input with current benefits
    function updateBenefitsInput() {
        const chips = benefitsContainer.querySelectorAll('.benefit-chip');
        const benefits = [];

        chips.forEach(chip => {
            const text = chip.querySelector('.benefit-text').textContent;
            benefits.push(text);
        });

        benefitsInput.value = JSON.stringify(benefits);
    }

    // Add new benefit from input
    function addNewBenefit() {
        const benefitText = newBenefitInput.value.trim();

        if (benefitText) {
            addBenefitChip(benefitText);
            newBenefitInput.value = '';
            updateBenefitsInput();
        }
    }

    // Handle Enter key in input
    newBenefitInput.addEventListener('keypress', function (e) {
        if (e.key === 'Enter') {
            e.preventDefault();
            addNewBenefit();
        }
    });

    // Add benefit button click
    addBenefitBtn.addEventListener('click', addNewBenefit);

    // Initialize
    initBenefits();

    // Helper function to escape HTML
    function escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
});