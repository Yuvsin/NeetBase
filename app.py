from flask import Flask, render_template, request, redirect
import sqlite3

app = Flask(__name__)


def get_db():
    return sqlite3.connect("problems.db")


def create_tables():
    connect = get_db()

    connect.executescript("""
        CREATE TABLE IF NOT EXISTS PROBLEM (
            ID INTEGER PRIMARY KEY,
            NAME TEXT NOT NULL,
            DIFFICULTY TEXT NOT NULL,
            DESCRIPTION TEXT
        );

        CREATE TABLE IF NOT EXISTS TOPIC (
            ID INTEGER PRIMARY KEY,
            NAME TEXT UNIQUE NOT NULL
        );

        CREATE TABLE IF NOT EXISTS PROBLEM_TOPIC (
            PROBLEM_ID INTEGER,
            TOPIC_ID INTEGER,
            FOREIGN KEY (PROBLEM_ID) REFERENCES PROBLEM(ID),
            FOREIGN KEY (TOPIC_ID) REFERENCES TOPIC(ID)
        );
    """)

    connect.commit()
    connect.close()


@app.route("/")
def home():
    connect = get_db()

    problems = connect.execute("""
        SELECT
            PROBLEM.ID,
            PROBLEM.NAME,
            PROBLEM.DIFFICULTY,
            GROUP_CONCAT(TOPIC.NAME, ', '),
            PROBLEM.DESCRIPTION
        FROM PROBLEM
        LEFT JOIN PROBLEM_TOPIC
            ON PROBLEM.ID = PROBLEM_TOPIC.PROBLEM_ID
        LEFT JOIN TOPIC
            ON TOPIC.ID = PROBLEM_TOPIC.TOPIC_ID
        GROUP BY PROBLEM.ID
    """).fetchall()

    connect.close()

    return render_template("index.html", problems=problems)


@app.route("/delete/<int:problem_id>", methods=["POST"])
def delete_question(problem_id):

    connect = get_db()

    # First remove topic connections
    connect.execute("""
        DELETE FROM PROBLEM_TOPIC
        WHERE PROBLEM_ID = ?
    """, (problem_id,))

    # Then remove the problem
    connect.execute("""
        DELETE FROM PROBLEM
        WHERE ID = ?
    """, (problem_id,))

    connect.commit()
    connect.close()

    return redirect("/")

@app.route("/edit/<int:problem_id>", methods=["POST"])
def edit_question(problem_id):

    name = request.form["name"]
    difficulty = request.form["difficulty"]
    description = request.form["description"]

    topics = request.form["topics"].split(",")
    topics = [topic.strip() for topic in topics]

    connect = get_db()
    cursor = connect.cursor()

    # Update the actual problem
    cursor.execute("""
        UPDATE PROBLEM
        SET NAME = ?, DIFFICULTY = ?, DESCRIPTION = ?
        WHERE ID = ?
    """, (name, difficulty, description, problem_id))

    # Remove old topic connections
    cursor.execute("""
        DELETE FROM PROBLEM_TOPIC
        WHERE PROBLEM_ID = ?
    """, (problem_id,))

    # Add the new topic connections
    for topic in topics:

        cursor.execute("""
            INSERT OR IGNORE INTO TOPIC (NAME)
            VALUES (?)
        """, (topic,))

        topic_id = cursor.execute("""
            SELECT ID FROM TOPIC
            WHERE NAME = ?
        """, (topic,)).fetchone()[0]

        cursor.execute("""
            INSERT INTO PROBLEM_TOPIC (PROBLEM_ID, TOPIC_ID)
            VALUES (?, ?)
        """, (problem_id, topic_id))

    connect.commit()
    connect.close()

    return redirect("/")

@app.route("/add", methods=["POST"])
def add_question():
    name = request.form["name"]
    difficulty = request.form["difficulty"]
    description = request.form["description"]

    topics = request.form["topics"].split(",")
    topics = [topic.strip() for topic in topics]

    connect = get_db()
    cursor = connect.cursor()

    cursor.execute("""
        INSERT INTO PROBLEM (NAME, DIFFICULTY, DESCRIPTION)
        VALUES (?, ?, ?)
    """, (name, difficulty, description))

    problem_id = cursor.lastrowid

    for topic in topics:

        cursor.execute("""
            INSERT OR IGNORE INTO TOPIC (NAME)
            VALUES (?)
        """, (topic,))

        topic_id = cursor.execute("""
            SELECT ID FROM TOPIC
            WHERE NAME = ?
        """, (topic,)).fetchone()[0]

        cursor.execute("""
            INSERT INTO PROBLEM_TOPIC (PROBLEM_ID, TOPIC_ID)
            VALUES (?, ?)
        """, (problem_id, topic_id))

    connect.commit()
    connect.close()

    return redirect("/")


create_tables()

if __name__ == "__main__":
    app.run(debug=True)