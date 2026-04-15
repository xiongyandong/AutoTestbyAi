function confirmDelete(url, name) {
    if (confirm('确定要删除 "' + name + '" 吗？此操作不可恢复。')) {
        $.ajax({
            url: url,
            method: 'POST',
            data: { csrfmiddlewaretoken: getCookie('csrftoken') },
            success: function() {
                location.reload();
            },
            error: function(xhr) {
                alert('删除失败: ' + (xhr.responseJSON?.error || '未知错误'));
            }
        });
    }
}

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
