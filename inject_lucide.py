import os

lucide_scripts = """
    <!-- Lucide Icons -->
    <script src="https://unpkg.com/lucide@latest"></script>
    <script>
        lucide.createIcons();
    </script>
</body>"""

for file in os.listdir('templates'):
    if file.endswith('.html'):
        path = os.path.join('templates', file)
        with open(path, 'r') as f:
            content = f.read()
            
        if 'lucide' not in content:
            new_content = content.replace('</body>', lucide_scripts)
            if content != new_content:
                with open(path, 'w') as f:
                    f.write(new_content)
                print(f"Injected Lucide into {path}")
