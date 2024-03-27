
from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, Depends, HTTPException, BackgroundTasks, status
from sqlalchemy import create_engine, Column, Integer, String,ForeignKey  
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session,relationship
from pydantic import BaseModel
from typing import Optional, List

app = FastAPI(
    description="<b>LMS API </b>",
    title="LMS APIs",
    summary="Library management",
    version="0.1.0",
    contact={"name": "Varsha mahale", "Email": "varshaofficialuse@gmail.com"},
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Database Schema model
class Book(Base):
    __tablename__ = "books"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    author = Column(String)
    publication_year = Column(Integer, index=True)
    reviews = relationship("Review", back_populates="book")


class Review(Base):
    __tablename__ = "reviews"
    id = Column(Integer, primary_key=True, index=True)
    review = Column(String, index=True)
    rating = Column(Integer, index=True)
    book_id = Column(Integer, ForeignKey('books.id'))  
    book = relationship("Book", back_populates="reviews")

Base.metadata.drop_all(bind=engine)
Base.metadata.create_all(bind=engine)

# Dependency to get the database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Pydantic model for request data
class BookCreate(BaseModel):
    title: str
    author: str
    publication_year: int

class ReviewCreate(BaseModel):
    review: str
    rating: int

# Pydantic model for response data
class BookResponse(BaseModel):
    id: int
    title: str
    author: str
    publication_year: int

class ReviewResponse(BaseModel):
    id: int
    review: str
    rating: int

# Database operations
def add_book_to_db(db: Session, book: BookCreate):
    db_book = Book(**book.dict())
    db.add(db_book)
    db.commit()
    db.refresh(db_book)
    return db_book

def add_review_to_db(db: Session, review: ReviewCreate, book_id: int):
    db_review = Review(**review.dict(), book_id=book_id)
    db.add(db_review)
    db.commit()
    db.refresh(db_review)
    return db_review

def get_books_from_db(db: Session):
    return db.query(Book).all()

def get_reviews_from_db(db: Session, book_id: int):
    return db.query(Review).filter(Review.book_id == book_id).all()

# API endpoints
@app.post("/books/", response_model=BookResponse)
async def create_book(book: BookCreate, db: Session = Depends(get_db)):
    return add_book_to_db(db, book)

@app.post("/reviews/{book_id}", response_model=ReviewResponse)
async def create_review(book_id: int, review: ReviewCreate, db: Session = Depends(get_db)):
    return add_review_to_db(db, review, book_id)

@app.get("/books/", response_model=List[BookResponse])
async def read_books(db: Session = Depends(get_db)):
    return get_books_from_db(db)

@app.get("/reviews/{book_id}", response_model=List[ReviewResponse])
async def read_reviews(book_id: int, db: Session = Depends(get_db)):
    return get_reviews_from_db(db, book_id)

# Run the FastAPI application using Uvicorn
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
