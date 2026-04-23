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

function initAppToasts() {
    document.querySelectorAll('.app-toast').forEach(function(toastEl) {
        const toast = new bootstrap.Toast(toastEl, {
            autohide: true,
            delay: 2000
        });
        toast.show();
    });
}

function initAuthRequiredValidation() {
    const forms = document.querySelectorAll('.auth-card form');
    if (!forms.length) return;

    const requiredErrorTexts = ['这个字段是必填项', '此字段是必填项', 'This field is required'];

    function isRequiredErrorText(text) {
        return requiredErrorTexts.some(function(pattern) {
            return text.indexOf(pattern) !== -1;
        });
    }

    function toggleRequiredState(input, forceShow) {
        const value = (input.value || '').trim();
        const requiredFeedback = input.parentElement.querySelector('.required-feedback');
        const serverErrors = Array.from(input.parentElement.querySelectorAll('.invalid-feedback:not(.required-feedback)'));
        const hasNonRequiredServerError = serverErrors.some(function(node) {
            return !isRequiredErrorText((node.textContent || '').trim());
        });

        serverErrors.forEach(function(node) {
            const isRequiredError = isRequiredErrorText((node.textContent || '').trim());
            if (isRequiredError) {
                node.hidden = value !== '' || !forceShow;
            }
        });

        if (requiredFeedback) {
            requiredFeedback.hidden = !(forceShow && value === '');
        }

        if (value !== '') {
            if (!hasNonRequiredServerError) {
                input.classList.remove('is-invalid');
            }
            return true;
        }

        if (forceShow) {
            input.classList.add('is-invalid');
        }
        return false;
    }

    forms.forEach(function(form) {
        const requiredFields = form.querySelectorAll('[data-required-field="true"]');
        if (!requiredFields.length) return;

        requiredFields.forEach(function(input) {
            // 记录页面初始渲染时是否已有服务端错误，避免初始化时清除它
            var initialServerError = input.classList.contains('is-invalid');
            input.addEventListener('input', function() {
                initialServerError = false;
                toggleRequiredState(input, false);
            });
            input.addEventListener('blur', function() {
                toggleRequiredState(input, false);
            });
            if (!initialServerError) {
                toggleRequiredState(input, false);
            }
        });

        form.addEventListener('submit', function(e) {
            let hasEmptyRequired = false;
            requiredFields.forEach(function(input) {
                const isFilled = toggleRequiredState(input, true);
                if (!isFilled) {
                    hasEmptyRequired = true;
                }
            });
            if (hasEmptyRequired) {
                e.preventDefault();
                const firstInvalid = form.querySelector('[data-required-field="true"].is-invalid');
                if (firstInvalid) {
                    firstInvalid.focus();
                }
            }
        });
    });
}

function initPasswordHints() {
    const passwordInput = document.querySelector('[data-password-input="true"]');
    if (!passwordInput) return;

    const rulesBox = document.getElementById(passwordInput.getAttribute('data-password-target'));
    if (!rulesBox) return;
    rulesBox.hidden = true;
    rulesBox.setAttribute('aria-hidden', 'true');

    const usernameInput = document.getElementById('id_username');
    const ruleElements = {
        length: rulesBox.querySelector('[data-rule="length"]'),
        not_numeric: rulesBox.querySelector('[data-rule="not_numeric"]'),
        not_common: rulesBox.querySelector('[data-rule="not_common"]'),
        not_similar: rulesBox.querySelector('[data-rule="not_similar"]'),
    };

    function updateHints() {
        const value = passwordInput.value || '';
        const username = usernameInput ? (usernameInput.value || '').trim().toLowerCase() : '';
        const lowered = value.toLowerCase();
        const commonPasswords = ['12345678', 'password', 'qwerty123', 'admin123', '123123123'];
        const hasValue = value.length > 0;

        const checks = {
            length: value.length >= 8,
            not_numeric: !/^\d+$/.test(value),
            not_common: !commonPasswords.includes(lowered),
            not_similar: !username || !lowered.includes(username),
        };

        const invalidExists = hasValue && Object.values(checks).some(function(result) { return !result; });
        rulesBox.classList.toggle('show', invalidExists);
        rulesBox.hidden = !invalidExists;
        rulesBox.setAttribute('aria-hidden', invalidExists ? 'false' : 'true');

        Object.keys(ruleElements).forEach(function(key) {
            if (!ruleElements[key]) return;
            ruleElements[key].classList.toggle('is-valid', hasValue && checks[key]);
        });
    }

    passwordInput.addEventListener('focus', updateHints);
    passwordInput.addEventListener('input', updateHints);
    if (usernameInput) {
        usernameInput.addEventListener('input', updateHints);
    }

    updateHints();
}

function initPasswordConfirmValidation() {
    const confirmInput = document.querySelector('[data-password-confirm="true"]');
    if (!confirmInput) return;

    const sourceInput = document.getElementById(confirmInput.getAttribute('data-password-source'));
    const feedback = document.getElementById('passwordConfirmFeedback');
    if (!sourceInput || !feedback) return;
    const form = confirmInput.closest('form');
    feedback.hidden = true;
    feedback.setAttribute('aria-hidden', 'true');

    // 记录页面初始渲染时是否已有服务端错误（后端返回的 is-invalid）
    const hasServerError = confirmInput.classList.contains('is-invalid');

    function updateConfirmState(forceShow) {
        const sourceValue = sourceInput.value || '';
        const confirmValue = confirmInput.value || '';
        const hasConfirmValue = confirmValue.length > 0;
        const mismatch = hasConfirmValue && sourceValue !== confirmValue;
        const shouldShow = mismatch && (forceShow || hasConfirmValue);

        // 只有用户开始输入后才接管 is-invalid/is-valid 状态
        if (hasConfirmValue || forceShow) {
            confirmInput.classList.toggle('is-invalid', mismatch);
            confirmInput.classList.toggle('is-valid', hasConfirmValue && !mismatch);
        }
        feedback.classList.toggle('show', shouldShow);
        feedback.hidden = !shouldShow;
        feedback.setAttribute('aria-hidden', shouldShow ? 'false' : 'true');

        if (!mismatch) {
            feedback.textContent = '两次输入的密码不一致';
        }

        return !mismatch;
    }

    sourceInput.addEventListener('input', function() {
        updateConfirmState(false);
    });
    confirmInput.addEventListener('input', function() {
        updateConfirmState(false);
    });
    confirmInput.addEventListener('blur', function() {
        updateConfirmState(true);
    });
    confirmInput.addEventListener('change', function() {
        updateConfirmState(true);
    });

    if (form) {
        form.addEventListener('submit', function() {
            updateConfirmState(true);
        });
    }

    updateConfirmState(false);
}

function initPasswordToggle() {
    document.querySelectorAll('[data-password-toggle="true"]').forEach(function(input) {
        // 用一个专用 wrapper 包裹 input，确保按钮 top:50% 相对 input 高度居中
        var inputWrapper = document.createElement('div');
        inputWrapper.style.cssText = 'position:relative;display:block;';
        input.parentElement.insertBefore(inputWrapper, input);
        inputWrapper.appendChild(input);
        input.style.paddingRight = '2.5rem';

        var btn = document.createElement('button');
        btn.type = 'button';
        btn.setAttribute('aria-label', '切换密码可见性');
        btn.style.cssText = [
            'position:absolute',
            'top:50%',
            'right:10px',
            'transform:translateY(-50%)',
            'background:none',
            'border:none',
            'padding:0',
            'cursor:pointer',
            'color:#6c757d',
            'line-height:1',
            'z-index:5',
        ].join(';');

        var icon = document.createElement('i');
        icon.className = 'bi bi-eye';
        icon.style.fontSize = '1rem';
        btn.appendChild(icon);

        btn.addEventListener('mouseenter', function() { icon.style.color = '#343a40'; });
        btn.addEventListener('mouseleave', function() { icon.style.color = '#6c757d'; });

        btn.addEventListener('click', function() {
            if (input.type === 'password') {
                input.type = 'text';
                icon.className = 'bi bi-eye-slash';
            } else {
                input.type = 'password';
                icon.className = 'bi bi-eye';
            }
            input.focus();
        });

        inputWrapper.appendChild(btn);
    });
}

// --- Auto-init on DOM ready ---
document.addEventListener('DOMContentLoaded', function() {
    initAppToasts();
    initSidebar();
    initAuthRequiredValidation();
    initPasswordHints();
    initPasswordConfirmValidation();
    initPasswordToggle();

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
