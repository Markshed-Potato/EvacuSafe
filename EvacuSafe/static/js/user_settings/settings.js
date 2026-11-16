document.addEventListener('DOMContentLoaded', function () {
    const darkToggle = document.querySelector('input[name="dark_mode"]');
    if (!darkToggle) return;

    // Live preview: swap the real dark theme class (no invert/hue-rotate hacks).
    // The actual preference is persisted server-side in UserSettings and applied
    // on every page load via the "dark-mode" class rendered in base.html.
    darkToggle.addEventListener('change', function () {
        document.body.classList.toggle('dark-mode', darkToggle.checked);
        document.body.classList.toggle('light-mode', !darkToggle.checked);
    });
});
