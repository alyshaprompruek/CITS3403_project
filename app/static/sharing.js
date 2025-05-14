// 打开分享弹窗
function openNewShareModal() {
    document.getElementById('newShareModal').classList.remove('hidden');
}

// 关闭分享弹窗
function closeNewShareModal() {
    document.getElementById('newShareModal').classList.add('hidden');
}

// 提交分享信息
async function confirmNewShare() {
    const email = document.getElementById('shareEmailInput').value;
    const expiry = document.getElementById('expiryDateInput').value;

    const response = await fetch('/api/create-share', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email: email, expiry: expiry })
    });

    const result = await response.json();
    if (result.success) {
        alert('分享成功！');
        window.location.reload();
    } else {
        alert('分享失败：' + result.message);
    }

    closeNewShareModal();
}