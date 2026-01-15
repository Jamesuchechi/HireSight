document.addEventListener('DOMContentLoaded', function () {
    const container = document.getElementById('education-widget');
    const hiddenInput = document.getElementById('id_education_json');
    const addBtn = document.getElementById('education-add-btn');
    const institutionInput = document.getElementById('education-new-institution');
    const degreeInput = document.getElementById('education-new-degree');
    const fieldInput = document.getElementById('education-new-field');
    const startInput = document.getElementById('education-new-start');
    const endInput = document.getElementById('education-new-end');
    if (!container || !hiddenInput || !addBtn) return;
    let items = [];
    try {
        items = JSON.parse(hiddenInput.value || '[]');
    } catch (e) {
        items = [];
    }
    function render() {
        container.innerHTML = '';
        items.forEach((it, idx) => {
            const card = document.createElement('div');
            card.className = 'p-3 rounded-xl bg-gray-50 border border-gray-100 mb-3';
            const title = document.createElement('div');
            title.className = 'flex justify-between items-start';
            const left = document.createElement('div');
            left.innerHTML = '<div class="font-semibold text-gray-900">' + (it.degree || '') + ' in ' + (it.field || '') + '</div><div class="text-sm text-gray-600">' + (it.institution || '') + ' • ' + (it.start_year || '') + (it.end_year ? ' - ' + it.end_year : '') + '</div>';
            const btn = document.createElement('button');
            btn.type = 'button';
            btn.className = 'text-sm text-red-600 hover:underline';
            btn.textContent = 'Remove';
            btn.addEventListener('click', function () {
                items.splice(idx, 1);
                updateHidden();
                render();
                saveRemote();
            });
            title.appendChild(left);
            title.appendChild(btn);
            card.appendChild(title);
            container.appendChild(card);
        });
        if (items.length === 0) {
            const hint = document.createElement('p');
            hint.className = 'text-sm text-gray-500';
            hint.textContent = 'No education entries yet. Add your degrees and institutions.';
            container.appendChild(hint);
        }
    }
    function updateHidden() {
        hiddenInput.value = JSON.stringify(items);
    }
    function getCookie(name) {
        const value = '; ' + document.cookie;
        const parts = value.split('; ' + name + '=');
        if (parts.length === 2) return parts.pop().split(';').shift();
    }
    async function saveRemote() {
        try {
            const resp = await fetch('/accounts/api/profile/education/save/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
                    'X-CSRFToken': getCookie('csrftoken') || ''
                },
                body: new URLSearchParams({ education_json: JSON.stringify(items) })
            });
            const data = await resp.json();
            if (!data.ok) console.warn('Failed to save education', data);
        } catch (err) {
            console.error('Error saving education:', err);
        }
    }
    addBtn.addEventListener('click', function (e) {
        e.preventDefault();
        const institution = institutionInput.value.trim();
        const degree = degreeInput.value.trim();
        const field = fieldInput.value.trim();
        const start = startInput.value.trim();
        const end = endInput.value.trim();
        if (!degree && !institution) return;
        items.push({ institution, degree, field, start_year: start, end_year: end });
        institutionInput.value = '';
        degreeInput.value = '';
        fieldInput.value = '';
        startInput.value = '';
        endInput.value = '';
        updateHidden();
        render();
        saveRemote();
    });
    render();
    updateHidden();
});