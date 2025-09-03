import user
import re
import os
import subprocess
from flask import Flask, render_template, request, redirect, url_for, session, flash, send_from_directory, get_flashed_messages, jsonify, Response


app = Flask(__name__, static_folder='static')  # Correctly set static folder
app.secret_key = "Test123"
app.debug = True

pw = "Hahanottoday" #-> change Imidiatly


"""----------------------------------Config Part----------------------------"""
def _find_inventarsystem_base():
    candidates = [
        os.environ.get("INVENTAR_BASE"),
        "/opt/Inventarsystem",
    ]
    for path in candidates:
        if path and os.path.exists(path):
            return path
    return None


BASE_DIR = _find_inventarsystem_base()


"""-----------------------------Logs Part-----------------------------------"""

def get_log():
    items = []
    for i in os.listdir(os.path.join(BASE_DIR, "logs")):
        item = {"type": None, "length": None, "last_row": None, "last_row_prev": None}
        file_type = i.replace(".log", "")
        item["type"] = file_type
        with open(os.path.join(BASE_DIR, "logs", f"{file_type}.log"), "r") as f:
            file_content = f.read()
            file_content_list = file_content.split("\n")
            length = len(file_content_list)
            item["length"] = length
            last_row = file_content_list[length-2]
            item["last_row"] = last_row
            if len(last_row) >= 30:
                item["last_row_prev"] = last_row[0:30]
            else:
                item["last_row_prev"] = last_row
        items.append(item)
    return items

"""------------------------------Backup Part---------------------------------"""

def get_list_back():
    list_directory = os.listdir("/var/backups")
    list_inv = []
    for i in list_directory:
        j = i.find("Inventarsystem")
        if j == 0:
            list_inv.append(i)
    return list_inv

def get_back():
    items = []
    for i in get_list_back():
        item = {"date": None, "size": None, "content": None}
        date = i.replace("Inventarsystem-", "")
        date = date.replace(".tar.gz", "")
        item["date"] = date
        size_b = os.path.getsize(os.path.join("/var/backups",i))
        size_gb = size_b / 1000000000
        size_gb = round(size_gb, 2)
        if size_gb == 0.0:
            size_mb = size_b / 1000000
            item["size"] = f"{round(size_mb, 2)} MB"
        else:
            item["size"] = f"{size_gb} GB"
        # jetzt noch content
        items.append(item)
    return items

def create_backup(pw):
    backup_path = os.path.join(BASE_DIR, "backup.sh")
    if not backup_path:
        return False

    cmd = f'cd "{BASE_DIR}" && bash "{backup_path}"'
    if pw:
        result = subprocess.run(
            ["sudo", "-S", "bash", "-lc", cmd],
            input=(pw + "\n").encode(),
        )
        return result.stdout
    else: 
        return False


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

def version_list():
    list_index = []
    list_commit = get_commit_history().split("\n")
    list_commit.pop(len(list_commit)-1)
    for i in list_commit:
        item = {"hash": None, "date": None, "description": None, "description_prev": None}
        commit_hash = i[0:7]
        item["hash"] = commit_hash
        commit_description = i[7:len(i)]
        item["description"] = commit_description
        if len(i) >= 30:
            commit_description_prev = i[7:30]
        else:
            commit_description_prev = i[7:len(i)]
        item["description_prev"] = commit_description_prev
        try:
            result = subprocess.run(
                ["git", "show", "-s", "--format=%ci", f"{commit_hash}"],
                cwd=BASE_DIR,
                capture_output=True,
                text=True,
                check=True,
            )
            item["date"] = result.stdout
        except subprocess.CalledProcessError as e:
            item["date"] = "1212-12-12"
        list_index.append(item)
    return list_index

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

SERVICE_NAME = os.getenv("INVENTAR_SERVICE", "inventarsystem-gunicorn.service")

def is_service_running(service=SERVICE_NAME):
    try:
        p = subprocess.run(
            ["systemctl", "is-active", service],
            capture_output=True, text=True, check=False
        )
        return p.stdout.strip() == "active"
    except Exception:
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

@app.route("/get_backups", methods=["GET"])
def get_backups():
    items = get_back()
    return {'items': items}

@app.route("/download_backup/<date>", methods=["GET", "POST"])
def download_backup(date):
    backups = os.path.join("/var/backups/")
    return send_from_directory(backups, f"Inventarsystem-{date}.tar.gz", as_attachment=True)

@app.route("/run_backup")
def run_backup():
    create_backup(pw)
    return redirect(url_for("backup"))

@app.route("/version")
def version():
    if 'username' not in session:
        flash('Ihnen ist es nicht gestattet auf dieser Internetanwendung, die eben besuchte Adrrese zu nutzen, versuchen sie es erneut nach dem sie sich mit einem berechtigten Nutzer angemeldet haben!', 'error')
        return redirect(url_for('login'))
    return render_template("version.html")

@app.route("/get_versions", methods=["GET"])
def get_versions():
    items = version_list()
    return {'items': items}

@app.route("/use_version/<version>", methods=["GET", "POST"])
def use_version(version):
    downgrading(pw, version)
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

@app.route("/start", methods=['GET', 'POST'])
def start():
    if 'username' not in session:
        flash('Ihnen ist es nicht gestattet auf dieser Internetanwendung, die eben besuchte Adrrese zu nutzen, versuchen sie es erneut nach dem sie sich mit einem berechtigten Nutzer angemeldet haben!', 'error')
        return redirect(url_for('login'))
    if request.method == 'POST':
        exe_start(pw)
    return render_template('home.html')

@app.route("/stop", methods=['GET', 'POST'])
def stop():
    if 'username' not in session:
        flash('Ihnen ist es nicht gestattet auf dieser Internetanwendung, die eben besuchte Adrrese zu nutzen, versuchen sie es erneut nach dem sie sich mit einem berechtigten Nutzer angemeldet haben!', 'error')
        return redirect(url_for('login'))
    if request.method == 'POST':
        exe_stop(pw)
    return render_template('home.html')

@app.route("/reload", methods=['GET', 'POST'])
def reload():
    if 'username' not in session:
        flash('Ihnen ist es nicht gestattet auf dieser Internetanwendung, die eben besuchte Adrrese zu nutzen, versuchen sie es erneut nach dem sie sich mit einem berechtigten Nutzer angemeldet haben!', 'error')
        return redirect(url_for('login'))
    if request.method == 'POST':
        exe_restart(pw)
    return render_template('home.html')

@app.route("/fix", methods=['GET', 'POST'])
def fix():
    if 'username' not in session:
        flash('Ihnen ist es nicht gestattet auf dieser Internetanwendung, die eben besuchte Adrrese zu nutzen, versuchen sie es erneut nach dem sie sich mit einem berechtigten Nutzer angemeldet haben!', 'error')
        return redirect(url_for('login'))
    if request.method == 'POST':
        exe_fix_all(pw)
    return render_template('home.html')

@app.route("/status", methods=['GET'])
def status():
    if 'username' not in session:
        flash('Ihnen ist es nicht gestattet auf dieser Internetanwendung, die eben besuchte Adrrese zu nutzen, versuchen sie es erneut nach dem sie sich mit einem berechtigten Nutzer angemeldet haben!', 'error')
        return redirect(url_for('login'))

    return jsonify({"running": is_service_running()}), 200

@app.route("/logs")
def logs():
    if 'username' not in session:
        flash('Ihnen ist es nicht gestattet auf dieser Internetanwendung, die eben besuchte Adrrese zu nutzen, versuchen sie es erneut nach dem sie sich mit einem berechtigten Nutzer angemeldet haben!', 'error')
        return redirect(url_for('login'))
    return render_template("logs.html")

@app.route("/get_logs", methods=["GET"])
def get_logs():
    items = get_log()
    return {'items': items}

@app.route("/download_logs/<type>", methods=["GET", "POST"])
def download_logs(type):
    backups = os.path.join(BASE_DIR, "logs")
    return send_from_directory(backups, f"{type}.log", as_attachment=True)

@app.route("/config")
def config():
    if 'username' not in session:
        flash('Ihnen ist es nicht gestattet auf dieser Internetanwendung, die eben besuchte Adrrese zu nutzen, versuchen sie es erneut nach dem sie sich mit einem berechtigten Nutzer angemeldet haben!', 'error')
        return redirect(url_for('login'))
    return render_template("config.html")

@app.route("/config_update", methods=["POST"])
def config_update():
    # Load config.json, apply any provided changes, and save back
    import json

    form = request.form
    # Resolve config path (prefer BASE_DIR)
    cfg_candidates = []
    if BASE_DIR:
        cfg_candidates.append(os.path.join(BASE_DIR, "config.json"))
    cfg_candidates.append(os.path.join(app.root_path, "config.json"))
    cfg_path = next((p for p in cfg_candidates if os.path.exists(p)), cfg_candidates[0])

    # Load current config (or start from empty dict)
    try:
        with open(cfg_path, "r", encoding="utf-8") as fh:
            cfg = json.load(fh)
    except Exception:
        cfg = {}

    changed = False

    # Update secret key
    if "key" in form:
        secret_key = (form.get("key") or "").strip()
        if secret_key:
            cfg["key"] = secret_key
            changed = True

    # Update Mongo DB name
    if "db_name" in form:
        db_name = (form.get("db_name") or "").strip()
        if db_name:
            cfg.setdefault("mongodb", {})["db"] = db_name
            changed = True

    # Scheduler intervals
    if "min_interval" in form:
        try:
            val = int(form.get("min_interval"))
            cfg.setdefault("scheduler", {}).update({"interval_minutes": max(1, val)})
            changed = True
        except (TypeError, ValueError):
            pass
    if "back_interval" in form:
        try:
            val = int(form.get("back_interval"))
            cfg.setdefault("scheduler", {}).update({"backup_interval_hours": max(1, val)})
            changed = True
        except (TypeError, ValueError):
            pass

    # Upload sizes (MB)
    if "max_size" in form:
        try:
            val = int(form.get("max_size"))
            cfg.setdefault("upload", {}).update({"max_size_mb": max(1, val)})
            changed = True
        except (TypeError, ValueError):
            pass
    if "max_image" in form:
        try:
            val = int(form.get("max_image"))
            cfg.setdefault("upload", {}).update({"image_max_size_mb": max(1, val)})
            changed = True
        except (TypeError, ValueError):
            pass
    if "max_video" in form:
        try:
            val = int(form.get("max_video"))
            cfg.setdefault("upload", {}).update({"video_max_size_mb": max(1, val)})
            changed = True
        except (TypeError, ValueError):
            pass

    # Allowed extensions (comma/space/semicolon separated, strip leading dots)
    if "al_ext1" in form:
        raw = (form.get("al_ext1") or "").strip()
        if raw:
            parts = re.split(r"[\s,;]+", raw)
            cleaned, seen = [], set()
            for p in parts:
                ext = p.lower().lstrip('.').strip()
                if ext and ext not in seen:
                    cleaned.append(ext)
                    seen.add(ext)
            if cleaned:
                cfg["allowed_extensions"] = cleaned
                changed = True

    # School periods (st_1..st_10, en_1..en_10)
    if any(k.startswith("st_") or k.startswith("en_") for k in form.keys()):
        sp = cfg.setdefault("schoolPeriods", {})
        for i in range(1, 11):
            st = (form.get(f"st_{i}") or "").strip()
            en = (form.get(f"en_{i}") or "").strip()
            if st and en:
                sp[str(i)] = {
                    "start": st,
                    "end": en,
                    "label": f"{i}. Stunde ({st} - {en})"
                }
                changed = True

    # Persist if anything changed
    if changed:
        try:
            with open(cfg_path, "w", encoding="utf-8") as fh:
                json.dump(cfg, fh, ensure_ascii=False, indent=4)
        except Exception:
            pass

    return redirect(url_for("config"))

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