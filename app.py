# app.py
from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from db_connector import get_db_connection, fetch_all_as_dict
import cx_Oracle
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'your_super_secret_key' # Important for sessions

# --- Authentication Mock (Simple placeholder logic) ---
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        # In a real app, you'd check password_hash
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Simple lookup for user ID based on username
        cursor.execute("SELECT user_id FROM \"USER\" WHERE username = :un", [username])
        user_data = cursor.fetchone()
        
        if user_data:
            session['user_id'] = user_data[0]
            session['username'] = username
            conn.close()
            return redirect(url_for('index'))
        else:
            conn.close()
            return render_template('login.html', error='Invalid credentials')

    return render_template('login.html', error=None)

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('username', None)
    return redirect(url_for('index'))
# ---------------------------------------------------


@app.route('/')
def index():
    conn = get_db_connection()
    if conn is None: return "Database connection failed", 500

    cursor = conn.cursor()
    
    # Fetch all movies and their average rating (using the PL/SQL function)
    cursor.execute("""
        SELECT 
            m.movie_id, 
            m.title, 
            m.release_year, 
            m.genre, 
            GET_AVG_RATING(m.movie_id) AS avg_rating 
        FROM MOVIE m
        ORDER BY m.release_year DESC
    """)
    movies = fetch_all_as_dict(cursor)
    conn.close()

    return render_template('index.html', movies=movies)


@app.route('/movie/<int:movie_id>')
def movie_detail(movie_id):
    conn = get_db_connection()
    if conn is None: return "Database connection failed", 500
    
    cursor = conn.cursor()
    
    # 1. Fetch movie details
    cursor.execute("SELECT * FROM MOVIE WHERE movie_id = :id", [movie_id])
    movie = fetch_all_as_dict(cursor)
    
    # 2. Fetch reviews
    cursor.execute("""
        SELECT 
            r.review_id, r.rating, r.review_text, r.review_date, u.username
        FROM REVIEW r
        JOIN "USER" u ON r.user_id = u.user_id
        WHERE r.movie_id = :id
        ORDER BY r.review_date DESC
    """, [movie_id])
    reviews = fetch_all_as_dict(cursor)

    # 3. Get average rating (using PL/SQL function)
    cursor.callproc("GET_AVG_RATING", [movie_id, cursor.OUT])
    avg_rating = cursor.getvalue(1)
    
    conn.close()

    if not movie:
        return "Movie not found", 404

    return render_template(
        'movie_detail.html', 
        movie=movie[0], 
        reviews=reviews, 
        avg_rating=f"{avg_rating:.1f}" if avg_rating else 'N/A'
    )


@app.route('/api/submit_review', methods=['POST'])
def submit_review_api():
    if 'user_id' not in session:
        return jsonify({"message": "Unauthorized"}), 401

    conn = get_db_connection()
    if conn is None: return jsonify({"message": "DB Error"}), 500

    try:
        data = request.json
        user_id = session['user_id']
        movie_id = data['movie_id']
        rating = data['rating']
        review_text = data.get('review_text', '')
        
        cursor = conn.cursor()
        
        # Call the PL/SQL Stored Procedure
        result_message = cursor.var(cx_Oracle.STRING)
        cursor.callproc("SUBMIT_REVIEW", [
            user_id, 
            movie_id, 
            rating, 
            review_text,
            result_message
        ])
        conn.commit()
        conn.close()
        
        message = result_message.getvalue()
        if "Error" in message:
            return jsonify({"message": message}), 400
            
        return jsonify({"message": message}), 201
        
    except Exception as e:
        conn.rollback()
        conn.close()
        return jsonify({"message": f"An internal error occurred: {str(e)}"}), 500


# --- Recommendation Route (Calls PL/SQL function) ---
@app.route('/recommendations')
def recommendations():
    if 'user_id' not in session:
        return redirect(url_for('login'))
        
    conn = get_db_connection()
    if conn is None: return "Database connection failed", 500
    
    user_id = session['user_id']
    cursor = conn.cursor()
    
    # 1. Call the PL/SQL function GET_RECOMMENDATIONS
    # Define the PL/SQL collection type (MOVIE_ID_LIST)
    MovieIdListType = conn.gettype("MOVIE_ID_LIST")
    
    recommended_ids_var = cursor.callfunc("GET_RECOMMENDATIONS", MovieIdListType, [user_id])
    
    # Convert the Oracle collection to a Python list
    recommended_ids = recommended_ids_var.aslist()
    
    recommended_movies = []
    if recommended_ids:
        # 2. Convert IDs into a comma-separated string for the final SQL query
        id_list_str = ', '.join(map(str, recommended_ids))
        
        # 3. Fetch full movie details for the recommended IDs
        cursor.execute(f"""
            SELECT movie_id, title, genre, GET_AVG_RATING(movie_id) AS avg_rating
            FROM MOVIE
            WHERE movie_id IN ({id_list_str})
        """)
        recommended_movies = fetch_all_as_dict(cursor)

    conn.close()
    return render_template('recommendations.html', movies=recommended_movies)

if __name__ == '__main__':
    # Set host to '0.0.0.0' to be accessible externally (useful if DB is remote)
    app.run(debug=True, host='0.0.0.0')