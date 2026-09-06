/* 卸载游戏：二次确认后用 POST 请求，成功后刷新页面。
   卸载是软删除（移到"已卸载游戏"），随时可在大厅右上角"🗑️ 已卸载"里还原。 */
function uninstallGame(name, displayName) {
    if (!confirm('确定卸载游戏「' + (displayName || name) + '」吗？\n卸载后会移到"已卸载游戏"中，可随时还原。')) return;
    fetch('/game/uninstall/' + encodeURIComponent(name), { method: 'POST' })
        .then(function (r) {
            if (!r.ok) throw new Error('HTTP ' + r.status);
            location.reload(); // 卸载成功：刷新大厅，卡片消失
        })
        .catch(function () { alert('卸载失败，请重试'); });
}