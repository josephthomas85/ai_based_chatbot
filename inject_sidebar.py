import os
import re

profile_link = '\n                    <li><a href="{{ url_for(\'profile_page\') }}"><span class="icon">👤</span>My Profile</a></li>'

for file in os.listdir('templates'):
    if file.endswith('.html') and file != 'staff_dashboard.html':
        path = os.path.join('templates', file)
        with open(path, 'r') as f:
            content = f.read()
        
        # Check if sidebar-nav exists and profile_page is not already in there
        if '<nav class="sidebar-nav">' in content and 'profile.html' not in content and 'profile_page' not in content:
            new_content = re.sub(r'(</ul>\s*</nav>)', profile_link + r'\n                \1', content)
            
            # Write only if changed
            if content != new_content:
                with open(path, 'w') as f:
                    f.write(new_content)
                print(f"Updated {path}")
