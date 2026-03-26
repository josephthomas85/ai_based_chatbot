import re
from nlp.intents import INTENTS, STOP_WORDS

class NLPProcessor:
    def __init__(self):
        self.intents = INTENTS
        self.stop_words = STOP_WORDS
    
    def tokenize(self, text):
        """Tokenize text into words"""
        # Convert to lowercase and remove punctuation
        text = text.lower()
        # Remove special characters but keep spaces
        text = re.sub(r'[^a-z0-9\s]', '', text)
        # Split into tokens
        tokens = text.split()
        return [token for token in tokens if token]  # Remove empty strings
    
    def remove_stopwords(self, tokens):
        """Remove common stopwords from tokens"""
        return [token for token in tokens if token not in self.stop_words]
    
    def extract_entities(self, text):
        """Extract entities (book titles, authors, etc.) from text"""
        entities = []
        
        # Simple entity extraction: words that are not stopwords and capitalized in original
        words = text.split()
        for word in words:
            # Check if word looks like an entity (contains numbers, is capitalized, or is a proper noun)
            if (word and 
                (any(char.isdigit() for char in word) or 
                 word[0].isupper() or 
                 word not in self.stop_words)):
                entities.append(word)
        
        return entities
    
    def classify_intent(self, tokens):
        """Classify intent based on tokens"""
        # Join tokens to create query string for matching
        text = ' '.join(tokens)
        
        # Check each intent
        for intent, keywords in self.intents.items():
            for keyword in keywords:
                # Check if keyword is in the text
                if keyword in text:
                    return intent
        
        # If multiple tokens, try partial matching
        if len(tokens) > 0:
            text_with_spaces = ' ' + ' '.join(tokens) + ' '
            for intent, keywords in self.intents.items():
                for keyword in keywords:
                    # Try to match at word boundaries
                    keyword_pattern = r'\s' + re.escape(keyword) + r'(?:\s|$)'
                    if re.search(keyword_pattern, text_with_spaces):
                        return intent
        
        return "unknown"
    
    def calculate_confidence(self, tokens, intent):
        """Calculate confidence score for intent classification"""
        if intent == "unknown":
            return 0.0
        
        # Base confidence
        confidence = 0.5
        
        # Increase confidence based on number of matching keywords
        keywords = self.intents.get(intent, [])
        text = ' '.join(tokens)
        
        matching_keywords = sum(1 for keyword in keywords if keyword in text)
        if matching_keywords > 0:
            confidence = min(1.0, 0.5 + (matching_keywords * 0.2))
        
        return round(confidence, 2)
    
    def process_message(self, message):
        """Process user message and return intent, entities, and confidence"""
        # Tokenize
        tokens = self.tokenize(message)
        
        # Remove stopwords (but keep for entity extraction)
        filtered_tokens = self.remove_stopwords(tokens)
        
        # Extract entities
        entities = self.extract_entities(message)
        
        # Classify intent
        intent = self.classify_intent(tokens)
        
        # Calculate confidence
        confidence = self.calculate_confidence(tokens, intent)
        
        return {
            'intent': intent,
            'entities': entities,
            'confidence': confidence,
            'tokens': tokens,
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
        from .intents import STOP_WORDS
        search_words = set(w for w in search_lower.split() if w not in STOP_WORDS and len(w) > 2)
        if not search_words:
            return None
            
        for book in books:
            book_title_words = set(w for w in book['title'].lower().split() if w not in STOP_WORDS)
            # If any significant word matches, consider it a match
            if search_words & book_title_words:
                return book
        
        return None
