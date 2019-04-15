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
    annotated = db_session.query(Audio).filter(Audio.annotated == "True").count()
    not_annotated = db_session.query(Audio).filter(Audio.annotated == "False").count()
    skipped = db_session.query(Audio).filter(Audio.annotated == "Skip").count()
    return render_template("index.html", annotated=annotated, not_annotated=not_annotated, skipped=skipped)


@app.route('/complete', methods=['GET'])
def complete():
    """Index Page."""
    return render_template("complete.html")


@app.route('/api/', methods=['GET', 'POST'])
def admin():
    """Admin Index Page."""
    if request.method == "GET":
        response = get_next_file()
        return jsonify(response)
    if request.method == "POST":
        # pdb.set_trace()
        form = request.form
        ret = False
        if "skip" in form:
            if "taskid" in form:
                skip_file(int(form["taskid"]))
                return redirect(url_for("index"))
        else:
            ret = process_annotation(request.get_json())

        if ret:
            next_song = get_next_file()
            return jsonify(next_song)
        else:
            abort(405)


def skip_file(fileid):
    file = db_session.query(Audio).filter(Audio.id_ == fileid).one()
    file.annotated = "Skip"
    db_session.commit()


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
                "Highlight &amp; Label the files with phrases.",
                "1. &nbsp; Click the play button and listen to the recording.",
                "2. &nbsp; For each phrase that you hear click and drag on the visualization to create a new annotation.",
                "3. &nbsp; When creating a new annotation be as precise as possible.",
                "4. &nbsp; Select the appropriate sentence for the selected portion of the audio",
                "5. &nbsp; You can listen to a selected portion by pressing the play button on top of the portion and make adjustments accordingly.",
                "6. &nbsp; Click Submit when all the phrases are marked. Annotation will not submit if all phrases are not marked."
            ]
        }
    }
    not_annotated = db_session.query(Audio).filter(Audio.annotated == "False").first()
    if not_annotated is None:
        return None

    audio_path = not_annotated.audio_file
    sentences = db_session.query(Sentences).filter(Sentences.audio_id == not_annotated.id_).all()

    if len(sentences) == 0:
        not_annotated.annotated = "Skip"
        db_session.commit()
        return get_next_file()

    annotatation_tags = [x.content for x in sentences]
    response["task"]["taskid"] = not_annotated.id_
    response["task"]["url"] = audio_path
    response["task"]["annotationTag"] = annotatation_tags
    return response


def process_annotation(data):
    """Process the annotation data."""
    try:
        task_id = data["task_id"]
        annotations = data["annotations"]
    except KeyError:
        return False
    # pdb.set_trace()
    try:
        audio = db_session.query(Audio).filter(Audio.id_ == task_id).one()
        assert audio.annotated == "False"
        sentences = db_session.query(Sentences).filter(Sentences.audio_id == task_id).all()
        assert len(sentences) == len(annotations)
    except (AssertionError, NoResultFound):
        return False

    for annotation in annotations:
        ann = Annotations(task_id, annotation["annotation"],
                          annotation["start"], annotation["end"])
        db_session.add(ann)

    audio.annotated = "True"
    db_session.commit()

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
