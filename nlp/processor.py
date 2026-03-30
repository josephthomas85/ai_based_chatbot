import re
from .ai_service import classify_intent_and_entities

class NLPProcessor:
    def process_message(self, message):
        """
        Process user message visually routing it through the LLM.
        Returns a standardised dictionary matching the old legacy NLP pattern
        but powered entirely by Llama 3.1 behind the scenes.
        """
        # Call Llama 3.1 for unified intent and entity extraction
        router_result = classify_intent_and_entities(message)
        
        intent = router_result.get("intent", "unknown")
        extracted_book = router_result.get("book_title")
        branch = router_result.get("branch")
        semester = router_result.get("semester")
        
        return {
            'intent': intent,
            'entities': [extracted_book] if extracted_book else [],
            'book_title': extracted_book,
            'branch': branch,
            'semester': semester,
            'confidence': 0.99,
            'tokens': message.lower().split(),
            'original_message': message
        }

    def find_book_by_name(self, books, search_query):
        """Find a book by name (partial matching)"""
        search_lower = search_query.lower().strip()
        # ignore blank queries
        if not search_lower:
            return None
            
        # First try exact or near-exact matches in titles
        for book in books:
            if search_lower in book['title'].lower() or book['title'].lower() in search_lower:
                return book
                
        # Try matching any significant words
        # (Since we removed stopwords from intents.py, we just use a basic list here)
        basic_stopwords = {'a', 'an', 'the', 'is', 'at', 'which', 'on', 'for', 'book', 'please'}
        words = [w for w in search_lower.split() if w not in basic_stopwords and len(w) > 2]
        
        if not words:
            return None
            
        for book in books:
            title_lower = book['title'].lower()
            author_lower = book['author'].lower()
            # If all significant words are in the title or author
            if all(word in title_lower or word in author_lower for word in words):
                return book
                
        return None
