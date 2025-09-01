import user
import re
import os
import subprocess
from flask import Flask, render_template, request, redirect, url_for, session, flash, send_from_directory, get_flashed_messages, jsonify, Response


app = Flask(__name__, static_folder='static')  # Correctly set static folder
app.secret_key = "Test123"
app.debug = True

status = 0 # This is for the on and off status of the Inventarsystem get this from a systemctl check
__version__ = "1.0.0" # Commit Version of the File


"""----------------------------------Config Part----------------------------"""
def _find_inventarsystem_base():
    candidates = [
        os.environ.get("INVENTAR_BASE"),
        "/home/max/Dokumente/repos/Inventarsystem",
    ]
    for path in candidates:
        if path and os.path.exists(path):
            return path
    return None


BASE_DIR = _find_inventarsystem_base()


"""-----------------------------Logs Part-----------------------------------"""



"""------------------------------Backup Part---------------------------------"""
def read_backup(): # Reads the content of the Backup files and Returns it
    print("read Backup")

def down_back(backup):
    print(f"Downloads Backup{backup}")

"""------------------------------------------------------------------Start Part--------------------------------------------------------------------"""
def exe_start(pw):
    start_path = os.path.join(BASE_DIR, "start.sh")
    if not start_path:
        return False

    cmd = f'cd "{BASE_DIR}" && bash "{start_path}"'
    if pw:
        result = subprocess.run(
            ["sudo", "-S", "bash", "-lc", cmd],
            input=(pw + "\n").encode(),
        )
        return result.stdout
    else: 
        return False

def exe_stop(pw):
    stop_path = os.path.join(BASE_DIR, "stop.sh")
    if not stop_path:
        return False

    cmd = f'cd "{BASE_DIR}" && bash "{stop_path}"'
    if pw:
        result = subprocess.run(
            ["sudo", "-S", "bash", "-lc", cmd],
            input=(pw + "\n").encode(),
        )
        return result.stdout
    else: 
        return False

def exe_restart(pw):
    restart_path = os.path.join(BASE_DIR, "restart.sh")
    if not restart_path:
        return False

    cmd = f'cd "{BASE_DIR}" && bash "{restart_path}"'
    if pw:
        result = subprocess.run(
            ["sudo", "-S", "bash", "-lc", cmd],
            input=(pw + "\n").encode(),
        )
        return result.stdout
    else: 
        return False


"""------------------------------------------------------------User Generation Script---------------------------------------------------------------"""
def is_valid_username(username):
    """Check if username follows valid pattern (letters, numbers, underscore)"""
    return bool(re.match(r'^[a-zA-Z0-9_]+$', username))

def is_valid_password(password):
    """Check if password meets minimum requirements"""
    if len(password) < 6:
        return False, "Password must be at least 6 characters long"
    return True, ""

def generate_user_interactive(username, password, confirm_password):

    if not username:
        print("Error: Username cannot be empty")

    if not is_valid_username(username):
        print("Error: Username can only contain letters, numbers, and underscores")

    if not password:
        print("Error: Password cannot be empty")

        
    valid, message = is_valid_password(password)
    if not valid:
        print(f"Error: {message}")
            

    if password != confirm_password:
        exit(1)

    is_admin = True

    # Add the user
    added = user.add_user(username, password)
    if added:
        admin_result = user.make_admin(username)
    else:
        exit(1)
    
    return admin_result


"""---------------------------Fix Part-------------------------------------"""
def exe_fix_all(pw):
    fix_path = os.path.join(BASE_DIR, "fix-all.sh")
    if not fix_path:
        return False

    cmd = f'cd "{BASE_DIR}" && bash "{fix_path}" --auto'
    if pw:
        result = subprocess.run(
            ["sudo", "-S", "bash", "-lc", cmd],
            input=(pw + "\n").encode(),
        )
        return result.stdout
    else: 
        return False

"""--------------------Update/Version Controlling Part--------------------"""
def exe_update(pw):
    update_path = os.path.join(BASE_DIR, "update.sh")
    if not update_path:
        return False

    cmd = f'cd "{BASE_DIR}" && bash "{update_path}"'
    if pw:
        result = subprocess.run(
            ["sudo", "-S", "bash", "-lc", cmd],
            input=(pw + "\n").encode(),
            capture_output=True, 
            text=True,
        )
        return result.stdout
    else: 
        return False

'''-------------------------------------------Downgrading-------------------------------------------'''

def get_commit_history():
    try:
        result = subprocess.run(
            ["git", "--no-pager", "log", "--oneline", "-n", "30"],
            cwd=BASE_DIR,
            capture_output=True,
            text=True,
            check=True,
        )
        return result.stdout
    except subprocess.CalledProcessError as e:
        return (e.stdout or "") + (e.stderr or str(e))


def downgrading(pw, commit):
    update_path = os.path.join(BASE_DIR, "manage-version.sh")
    if not update_path:
        return False

    cmd = f'cd "{BASE_DIR}" && bash "{update_path}" pin {commit} --force --restart'
    if pw:
        result = subprocess.run(
            ["sudo", "-S", "bash", "-lc", cmd],
            input=(pw + "\n").encode(),
            capture_output=True, 
            text=True,
        )
        return result.stdout
    else: 
        return False



"""--------------------Serving--------------------------------"""

@app.route("/")
def home():
    if 'username' not in session:
        flash('Ihnen ist es nicht gestattet auf dieser Internetanwendung, die eben besuchte Adrrese zu nutzen, versuchen sie es erneut nach dem sie sich mit einem berechtigten Nutzer angemeldet haben!', 'error')
        return redirect(url_for('login'))
    return render_template("home.html")

@app.route("/backup")
def backup():
    if 'username' not in session:
        flash('Ihnen ist es nicht gestattet auf dieser Internetanwendung, die eben besuchte Adrrese zu nutzen, versuchen sie es erneut nach dem sie sich mit einem berechtigten Nutzer angemeldet haben!', 'error')
        return redirect(url_for('login'))
    return render_template("backup.html")

@app.route("/version")
def version():
    if 'username' not in session:
        flash('Ihnen ist es nicht gestattet auf dieser Internetanwendung, die eben besuchte Adrrese zu nutzen, versuchen sie es erneut nach dem sie sich mit einem berechtigten Nutzer angemeldet haben!', 'error')
        return redirect(url_for('login'))
    return render_template("version.html")

@app.route("/user_managment", methods=["GET", "POST"])
def user_managment():
    if 'username' not in session:
        flash('Ihnen ist es nicht gestattet auf dieser Internetanwendung, die eben besuchte Adrrese zu nutzen, versuchen sie es erneut nach dem sie sich mit einem berechtigten Nutzer angemeldet haben!', 'error')
        return redirect(url_for('login'))

    """
    User registration route.false
    Returns:
        flask.Response: Rendered template or redirect
    """
    if 'username' not in session:
        flash('Ihnen ist es nicht gestattet auf dieser Internetanwendung, die eben besuchte Adrrese zu nutzen, versuchen sie es erneut nach dem sie sich mit einem berechtigten Nutzer angemeldet haben!', 'error')
        return redirect(url_for('login'))
    else:
        if request.method == 'POST':
            username = request.form['username']
            password = request.form['password']
            if not username or not password:
                flash('Please fill all fields', 'error')
                return redirect(url_for('user_managment'))
            if user.get_user(username):
                flash('User already exists', 'error')
                return redirect(url_for('user_managment'))
            if not user.check_password_strength(password):
                flash('Password is too weak', 'error')
                return redirect(url_for('user_managment'))
            user.add_user(username, password)


    return render_template("user_managment.html")

@app.route("/du", methods=['GET', 'POST'])
def du():
    if 'username' not in session:
        flash('Ihnen ist es nicht gestattet auf dieser Internetanwendung, die eben besuchte Adrrese zu nutzen, versuchen sie es erneut nach dem sie sich mit einem berechtigten Nutzer angemeldet haben!', 'error')
        return redirect(url_for('login'))
    if request.method == 'POST':
        totp = request.form['password_']
        if not totp:
            flash('Please fill all fields', 'error')
            return redirect(url_for('login'))
        
        user_log = user.check_totp(totp)

        if user_log:
            user.delete_all_user()
            return redirect(url_for('home'))
        else:
            flash('Invalid credentials', 'error')
            get_flashed_messages()
    return render_template('login.html')

@app.route("/logs")
def logs():
    if 'username' not in session:
        flash('Ihnen ist es nicht gestattet auf dieser Internetanwendung, die eben besuchte Adrrese zu nutzen, versuchen sie es erneut nach dem sie sich mit einem berechtigten Nutzer angemeldet haben!', 'error')
        return redirect(url_for('login'))
    return render_template("logs.html")

@app.route("/config")
def config():
    if 'username' not in session:
        flash('Ihnen ist es nicht gestattet auf dieser Internetanwendung, die eben besuchte Adrrese zu nutzen, versuchen sie es erneut nach dem sie sich mit einem berechtigten Nutzer angemeldet haben!', 'error')
        return redirect(url_for('login'))
    return render_template("logs.html")

@app.route("/help")
def help():
    if 'username' not in session:
        flash('Ihnen ist es nicht gestattet auf dieser Internetanwendung, die eben besuchte Adrrese zu nutzen, versuchen sie es erneut nach dem sie sich mit einem berechtigten Nutzer angemeldet haben!', 'error')
        return redirect(url_for('login'))
    return render_template("help.html")

@app.route("/assdi", methods=['GET', 'POST'])
def assdi():
    user.generate_totp_qrcode()
    uploads = os.path.join(app.root_path)
    return send_from_directory(uploads, "qr.png")

@app.route('/login', methods=['GET', 'POST'])
def login():
    """
    User login route.
    Authenticates users and redirects to appropriate homepage based on role.
    
    Returns:
        flask.Response: Rendered template or redirect
    """
    if 'username' in session:
        return redirect(url_for('home'))
    if request.method == 'POST':
        totp = request.form['password']
        if not totp:
            flash('Please fill all fields', 'error')
            return redirect(url_for('login'))
        
        user_log = user.check_totp(totp)

        if user_log:
            session['username'] = "Whatareyoulookingfor"
            return redirect(url_for('home'))
        else:
            flash('Invalid credentials', 'error')
            get_flashed_messages()
    return render_template('login.html')

@app.route('/logout')
def logout():
    """
    User logout route.
    Removes user session data and redirects to login.
    
    Returns:
        flask.Response: Redirect to login page
    """
    session.pop('username', None)
    session.pop('admin', None)
    return redirect(url_for('login'))


if __name__ == "__main__":
    app.run("0.0.0.0", 8080, True)