"""Main application code."""
from flask import Flask
from flask import request
from flask import session
from flask import render_template, url_for, redirect
from flask import jsonify

import pdb
from sqlalchemy.orm import scoped_session
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine, exists
from sqlalchemy.orm.exc import NoResultFound
import sys

# from gevent.pywsgi import WSGIServer

from settings import DB_URL
from settings import Key
# from models import Songs, GenreProf, Personality

print("Setting up app...")
app = Flask(__name__)
app.secret_key = Key
print("Creating database link and session...")
engine = create_engine(DB_URL)
db_session = scoped_session(sessionmaker(bind=engine))


@app.route('/', methods=['GET'])
def index():
    """Index Page."""
    return render_template("index.html")


@app.route('/api/', methods=['GET', 'POST'])
def admin():
    """Admin Index Page."""
    if request.method == "GET":
        response = get_next_file()
        return jsonify(response)
    if request.method == "POST":
        pdb.set_trace()
        ret = process_annotation(request.data)
        if ret:
            next_song = get_next_file()
        return jsonify(response)


def get_next_file():
    """Get the next un-annotated file for annotation."""
    response = {
        "task": {
            "feedback": "none",
            "visualization": "spectrogram",
            "annotationTag": [],    # Add annotation sentences here
            "url": "/static/wav/spectrogram_demo_doorknock_mono.wav",   # URL for the audio file
            "proximityTag": [],
            "alwaysShowTags": "True",
            "instructions": [
                "Highlight &amp; Label the files with sentences.",
                "2. &nbsp; Click the play button and listen to the recording.",
                "3. &nbsp; For each sentence that you hear click and drag on the visualization to create a new annotation.",
                "4. &nbsp; When creating a new annotation be as precise as possible.",
                "5. &nbsp; Select the appropriate sentence for the selected portion of the audio",
                "6. &nbsp; Click Submit when all the sentences are marked."
            ]
        }
    }
    return response


if __name__ == "__main__":
    if len(sys.argv) <= 1:
        print("Usage:\n\tpython app.py [host address] [port]\n")
        sys.exit(0)

    IP_addr = sys.argv[1]
    port = sys.argv[2]
    try:
        print("Running server...")
        app.run(host=IP_addr, debug=True, port=int(port))

    # http_server = WSGIServer((IP_addr, int(port)), app)
    # print("Server running on http://{}:{}".format(IP_addr, port))
    # try:
    #     http_server.serve_forever()
    except KeyboardInterrupt:
        print("Exiting server")
        sys.exit(0)
