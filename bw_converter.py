import os
import re

def hex_to_gray(match):
    hex_str = match.group(0).lower()
    
    # Some hex codes might just be 3 chars #fff
    if len(hex_str) == 4:
        r = int(hex_str[1]*2, 16)
        g = int(hex_str[2]*2, 16)
        b = int(hex_str[3]*2, 16)
    elif len(hex_str) == 7:
        r = int(hex_str[1:3], 16)
        g = int(hex_str[3:5], 16)
        b = int(hex_str[5:7], 16)
    else:
        # e.g., 8-char hex with alpha, let's ignore or just gray the RGB part
        if len(hex_str) == 9:
            r = int(hex_str[1:3], 16)
            g = int(hex_str[3:5], 16)
            b = int(hex_str[5:7], 16)
            a = hex_str[7:9]
            y = int(0.299*r + 0.587*g + 0.114*b)
            return f"#{y:02x}{y:02x}{y:02x}{a}"
        return hex_str
        
    y = int(0.299*r + 0.587*g + 0.114*b)
    
    # Optional: Enhance contrast by pushing darks to black and lights to white
    # If the user specifically said "black and white theme", maybe push to extremes?
    # No, Grayscale looks much more premium. Let's stick to true luminance.
    
    return f"#{y:02x}{y:02x}{y:02x}"

def process_dir(directory):
    count = 0
    # Regex to match hex codes #123, #123456, #12345678 strictly
    hex_pattern = re.compile(r'#[0-9a-fA-F]{3,8}\b')
    
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith('.html') or file.endswith('.css') or file.endswith('.js'):
                path = os.path.join(root, file)
                with open(path, 'r') as f:
                    content = f.read()
                
                # Only replace things that look like color hexes. 
                # (We don't want to replace ID selectors like #myModal if there are exactly 3/6 a-f chars, 
                # but usually IDs have different names. Let's restrict it to matching within color/background context?
                # Actually, hex_pattern matching `#[0-9a-fA-F]{3}` could match `id="#bad"`. 
                # Better regex: match `#` followed by hex, ONLY if it's inside a CSS rule or style tag.
                # Since this is a quick script, let's just pre-filter by matching `[:\s]#`
                
                def safe_replace(match):
                    prefix = match.group(1)
                    hx = match.group(2)
                    return prefix + hex_to_gray(re.match(r'.*', hx)) # using fake match obj
                
                # Match "color: #fff", "background: #fff", etc.
                new_content = re.sub(r'([:,]\s*)(#[0-9a-fA-F]{3,8}\b)', lambda m: m.group(1) + hex_to_gray(re.match(r'.*', m.group(2))), content)
                # Also match inside quotes like color="#fff"
                new_content = re.sub(r'([="]\s*)(#[0-9a-fA-F]{3,8}\b)', lambda m: m.group(1) + hex_to_gray(re.match(r'.*', m.group(2))), new_content)

                if new_content != content:
                    with open(path, 'w') as f:
                        f.write(new_content)
                    count += 1
                    print(f"Grayscaled {path}")
    return count

def main():
    c1 = process_dir('templates')
    c2 = process_dir('static')
    print(f"Total files updated: {c1 + c2}")

if __name__ == '__main__':
    main()
