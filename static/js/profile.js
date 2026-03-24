document.addEventListener('DOMContentLoaded', () => {
    loadProfileData();

    // Elements
    const avatarWrapper = document.getElementById('avatarWrapper');
    const photoInput = document.getElementById('photoInput');
    const profileImage = document.getElementById('profileImage');
    const savePhotoBtn = document.getElementById('savePhotoBtn');
    
    // Photo Selection
    avatarWrapper.addEventListener('click', () => {
        photoInput.click();
    });

    photoInput.addEventListener('change', (e) => {
        const file = e.target.files[0];
        if (file) {
            // Preview
            const reader = new FileReader();
            reader.onload = (e) => {
                profileImage.src = e.target.result;
            };
            reader.readAsDataURL(file);
            savePhotoBtn.style.display = 'block';
        }
    });

    // Upload Photo Submit
    savePhotoBtn.addEventListener('click', async () => {
        const file = photoInput.files[0];
        if (!file) return;

        const formData = new FormData();
        formData.append('photo', file);

        showLoading(true);
        try {
            const res = await fetch('/api/user/upload_photo', {
                method: 'POST',
                body: formData
            });
            const data = await res.json();
            if (data.success) {
                alert('Photo uploaded successfully!');
                savePhotoBtn.style.display = 'none';
            } else {
                alert(data.message || 'Error uploading photo.');
            }
        } catch (e) {
            console.error(e);
            alert("Network error.");
        } finally {
            showLoading(false);
        }
    });

    // Profile Details Form Submit
    document.getElementById('profileForm').addEventListener('submit', async (e) => {
        e.preventDefault();
        showLoading(true);
        const msgDiv = document.getElementById('profileMessage');
        msgDiv.textContent = '';

        const payload = {
            fullname: document.getElementById('fullname').value,
            username: document.getElementById('username').value,
            email: document.getElementById('email').value,
            phone: document.getElementById('phone').value
        };

        try {
            const res = await fetch('/api/user/update_profile', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });
            const data = await res.json();
            
            if (data.success) {
                msgDiv.textContent = 'Profile updated successfully!';
                msgDiv.style.color = '#27ae60'; // Standard green for positive impact even in monochrome it looks fine or standard dark color
                msgDiv.style.fontWeight = 'bold';
                document.getElementById('displayFullname').textContent = payload.fullname;
                document.getElementById('displayUsername').textContent = '@' + payload.username;
            } else {
                msgDiv.textContent = data.message || 'Update failed.';
                msgDiv.style.color = '#e74c3c';
            }
        } catch (error) {
            console.error(error);
            msgDiv.textContent = 'Network error during save.';
            msgDiv.style.color = '#e74c3c';
        } finally {
            showLoading(false);
        }
    });
});

async function loadProfileData() {
    showLoading(true);
    try {
        const res = await fetch('/api/user/profile');
        if (res.status === 401) {
            window.location.href = '/login';
            return;
        }
        
        const data = await res.json();
        if (data.success) {
            const u = data.user;
            document.getElementById('fullname').value = u.fullname || '';
            document.getElementById('username').value = u.username || '';
            document.getElementById('email').value = u.email || '';
            document.getElementById('phone').value = u.phone || '';
            document.getElementById('registereddate').value = u.registereddate || '';
            
            document.getElementById('displayFullname').textContent = u.fullname;
            document.getElementById('displayUsername').textContent = '@' + u.username;
            
            if (u.profile_photo) {
                // Prepend base url slash if needed, but the API will return full path like '/static/uploads/...'
                document.getElementById('profileImage').src = u.profile_photo;
            }
        }
    } catch(e) {
        console.error("Failed to load profile data", e);
    } finally {
        showLoading(false);
    }
}

function showLoading(show) {
    document.getElementById('loadingSpinner').style.display = show ? 'flex' : 'none';
}
