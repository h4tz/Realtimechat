# Minimal Chat MVP

A minimalistic real-time chat application built with Django and Channels.

## Features

- **Clean UI**: Minimalistic design focused on functionality
- **Real-time Messaging**: WebSocket-based instant messaging
- **Room-based Chat**: Multiple chat rooms support
- **Typing Indicators**: See when others are typing
- **Responsive Design**: Works on desktop and mobile
- **User Authentication**: Integrated with Django's auth system

## Tech Stack

- **Backend**: Django 4.x
- **Real-time**: Django Channels
- **Database**: SQLite (default)
- **Frontend**: Vanilla JavaScript
- **Styling**: CSS with modern design principles

## Quick Start

1. **Setup Environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. **Run Migrations**
   ```bash
   python manage.py migrate
   ```

3. **Start Server**
   ```bash
   python manage.py runserver
   ```

4. **Access the Application**
   Open your browser and navigate to: `http://127.0.0.1:8000`

## Usage

1. **Join a Room**: Enter a room name on the main page and click "Join Room"
2. **Chat**: Type messages and press Enter or click "Send"
3. **Switch Rooms**: Return to the main page to join different rooms

## File Structure

```
chat/
├── templates/
│   └── chat/
│       ├── minimal_index.html    # Room selection page
│       └── minimal_room.html     # Chat room interface
├── static/
│   └── chat/
│       ├── chat.js              # WebSocket client logic
│       └── minimal_style.css    # Minimalistic styling
├── consumers.py                 # WebSocket consumers
├── models.py                    # Data models
├── views.py                     # Django views
└── routing.py                   # WebSocket routing
```

## Key Features Details

### Real-time Communication
- WebSocket connections for instant messaging
- Automatic reconnection on connection loss
- Typing indicators with timeout

### User Experience
- Clean, distraction-free interface
- Smooth animations and transitions
- Mobile-responsive design
- Keyboard shortcuts (Enter to send)

### Technical Implementation
- Async WebSocket consumers for scalability
- Django Channels for real-time functionality
- CSS Grid and Flexbox for responsive layout
- Vanilla JavaScript for optimal performance

## Customization

### Styling
- All styles are in `minimal_style.css`
- Colors, fonts, and spacing can be easily modified
- CSS variables used for consistent theming

### Functionality
- Add new features by modifying `consumers.py`
- Extend views in `views.py` for additional endpoints
- Customize templates in the `templates/chat/` directory

## Development

### Adding New Features
1. Update WebSocket consumers in `consumers.py`
2. Add new views in `views.py`
3. Create/update templates as needed
4. Add CSS to `minimal_style.css`

### Testing
```bash
python manage.py test
```

## Deployment

### Production Setup
1. Use a production-ready database (PostgreSQL/MySQL)
2. Configure WebSocket server (Daphne for production)
3. Set up reverse proxy (Nginx)
4. Use production settings for static files

### Environment Variables
Create a `.env` file for production settings:
```
DEBUG=False
SECRET_KEY=your-secret-key
DATABASE_URL=your-database-url
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

This project is licensed under the MIT License.

## Support

For issues and questions:
1. Check the existing issues
2. Create a new issue with detailed description
3. Include steps to reproduce the problem

---

**Note**: This is a minimal MVP implementation focused on core functionality. Additional features can be added as needed.