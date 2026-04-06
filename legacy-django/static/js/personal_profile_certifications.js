document.addEventListener('DOMContentLoaded', function () {
    const container = document.getElementById('certifications-widget');
    const hiddenInput = document.getElementById('id_certifications_json');
    const addBtn = document.getElementById('certifications-add-btn');
    const nameInput = document.getElementById('certifications-new-name');
    const issuerInput = document.getElementById('certifications-new-issuer');
    const dateInput = document.getElementById('certifications-new-date');
    const urlInput = document.getElementById('certifications-new-url');

    if (!container || !hiddenInput) return;

    let certifications = [];

    try {
        const raw = hiddenInput.value || '[]';
        certifications = JSON.parse(raw);
    } catch (e) {
        certifications = [];
    }

    function render() {
        container.innerHTML = '';
        certifications.forEach((cert, idx) => {
            const item = document.createElement('div');
            item.className = 'flex items-center justify-between gap-3 mb-3';

            const left = document.createElement('div');
            left.className = 'flex items-center gap-3';

            const badge = document.createElement('div');
            badge.className = 'px-3 py-1 rounded-full bg-gray-100 text-sm text-gray-800 font-medium';
            badge.textContent = cert.name || '';

            const issuer = document.createElement('div');
            issuer.className = 'text-xs text-gray-500';
            issuer.textContent = cert.issuer ? `by ${cert.issuer}` : '';

            const date = document.createElement('div');
            date.className = 'text-xs text-gray-400';
            date.textContent = cert.date || '';

            left.appendChild(badge);
            left.appendChild(issuer);
            left.appendChild(date);

            const removeBtn = document.createElement('button');
            removeBtn.type = 'button';
            removeBtn.className = 'text-sm text-red-600 hover:underline';
            removeBtn.textContent = 'Remove';
            removeBtn.addEventListener('click', function () {
                certifications.splice(idx, 1);
                updateHidden();
                render();
                saveRemote();
            });

            item.appendChild(left);
            item.appendChild(removeBtn);

            container.appendChild(item);
        });

        if (certifications.length === 0) {
            const hint = document.createElement('p');
            hint.className = 'text-sm text-gray-500';
            hint.textContent = 'No certifications added yet. Add your professional certifications.';
            container.appendChild(hint);
        }
    }

    function updateHidden() {
        hiddenInput.value = JSON.stringify(certifications);
    }

    function getCookie(name) {
        const value = `; ${document.cookie}`;
        const parts = value.split(`; ${name}=`);
        if (parts.length === 2) return parts.pop().split(';').shift();
    }

    async function saveRemote() {
        try {
            const resp = await fetch('/accounts/api/profile/certifications/save/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
                    'X-CSRFToken': getCookie('csrftoken') || ''
                },
                body: new URLSearchParams({ certifications_json: JSON.stringify(certifications) })
            });
            const data = await resp.json();
            if (!data.ok) {
                console.warn('Failed to save certifications remotely', data);
            }
        } catch (err) {
            console.error('Error saving certifications:', err);
        }
    }

    addBtn.addEventListener('click', function (e) {
        e.preventDefault();
        const name = nameInput.value.trim();
        const issuer = issuerInput.value.trim();
        const date = dateInput.value.trim();
        const url = urlInput.value.trim();

        if (!name) return;

        certifications.push({
            name: name,
            issuer: issuer,
            date: date,
            url: url
        });

        nameInput.value = '';
        issuerInput.value = '';
        dateInput.value = '';
        urlInput.value = '';

        updateHidden();
        render();
        saveRemote();
    });

    // Initial render
    render();
    updateHidden();
});