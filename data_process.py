"""Add new data to database."""
import contextlib
import os
import string
import wave

from models import get_debug_session, Audio, Sentences
from settings import DB_URL, text_path, prefix

import pdb


def process_data(filename, prefix):
    """Process the data before adding to db."""
    f = open(filename, "r")
    fnames = []
    texts = []
    for line in f:
        data = line.split('"')
        fname = data[0].strip('(').strip()
        fname = os.path.join(prefix, fname) + ".wav"
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

        t = text.translate(str.maketrans('', '', string.punctuation))
        t = t.split()
        t = [x for x in t if len(x.strip()) > 0]
        num_words = len(t)
        sentences = []
        with contextlib.closing(wave.open(fname, 'r')) as f:
            frames = f.getnframes()
            rate = f.getframerate()
            duration = frames / float(rate)
            if duration > mean_len:
                num_parts = int(duration // mean_len) + 1
                part_len = num_words // num_parts
                for i in range(num_parts):
                    start = int(i * part_len)
                    end = int((i+1) * part_len)
                    if i == num_parts - 1:
                        sentences.append(" ".join(t[start::]))
                    else:
                        sentences.append(" ".join(t[start: end]))
                sentences = [x for x in sentences if len(x.strip()) > 0]
                count += 1
                add_in_db(fname, sentences, session)
        print("Processes files: ", count)


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
    fnames, texts = process_data(text_path, prefix)
    add_to_db(fnames, texts)
