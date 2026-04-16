/* =====================================================
   Pytest 测试平台 - 主 JS
   ===================================================== */

// --- CSRF Token ---
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

// --- Delete Confirm Modal ---
function confirmDelete(url, name) {
    const modal = document.getElementById('deleteConfirmModal');
    if (!modal) {
        // Fallback to native confirm if modal not in DOM
        if (confirm('确认删除 "' + name + '"？此操作不可恢复。')) {
            doPostDelete(url);
        }
        return;
    }
    document.getElementById('deleteItemName').textContent = name;
    const confirmBtn = document.getElementById('deleteConfirmBtn');
    confirmBtn.onclick = function() {
        doPostDelete(url);
        bootstrap.Modal.getInstance(modal).hide();
    };
    new bootstrap.Modal(modal).show();
}

function doPostDelete(url) {
    const form = document.createElement('form');
    form.method = 'POST';
    form.action = url;
    const csrf = document.createElement('input');
    csrf.type = 'hidden';
    csrf.name = 'csrfmiddlewaretoken';
    csrf.value = getCookie('csrftoken');
    form.appendChild(csrf);
    document.body.appendChild(form);
    form.submit();
}

// --- JSON Format & Validate ---
function formatJsonField(textareaId) {
    const el = document.getElementById(textareaId);
    if (!el) return;
    try {
        const val = el.value.trim();
        if (!val) return;
        const obj = JSON.parse(val);
        el.value = JSON.stringify(obj, null, 2);
        el.classList.remove('is-invalid');
        el.classList.add('is-valid');
        setTimeout(() => el.classList.remove('is-valid'), 2000);
    } catch (e) {
        el.classList.add('is-invalid');
    }
}

function validateJsonField(textareaId) {
    const el = document.getElementById(textareaId);
    if (!el) return true;
    const val = el.value.trim();
    if (!val) return true;
    try {
        JSON.parse(val);
        el.classList.remove('is-invalid');
        return true;
    } catch (e) {
        el.classList.add('is-invalid');
        return false;
    }
}

// Validate all JSON fields before form submit
function validateAllJsonFields(formId) {
    const form = document.getElementById(formId);
    if (!form) return true;
    let valid = true;
    form.querySelectorAll('textarea[data-json="true"]').forEach(function(el) {
        if (!validateJsonField(el.id)) valid = false;
    });
    return valid;
}

// --- Sidebar Toggle (mobile) ---
function initSidebar() {
    const toggle = document.querySelector('.sidebar-toggle');
    const sidebar = document.querySelector('.sidebar');
    const overlay = document.querySelector('.sidebar-overlay');
    if (!toggle || !sidebar) return;

    toggle.addEventListener('click', function() {
        sidebar.classList.toggle('show');
        if (overlay) overlay.classList.toggle('show');
    });
    if (overlay) {
        overlay.addEventListener('click', function() {
            sidebar.classList.remove('show');
            overlay.classList.remove('show');
        });
    }
}

// --- Auto-init on DOM ready ---
document.addEventListener('DOMContentLoaded', function() {
    initSidebar();

    // Auto-format JSON fields on form submit
    document.querySelectorAll('form[data-json-format="true"]').forEach(function(form) {
        form.addEventListener('submit', function(e) {
            let valid = true;
            form.querySelectorAll('textarea[data-json="true"]').forEach(function(el) {
                const val = el.value.trim();
                if (val) {
                    try {
                        el.value = JSON.stringify(JSON.parse(val), null, 2);
                        el.classList.remove('is-invalid');
                    } catch (err) {
                        el.classList.add('is-invalid');
                        valid = false;
                    }
                }
            });
            if (!valid) {
                e.preventDefault();
                alert('JSON 格式错误，请检查标红的字段');
            }
        });
    });

    // Dismiss alerts after 5s
    document.querySelectorAll('.alert-dismissible').forEach(function(alert) {
        setTimeout(function() {
            const bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        }, 5000);
    });
});
