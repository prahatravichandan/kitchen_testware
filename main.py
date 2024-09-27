from sanic import Sanic
from sanic.response import json
from sanic_ext import Extend
import pandas as pd

app = Sanic("MyHelloWorldApp")
app.config.CORS_ORIGINS = "*"
Extend(app)

# Load the DataFrame
df = pd.read_csv('customer reviews.csv')

# Function to filter the DataFrame
def filter_books(df, rating=None, book_name=None, author_name=None, keywords=None):
    filtered_df = pd.DataFrame()

    # Check for matches based on provided criteria
    if rating and book_name and author_name:
        filtered_df = df[
            (df['reviewer rating'] == float(rating)) &
            (df['book name'].str.contains(book_name, case=False, na=False)) &
            (df['reviewer'].str.contains(author_name, case=False, na=False))
        ]
    elif rating and book_name:
        filtered_df = df[
            (df['reviewer rating'] == float(rating)) &
            (df['book name'].str.contains(book_name, case=False, na=False))
        ]
    elif rating and author_name:
        filtered_df = df[
            (df['reviewer rating'] == float(rating)) &
            (df['reviewer'].str.contains(author_name, case=False, na=False))
        ]
    elif book_name and author_name:
        filtered_df = df[
            (df['book name'].str.contains(book_name, case=False, na=False)) &
            (df['reviewer'].str.contains(author_name, case=False, na=False))
        ]
    elif rating:
        filtered_df = df[df['reviewer rating'] == float(rating)]
    elif book_name:
        filtered_df = df[df['book name'].str.contains(book_name, case=False, na=False)]
    elif author_name:
        filtered_df = df[df['reviewer'].str.contains(author_name, case=False, na=False)]
    
    # Check for keywords
    if keywords:
        for keyword in keywords.split(','):
            filtered_df = pd.concat([filtered_df, df[df.apply(lambda row: row.astype(str).str.contains(keyword, case=False).any(), axis=1)]])
    
    # Remove duplicates, if any
    filtered_df = filtered_df.drop_duplicates()

    return filtered_df

# API endpoint to filter books
@app.get("/filter_books")
async def filter_books_endpoint(request):
    rating = request.args.get('rating')
    book_name = request.args.get('book_name')
    author_name = request.args.get('reviewer')  # Corrected from 'reviewer' to 'author_name'
    keywords = request.args.get('keywords')
    
    filtered_df = filter_books(df, rating, book_name, author_name, keywords)
    
    # Check if the filtered DataFrame is empty
    if filtered_df.empty:
        suggestions = []
        
        # Suggest based on different criteria
        if rating:
            suggestion_df = df[df['reviewer rating'] == float(rating)]
            if not suggestion_df.empty:
                suggestions.append(f"Books with rating {rating}: {', '.join(suggestion_df['book name'].tolist())}")
        
        if book_name:
            suggestion_df = df[df['book name'].str.contains(book_name, case=False, na=False)]
            if not suggestion_df.empty:
                suggestions.append(f"Books containing '{book_name}': {', '.join(suggestion_df['book name'].tolist())}")
        
        if author_name:
            suggestion_df = df[df['reviewer'].str.contains(author_name, case=False, na=False)]
            if not suggestion_df.empty:
                suggestions.append(f"Books reviewed by '{author_name}': {', '.join(suggestion_df['book name'].tolist())}")

        return json({"message": "No data found", "suggestions": suggestions}, status=404)
    
    return json(filtered_df.to_dict(orient='records'))

# Run the app
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)
