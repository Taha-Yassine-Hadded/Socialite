# Socialite

## Overview
Socialite is a Django-based social platform designed to inspire users to explore the world and share their travel experiences. It enables users to connect, create communities, and engage through posts, photos, and discussions about global destinations, fostering cultural exchange and communication among travelers worldwide.

## Features
- **Real-Time Interaction**: Engage with other users via live chat and receive instant updates through WebSocket notifications.
- **User Authentication**: Secure access and account management using Django's authentication system.
- **Admin Panel**: Efficient platform administration with Django Admin for managing users, posts, and communities.
- **Community Building**: Create and join communities to share travel stories, photos, and tips.
- **Responsive Design**: Styled with Tailwind CSS for a seamless experience across devices.

## Technologies
- **Backend**: Django, MongoDB
- **Frontend**: Django Templates, Tailwind CSS
- **Real-Time Features**: WebSockets
- **Version Control**: Git, GitHub

## Installation
1. Clone the repository:
   ```
   git clone https://github.com/your-username/socialite.git
   ```
2. Navigate to the project directory:
   ```
   cd socialite
   ```
3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
4. Set up MongoDB and configure the connection in `settings.py`.
5. Run migrations:
   ```
   python manage.py migrate
   ```
6. Start the development server:
   ```
   python manage.py runserver
   ```

## Usage
- Register or log in to create a profile.
- Explore communities, share posts, and connect with travelers.
- Use the chat feature for real-time discussions.
- Admins can manage content via the Django Admin panel.

## Contributing
1. Fork the repository.
2. Create a new branch (`git checkout -b feature-branch`).
3. Commit your changes (`git commit -m "Add feature"`).
4. Push to the branch (`git push origin feature-branch`).
5. Open a pull request.

## License
This project is licensed under the MIT License.
