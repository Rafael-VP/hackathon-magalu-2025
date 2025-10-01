# server.py
from flask import Flask, request, jsonify
from threading import Lock
import time

MAX_CONNECTIONS = 2

app = Flask(__name__)

rooms = {}
lock = Lock()

@app.route('/join_room', methods=['POST'])
def join_room():
    data = request.json
    room_name = data.get('room_name')
    user_id = data.get('user_id')

    with lock:
        if room_name not in rooms:
            rooms[room_name] = {
                "users": set(),
                "status": "waiting",
                "timers_started": {},
                "cancelled_by": None,
                "duration_seconds": None, # ADDED: To store the session duration
                "started_at": None       # ADDED: To store the universal start time
            }
        
        room = rooms[room_name]
        if len(room["users"]) < MAX_CONNECTIONS or user_id in room["users"]:
            room["users"].add(user_id)
            room["timers_started"][user_id] = False
        else:
            return jsonify({"error": "Room is full"}), 409

    response_data = rooms[room_name].copy()
    response_data["users"] = list(rooms[room_name]["users"])
    return jsonify(response_data)

@app.route('/start_timer', methods=['POST'])
def start_timer():
    data = request.json
    room_name = data.get('room_name')
    user_id = data.get('user_id')
    duration_seconds = data.get('duration_seconds')

    with lock:
        if room_name in rooms and user_id in rooms[room_name]["users"]:
            room = rooms[room_name]
            room["timers_started"][user_id] = True
            
            # The first user to start sets the duration for the room
            if room["duration_seconds"] is None:
                room["duration_seconds"] = duration_seconds
            
            # If all users have now started, officially begin the session
            if len(room["users"]) == MAX_CONNECTIONS and all(room["timers_started"].values()):
                room["status"] = "running"
                room["started_at"] = time.time() # Record universal start time
    
    response_data = rooms.get(room_name, {}).copy()
    response_data["users"] = list(response_data.get("users", set()))
    return jsonify(response_data), 200

# ... (The /cancel_timer and /room_status endpoints remain the same) ...
@app.route('/cancel_timer', methods=['POST'])
def cancel_timer():
    data = request.json
    room_name = data.get('room_name')
    user_id = data.get('user_id')
    with lock:
        if room_name in rooms:
            rooms[room_name]["status"] = "cancelled"
            rooms[room_name]["cancelled_by"] = user_id
    return jsonify({"message": "Session cancelled"}), 200

@app.route('/room_status', methods=['GET'])
def room_status():
    room_name = request.args.get('room_name')
    with lock:
        room_data = rooms.get(room_name)
        if room_data:
            serializable_data = room_data.copy()
            serializable_data["users"] = list(room_data["users"])
            return jsonify(serializable_data)
    return jsonify({"error": "Room not found"}), 404

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
