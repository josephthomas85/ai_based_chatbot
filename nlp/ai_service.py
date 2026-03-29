import os
from openai import OpenAI
from config import Config

# Initialize client lazily to avoid crashing on import if key isn't set
_client = None

def get_client():
    global _client
    if _client is None:
        if not Config.GROQ_API_KEY:
            raise ValueError("GROQ_API_KEY is not set in environment or config. Please get one at console.groq.com")
        
        # Groq uses the exact same interface as OpenAI, just with a different Base URL
        _client = OpenAI(
            api_key=Config.GROQ_API_KEY,
            base_url="https://api.groq.com/openai/v1"
        )
    return _client

def generate_book_summary(title: str, author: str, category: str, copies: int, lines: int = 5) -> str:
    """
    Calls Groq AI to generate a rich, contextual summary of a specific book for free.
    Returns exactly the number of lines requested.
    """
    try:
        client = get_client()
    except ValueError:
        return (
            f"**{title}** is a resource in {category}, written by {author}.\n"
            "*(AI summaries are disabled because the Groq API key is missing)*"
        )
    
    system_prompt = (
        "You are an expert, knowledgeable librarian returning book summaries.\n"
        f"Your task is to summarise the book provided. You MUST return exactly {lines} lines, "
        "with each line separated by a newline.\n"
        "Do NOT use emojis anywhere in your response.\n"
        "Do NOT use bullet points or numbering starting the lines.\n"
        "Do NOT include availability information; the system handles that separately.\n"
        "Each line should cover the following concepts in order if possible:\n"
        "1. Standard introduction (Title by Author is a book about X domain).\n"
        "2. Core themes and topics covered.\n"
        "3. Author's expertise or writing style.\n"
        "4. The target audience (who is it for).\n"
        "5. Why it matters (value addition).\n"
        "Use markdown for bolding the title, but no lists."
    )
    
    user_prompt = f"Please summarise the book '{title}' by {author} in the category '{category}'."
    
    try:
        response = client.chat.completions.create(
            model=Config.AI_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.7,
            max_tokens=600
        )
        content = response.choices[0].message.content.strip()
        return content
    except Exception as e:
        print(f"AI error in summary (Groq): {e}")
        return (
            f"**{title}** is a resource in {category}, written by {author}.\n"
            "An AI summary could not be generated at this time due to an API error."
        )

import json

def classify_intent_and_entities(message: str) -> dict:
    """
    Acts as a Semantic Router using Llama 3.1.
    Classifies the user's message into exactly one predefined intent and extracts any target book title.
    Returns a dictionary: {"intent": str, "book_title": str | None}
    """
    try:
        client = get_client()
    except ValueError:
        # Fallback if API key is missing
        return {"intent": "unknown", "book_title": None}

    system_prompt = (
        "You are the intent router for a Library Management System chatbot.\n"
        "Your sole job is to read the user's message and classify it into exactly ONE of the following intents:\n"
        "- borrowbook: The user wants to borrow, check out, or read a book.\n"
        "- returnbook: The user wants to return or give back a book.\n"
        "- showallbooks: The user wants to see all books or the catalog.\n"
        "- searchbook: The user is looking for a specific book, author, or category, or asking if we have a book.\n"
        "- semesterbooks: The user is asking for books for a specific semester and/or branch/department (e.g. 'CSE S3 books', 'show books for ECE 5th semester', 'what books do I need for ME S4', 'S1 common books').\n"
        "- mybooks: The user wants to see what books they currently have borrowed.\n"
        "- history: The user wants to see their past borrowing history or past books.\n"
        "- overdue: The user wants to check if they have any overdue books or fines.\n"
        "- recommend: The user wants YOU to give them new book recommendations.\n"
        "- summarize: The user wants a summary, explanation, synopsis, or overview of a book.\n"
        "- help: The user wants to know what the bot can do, or needs instructions.\n"
        "- cancel: The user wants to stop, cancel, or abort the current action.\n"
        "- unknown: The user is asking a follow-up question (e.g. 'why did you suggest that?', 'why did you recommend this?'), making casual conversation, or asking an unrelated question.\n\n"
        "If the user mentions a specific book title in their query, extract it.\n"
        "If the intent is 'semesterbooks', also extract the branch (e.g. CSE, ECE, EEE, ME, CIVIL, AUTOMOBILE, COMMON) and semester (e.g. S1, S2, S3, S4, S5, S6, S7, S8).\n"
        "Map semester words: 'first'->S1, 'second'->S2, 'third'->S3, 'fourth'->S4, 'fifth'->S5, 'sixth'->S6, 'seventh'->S7, 'eighth'->S8, '1st'->S1, '2nd'->S2, '3rd'->S3, '4th'->S4, '5th'->S5, '6th'->S6, '7th'->S7, '8th'->S8.\n"
        "If branch is not mentioned for semesterbooks, set it to 'COMMON'.\n"
        "IMPORTANT: You MUST respond in pure JSON format ONLY. Do not write anything outside the JSON.\n"
        'Format: {"intent": "chosen_intent_string", "book_title": "extracted_title_or_null", "branch": "branch_or_null", "semester": "semester_code_or_null"}'
    )

    try:
        response = client.chat.completions.create(
            model=Config.AI_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": message}
            ],
            temperature=0.1,
            response_format={"type": "json_object"},
            max_tokens=100
        )
        content = response.choices[0].message.content.strip()
        parsed = json.loads(content)
        
        # Ensure fallback sanity checks
        intent = parsed.get("intent", "unknown")
        book_title = parsed.get("book_title", None)
        branch = parsed.get("branch", None)
        semester = parsed.get("semester", None)
        
        valid_intents = {"borrowbook", "returnbook", "showallbooks", "searchbook", "semesterbooks", "mybooks", "history", "overdue", "summarize", "recommend", "help", "cancel", "unknown"}
        if intent not in valid_intents:
            intent = "unknown"
        
        # Normalise branch and semester strings
        if branch:
            branch = branch.upper().strip()
        if semester:
            semester = semester.upper().strip()
            
        return {"intent": intent, "book_title": book_title, "branch": branch, "semester": semester}
        
    except Exception as e:
        print(f"AI Router error: {e}")
        return {"intent": "unknown", "book_title": None}

def generate_chat_response(message: str, username: str, user_history: list = None, available_books_sample: list = None, chat_history: list = None) -> str:
    """
    Uses Groq as a conversational fallback for messages the intent parser doesn't understand.
    Has conversational memory via chat_history.
    """
    try:
        client = get_client()
    except ValueError:
        return "I'm having trouble connecting to my AI brain right now because my Groq API key is missing. Can you try asking me about books directly?"
        
    books_context = ""
    if available_books_sample:
        titles = [b['title'] for b in available_books_sample[:5]]
        books_context = f"\nHere are some books currently in the catalog: {', '.join(titles)}."
        
    history_context = ""
    if user_history:
        history_context = "\nUser is currently borrowing: " + ", ".join([h['title'] for h in user_history])

    system_prompt = (
        "You are a helpful, polite library management system AI assistant.\n"
        f"The user's name is {username}.\n"
        "Keep your responses concise, helpful, and friendly.\n"
        "Do not use emojis.\n"
        "Your goal is to assist them with library-related tasks (finding books, borrowing, returning, recommending).\n"
        "If a user asks about previous messages or recommendations shown to them, use your memory of the chat history to explain or help them.\n"
        f"{books_context}{history_context}\n"
        "If a user asks about something completely unrelated to books, reading, or the library, politely "
        "guide them back to library topics."
    )
    
    # Build the messages payload
    messages = [{"role": "system", "content": system_prompt}]
    
    if chat_history:
        messages.extend(chat_history)
        
    messages.append({"role": "user", "content": message})
    
    try:
        response = client.chat.completions.create(
            model=Config.AI_MODEL,
            messages=messages,
            temperature=0.8,
            max_tokens=500
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"AI error in chat (Groq): {e}")
        return "I'm having trouble connecting to my AI brain right now. Can you try asking me about books directly?"


def generate_ai_recommendations(user_history: list, available_books_data: list) -> dict:
    """
    Acts as a personalized Recommendation Engine using Llama 3.1 JSON mode.
    Selects 3 highly relevant books from the available catalog based on the user's past borrowing history.
    Returns: {"explanation": str, "recommended_bookids": [str, str, str]}
    """
    try:
        client = get_client()
    except ValueError:
        # Fallback if API key is missing
        return {
            "explanation": "*(AI personalized recommendations are disabled because the Groq API key is missing. Here are some default books instead:)*",
            "recommended_bookids": [b["bookid"] for b in available_books_data[:3]]
        }

    # Format history and catalog for the prompt
    import random
    history_str = ", ".join(user_history) if user_history else "None (New User)"
    
    # Send a lightweight, token-efficient version of the catalog to the LLM
    # Groq's Free Tier limits requests to 6000 TPM, so we must truncate a large catalog
    # Randomly shuffle and pick a maximum of 40 available books to keep tokens < 2000
    catalog_sample = list(available_books_data)
    random.shuffle(catalog_sample)
    catalog_sample = catalog_sample[:40]
    
    catalog_lines = []
    for b in catalog_sample:
        catalog_lines.append(f"ID: {b['bookid']} | Title: '{b['title']}' | Category: {b.get('category', 'General')}")
    catalog_str = "\n".join(catalog_lines)

    system_prompt = (
        "You are an expert, knowledgeable librarian returning personalized book recommendations.\n"
        "Your task is to review the user's past borrowing history to understand their reading tastes.\n"
        "Using ONLY the provided 'Available Catalog', select EXACTLY 3 highly relevant books that the user would enjoy reading next.\n"
        "If the user has no history (New User), pick 3 diverse, highly-rated books from the catalog to get them started.\n"
        "You must provide a brief, friendly, conversational 'explanation' (2-3 sentences max) explaining WHY you chose these 3 specific books based on their history.\n"
        "Do NOT use emojis in your explanation.\n"
        "IMPORTANT: You MUST respond in pure JSON format ONLY. Do not write anything outside the JSON.\n"
        'Format: {"explanation": "Your conversational explanation here.", "recommended_bookids": ["bookid1", "bookid2", "bookid3"]}'
    )
    
    user_prompt = f"User's Borrowing History:\n{history_str}\n\nAvailable Catalog:\n{catalog_str}"

    try:
        response = client.chat.completions.create(
            model=Config.AI_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.6,
            response_format={"type": "json_object"},
            max_tokens=300
        )
        content = response.choices[0].message.content.strip()
        parsed = json.loads(content)
        
        # Ensure we always return exactly 3 valid bookids, fallback if LLM hallucinates
        valid_ids = {b["bookid"] for b in available_books_data}
        final_ids = [bid for bid in parsed.get("recommended_bookids", []) if bid in valid_ids][:3]
        
        # If the LLM failed to return 3 valid IDs, pad with random defaults
        while len(final_ids) < 3 and len(final_ids) < len(available_books_data):
            for b in available_books_data:
                if b["bookid"] not in final_ids:
                    final_ids.append(b["bookid"])
                    break
                    
        return {
            "explanation": parsed.get("explanation", "Here are some books I think you'll enjoy!"),
            "recommended_bookids": final_ids
        }
        
    except Exception as e:
        print(f"AI error in recommendations (Groq): {e}")
        return {
            "explanation": "An AI error occurred, but here are some popular books available right now:",
            "recommended_bookids": [b["bookid"] for b in available_books_data[:3]]
        }
