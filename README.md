# 🌍 Socialite

## 📖 Overview
Socialite is a Django-based social platform that inspires users to explore the world and share their travel experiences. Connect with others, create communities, and engage through posts, photos, and discussions about global destinations, fostering cultural exchange among travelers worldwide.

## ✨ Features
- **💬 Real-Time Interaction**: Live chat and instant WebSocket notifications.
- **🔒 User Authentication**: Secure access with Django authentication.
- **🛠️ Admin Panel**: Manage users, posts, and communities via Django Admin.
- **🌐 Community Building**: Share travel stories, photos, and tips in communities.
- **📱 Responsive Design**: Sleek UI with Tailwind CSS for all devices.

## 🛠️ Technologies
- **Backend**: Django, MongoDB
- **Frontend**: Django Templates, Tailwind CSS
- **Real-Time**: WebSockets
- **Version Control**: Git, GitHub

## 🚀 Installation
1. Clone the repository:
   ```
   git clone https://github.com/Taha-Yassine-Hadded/Socialite.git
   ```
2. Navigate to the project directory:
   ```
   cd Socialite
   ```
3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
4. Set up MongoDB and configure in `settings.py`.
5. Run migrations:
   ```
   python manage.py migrate
   ```
6. Start the server:
   ```
   python manage.py runserver
   ```

## 📋 Usage
- 🧑‍💻 Register or log in to create a profile.
- 🌎 Explore communities and share posts.
- 💬 Use real-time chat for discussions.
- 🔧 Admins can manage content via Django Admin.

##NEW FEATURES FOR PREMIUM/BUSINESS/FREEMIUM
- **🔒 Premium Features**: Exclusive content, ad-free experience.
- **📈 Analytics**: Track community growth and engagement.
- **🔒 Content Moderation**: Moderate posts and comments
commands to run:

pip install python-dateutil
python manage.py makemigrations
python manage.py migrate
pip install stripe requests python-dateutil