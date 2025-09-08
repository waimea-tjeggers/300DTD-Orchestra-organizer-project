#===========================================================
# YOUR PROJECT TITLE HERE
# YOUR NAME HERE
#-----------------------------------------------------------
# BRIEF DESCRIPTION OF YOUR PROJECT HERE
#===========================================================


from flask import Flask, render_template, request, flash, redirect, session
from werkzeug.security import generate_password_hash, check_password_hash
import html

from app.helpers.session import init_session
from app.helpers.db      import connect_db
from app.helpers.errors  import init_error, not_found_error
from app.helpers.logging import init_logging
from app.helpers.auth    import login_required
from app.helpers.time    import init_datetime, utc_timestamp, utc_timestamp_now


# Create the app
app = Flask(__name__)

# Configure app
init_session(app)   # Setup a session for messages, etc.
init_logging(app)   # Log requests
init_error(app)     # Handle errors and exceptions
init_datetime(app)  # Handle UTC dates in timestamps


#-----------------------------------------------------------
# Home page route
#-----------------------------------------------------------
@app.get("/")
def index():
        with connect_db as client:
        #Get all the things from the DB
            sql = """
            SELECT class.id,
                   class.name,
                   class.users_id,
                   class.practice_times


            FROM class 
            JOIN users ON class.user_id = users.id
            JOIN practice_times on class.practice_times = practice_times.id

            WHERE class.user_id = ?

            ORDER BY class.name ASC
        """
        params=[]
        result = client.execute(sql, params)
        classes = result.rows
        return render_template("pages/home.jinja")


#-----------------------------------------------------------
# About page route
#-----------------------------------------------------------
@app.get("/about/")
def about():
    return render_template("pages/about.jinja")

#-----------------------------------------------------------
# add class page route
#-----------------------------------------------------------
@app.get("/add_class_form/")
def add_class_form():
    return render_template("pages/add_class_form.jinja")

#-----------------------------------------------------------
# add practice page route
#-----------------------------------------------------------
@app.get("/add_practice_form/")
def add_practice_form():
    return render_template("pages/add_practice_form.jinja")

#-----------------------------------------------------------
# add song page route
#-----------------------------------------------------------
@app.get("/add_song_form/")
def add_song_form():
    return render_template("pages/add_song_form.jinja")

#-----------------------------------------------------------
# add student page route
#-----------------------------------------------------------
@app.get("/add_student_form/")
def add_student_form():
    return render_template("pages/add_student_form.jinja")


#-----------------------------------------------------------
# Things page route - Show all the things, and new thing form
#-----------------------------------------------------------
@app.get("/things/")
def show_all_things():
    with connect_db() as client:
        # Get all the things from the DB
        sql = """
            SELECT things.id,
                   things.name,
                   users.name AS owner

            FROM things
            JOIN users ON things.user_id = users.id

            ORDER BY things.name ASC
        """
        params=[]
        result = client.execute(sql, params)
        things = result.rows

        # And show them on the page
        return render_template("pages/things.jinja", things=things)


#-----------------------------------------------------------
# Thing page route - Show details of a single thing
#-----------------------------------------------------------
@app.get("/thing/<int:id>")
def show_one_thing(id):
    with connect_db() as client:
        # Get the thing details from the DB, including the owner info
        sql = """
            SELECT things.id,
                   things.name,
                   things.price,
                   things.user_id,
                   users.name AS owner

            FROM things
            JOIN users ON things.user_id = users.id

            WHERE things.id=?
        """
        params = [id]
        result = client.execute(sql, params)

        # Did we get a result?
        if result.rows:
            # yes, so show it on the page
            thing = result.rows[0]
            return render_template("pages/thing.jinja", thing=thing)

        else:
            # No, so show error
            return not_found_error()


#-----------------------------------------------------------
# Route for adding a thing, using data posted from a form
# - Restricted to logged in users
#-----------------------------------------------------------
@app.post("/add-practice")
@login_required
def add_a_thing():
    # Get the data from the form
    day  = request.form.get("day")
    time = request.form.get("time")
    permanent = request.form.get(permanent)

    # Sanitise the text inputs
    day = html.escape(day)

    # Get the user id from the session
    

    with connect_db() as client:
        # Add the thing to the DB
        sql = "INSERT INTO things (day, time, permanent) VALUES (?, ?, ?)"
        params = [day, time, permanent]
        client.execute(sql, params)

        # Go back to the home page
        flash("success")
        return redirect("/")

#-----------------------------------------------------------
# Route for adding a thing, using data posted from a form
# - Restricted to logged in users
#-----------------------------------------------------------
@app.post("/add-class")
@login_required
def add_a_thing():
    

    # Get the data from the form
    class_name  = request.form.get("name")
    user_id = session.user_id
    # Sanitise the text inputs
    class_name = html.escape(class_name)

    # Get the user id from the session
    

    with connect_db() as client:
        # Add the thing to the DB
        sql = "INSERT INTO things (class_name,user_id) VALUES (?,?)"
        params = [class_name,user_id]
        client.execute(sql, params)

        # Go back to the home page
        flash("success")
        return redirect("/")
    

#-----------------------------------------------------------
# Route for deleting a thing, Id given in the route
# - Restricted to logged in users
#-----------------------------------------------------------
@app.get("/delete/<int:id>")
@login_required
def delete_a_thing(id):
    # Get the user id from the session
    user_id = session["user_id"]

    with connect_db() as client:
        # Delete the thing from the DB only if we own it
        sql = "DELETE FROM things WHERE id=? AND user_id=?"
        params = [id, user_id]
        client.execute(sql, params)

        # Go back to the home page
        flash("Thing deleted", "success")
        return redirect("/things")







#-----------------------------------------------------------
# User registration form route(student)
#-----------------------------------------------------------
@app.get("/register_student")
def register_form_student():
    return render_template("pages/register_student.jinja")


#-----------------------------------------------------------
# User login form route(student)
#-----------------------------------------------------------
@app.get("/login_student")
def login_form_student():
    return render_template("pages/login_student.jinja")


#-----------------------------------------------------------
# User registration form route(teacher)
#-----------------------------------------------------------
@app.get("/register_teacher")
def register_form_teacher():
    return render_template("pages/register_teacher.jinja")


#-----------------------------------------------------------
# User login form route(teacher)
#-----------------------------------------------------------
@app.get("/login_teacher")
def login_form_teacher():
    return render_template("pages/login_teacher.jinja")

#-----------------------------------------------------------
# Route for adding a user when registration form submitted(teacher)
#-----------------------------------------------------------
@app.post("/add-user-teacher")
def add_user_teacher():
    # Get the data from the form
    name = request.form.get("name")
    username = request.form.get("username")
    password = request.form.get("password")

    with connect_db() as client:
        # Attempt to find an existing record for that user
        sql = "SELECT * FROM users WHERE username = ?"
        params = [username]
        result = client.execute(sql, params)

        

        # No existing record found, so safe to add the user
        if not result.rows:
            # Sanitise the name
            name = html.escape(name)

            # Salt and hash the password
            hash = generate_password_hash(password)

            # Add the user to the users table
            sql = "INSERT INTO users (name, username, password_hash, admin) VALUES (?, ?, ?, 1)"
            params = [name, username, hash]
            client.execute(sql, params)

            # And let them know it was successful and they can login
            flash("Registration successful", "success")
            return redirect("/login")

        # Found an existing record, so prompt to try again
        flash("Username already exists. Try again...", "error")
        return redirect("/register_teacher")

#-----------------------------------------------------------
# Route for adding a user when registration form submitted(student)
#-----------------------------------------------------------
@app.post("/add-user-student")
def add_user_student():
    # Get the data from the form
    name = request.form.get("name")
    username = request.form.get("username")
    password = request.form.get("password")
    instrument = request.form.get("instrument")

    with connect_db() as client:
        # Attempt to find an existing record for that user
        sql = "SELECT * FROM users WHERE username = ?"
        params = [username]
        result = client.execute(sql, params)

        # No existing record found, so safe to add the user
        if not result.rows:
            # Sanitise the name
            name = html.escape(name)

            # Salt and hash the password
            hash = generate_password_hash(password)

            # Add the user to the users table
            sql = "INSERT INTO users (name, username, password_hash, instrument) VALUES (?, ?, ?, ?)"
            params = [name, username, hash, instrument]
            client.execute(sql, params)

            # And let them know it was successful and they can login
            flash("Registration successful", "success")
            return redirect("/login")

        # Found an existing record, so prompt to try again
        flash("Username already exists. Try again...", "error")
        return redirect("/register_student")


#-----------------------------------------------------------
# Route for processing a user login(student)
#-----------------------------------------------------------
@app.post("/login-user-student")
def login_user_student():
    # Get the login form data
    username = request.form.get("username")
    password = request.form.get("password")

    with connect_db() as client:
        # Attempt to find a record for that user
        sql = "SELECT * FROM users WHERE username = ?"
        params = [username]
        result = client.execute(sql, params)

        # Did we find a record?
        if result.rows:
            # Yes, so check password
            user = result.rows[0]
            hash = user["password_hash"]

            # Hash matches?
            if check_password_hash(hash, password):
                # Yes, so save info in the session
                session["user_id"]   = user["id"]
                session["user_name"] = user["name"]
                session["admin"] = False
                session["logged_in"] = True

                # And head back to the home page
                flash("Login successful", "success")
                return redirect("/")

        # Either username not found, or password was wrong
        flash("Invalid credentials", "error")
        return redirect("/login_student")


#-----------------------------------------------------------
# Route for processing a user login(teacher)
#-----------------------------------------------------------
@app.post("/login-user-teacher")
def login_user_teacher():
    # Get the login form data
    username = request.form.get("username")
    password = request.form.get("password")

    with connect_db() as client:
        # Attempt to find a record for that user
        sql = "SELECT * FROM users WHERE username = ? AND admin = 1"
        params = [username]
        result = client.execute(sql, params)

        # Did we find a record?
        if result.rows:
            # Yes, so check password
            user = result.rows[0]
            hash = user["password_hash"]

            # Hash matches?
            if check_password_hash(hash, password):
                # Yes, so save info in the session
                session["user_id"]   = user["id"]
                session["user_name"] = user["name"]
                session["admin"] = True
                session["logged_in"] = True

                # And head back to the home page
                flash("Login successful", "success")
                return redirect("/")

        # Either username not found, or password was wrong
        flash("Invalid credentials", "error")
        return redirect("/login_teacher")
    

#-----------------------------------------------------------
# Route for adding a song when registration form submitted
#-----------------------------------------------------------
@app.post("/add-song")
@login_required
def add_song():
    # Get the data from the form
    name = request.form.get("name")
    image = request.form.get("image")
    link_to_song = request.form.get("link_to_song")
    notes = request.form.get("notes")
    
    # Add the user to the users table
    with connect_db() as client:
        sql = "INSERT INTO pieces (name, image, link_to_song, notes) VALUES (?, ?, ?, ?)"
        params = [name, image, link_to_song, notes]
        client.execute(sql, params)

    # And let them know it was successful and they can login
    flash("Registration successful", "success")
    return redirect("/")

#-----------------------------------------------------------
# Route for adding a song when registration form submitted
#-----------------------------------------------------------
@app.post("/add-practice")
@login_required
def add_practice():
    # Get the data from the form
    day = request.form.get("day")
    time = request.form.get("time")
    permanent = request.form.get("permanent")
    
    # Add the user to the users table
    with connect_db() as client:
        sql = "INSERT INTO practice_time (day, time, permanent,) VALUES (?, ?, ?,)"
        params = [day, time, permanent]
        client.execute(sql, params)

    # And let them know it was successful and they can login
    flash("Registration successful", "success")
    return redirect("/")





#-----------------------------------------------------------
# Route for processing a user logout
#-----------------------------------------------------------
@app.get("/logout")
def logout():
    # Clear the details from the session
    session.pop("user_id", None)
    session.pop("user_name", None)
    session.pop("admin", None)
    session.pop("logged_in", None)

    # And head back to the home page
    flash("Logged out successfully", "success")
    return redirect("/")

