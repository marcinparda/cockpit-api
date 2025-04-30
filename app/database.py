from sqlmodel import create_engine, SQLModel

DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(DATABASE_URL)


def init_db():
    SQLModel.metadata.create_all(engine)
