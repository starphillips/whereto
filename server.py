from flask import Flask, render_template, url_for, request, redirect, flash
import csv, os, re
from models import db, Comment

app = Flask(__name__)




BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_SQLITE = f"sqlite:///{os.path.join(BASE_DIR, 'whereto.db')}"
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL", DEFAULT_SQLITE)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SECRET_KEY"] = os.getenv("FLASK_SECRET_KEY", "change-me")

db.init_app(app)
with app.app_context():
    db.create_all()
CONTACTS_FILE = os.path.join(BASE_DIR, "database.csv")
print("Using database file at:", CONTACTS_FILE)

def write_to_csv(data):
    with open(CONTACTS_FILE, mode='a') as database:
        name = data["name"]
        email = data["email"]
        subject = data["subject"]
        message = data["message"]
        csv_writer = csv.writer(database, delimiter=',',
                                quotechar=' ', quoting=csv.QUOTE_MINIMAL)
        csv_writer.writerow([name, email, subject, message])


@app.route('/submit_form', methods=['POST', 'GET'])
def submit_form():
    if request.method == 'POST':
        try:
            data = request.form.to_dict()
            write_to_csv(data)
            print(data)
            return redirect('thankyou.html')
        except:
            return 'Unable to save to database'
    else:
        return 'Error in Sending. Please try again.'
    

@app.route('/')
def my_home():
    return render_template("index.html")


@app.route('/<string:page_name>')
def html_page(page_name):
    if page_name == "event-page.html":
        thread = "event-page"  # use a clean slug (not the filename)
        comments = get_thread_comments(thread=thread)
        return render_template(page_name, thread=thread, comments=comments)
    # all other pages render as-is
    return render_template(page_name)


URL_RE = re.compile(r'^https?://', re.IGNORECASE)


def get_thread_comments(thread: str):
    """Return a structure: roots, replies_by_parent for rendering."""
    items = (Comment.query
             .filter_by(thread=thread, is_approved=True)
             .order_by(Comment.created_at.asc())
             .all())
    roots = [c for c in items if c.parent_id is None]
    replies_by_parent = {}
    for c in items:
        if c.parent_id:
            replies_by_parent.setdefault(c.parent_id, []).append(c)
    return {"roots": roots, "replies": replies_by_parent}

@app.post("/comments/<thread>")
def post_comment(thread):
    # Honeypot check (bots fill this)
    if request.form.get("website"):  # our hidden trap field
        # Pretend success but do nothing
        flash("Thanks!")
        return redirect(request.referrer or url_for('html_page', page_name='index.html'))

    name = (request.form.get("name") or "").strip()
    text = (request.form.get("comment") or "").strip()
    social = (request.form.get("social") or request.form.get("website") or "").strip()  # accept either
    parent_id = request.form.get("parent_id") or None
    parent_id = int(parent_id) if parent_id and parent_id.isdigit() else None

    if not name or not text:
        flash("Name and comment are required.")
        return redirect(request.referrer or url_for('html_page', page_name='index.html'))

    if social and not URL_RE.match(social):
        social = "https://" + social

    c = Comment(thread=thread, parent_id=parent_id, name=name[:80],
                social_url=social[:255] if social else None, text=text)
    db.session.add(c)
    db.session.commit()
    flash("Comment posted!")
    # Back to the page’s #blog-comments anchor if present
    return redirect((request.referrer or url_for('html_page', page_name='index.html')) + "#blog-comments")