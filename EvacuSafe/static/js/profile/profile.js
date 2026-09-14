document.addEventListener('DOMContentLoaded', function () {
    const fileInput = document.querySelector('input[type="file"][name="avatar"]');
    const preview = document.getElementById('avatar-preview');
    if (!fileInput || !preview) return;

    fileInput.addEventListener('change', function () {
        const file = fileInput.files[0];
        if (!file) return;
        const reader = new FileReader();
        reader.onload = function (e) {
            preview.style.backgroundImage = `url(${e.target.result})`;
            const fallback = preview.querySelector('.avatar-fallback');
            if (fallback) fallback.textContent = '';
        };
        reader.readAsDataURL(file);
    });
});
