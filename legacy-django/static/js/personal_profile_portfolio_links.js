document.addEventListener('DOMContentLoaded', function () {
    const container = document.getElementById('portfolio-links-widget');
    const hiddenInput = document.getElementById('id_portfolio_links_json');
    const addBtn = document.getElementById('portfolio-links-add-btn');
    const typeSelect = document.getElementById('portfolio-links-new-type');
    const urlInput = document.getElementById('portfolio-links-new-url');

    if (!container || !hiddenInput) return;

    let portfolioLinks = [];

    try {
        const raw = hiddenInput.value || '[]';
        portfolioLinks = JSON.parse(raw);
    } catch (e) {
        portfolioLinks = [];
    }

    function render() {
        container.innerHTML = '';
        portfolioLinks.forEach((link, idx) => {
            const item = document.createElement('div');
            item.className = 'flex items-center justify-between gap-3 mb-3';

            const left = document.createElement('div');
            left.className = 'flex items-center gap-3';

            const badge = document.createElement('div');
            badge.className = 'px-3 py-1 rounded-full bg-gray-100 text-sm text-gray-800 font-medium';
            badge.textContent = link.type || '';

            const url = document.createElement('div');
            url.className = 'text-xs text-gray-500 truncate max-w-xs';
            url.textContent = link.url || '';

            left.appendChild(badge);
            left.appendChild(url);

            const removeBtn = document.createElement('button');
            removeBtn.type = 'button';
            removeBtn.className = 'text-sm text-red-600 hover:underline';
            removeBtn.textContent = 'Remove';
            removeBtn.addEventListener('click', function () {
                portfolioLinks.splice(idx, 1);
                updateHidden();
                render();
                saveRemote();
            });

            item.appendChild(left);
            item.appendChild(removeBtn);

            container.appendChild(item);
        });

        if (portfolioLinks.length === 0) {
            const hint = document.createElement('p');
            hint.className = 'text-sm text-gray-500';
            hint.textContent = 'No portfolio links added yet. Add links to showcase your work.';
            container.appendChild(hint);
        }
    }

    function updateHidden() {
        hiddenInput.value = JSON.stringify(portfolioLinks);
    }

    function getCookie(name) {
        const value = `; ${document.cookie}`;
        const parts = value.split(`; ${name}=`);
        if (parts.length === 2) return parts.pop().split(';').shift();
    }

    async function saveRemote() {
        try {
            const resp = await fetch('/accounts/api/profile/portfolio-links/save/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
                    'X-CSRFToken': getCookie('csrftoken') || ''
                },
                body: new URLSearchParams({ portfolio_links_json: JSON.stringify(portfolioLinks) })
            });
            const data = await resp.json();
            if (!data.ok) {
                console.warn('Failed to save portfolio links remotely', data);
            }
        } catch (err) {
            console.error('Error saving portfolio links:', err);
        }
    }

    addBtn.addEventListener('click', function (e) {
        e.preventDefault();
        const type = typeSelect.value;
        const url = urlInput.value.trim();

        if (!url) return;

        portfolioLinks.push({
            type: type,
            url: url
        });

        typeSelect.value = 'website';
        urlInput.value = '';

        updateHidden();
        render();
        saveRemote();
    });

    // Initial render
    render();
    updateHidden();
});