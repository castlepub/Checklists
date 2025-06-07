# Castle Pub Checklist App

A mobile-friendly web application for The Castle Pub staff to manage their daily checklists. The app supports real-time Telegram notifications for task completion and checklist submission.

## Features

- Multiple checklists (Opening, Closing, Kitchen Opening, Kitchen Closing, Weekly Cleaning)
- Real-time Telegram notifications
- Mobile-friendly interface
- Digital signature capture
- Optional comments for each task
- Task completion tracking

## Tech Stack

- Backend: FastAPI (Python)
- Database: PostgreSQL
- Frontend: HTML + Vanilla JavaScript
- UI Framework: Bootstrap 5
- Signature Capture: SignaturePad.js
- Notifications: Telegram Bot API

## Local Development Setup

1. Clone the repository:
```bash
git clone <repository-url>
cd castle_checklist_app
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create a `.env` file with the following variables:
```
DATABASE_URL=postgresql://user:password@localhost:5432/castle_checklist
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
TELEGRAM_CHAT_ID=your_telegram_chat_id
```

5. Initialize the database:
```bash
python init_db.py
```

6. Run the development server:
```bash
uvicorn app.main:app --reload
```

## Railway Deployment

1. Create a new Railway project:
   - Go to [Railway](https://railway.app)
   - Create a new project
   - Add a PostgreSQL plugin

2. Configure environment variables in Railway:
   - `DATABASE_URL`: Railway will provide this automatically
   - `TELEGRAM_BOT_TOKEN`: Your Telegram bot token
   - `TELEGRAM_CHAT_ID`: Your Telegram group chat ID

3. Deploy the application:
   - Connect your GitHub repository
   - Railway will automatically detect the Python application
   - Set the start command to: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`

4. Initialize the database:
   - Use Railway's CLI or web terminal
   - Run: `python init_db.py`

## Telegram Bot Setup

1. Create a new bot:
   - Message @BotFather on Telegram
   - Use the `/newbot` command
   - Follow the instructions to create your bot
   - Save the bot token

2. Get the chat ID:
   - Add the bot to your manager's group
   - Send a message in the group
   - Access: `https://api.telegram.org/bot<YourBOTToken>/getUpdates`
   - Look for the `chat.id` in the response

3. Update your environment variables with the bot token and chat ID

## Project Structure

```
castle_checklist_app/
├── app/
│   ├── __init__.py
│   ├── main.py           # FastAPI application
│   ├── models.py         # Database models
│   ├── database.py       # Database connection
│   ├── telegram.py       # Telegram integration
│   └── seed_data.py      # Initial data seeding
├── static/
│   ├── css/
│   │   └── style.css
│   └── js/
│       └── app.js
├── templates/
│   └── index.html
├── tests/
├── .env.example
├── .gitignore
├── init_db.py
├── requirements.txt
└── README.md
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

MIT License
