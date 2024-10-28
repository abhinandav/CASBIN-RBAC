from sqlalchemy import Column, Integer, String, create_engine,DateTime, func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

DATABASE_URL = "postgresql://postgres:1234@localhost/casbin"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()



class Employee(Base):
    __tablename__ = "employee"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    position = Column(String)
    status = Column(String)


class Items(Base):
    __tablename__ = "item"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    price = Column(Integer, nullable=True)
    tax = Column(Integer, nullable=True)
    created = Column(DateTime, default=func.now(), nullable=True)
    updated = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=True)

Base.metadata.create_all(bind=engine)




def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()