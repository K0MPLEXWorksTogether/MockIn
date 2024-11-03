from flask import Flask, render_template, session, redirect, request
from flask import url_for
from flask_socketio import join_room, leave_room, send, SocketIO
import random
from string import ascii_uppercase

app = Flask(__name__)
app.config["SECRET_KEY"] = "somethingRandom"
socketIO = SocketIO(app)

rooms = dict()
def generateUniqueCode(length: int) -> int:
    while True:
        code = ""
        for _ in range(length):
            code += random.choice(ascii_uppercase)
        
        if code not in rooms:
            break

    return code

@app.route("/", methods=["GET", "POST"])
def home():
    session.clear()
    if request.method == "POST":
        name = request.form.get("name")
        code = request.form.get("code")
        join = request.form.get("join", False)
        create = request.form.get("create", False)

        if not name:
            return render_template("home.html", error="Please Enter A Name.", code=code, name=name)

        if join != False and not code:
            return render_template("home.html", error="Please Enter A Room Code.", code=code, name=name)

        room = code
        if create != False:
            room = generateUniqueCode(4)
            rooms[room] = {"members": 0, "messages": []}
        elif code not in rooms:
            return render_template("home.html", error="Room Does Not Exist.", code=code, name=name)

        session["room"] = room
        session["name"] = name

        return redirect(url_for("room"))
    return render_template("home.html")

@app.route("/room")
def room():
    room = session.get("room")
    if room is None or session.get("name") is None or room not in rooms:
        return redirect(url_for("home"))
    return render_template("room.html", code=room, messages=rooms[room]["messages"])

@socketIO.on("connect")
def connect(auth):
    room = session.get("room")
    name = session.get("name")

    if not room or not name:
        return
    
    if room not in rooms:
        leave_room(room)
        return

    join_room(room)
    send({"name": name, "message": "has entered the room."}, to=room)
    rooms[room]["members"] += 1

@socketIO.on("disconnect")
def disconnect():
    room = session.get("room")
    name = session.get("name")

    leave_room(room)

    if room in rooms:
        rooms[room]["members"] -= 1

        if rooms[room]["members"] <= 0:
            del rooms[room]

    send({"name": name, "message": "has left the room."}, to=room)

@socketIO.on("message")
def message(data):
    room = session.get("room")
    if room not in rooms:
        return

    content = {
        "name": session.get("name"),
        "message": data["data"]
    }

    send(content, to=room)
    rooms[room]["messages"].append(content)

if __name__ == "__main__":
    socketIO.run(app, debug=True)