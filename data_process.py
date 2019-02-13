"""Add new data to database."""
import contextlib
import os
import wave

from models import get_debug_session, Audio, Sentences
from settings import DB_URL


def process_data(filename, prefix):
    """Process the data before adding to db."""
    f = open(filename, "r")
    fnames = []
    texts = []
    for line in f:
        data = line.split('"')
        fname = data[0].strip('(').strip()
        os.path.join(prefix, fname)
        text = data[1].strip()
        fnames.append(fname)
        texts.append(text)
    f.close()

    return fnames, texts


def add_to_db(fnames, texts):
    """Split into sentences and add to DB."""
    session = get_debug_session(DB_URL)
    mean_len = 6.5
    total = len(fnames)
    count = 0
    for fname, text in zip(fnames, texts):
        print("Processing ", (100.0 * count)/total, "%")
        count += 1

        t = text.split()
        sentences = []
        with contextlib.closing(wave.open(fname, 'r')) as f:
            frames = f.getnframes()
            rate = f.getframerate()
            duration = frames / float(rate)
            if duration > mean_len:
                splits = (duration // mean_len) + 1
                for i in range(splits):
                    start = int(i * mean_len)
                    end = int((i+1) * mean_len)
                    sentences.append(t[start: end])

        add_in_db(fname, sentences, session)


def add_in_db(audio, sentences, session):
    """Add audio and coresponding sentences to DB."""
    a = Audio(audio)
    session.add(a)
    session.flush()
    for s in sentences:
        sen = Sentences(a.id_, s)
        session.add(sen)
    session.commit()


if __name__ == "__main__":
    text_path = "/home/chris/tel_f_tts/txt.done.data"
    prefix = "/home/chris/audio-annotator/static/wav/Telugu/"
    train_file = "filelists/ljs_audio_text_train_filelist.txt"
    val_file = "filelists/ljs_audio_text_val_filelist.txt"

    fnames, texts = process_data(text_path, prefix)
    add_to_db(fnames, texts)
