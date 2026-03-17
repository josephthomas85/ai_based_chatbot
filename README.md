# AI-Based Library Management Chatbot

An intelligent library management system featuring an AI-powered chatbot that allows users to interact with the library catalog through natural language queries.

## Features

- 📚 **Book Search**: Search for books by title, author, or category
- 🤖 **AI Chatbot**: Natural language processing for intelligent interactions
- 📝 **Book Borrowing**: Check out books from the library
- ↩️ **Book Return**: Return borrowed books
- 👤 **User Authentication**: Secure login and registration
- 📊 **Availability Tracking**: Real-time book availability status
- 💬 **Interactive Chat**: Chat interface with smart suggestions

## Tech Stack

- **Frontend**: HTML5, CSS3, JavaScript (Vanilla)
- **Backend**: Python Flask
- **NLP**: Custom NLTK-based processor
- **Database**: JSON files
- **Authentication**: bcrypt password hashing

## Project Structure

```
ai_based_chatbot/
├── app.py                          # Main Flask application
├── config.py                       # Configuration settings
├── requirements.txt                # Python dependencies
├── README.md                       # This file
│
├── api/                            # API routes
│   ├── __init__.py
│   ├── auth.py                     # Authentication endpoints
│   ├── books.py                    # Book management endpoints
│   └── chat.py                     # Chatbot endpoints
│
├── nlp/                            # NLP processing module
│   ├── __init__.py
│   ├── processor.py                # NLP processor
│   └── intents.py                  # Intent definitions
│
├── database/                       # JSON databases
│   ├── users.json                  # User information
│   ├── books.json                  # Book catalog
│   └── transactions.json           # Borrow/return history
│
├── static/                         # Static files
│   ├── css/
│   │   ├── login.css               # Login page styles
│   │   └── home.css                # Home page styles
│   └── js/
│       ├── login.js                # Login page logic
│       └── home.js                 # Home page logic
│
└── templates/                      # HTML templates
    ├── login.html                  # Login page
    └── home.html                   # Main application page
```

## Installation

### Prerequisites

- Python 3.7 or higher
- pip (Python package manager)

### Setup

1. **Clone or download the project**

   ```bash
   cd ai_based_chatbot
   ```

2. **Create a virtual environment** (recommended)

   ```bash
   # On Windows
   python -m venv venv
   venv\Scripts\activate

   # On macOS/Linux
   python -m venv venv
   source venv/bin/activate
   ```

3. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   ```

## Running the Application

### Development

```bash
python app.py
```

The application will start on `http://localhost:5000`

### Development with Debug Mode

```bash
set FLASK_ENV=development  # On Windows
# or
export FLASK_ENV=development  # On macOS/Linux

python app.py
```

## Usage

### First Time Setup

1. **Open the application**
   - Navigate to `http://localhost:5000` in your browser

2. **Create an account or login**
   - Click "Register here" to create a new account
   - Or use demo credentials (after registration)

3. **Browse and search for books**
   - Use "Show All Books" to see the catalog
   - Use the chatbot to search and interact with the library

### Demo Login Credentials

After registration, you can create your own account. Sample accounts can be added by editing `database/users.json`.

### Chatbot Commands

The chatbot understands various natural language queries:

- "Show all books" - Display all available books
- "Search for Python" - Search for books by title
- "Borrow a book" - Initiate book borrowing process
- "Return a book" - Return a borrowed book
- "Check status" - Check book availability

## API Endpoints

### Authentication
- `POST /api/login` - User login
- `POST /api/logout` - User logout
- `POST /api/register` - User registration

### Books
- `GET /api/books` - Get all books
- `GET /api/books/<bookid>` - Get specific book details
- `POST /api/books/borrow` - Borrow a book
- `POST /api/books/return` - Return a book
- `GET /api/books/user/<userid>/borrowed` - Get user's borrowed books

### Chatbot
- `POST /api/chat` - Send message to chatbot

## Database Schema

### users.json
Stores user account information and borrowed book lists.

### books.json
Contains the library catalog with book details and availability.

### transactions.json
Records all borrow/return transactions with timestamps.

## NLP Processing

The chatbot uses a custom NLP processor featuring:

- **Tokenization**: Breaking input into word tokens
- **Intent Recognition**: Identifying user intent (search, borrow, return, etc.)
- **Entity Extraction**: Extracting book titles, authors, and keywords
- **Confidence Scoring**: Determining accuracy of intent classification

### Supported Intents

- `showallbooks`: Display all books
- `searchbook`: Search for specific books
- `borrowbook`: Borrow a book (you can just type "Borrow &lt;title&gt;" in one line or ask for a list first)
- `returnbook`: Return a book ("Return &lt;title&gt;" also works immediately)
- `checkstatus`: Check book availability

## Features Overview

### Login & Registration
- Secure password hashing with bcrypt
- Session-based authentication
- Email optional for registration

### Book Management
- Browse complete library catalog
- Search functionality
- Real-time availability tracking
- Borrow/return management

### Chatbot Interface
- Natural language query processing
- Smart suggestions for next actions
- Contextual responses
- Book information display

### User Experience
- Responsive design (works on desktop, tablet, mobile)
- Real-time chat interface
- Quick action buttons
- Modal dialogs for book selection

## Performance Requirements

- Response Time: < 2 seconds for chat responses
- Concurrent Users: Support 50+ simultaneous users
- Database Size: Handle 10,000+ book records
- Uptime: 99.5% availability

## Security Features

- Password hashing using bcrypt
- Session-based authentication
- CSRF token support
- XSS prevention
- Input validation and sanitization

## Future Enhancements

- Multi-language NLP support
- Voice input capability
- Book recommendation engine
- Reading history tracking
- Fine payment system
- Email notifications
- WebSocket for real-time updates
- Mobile app
- PostgreSQL integration
- Redis caching

## Troubleshooting

### Application won't start
- Ensure Python 3.7+ is installed
- Check all dependencies are installed: `pip install -r requirements.txt`
- Verify port 5000 is not in use

### Database errors
- Ensure `database/` directory exists
- Check JSON files are properly formatted
- Delete JSON files to reset with empty databases

### Login issues
- Clear browser cache and cookies
- Ensure JavaScript is enabled
- Check browser console for errors (F12)

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see LICENSE file for details.

## Support

For issues or questions:
1. Check the Troubleshooting section
2. Review the project specification
3. Check browser console for error messages
4. Enable debug mode for detailed logging

## Authors

- Arjun - Main Developer

## Acknowledgments

- Flask documentation and community
- NLTK for NLP capabilities
- bcrypt for secure password hashing

---

**Last Updated**: March 2026
