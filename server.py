# server.py
from flask import Flask, request, jsonify
from threading import Lock

app = Flask(__name__)

# In-memory storage for rooms. In a real app, you'd use a database.
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
                "status": "waiting", # waiting, running, cancelled
                "timers_started": {},
                "cancelled_by": None
            }
        
        room = rooms[room_name]
        if len(room["users"]) < 2 or user_id in room["users"]:
            room["users"].add(user_id)
            room["timers_started"][user_id] = False
        else:
            return jsonify({"error": "Room is full"}), 409

    #return jsonify(rooms[room_name], users=list(rooms[room_name]["users"]))
    # Correct approach
    response_data = rooms[room_name].copy()
    response_data["users"] = list(rooms[room_name]["users"])
    return jsonify(response_data)

@app.route('/start_timer', methods=['POST'])
def start_timer():
    data = request.json
    room_name = data.get('room_name')
    user_id = data.get('user_id')

    with lock:
        if room_name in rooms and user_id in rooms[room_name]["users"]:
            rooms[room_name]["timers_started"][user_id] = True
            # If all users have started, set the room to running
            if all(rooms[room_name]["timers_started"].values()):
                rooms[room_name]["status"] = "running"
    
    return jsonify(rooms.get(room_name, {})), 200

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
            # Create a serializable copy
            serializable_data = room_data.copy()
            serializable_data["users"] = list(room_data["users"])
            return jsonify(serializable_data)
    return jsonify({"error": "Room not found"}), 404
    
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5050)
