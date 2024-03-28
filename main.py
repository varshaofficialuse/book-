
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

def get_all_books_from_db(db: Session):
    return db.query(Book).all()

def get_reviews_from_db(db: Session, book_id: int):
    return db.query(Review).filter(Review.book_id == book_id).all()

def get_books_from_db(db: Session, author: Optional[str] = None, publication_year: Optional[int] = None):
    query = db.query(Book)
    if author:
        query = query.filter(Book.author == author)
    if publication_year:
        query = query.filter(Book.publication_year == publication_year)
    return query.all()

# Update Book
def update_book_in_db(db: Session, book_id: int, book_update: BookCreate):
    db_book = db.query(Book).filter(Book.id == book_id).first()
    if db_book:
        for key, value in book_update.dict().items():
            setattr(db_book, key, value)
        db.commit()
        db.refresh(db_book)
        return db_book
    else:
        raise HTTPException(status_code=404, detail="Book not found")

# Delete Book
def delete_book_from_db(db: Session, book_id: int):
    db_book = db.query(Book).filter(Book.id == book_id).first()
    if db_book:
        db.delete(db_book)
        db.commit()
        return db_book
    else:
        raise HTTPException(status_code=404, detail="Book not found")

# Update Review
def update_review_in_db(db: Session, book_id: int, review_id: int, review_update: ReviewCreate):
    db_review = db.query(Review).filter(Review.id == review_id, Review.book_id == book_id).first()
    if db_review:
        for key, value in review_update.dict().items():
            setattr(db_review, key, value)
        db.commit()
        db.refresh(db_review)
        return db_review
    else:
        raise HTTPException(status_code=404, detail="Review not found")

# Delete Review
def delete_review_from_db(db: Session, book_id: int, review_id: int):
    db_review = db.query(Review).filter(Review.id == review_id, Review.book_id == book_id).first()
    if db_review:
        db.delete(db_review)
        db.commit()
        return db_review
    else:
        raise HTTPException(status_code=404, detail="Review not found")



# API endpoints
@app.post("/books/", response_model=BookResponse,summary="Create a New Book")
async def create_book(book: BookCreate, db: Session = Depends(get_db)):
    return add_book_to_db(db, book)

@app.get("/allbooks/", response_model=List[BookResponse],summary="Read All the Books")
async def read_books(db: Session = Depends(get_db)):
    return get_all_books_from_db(db)


@app.put("/books/{book_id}", response_model=BookResponse,summary="Update the Book")
async def update_book(book_id: int, book_update: BookCreate, db: Session = Depends(get_db)):
    return update_book_in_db(db, book_id, book_update)

# Delete a book
@app.delete("/books/{book_id}", response_model=BookResponse,summary="Delete Book")
async def delete_book(book_id: int, db: Session = Depends(get_db)):
    return delete_book_from_db(db, book_id)




@app.post("/reviews/{book_id}", response_model=ReviewResponse,summary="Create a review for a book")
async def create_review(book_id: int, review: ReviewCreate, db: Session = Depends(get_db)):
    return add_review_to_db(db, review, book_id)


@app.get("/reviews/{book_id}", response_model=List[ReviewResponse],summary="read all the reviews by the book ID")
async def read_reviews(book_id: int, db: Session = Depends(get_db)):
    return get_reviews_from_db(db, book_id)

# Update a review
@app.put("/reviews/{book_id}/{review_id}", response_model=ReviewResponse,summary="Update the reviews of book by ID")
async def update_review(book_id: int, review_id: int, review_update: ReviewCreate, db: Session = Depends(get_db)):
    return update_review_in_db(db, book_id, review_id, review_update)

# Delete a review
@app.delete("/reviews/{book_id}/{review_id}", response_model=ReviewResponse,summary="Delete a Book")
async def delete_review(book_id: int, review_id: int, db: Session = Depends(get_db)):
    return delete_review_from_db(db, book_id, review_id)




@app.get("/books/", response_model=List[BookResponse],tags=["Search a Book by Author or publication year"])
async def read_books(author: Optional[str] = None, publication_year: Optional[int] = None, db: Session = Depends(get_db)):
    return get_books_from_db(db, author, publication_year)


# Update the database operation function to handle filtering



# Run the FastAPI application using Uvicorn
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
