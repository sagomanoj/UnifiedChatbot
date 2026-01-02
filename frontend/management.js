const API_URL = 'http://localhost:8000';
let activeingestAppName = null;

document.addEventListener('DOMContentLoaded', () => {
    fetchAppsDetailed();

    document.getElementById('add-app-btn').addEventListener('click', addApp);
    document.getElementById('mgmt-file-upload').addEventListener('change', handleFileUpload);
});

async function fetchAppsDetailed() {
    try {
        const response = await fetch(`${API_URL}/management/apps`);
        const apps = await response.json();
        renderApps(apps);
    } catch (err) {
        console.error('Failed to fetch detailed apps:', err);
    }
}

function renderApps(apps) {
    const list = document.getElementById('apps-list');
    list.innerHTML = '';

    if (apps.length === 0) {
        list.innerHTML = '<tr><td colspan="3">No applications found. Add one above.</td></tr>';
        return;
    }

    apps.forEach(app => {
        const tr = document.createElement('tr');

        const manualStatus = app.manual
            ? `<span class="status-badge has-manual"><i class="fas fa-check"></i> ${app.manual}</span>`
            : `<span class="status-badge">No manual</span>`;

        tr.innerHTML = `
            <td><strong>${app.name}</strong></td>
            <td>${manualStatus}</td>
            <td>
                <div style="display: flex; gap: 0.5rem;">
                    <button class="btn btn-upload" onclick="triggerUpload('${app.name}')">
                        <i class="fas fa-file-upload"></i> ${app.manual ? 'Update' : 'Upload'}
                    </button>
                    <button class="btn btn-danger" onclick="deleteApp('${app.name}')">
                        <i class="fas fa-trash-alt"></i> Delete
                    </button>
                </div>
            </td>
        `;
        list.appendChild(tr);
    });
}

async function addApp() {
    const input = document.getElementById('new-app-name');
    const name = input.value.trim();
    if (!name) return;

    try {
        const response = await fetch(`${API_URL}/management/apps`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ name })
        });

        if (response.ok) {
            input.value = '';
            fetchAppsDetailed();
        }
    } catch (err) {
        console.error('Add app failed:', err);
    }
}

async function deleteApp(name) {
    if (!confirm(`Are you sure you want to delete ${name}?`)) return;

    try {
        const response = await fetch(`${API_URL}/management/apps/${encodeURIComponent(name)}`, {
            method: 'DELETE'
        });
        if (response.ok) fetchAppsDetailed();
    } catch (err) {
        console.error('Delete app failed:', err);
    }
}

function triggerUpload(appName) {
    activeingestAppName = appName;
    document.getElementById('mgmt-file-upload').click();
}

async function handleFileUpload(e) {
    const file = e.target.files[0];
    if (!file || !activeingestAppName) return;

    const formData = new FormData();
    formData.append('file', file);

    const btn = document.querySelector(`button[onclick="triggerUpload('${activeingestAppName}')"]`);
    const originalText = btn.innerHTML;
    btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Processing...';
    btn.disabled = true;

    try {
        const response = await fetch(`${API_URL}/management/upload/${encodeURIComponent(activeingestAppName)}`, {
            method: 'POST',
            body: formData
        });

        if (response.ok) {
            alert(`Manual updated for ${activeingestAppName}`);
            fetchAppsDetailed();
        } else {
            alert('Upload failed. Check server logs.');
        }
    } catch (err) {
        console.error('Upload failed:', err);
        alert('Upload error');
    } finally {
        btn.innerHTML = originalText;
        btn.disabled = false;
        activeingestAppName = null;
        e.target.value = ''; // Reset input
    }
}
