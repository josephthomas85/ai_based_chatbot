"""
AI Book Summarizer
Generates intelligent, contextual book summaries using a knowledge-synthesis
template engine. Summaries are structured as 5 informative lines covering:
  1. What the book is / its core theme
  2. What reader will learn / key topics
  3. Author context and credibility
  4. Who it is suited for
  5. Why it matters / takeaway
"""

import re

# ─────────────────────────────────────────────
# Category → Domain Knowledge Templates
# ─────────────────────────────────────────────
CATEGORY_KNOWLEDGE = {
    "Python": {
        "domain": "Python programming language",
        "themes": ["object-oriented programming", "scripting", "automation", "data manipulation"],
        "audience": "beginner to intermediate programmers",
        "value": "Python is the most versatile language for data science, automation, and web development",
        "topics": ["functions", "modules", "data structures", "file I/O", "OOP concepts"],
    },
    "Data Science": {
        "domain": "data science and analytics",
        "themes": ["data analysis", "machine learning", "statistical modelling", "data visualisation"],
        "audience": "aspiring data scientists and analysts",
        "value": "Data science skills are among the most sought-after in modern tech industries",
        "topics": ["pandas", "NumPy", "Matplotlib", "predictive models", "data cleaning"],
    },
    "Machine Learning": {
        "domain": "machine learning and artificial intelligence",
        "themes": ["neural networks", "supervised learning", "model training", "AI algorithms"],
        "audience": "developers and researchers entering AI",
        "value": "Machine learning powers modern recommendations, search, and autonomy systems",
        "topics": ["regression", "classification", "deep learning", "TensorFlow", "scikit-learn"],
    },
    "Artificial Intelligence": {
        "domain": "artificial intelligence",
        "themes": ["intelligent systems", "reasoning", "natural language", "computer vision"],
        "audience": "technology enthusiasts and AI practitioners",
        "value": "AI is reshaping every industry from healthcare to finance",
        "topics": ["NLP", "neural networks", "reinforcement learning", "ethics in AI"],
    },
    "Web Development": {
        "domain": "web development",
        "themes": ["HTML", "CSS", "JavaScript", "backend systems", "RESTful APIs"],
        "audience": "frontend and fullstack developers",
        "value": "Web development remains the most in-demand skill set in the software industry",
        "topics": ["responsive design", "frameworks", "databases", "authentication", "deployment"],
    },
    "System Design": {
        "domain": "software system design and architecture",
        "themes": ["scalability", "distributed systems", "microservices", "database design"],
        "audience": "senior developers and architects",
        "value": "Strong system design skills are critical for building large-scale, reliable software",
        "topics": ["load balancing", "caching", "CAP theorem", "APIs", "message queues"],
    },
    "Cloud": {
        "domain": "cloud computing",
        "themes": ["AWS", "Azure", "GCP", "cloud infrastructure", "serverless computing"],
        "audience": "DevOps engineers and cloud architects",
        "value": "Cloud adoption is accelerating across enterprises worldwide",
        "topics": ["EC2", "S3", "Lambda", "Kubernetes", "Terraform"],
    },
    "DevOps": {
        "domain": "DevOps practices and CI/CD pipelines",
        "themes": ["automation", "containerisation", "continuous integration", "monitoring"],
        "audience": "developers and operations engineers",
        "value": "DevOps bridges the gap between development and reliable production systems",
        "topics": ["Docker", "Kubernetes", "Jenkins", "Git", "infrastructure as code"],
    },
    "Database": {
        "domain": "database systems and data management",
        "themes": ["SQL", "NoSQL", "transactions", "query optimisation", "schema design"],
        "audience": "backend developers and DBAs",
        "value": "Efficient database design is the backbone of every reliable application",
        "topics": ["indexing", "ACID properties", "joins", "replication", "Redis"],
    },
    "JavaScript": {
        "domain": "JavaScript programming",
        "themes": ["async programming", "DOM manipulation", "React", "Node.js", "ES6+"],
        "audience": "web developers of all levels",
        "value": "JavaScript is the only language that runs natively in every browser",
        "topics": ["promises", "closures", "event loop", "TypeScript", "REST API integration"],
    },
    "Golang": {
        "domain": "Go (Golang) programming language",
        "themes": ["concurrency", "high performance", "microservices", "systems programming"],
        "audience": "backend engineers and systems programmers",
        "value": "Go delivers C-like performance with Python-like simplicity",
        "topics": ["goroutines", "channels", "interfaces", "error handling", "packages"],
    },
    "Rust": {
        "domain": "Rust systems programming",
        "themes": ["memory safety", "ownership model", "zero-cost abstractions", "concurrency"],
        "audience": "experienced programmers interested in safe systems software",
        "value": "Rust eliminates memory bugs without a garbage collector",
        "topics": ["ownership", "lifetimes", "traits", "pattern matching", "crates"],
    },
    "Security": {
        "domain": "cybersecurity and ethical hacking",
        "themes": ["penetration testing", "cryptography", "network security", "vulnerability assessment"],
        "audience": "security professionals and developers",
        "value": "Security knowledge is essential in a world of increasing cyber threats",
        "topics": ["OWASP Top 10", "encryption", "authentication", "firewalls", "incident response"],
    },
    "Medical": {
        "domain": "medical science and healthcare",
        "themes": ["anatomy", "diagnostic processes", "clinical practice", "patient care"],
        "audience": "medical students, practitioners, and healthcare enthusiasts",
        "value": "Medical knowledge underpins human health and the entire healthcare industry",
        "topics": ["physiology", "pharmacology", "disease mechanisms", "evidence-based medicine"],
    },
    "Finance": {
        "domain": "finance and investment",
        "themes": ["investing", "risk management", "financial markets", "personal finance"],
        "audience": "investors, finance professionals, and curious readers",
        "value": "Financial literacy is one of the most impactful skills for long-term wealth",
        "topics": ["stocks", "bonds", "portfolio theory", "valuation", "behavioural finance"],
    },
    "Management": {
        "domain": "business management and leadership",
        "themes": ["team leadership", "strategy", "productivity", "organisational behaviour"],
        "audience": "managers, entrepreneurs, and aspiring leaders",
        "value": "Effective management multiplies team output and drives organisational success",
        "topics": ["decision making", "motivation", "OKRs", "delegation", "communication"],
    },
    "General": {
        "domain": "knowledge and learning",
        "themes": ["broad concepts", "foundational principles", "practical application"],
        "audience": "general readers seeking to expand their knowledge",
        "value": "Continuous learning is the most consistent predictor of long-term success",
        "topics": ["core ideas", "case studies", "real-world examples", "frameworks"],
    },
}

# ─────────────────────────────────────────────
# Raw title → curated summary overrides
# High-value books get hand-crafted summaries
# ─────────────────────────────────────────────
CURATED_SUMMARIES = {
    "clean code": [
        "**Clean Code** by Robert C. Martin is a foundational guide to writing readable, maintainable software.",
        "It teaches naming conventions, small functions, proper comments, and refactoring techniques used by professional developers.",
        "Robert C. Martin ('Uncle Bob') is one of the most influential figures in software engineering best practices.",
        "Essential reading for any developer who writes code that other humans will also need to read and maintain.",
        "The book's central message: code is written once but read hundreds of times — so clarity is the highest virtue.",
    ],
    "python crash course": [
        "**Python Crash Course** is a fast-paced, hands-on introduction to Python 3 programming.",
        "Covers variables, loops, functions, classes, file handling, and ends with three real projects: a game, data visualisations, and a web app.",
        "Written by Eric Matthes, an experienced Python educator known for highly accessible yet thorough explanations.",
        "Ideal for complete beginners who want a structured path from zero to building real Python applications.",
        "One of the best-selling Python books worldwide — a proven roadmap for getting hands-on with Python quickly.",
    ],
    "the pragmatic programmer": [
        "**The Pragmatic Programmer** is a timeless collection of advice on becoming a more effective software professional.",
        "Topics include DRY principle, orthogonality, tracer bullets, prototyping, and how to negotiate technical debt with pragmatism.",
        "Co-authored by David Thomas and Andrew Hunt, both seasoned software consultants with decades of real-world experience.",
        "A must-read for developers at all levels who want to develop wisdom and craft alongside technical skills.",
        "Its 'your knowledge portfolio' metaphor alone makes it worth reading — treat your learning like a financial investment.",
    ],
    "designing data-intensive applications": [
        "**Designing Data-Intensive Applications** (DDIA) by Martin Kleppmann is the definitive guide to modern data systems.",
        "Covers the internals of databases, replication, partitioning, transactions, batch & stream processing, and distributed systems.",
        "Martin Kleppmann is a researcher and lecturer at Cambridge University with deep expertise in distributed databases.",
        "Indispensable for senior engineers, tech leads, and architects building reliable, large-scale data pipelines.",
        "The book demystifies the 'magic' inside systems like Kafka, PostgreSQL, and Cassandra with clear, intuitive explanations.",
    ],
}

# ─────────────────────────────────────────────
# Helper: match category from book data
# ─────────────────────────────────────────────
def _get_category_info(book: dict) -> dict:
    category = book.get("category", "General")
    # Try to find a matching template
    for key in CATEGORY_KNOWLEDGE:
        if key.lower() in category.lower():
            return CATEGORY_KNOWLEDGE[key]
    # Try matching against title words
    title_lower = book.get("title", "").lower()
    for key in CATEGORY_KNOWLEDGE:
        if key.lower() in title_lower:
            return CATEGORY_KNOWLEDGE[key]
    return CATEGORY_KNOWLEDGE["General"]


# ─────────────────────────────────────────────
# Helper: extract year context
# ─────────────────────────────────────────────
def _year_context(year: int) -> str:
    if year >= 2020:
        return "a cutting-edge modern"
    elif year >= 2015:
        return "a highly relevant contemporary"
    elif year >= 2010:
        return "a well-established influential"
    elif year >= 2000:
        return "a classic foundational"
    else:
        return "a seminal legendary"


from .ai_service import generate_book_summary

# ─────────────────────────────────────────────
# Main summarization function
# ─────────────────────────────────────────────
def summarize_book(book: dict, lines: int = 5) -> str:
    """
    Generate a formatted AI summary of a book using OpenAI.
    Returns a markdown-formatted multi-line summary string.

    Args:
        book: dict with keys title, author, category, publicationyear, etc.
        lines: number of summary lines requested (default 5)
    """
    title = book.get("title", "Unknown")
    author = book.get("author", "Unknown")
    category = book.get("category", "General")
    copies = book.get("availablecopies", 0)

    # Call the OpenAI service to get a generated summary
    summary_text = generate_book_summary(title=title, author=author, category=category, copies=copies, lines=lines)

    availability = f"\n\nLibrary Status: {'Available' if copies > 0 else 'Currently out of stock'} ({copies} copies)"
    return summary_text + availability



# ─────────────────────────────────────────────
# Extract book name from a user query
# ─────────────────────────────────────────────
# Patterns that wrap the book title
_EXTRACT_PATTERNS = [
    r"explain\s+(.+?)\s+in\s+\d+\s+lines?",
    r"explain\s+in\s+\d+\s+lines?\s+(.+)",
    r"summarize\s+(.+)",
    r"summary\s+of\s+(.+)",
    r"give\s+(?:me\s+)?(?:a\s+)?summary\s+of\s+(.+)",
    r"tell\s+me\s+about\s+(.+)",
    r"what\s+is\s+(.+?)\s+about",
    r"describe\s+(.+)",
    r"what\s+does\s+(.+?)\s+cover",
    r"overview\s+of\s+(.+)",
    r"synopsis\s+of\s+(.+)",
    r"about\s+the\s+book\s+(.+)",
    r"info\s+about\s+(.+)",
    r"details\s+about\s+(.+)",
]

def extract_book_name_from_query(message: str) -> str | None:
    """
    Extract the book title from a user summarise query.
    Returns the extracted name or None if not found.
    """
    msg = message.strip().lower()
    # Common non-book phrases to reject even if extracted
    _noise_phrases = {
        'a book', 'the book', 'this book', 'that book', 'it', 'the', 'a',
        'one', 'any book', 'some book', 'my book', 'any', 'something',
    }
    for pattern in _EXTRACT_PATTERNS:
        m = re.search(pattern, msg, re.IGNORECASE)
        if m:
            name = m.group(1).strip(" .,?!")
            # Remove trailing noise like "for me", "please", "now"
            name = re.sub(r'\b(for me|please|now|quickly|briefly)\b', '', name).strip()
            # Reject if too short or is a generic noise phrase
            if len(name) >= 3 and name not in _noise_phrases:
                return name
    return None


def extract_line_count(message: str) -> int:
    """Extract requested number of lines from query (defaults to 5)."""
    m = re.search(r'in\s+(\d+)\s+lines?', message, re.IGNORECASE)
    if m:
        n = int(m.group(1))
        return max(1, min(n, 10))  # clamp between 1 and 10
    if re.search(r'in\s+(five|four|three|six|seven)\s+lines?', message, re.IGNORECASE):
        word_map = {"five": 5, "four": 4, "three": 3, "six": 6, "seven": 7}
        w = re.search(r'(five|four|three|six|seven)', message, re.IGNORECASE).group(1).lower()
        return word_map[w]
    return 5
