from sqlalchemy import create_engine, Column, Integer, Float, String, DateTime
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime


engine = create_engine('sqlite:///vkbot.sqlite')
Base = declarative_base()


def get_session():
    Session = sessionmaker(bind=engine)
    session = Session()
    return session


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    username = Column(String(255), nullable=False, default="Игрок")
    first_name = Column(String(255), nullable=False)
    last_name = Column(String(255), nullable=False)
    user_id = Column(String(255), unique=True, nullable=False)
    chat_id = Column(String(255), nullable=False)
    beer_coin = Column(Integer(), nullable=False, default=0)
    liters = Column(Float(), nullable=False, default=0)
    last_activity = Column(DateTime, default=datetime(1970, 1, 1))
    updated_at = Column(DateTime, default=datetime.now)
    created_at = Column(DateTime, default=datetime.now)


def add_user(user_id, chat_id, first_name, last_name):
    session = get_session()
    user = session.query(User).filter_by(user_id=user_id).first()
    if user is None:
        user = User(
            user_id=user_id,
            chat_id=chat_id,
            first_name=first_name,
            last_name=last_name
        )
        session.add(user)
        session.commit()


Base.metadata.create_all(bind=engine)
# Base.metadata.drop_all(bind=engine)
