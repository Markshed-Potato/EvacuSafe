document.addEventListener('DOMContentLoaded', function () {
    const badge = document.getElementById('system-status-badge');
    if (!badge) return;

    function tick() {
        const now = new Date();
        badge.title = 'Last checked: ' + now.toLocaleTimeString();
    }
    tick();
    setInterval(tick, 30000);
});
