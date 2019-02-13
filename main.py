"""Server code."""
from flask import Flask
from flask import request
from flask import render_template, url_for, redirect, abort
from flask import jsonify

import pdb
import sys

from sqlalchemy import create_engine
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.orm import scoped_session
from sqlalchemy.orm import sessionmaker

# from gevent.pywsgi import WSGIServer

from models import Audio, Sentences, Annotations
from settings import DB_URL
from settings import Key

print("Setting up app...")
app = Flask(__name__)
app.secret_key = Key
print("Creating database link and db_session...")
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
        ret, response = get_next_file()
        if ret:
            return jsonify(response)
        else:
            abort(404)
    if request.method == "POST":
        ret = process_annotation(request.get_json())
        if ret:
            next_song = get_next_file()
            return jsonify(next_song)
        else:
            abort(405)


def get_next_file():
    """Get the next un-annotated file for annotation."""
    response = {
        "task": {
            "taskid": "22",
            "feedback": "none",
            "visualization": "spectrogram",
            "annotationTag": ["Test", "test"],    # Add annotation sentences here
            "url": "/static/wav/paris.wav",   # URL for the audio file
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
    return True, response
    try:
        not_annotated = db_session.query(Audio).filter(Audio.annotated == "False").one()
        audio_path = not_annotated.audio_file
    except NoResultFound:
        return False, None

    sentences = db_session.query(Sentences).filter(Sentences.audio_id == not_annotated.id_)
    if len(sentences) == 0:
        return False, None

    annotatation_tags = [x.content for x in sentences]
    response["taskid"] = not_annotated.id_
    response["url"] += audio_path
    response["annotationTag"] = annotatation_tags


def process_annotation(data):
    """Process the annotation data."""
    try:
        task_id = data["task_id"]
        annotations = data["annotations"]
    except KeyError:
        return False

    try:
        audio = db_session.query(Audio).filter(Audio.id_ == task_id).one()
        assert audio.annotated == "False"
        sentences = db_session.query(Sentences).filter(Sentences.audio_id == task_id)
        assert len(sentences) == len(annotations)
    except (AssertionError, NoResultFound):
        return False

    for annotation in annotations:
        ann = Annotations(task_id, annotation["annotation"],
                          annotation["start"], annotation["end"])
        db_session.add(ann)

    audio.annotated = True
    db_session.commit()
    print("Jai Mishra")

    return True



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
