# audio-annotator

[![MIT licensed](https://img.shields.io/badge/license-BSD2-blue.svg)](https://github.com/CrowdCurio/audio-annotator/blob/master/LICENSE.txt)

### Description
audio-annotator is a web interface that allows users to annotate audio recordings.

It has 3 types of audio visualizations (wavesurfer.params.visualization)
   1. invisible (appears as a blank rectangle that users can draw regions on)
   2. spectrogram (audio file is represented by a spectrogram that users can draw regions on)
   3. waveform (audio file is represented by a waveform that users can draw regions on)

Screenshot:
<kbd>
![audio-annotator screenshot](https://github.com/CrowdCurio/audio-annotator/blob/master/static/img/task-interface.png)
</kbd>

Annotator is interfaced with a Python backend based on Flask.

Data is served and pushed at `/api` path. You need to run the server using:

`python main.py [host] [port]`

The `/` path will serve the annotation program, most of which is in Javascript.

This will communicate with the `/api` path for audio files and annotations

### Usage
- Install all requirements: `pip install -r requirements.txt`

- Add all data into a file in the following format:
  ```
  ...
  audio1.mp3|This is the text that is spoken in audio1.mp3
  audio2.mp3|This is the text that is spoken in audio2.mp3
  audio3.mp3|This is the text that is spoken in audio3.mp3
  ....
  ```
  NOTE: Only copy the name of the audio file, not the entire path. Each entry in new line. Don't include any other info in this file.

  Add the path of this file into `text_path` variable in `settings.py`

- Copy all the audio files into `static/wav/[Dataset]/`, where `[Dataset]` is a name for the specific dataset. [You will have to create an appropriate folder]. Update the path in `settings.py` on the `prefix` variable.

- Prepare the database and split the audio text into correct size phrases:

  Run:

  ```
  python database.py        # This will create a database.
  python data_process.py    # This will split text from each audio file and add them to the database.
  ```

- Run the server: `python main.py 0.0.0.0 8080`

  Alternatively, you can also run a multi-threaded server for multiple requests using gunicorn: `gunicorn --workers 10 --timeout 60 --bind 0.0.0.0:8088 main:app`

  Annotator should be running on `http://localhost:8080`
