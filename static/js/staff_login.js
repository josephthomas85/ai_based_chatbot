document.addEventListener('DOMContentLoaded', () => {
    const form = document.getElementById('staffLoginForm');
    if (!form) return;
    
    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        const username = document.getElementById('username').value.trim();
        const password = document.getElementById('password').value;
        const errMsg = document.getElementById('errorMessage');
        
        try {
            const res = await fetch('/api/staff/login', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ username, password })
            });
            const data = await res.json();
            
            if (data.success) {
                window.location.href = '/staff/dashboard';
            } else {
                errMsg.textContent = data.message || "Invalid credentials.";
                errMsg.style.color = "#777777";
                errMsg.style.marginTop = "10px";
            }
        } catch (e) {
            errMsg.textContent = "Network error occurred.";
        }
    });
});
