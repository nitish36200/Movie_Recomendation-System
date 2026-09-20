
import os
import pickle
from flask import Flask, render_template, request, session

app = Flask(__name__)
app.secret_key = "movie-recommendation-secret-key"

# Get the directory containing app.py
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Load movie data
with open(os.path.join(BASE_DIR, "movie_list.pkl"), "rb") as file:
    movies = pickle.load(file)

# Load similarity matrix
with open(os.path.join(BASE_DIR, "simis.pkl"), "rb") as file:
    similarity = pickle.load(file)


def recommend(movie_name):
    # Find the movie in the dataset
    matches = movies[
        movies["title"].str.lower() == movie_name.lower()
    ]

    if matches.empty:
        return []

    # Get movie index
    movie_index = matches.index[0]

    # Get similarity scores
    distances = similarity[movie_index]

    # Sort by similarity, excluding the searched movie
    movie_list = sorted(
        enumerate(distances),
        key=lambda x: x[1],
        reverse=True
    )[1:6]

    recommendations = []

    for index, score in movie_list:
        recommendations.append({
            "title": movies.iloc[index]["title"],
            "score": round(float(score), 3)
        })

    return recommendations


@app.route("/", methods=["GET", "POST"])
def home():
    recommendations = []
    searched_movie = ""
    error = None

    # Initialize recent search history
    if "history" not in session:
        session["history"] = []

    if request.method == "POST":
        searched_movie = request.form.get("movie", "").strip()

        if searched_movie:
            # Find movie title without case sensitivity
            matches = movies[
                movies["title"].str.lower()
                == searched_movie.lower()
            ]

            if matches.empty:
                error = "Movie not found. Please try another title."
            else:
                searched_movie = matches.iloc[0]["title"]
                recommendations = recommend(searched_movie)

                # Add to search history
                history = session["history"]

                if searched_movie in history:
                    history.remove(searched_movie)

                history.insert(0, searched_movie)

                # Keep only the latest 10 searches
                session["history"] = history[:10]
                session.modified = True

    return render_template(
        "index.html",
        recommendations=recommendations,
        searched_movie=searched_movie,
        history=session.get("history", []),
        error=error
    )


@app.route("/remove/<int:index>", methods=["POST"])
def remove_history(index):
    history = session.get("history", [])

    if 0 <= index < len(history):
        history.pop(index)

    session["history"] = history
    session.modified = True

    return render_template(
        "index.html",
        recommendations=[],
        searched_movie="",
        history=history,
        error=None
    )


if __name__ == "__main__":
    app.run(debug=True)