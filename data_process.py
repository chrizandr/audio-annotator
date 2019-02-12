import numpy as np
import os


def process_data(filename, prefix):
    f = open(filename, "r")
    fnames = []
    texts = []
    for line in f:
        data = line.split('"')
        fname = data[0].strip('(').strip()
        text = data[1].strip()
        fnames.append(fname)
        texts.append(text)
    f.close()

    return fnames, texts


if __name__ == "__main__":
    text_path = "/home/chris/tel_f_tts/txt.done.data"
    prefix = "/ssd_scratch/cvit/chris/Telugu/wavs/"
    train_file = "filelists/ljs_audio_text_train_filelist.txt"
    val_file = "filelists/ljs_audio_text_val_filelist.txt"

    data = process_data(text_path, prefix)
    shuffle_into_files(train_file, val_file, data)
