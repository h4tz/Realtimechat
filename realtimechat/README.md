🗨️ Real-Time Django Chat App
This is a real-time chat application built using Django, WebSockets (via Django Channels), and HTML/JavaScript for frontend communication. The app supports:

🔒 Private messaging between two users

🏠 Group chat rooms for multiple users

🧑‍💬 Username-based chat sessions

📸 Features
👥 Real-time communication between users

💬 Join a public room or create one with a name

📩 Chat privately with a specific user

📌 Simple interface to enter your username, recipient's username, and room name

🔐 Secure WebSocket connections

🚀 Tech Stack
Layer	Tech Used
Backend	Django, Django Channels
Frontend	HTML, CSS, JavaScript
WebSocket	Channels (ASGI)
Database	SQLite (for testing)
Auth	Django's User Model

🏗️ Project Structure
bash
Copy code
realtimechat/
├── chat/               # Chat app (routing, consumers, models)
├── realtimechat/       # Project settings & ASGI config
├── staticfiles/        # Static files
├── manage.py
├── db.sqlite3
├── requirements.txt
├── README.md
🔧 Installation & Setup
bash
Copy code
# Clone the repo
git clone https://github.com/yourusername/realtimechat.git
cd realtimechat

# Create and activate a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows use: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Run the server
python manage.py runserver
Then open your browser and go to:
http://127.0.0.1:8000

💡 How to Use
Visit the chat interface.

Enter your username, the recipient’s username, and a room name.

Start chatting in that room.

If the recipient joins the same room, messages appear in real time!

🧠 What I Learned
Setting up WebSocket connections using Django Channels

Handling multiple users in the same room

Building private 1:1 chat functionality

Working with ASGI applications in Django

Sending and receiving messages with JavaScript WebSocket API

Managing user sessions and dynamic URL routing