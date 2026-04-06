document.addEventListener('DOMContentLoaded', function () {
    const container = document.getElementById('skills-widget');
    const hiddenInput = document.getElementById('id_skills_json');
    const addBtn = document.getElementById('skills-add-btn');
    const nameInput = document.getElementById('skills-new-name');
    const profSelect = document.getElementById('skills-new-proficiency');

    if (!container || !hiddenInput) return;

    let skills = [];

    try {
        const raw = hiddenInput.value || '[]';
        skills = JSON.parse(raw);
    } catch (e) {
        skills = [];
    }

    function render() {
        container.innerHTML = '';
        skills.forEach((s, idx) => {
            const item = document.createElement('div');
            item.className = 'flex items-center justify-between gap-3 mb-3';

            const left = document.createElement('div');
            left.className = 'flex items-center gap-3';

            const badge = document.createElement('div');
            badge.className = 'px-3 py-1 rounded-full bg-gray-100 text-sm text-gray-800 font-medium';
            badge.textContent = s.skill || '';

            const prof = document.createElement('div');
            prof.className = 'text-xs text-gray-500';
            prof.textContent = s.proficiency || '';

            left.appendChild(badge);
            left.appendChild(prof);

            const removeBtn = document.createElement('button');
            removeBtn.type = 'button';
            removeBtn.className = 'text-sm text-red-600 hover:underline';
            removeBtn.textContent = 'Remove';
            removeBtn.addEventListener('click', function () {
                skills.splice(idx, 1);
                updateHidden();
                render();
                saveRemote();
            });

            item.appendChild(left);
            item.appendChild(removeBtn);

            container.appendChild(item);
        });

        if (skills.length === 0) {
            const hint = document.createElement('p');
            hint.className = 'text-sm text-gray-500';
            hint.textContent = 'No skills added yet. Add your top skills with a proficiency level.';
            container.appendChild(hint);
        }
    }

    function updateHidden() {
        hiddenInput.value = JSON.stringify(skills);
    }

    function getCookie(name) {
        const value = `; ${document.cookie}`;
        const parts = value.split(`; ${name}=`);
        if (parts.length === 2) return parts.pop().split(';').shift();
    }

    async function saveRemote() {
        try {
            const resp = await fetch('/accounts/api/profile/skills/save/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
                    'X-CSRFToken': getCookie('csrftoken') || ''
                },
                body: new URLSearchParams({ skills_json: JSON.stringify(skills) })
            });
            const data = await resp.json();
            if (!data.ok) {
                console.warn('Failed to save skills remotely', data);
            }
        } catch (err) {
            console.error('Error saving skills:', err);
        }
    }

    addBtn.addEventListener('click', function (e) {
        e.preventDefault();
        const name = nameInput.value.trim();
        const prof = profSelect.value;
        if (!name) return;
        skills.push({ skill: name, proficiency: prof });
        nameInput.value = '';
        profSelect.value = 'intermediate';
        updateHidden();
        render();
        saveRemote();
    });

    // Initial render
    render();
    updateHidden();
});
