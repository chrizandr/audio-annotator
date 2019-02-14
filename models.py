"""Models for Hydra Classes."""
from settings import DB_URL
from sqlalchemy import create_engine, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, Float
from sqlalchemy.orm import sessionmaker

import pdb


Base = declarative_base()


class Audio(Base):
    """Model for Audio files.

    The audio files for which annotation needs to be done.
    """

    __tablename__ = "audio"

    id_ = Column(Integer, primary_key=True)
    audio_file = Column(String, unique=True)
    annotated = Column(String)

    def __init__(self, audio_file):
        """Create admin."""
        self.annotated = "False"
        self.audio_file = audio_file

    def __repr__(self):
        """Verbose object name."""
        return "<id_='%s', annotated='%s'>" % (self.id_, self.annotated)


class Sentences(Base):
    """Sentences present in a song."""

    __tablename__ = "sentences"

    id_ = Column(Integer, primary_key=True)
    audio_id = Column(Integer, ForeignKey("audio.id_"), unique=False)
    content = Column(String(convert_unicode=True))

    def __init__(self, audio_id, content):
        """Create new instance."""
        self.audio_id = audio_id
        self.content = content

    def __repr__(self):
        """Verbose object name."""
        return "<audio_id='%s', content='%s'>" % (self.audio_id, self.content)


class Annotations(Base):
    """Annotations for the sentences."""

    __tablename__ = "annotations"

    id_ = Column(Integer, primary_key=True)
    audio_id = Column(Integer, ForeignKey("audio.id_"), unique=False)
    sentence = Column(String(convert_unicode=True))
    start_time = Column(Float)
    end_time = Column(Float)

    def __init__(self, audio_id, sentence, start_time, end_time):
        """Create new instance."""
        self.audio_id = audio_id
        self.sentence = sentence
        self.start_time = start_time
        self.end_time = end_time

    def __repr__(self):
        """Verbose object name."""
        return "<audio_id='%s', sentence='%s'>" % (self.audio_id, self.sentence)


def get_debug_session(DB_URL):
    """Get a DB session for debugging."""
    engine = create_engine(DB_URL)
    Session = sessionmaker(bind=engine)
    session = Session()
    return session


def setup(DB_URL):
    """Setup."""
    # Create database tables
    engine = create_engine(DB_URL)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    return session


if __name__ == "__main__":
    session = setup(DB_URL)
    # session = get_debug_session(DB_URL)
    # pdb.set_trace()
