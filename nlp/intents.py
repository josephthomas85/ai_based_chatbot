# Intent definitions for NLP processing — expanded for natural language
INTENTS = {
    "greeting": [
        "hi", "hello", "hey", "good morning", "good afternoon",
        "good evening", "hiya", "greetings", "howdy", "what's up",
        "sup", "yo", "hi there", "good day"
    ],

    "showallbooks": [
        "show all books", "list books", "available books", "show books",
        "all books", "list all books", "what books do you have",
        "display books", "browse books", "what's available", "what is available",
        "catalog", "show catalogue", "library catalog", "list everything",
        "show everything", "all titles", "every book", "full list",
        "see all books", "view all books", "show the library"
    ],

    "searchbook": [
        "find book", "search for", "looking for", "find me",
        "search", "do you have", "where is", "can you find",
        "is there a book", "do you carry", "look for", "locate",
        "find a book", "help me find", "any books on", "books about",
        "books by", "written by", "author", "title", "topic",
        "genre", "check if", "have any", "got any"
    ],

    "borrowbook": [
        "borrow", "checkout", "take out", "rent", "borrow book",
        "can i borrow", "i want to borrow", "check out",
        "i'd like to borrow", "id like to borrow", "want to borrow",
        "issue a book", "get a book", "take a book", "loan a book",
        "pick up", "grab", "reserve", "i need", "give me"
    ],

    "returnbook": [
        "return", "give back", "check in", "return book",
        "i want to return", "returning", "bring back",
        "i'd like to return", "id like to return", "hand in",
        "hand back", "drop off", "submit", "i'm done with",
        "finished with", "done reading"
    ],

    "checkstatus": [
        "status", "availability", "is available", "available",
        "is it available", "check availability", "when available",
        "when will be available", "how many copies", "copies available",
        "in stock", "out of stock", "check stock", "still available"
    ],

    "mybooks": [
        "my books", "my borrowed books", "books i have",
        "borrowed books", "what do i have", "my current books",
        "books on loan", "my loans", "what have i borrowed",
        "my active loans", "my checkouts", "currently borrowing",
        "show my books", "my account", "books i owe"
    ],

    "recommend": [
        "recommend", "suggest", "recommend books",
        "suggest books", "what should i read", "book recommendations",
        "recommend me", "suggest me", "any suggestions",
        "what's popular", "what's good", "something to read",
        "interesting books", "new books", "popular books",
        "top books", "good reads", "reading suggestions"
    ],

    "help": [
        "help", "what can you do", "how does this work",
        "what are your features", "how do i", "instructions",
        "guide me", "assist", "commands", "options",
        "what can i ask", "how to use"
    ],

    "history": [
        "history", "borrow history", "past books", "previous books",
        "what have i read", "books i've read", "completed loans",
        "returned books", "my history", "reading history"
    ],

    "overdue": [
        "overdue", "late books", "past due", "overdue books",
        "late fees", "missed deadline", "should have returned",
        "due date passed"
    ]
}

# Keywords that shouldn't be matched as standalone intents
STOP_WORDS = {
    "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for",
    "of", "with", "by", "from", "as", "is", "was", "are", "be", "have",
    "has", "had", "do", "does", "did", "will", "would", "should", "could",
    "i", "you", "he", "she", "it", "we", "they", "what", "which", "who",
    "where", "when", "why", "how", "can", "me", "my", "your", "his", "her",
    "this", "that", "these", "those", "there", "here", "please", "thanks"
}
