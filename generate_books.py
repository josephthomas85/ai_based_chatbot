"""
Book Database Generator
Generates 10,000 books for the library catalog
"""

import json
from datetime import datetime
import random

# Book titles, authors, and categories for generating realistic data
GENRES = [
    "Programming", "Web Development", "AI/ML", "Database", "DevOps",
    "Mobile Development", "Game Development", "Data Science", "Cloud Computing",
    "Cybersecurity", "Software Architecture", "Testing", "Design Patterns",
    "Fiction", "Non-Fiction", "Business", "Self-Help", "Science", "History",
    "Mystery", "Romance", "Fantasy", "Science Fiction", "Biography", "Education"
]

ADJECTIVES = [
    "Complete", "Advanced", "Introduction to", "Mastering", "Professional",
    "Essential", "Ultimate", "Practical", "Beginner's", "Expert",
    "The Art of", "The Science of", "Deep Dive into", "Modern", "Classic"
]

TECH_KEYWORDS = [
    "Python", "JavaScript", "Java", "C++", "C#", "Ruby", "Go", "Rust",
    "TypeScript", "PHP", "Swift", "Kotlin", "Scala", "R", "MATLAB",
    "Node.js", "Django", "Flask", "FastAPI", "Spring", "ASP.NET",
    "React", "Vue", "Angular", "Svelte", "Next.js", "Nuxt",
    "Docker", "Kubernetes", "AWS", "Azure", "GCP", "Terraform",
    "TensorFlow", "PyTorch", "Keras", "Scikit-learn", "Pandas",
    "SQL", "NoSQL", "MongoDB", "PostgreSQL", "MySQL", "Redis",
    "REST API", "GraphQL", "Microservices", "Blockchain", "IoT"
]

GENERAL_TOPICS = [
    "Business Leadership", "Entrepreneurship", "Personal Development",
    "Time Management", "Communication Skills", "Critical Thinking",
    "Problem Solving", "Creativity", "Innovation", "Change Management",
    "Project Management", "Agile Methodology", "UX Design", "UI Design",
    "Writing", "Public Speaking", "Negotiation", "Finance", "Investment"
]

AUTHORS_FIRST = [
    "John", "Jane", "Michael", "Sarah", "David", "Emma", "Robert", "Lisa",
    "James", "Mary", "Richard", "Patricia", "Thomas", "Jennifer", "Charles",
    "Linda", "Daniel", "Barbara", "Matthew", "Susan", "Anthony", "Jessica",
    "Mark", "Margaret", "Donald", "Nancy", "Andrew", "Karen", "Joshua", "Betty"
]

AUTHORS_LAST = [
    "Smith", "Johnson", "Williams", "Brown", "Jones", "Miller", "Davis",
    "Rodriguez", "Martinez", "Hernandez", "Lopez", "Gonzalez", "Wilson",
    "Anderson", "Thomas", "Taylor", "Moore", "Jackson", "Martin", "Lee",
    "Perez", "Thompson", "White", "Harris", "Sanchez", "Clark", "Ramirez",
    "Lewis", "Robinson", "Walker"
]

def generate_books(count=10000):
    """Generate realistic book data"""
    books = []
    
    for i in range(1, count + 1):
        bookid = f"BK{str(i).zfill(5)}"
        
        # Generate title
        adjective = random.choice(ADJECTIVES)
        
        if random.random() > 0.4:  # 60% tech books
            keyword = random.choice(TECH_KEYWORDS)
            title = f"{adjective} {keyword}"
        else:  # 40% general books
            topic = random.choice(GENERAL_TOPICS)
            title = f"{adjective} {topic}"
        
        # Generate author
        author = f"{random.choice(AUTHORS_FIRST)} {random.choice(AUTHORS_LAST)}"
        
        # Generate ISBN
        isbn = f"978-{random.randint(1000000000, 9999999999)}"
        
        # Select category
        category = random.choice(GENRES)
        
        # Publication year (mostly recent, some older)
        if random.random() > 0.3:
            publicationyear = random.randint(2020, 2024)
        else:
            publicationyear = random.randint(2010, 2019)
        
        # Total and available copies
        totalcopies = random.randint(1, 10)
        availablecopies = random.randint(0, totalcopies)
        status = "available" if availablecopies > 0 else "unavailable"
        
        # Location in library
        shelf = chr(65 + random.randint(0, 25))  # A-Z
        shelf_number = random.randint(1, 30)
        location = f"Shelf {shelf}-{str(shelf_number).zfill(2)}"
        
        book = {
            "bookid": bookid,
            "title": title,
            "author": author,
            "isbn": isbn,
            "category": category,
            "publicationyear": publicationyear,
            "totalcopies": totalcopies,
            "availablecopies": availablecopies,
            "status": status,
            "location": location
        }
        
        books.append(book)
        
        if i % 1000 == 0:
            print(f"Generated {i} books...")
    
    return books

def save_books(books, filepath):
    """Save books to JSON file"""
    data = {"books": books}
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"Saved {len(books)} books to {filepath}")

if __name__ == "__main__":
    import os, sys
    
    # determine number of books to generate (default 10000, override with first argument)
    try:
        count = int(sys.argv[1])
    except (IndexError, ValueError):
        count = 10000
    
    # Get the database path
    db_path = os.path.join(os.path.dirname(__file__), "database", "books.json")
    
    print(f"Generating {count} books...")
    books = generate_books(count)
    
    print(f"Saving to {db_path}...")
    save_books(books, db_path)
    
    print("✓ Book database generated successfully!")
    print(f"Total books: {len(books)}")
    
    # Print some statistics
    with open(db_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
        total = len(data['books'])
        available = sum(1 for b in data['books'] if b['status'] == 'available')
        print(f"Available: {available}/{total} books")
