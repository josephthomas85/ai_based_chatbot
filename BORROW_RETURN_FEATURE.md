# Updated Borrow & Return Workflow

## New Natural Language Borrow Feature

### Borrow Books Through Chat

Instead of clicking the "Borrow Book" button in the sidebar, you can now:

1. **Type "Borrow book"** in the chat
2. **See a list of available books** with number of copies
3. **Type the book name** you want to borrow (e.g., "Python Programming")
4. **Instant confirmation** with due date

**Example Chat:**
```
User: borrow book
Bot: Here are the 4 available books. Just tell me the book name you want to borrow:
     - Python Programming by John Smith (2 available)
     - Web Development with Flask by Sarah Johnson (2 available)
     - JavaScript Complete Guide by Emma Wilson (4 available)
     - Natural Language Processing by Michael Chen (1 available)

User: Python Programming
Bot: ✓ Successfully borrowed 'Python Programming' by John Smith!
     Due date: 2026-04-01
```

## New Natural Language Return Feature

### Return Books Through Chat

1. **Type "Return book"** in the chat
2. **See your borrowed books** with due dates
3. **Type the book name** you want to return
4. **Instant confirmation** with return date

**Example Chat:**
```
User: return book
Bot: You have 1 borrowed book(s). Just tell me the name of the book you want to return:
     - Python Programming by John Smith (Due: 2026-04-01)

User: Python Programming
Bot: ✓ Successfully returned 'Python Programming' by John Smith!
     Thank you! The book has been added back to our library.
```

## How It Works

### Smart Book Matching

The system intelligently matches partial book names:
- "Python" → "Python Programming"
- "web development" → "Web Development with Flask"
- "JS guide" → "JavaScript Complete Guide"
- Multiple word matching supported

### Conversation Context

The chatbot maintains conversation context:
- After asking to borrow/return, it stays in that mode
- Type partial book names and the system will find the match
- Clear, helpful error messages if book not found
- Suggestions show top 3 matching books

## Features Added

✅ Type book names instead of selecting from modal
✅ Conversation-based workflow
✅ Partial book name matching
✅ Real-time availability tracking
✅ Confirmation with due dates
✅ Error handling for unavailable books
✅ Smart suggestions after borrowing/returning

## Modified Files

- `api/chat.py` - Added book name matching and transaction processing
- `nlp/processor.py` - Added `find_book_by_name()` method
- `static/js/home.js` - Added context tracking and state management

## Try It Out!

1. Start the application
2. Login to your account
3. Type "Borrow book" in the chat
4. Select from displayed books
5. Type a book name to borrow it!

---

**Updated**: March 1, 2026
