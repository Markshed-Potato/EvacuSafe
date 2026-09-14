document.addEventListener('DOMContentLoaded', function () {
    const pw1 = document.getElementById('id_password1');
    const pw2 = document.getElementById('id_password2');
    const submitBtn = document.querySelector('.auth-container button[type="submit"]');

    if (pw1 && pw2 && submitBtn) {
        function checkMatch() {
            if (pw2.value && pw1.value !== pw2.value) {
                pw2.setCustomValidity('Passwords do not match');
            } else {
                pw2.setCustomValidity('');
            }
        }
        pw1.addEventListener('input', checkMatch);
        pw2.addEventListener('input', checkMatch);
    }
});
