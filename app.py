import os

from dotenv import load_dotenv
from flask import Flask, render_template
from flask_login import LoginManager, current_user
from flask_socketio import SocketIO, join_room, leave_room

from authentication import authentication
from chat import chat
from dashboard import dashboard_operations
from database import get_user, save_message, fetch_latest_message, db_initialize_sequence

# Load environment variables
load_dotenv("./.env")

app = Flask(__name__)

# Secret key fallback
app.config["SECRET_KEY"] = os.getenv("FLASK_SECRETKEY") or "fallback_super_secret_key"

login_manager = LoginManager(app)
socketio = SocketIO(app)

# Blueprints
app.register_blueprint(authentication)
app.register_blueprint(chat)
app.register_blueprint(dashboard_operations)

# Jinja2 Filters
app.jinja_env.filters['fetch_latest_message'] = fetch_latest_message

# Initialize sequence
db_initialize_sequence("room_id")


# User loader for flask-login
@login_manager.user_loader
def load_user(username):
    return get_user(username)


@app.route('/')
def home():
    if current_user.is_authenticated:
        return render_template(
            "index.html",
            logged_in=current_user.is_authenticated,
            current_user=current_user
        )
    return render_template("index.html")


# SocketIO Events
@socketio.on("join_room")
def handle_join_room_event(data):
    app.logger.info(f"{data['username']} has joined the room {data['room_id']}")
    join_room(data["room_id"])
    socketio.emit("join_room_announcement", data)


@socketio.on("send_message")
def handle_send_message_event(data):
    app.logger.info(f"{data['username']} sent message to room {data['room_id']}: {data['message']}")
    save_message(room_id=data['room_id'], text=data['message'], sender=data['username'])
    socketio.emit("receive_message", data, room=data["room_id"])


@socketio.on("leave_room")
def handle_leave_room_event(data):
    app.logger.info(f"{data['username']} has left the room {data['room_id']}")
    leave_room(data['room_id'])
    socketio.emit('leave_room_announcement', data, room=data['room_id'])


if __name__ == '__main__':
    socketio.run(app, debug=True)
