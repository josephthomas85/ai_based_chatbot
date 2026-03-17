# Intent definitions for NLP processing
INTENTS = {
    "greeting": [
        "hi",
        "hello",
        "hey",
        "good morning",
        "good afternoon",
        "good evening",
        "hiya",
        "greetings"
    ],

    "showallbooks": [
        "show all books",
        "list books",
        "available books",
        "show books",
        "all books",
        "list all books",
        "what books do you have",
        "display books"
    ],
    "searchbook": [
        "find book",
        "search for",
        "looking for",
        "find me",
        "search",
        "do you have",
        "where is",
        "can you find"
    ],
    "borrowbook": [
        "borrow",
        "checkout",
        "take out",
        "rent",
        "borrow book",
        "can i borrow",
        "i want to borrow",
        "check out"
    ],
    "returnbook": [
        "return",
        "give back",
        "check in",
        "return book",
        "i want to return",
        "returning",
        "bring back"
    ],
    "checkstatus": [
        "status",
        "availability",
        "is available",
        "available",
        "is it available",
        "check availability",
        "when available",
        "when will be available"
    ],
    "mybooks": [
        "my books",
        "my borrowed books",
        "books i have",
        "borrowed books",
        "what do i have",
        "my current books",
        "books on loan",
        "my loans"
    ],
    "recommend": [
        "recommend",
        "suggest",
        "recommend books",
        "suggest books",
        "what should i read",
        "book recommendations",
        "recommend me",
        "suggest me"
    ]
}

# Keywords that shouldn't be matched
STOP_WORDS = {
    "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for",
    "of", "with", "by", "from", "as", "is", "was", "are", "be", "have",
    "has", "had", "do", "does", "did", "will", "would", "should", "could",
    "i", "you", "he", "she", "it", "we", "they", "what", "which", "who",
    "where", "when", "why", "how", "can", "me", "my", "your", "his", "her"
}
