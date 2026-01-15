document.addEventListener('DOMContentLoaded', function () {
    const container = document.getElementById('experience-widget');
    const hiddenInput = document.getElementById('id_experience_json');
    const addBtn = document.getElementById('experience-add-btn');

    const roleInput = document.getElementById('experience-new-role');
    const companyInput = document.getElementById('experience-new-company');
    const startInput = document.getElementById('experience-new-start');
    const endInput = document.getElementById('experience-new-end');
    const currentInput = document.getElementById('experience-new-current');
    const descInput = document.getElementById('experience-new-description');

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
            left.innerHTML = `<div class="font-semibold text-gray-900">${it.role || ''}</div><div class="text-sm text-gray-600">${it.company || ''} • ${it.start_date || ''}${it.current ? ' - Present' : (it.end_date ? ' - ' + it.end_date : '')}</div>`;

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

            const desc = document.createElement('div');
            desc.className = 'mt-2 text-sm text-gray-700';
            desc.textContent = it.description || '';

            card.appendChild(title);
            card.appendChild(desc);

            container.appendChild(card);
        });

        if (items.length === 0) {
            const hint = document.createElement('p');
            hint.className = 'text-sm text-gray-500';
            hint.textContent = 'No experience entries yet. Add jobs to build your timeline.';
            container.appendChild(hint);
        }
    }

    function updateHidden() {
        hiddenInput.value = JSON.stringify(items);
    }

    function getCookie(name) {
        const value = `; ${document.cookie}`;
        const parts = value.split(`; ${name}=`);
        if (parts.length === 2) return parts.pop().split(';').shift();
    }

    async function saveRemote() {
        try {
            const resp = await fetch('/accounts/api/profile/experience/save/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
                    'X-CSRFToken': getCookie('csrftoken') || ''
                },
                body: new URLSearchParams({ experience_json: JSON.stringify(items) })
            });
            const data = await resp.json();
            if (!data.ok) console.warn('Failed to save experience', data);
        } catch (err) {
            console.error('Error saving experience:', err);
        }
    }

    addBtn.addEventListener('click', function (e) {
        e.preventDefault();
        const role = roleInput.value.trim();
        const company = companyInput.value.trim();
        const start = startInput.value;
        const end = endInput.value;
        const current = currentInput.checked;
        const desc = descInput.value.trim();

        if (!role && !company) return;

        items.push({ role, company, start_date: start, end_date: end, current, description: desc });

        roleInput.value = '';
        companyInput.value = '';
        startInput.value = '';
        endInput.value = '';
        currentInput.checked = false;
        descInput.value = '';

        updateHidden();
        render();
        saveRemote();
    });

    render();
    updateHidden();
});
