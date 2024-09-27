from sanic import Sanic
from sanic.response import json
from sanic_ext import Extend
from sqlalchemy import create_engine, Column, String, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.future import select

app = Sanic("MyHelloWorldApp")
app.config.CORS_ORIGINS = "*"
Extend(app)

# Database setup for MySQL
DATABASE_URL = "mysql+pymysql://username:password@localhost:3306/booksdb"  # Update with your credentials and database name
engine = create_engine(DATABASE_URL, future=True, echo=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Define the Review model
class Review(Base):
    __tablename__ = 'reviews'
    
    id = Column(String, primary_key=True)
    book_name = Column(String)
    reviewer = Column(String)
    reviewer_rating = Column(Float)

# Create the database tables if they don't exist
Base.metadata.create_all(bind=engine)

# Function to filter books using a database query
async def filter_books(rating=None, book_name=None, author_name=None, keywords=None):
    async with SessionLocal() as session:
        query = select(Review)

        if rating:
            query = query.where(Review.reviewer_rating == float(rating))
        if book_name:
            query = query.where(Review.book_name.ilike(f"%{book_name}%"))
        if author_name:
            query = query.where(Review.reviewer.ilike(f"%{author_name}%"))
        
        result = await session.execute(query)
        filtered_books = result.scalars().all()

        # If keywords are provided, filter again based on keywords
        if keywords:
            keyword_matches = []
            for keyword in keywords.split(','):
                keyword_query = select(Review).where(
                    (Review.book_name.ilike(f"%{keyword}%")) |
                    (Review.reviewer.ilike(f"%{keyword}%"))
                )
                keyword_result = await session.execute(keyword_query)
                keyword_matches.extend(keyword_result.scalars().all())
            filtered_books.extend(keyword_matches)

        return list(set(filtered_books))  # Remove duplicates

# API endpoint to filter books
@app.get("/filter_books")
async def filter_books_endpoint(request):
    rating = request.args.get('rating')
    book_name = request.args.get('book_name')
    author_name = request.args.get('reviewer')  # Using reviewer as author name
    keywords = request.args.get('keywords')
    
    filtered_books = await filter_books(rating, book_name, author_name, keywords)

    if not filtered_books:
        suggestions = []
        
        # Suggest based on different criteria
        if rating:
            async with SessionLocal() as session:
                suggestion_query = select(Review).where(Review.reviewer_rating == float(rating))
                suggestion_result = await session.execute(suggestion_query)
                suggestion_books = suggestion_result.scalars().all()
                if suggestion_books:
                    suggestions.append(f"Books with rating {rating}: {', '.join([book.book_name for book in suggestion_books])}")
        
        if book_name:
            async with SessionLocal() as session:
                suggestion_query = select(Review).where(Review.book_name.ilike(f"%{book_name}%"))
                suggestion_result = await session.execute(suggestion_query)
                suggestion_books = suggestion_result.scalars().all()
                if suggestion_books:
                    suggestions.append(f"Books containing '{book_name}': {', '.join([book.book_name for book in suggestion_books])}")

        if author_name:
            async with SessionLocal() as session:
                suggestion_query = select(Review).where(Review.reviewer.ilike(f"%{author_name}%"))
                suggestion_result = await session.execute(suggestion_query)
                suggestion_books = suggestion_result.scalars().all()
                if suggestion_books:
                    suggestions.append(f"Books reviewed by '{author_name}': {', '.join([book.book_name for book in suggestion_books])}")

        return json({"message": "No data found", "suggestions": suggestions}, status=404)

    return json([{"book_name": book.book_name, "reviewer": book.reviewer, "reviewer_rating": book.reviewer_rating} for book in filtered_books])

# Run the app
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)
