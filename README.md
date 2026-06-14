# Campus Marketplace

A full-stack web application where university students can buy and sell items on campus. Built with Flask, SQLite, and real-time chat using Socket.IO.

## Features

- **User Authentication** — Sign up and login with your college email. Passwords are securely hashed.
- **Post Listings** — Create listings with a title, description, price, category, and photo.
- **Browse Listings** — View all available items posted by students on campus.
- **Real-Time Chat** — Message sellers directly through an in-app chat system powered by WebSockets.
- **Inbox** — View all your active conversations in one place.
- **User Profile** — View your listings, bio, and contact information in one place.

## Tech Stack

- **Backend:** Python, Flask, Flask-SocketIO
- **Database:** SQLite
- **Frontend:** HTML, CSS, JavaScript
- **Authentication:** Werkzeug password hashing with session management
- **Real-Time:** WebSockets via Socket.IO

## Getting Started

1. Clone the repository
```bash
git clone https://github.com/samyuktha-gorapalli/campus-marketplace.git
cd campus-marketplace
```

2. Create and activate a virtual environment
```bash
python3 -m venv venv
source venv/bin/activate
```

3. Install dependencies
```bash
pip install flask flask-socketio werkzeug pillow
```

4. Run the app
```bash
python3 app.py
```

5. Open your browser and go to `http://localhost:5000`

## Future Features

- Search and filter listings by category and price
- Delete and edit your own listings
- Price estimator using machine learning
- Email notifications for new messages
- Mark items as sold

## Contributing

This project is open to collaboration! If you have ideas for new features, improvements, or bug fixes, feel free to:

1. Fork the repository
2. Create a new branch (`git checkout -b feature/your-idea`)
3. Commit your changes (`git commit -m "Add your idea"`)
4. Push to the branch (`git push origin feature/your-idea`)
5. Open a Pull Request

Or simply reach out to me directly — always happy to connect with fellow developers and students!

## Author

Samyuktha Gorapalli — [GitHub](https://github.com/samyuktha-gorapalli)
