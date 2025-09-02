from flask import Flask, request, Response, render_template
import os, re, asyncio
from dotenv import load_dotenv
import httpx

load_dotenv()
app = Flask(__name__)
app.config["SECRET_KEY"] = os.getenv("FLASK_SECRET_KEY", "dev")

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

@app.route('/')
def my_home():
    return render_template("index.html")


@app.route('/<string:page_name>')
def html_page(page_name):
    return render_template(page_name)


def write_to_csv(data):
    with open('database.csv', mode='a') as database:
        name = data["name"]
        email = data["email"]
        message = data["message"]
        csv_writer = csv.writer(database, delimiter=',',
                                quotechar=' ', quoting=csv.QUOTE_MINIMAL)
        csv_writer.writerow([name, email, message])


# This route replaces contact.php (same path so your frontend JS works)
@app.post("/forms/contact.php")
def contact_php():
    name = (request.form.get("name") or "").strip()
    email = (request.form.get("email") or "").strip()
    subject = (request.form.get("subject") or "").strip()
    message = (request.form.get("message") or "").strip()

    if not name or not subject or not message or not EMAIL_RE.match(email):
        return Response("Please complete all fields with a valid email.", status=400, mimetype="text/plain")

    body = (
        "New contact form submission\n\n"
        f"Name: {name}\nEmail: {email}\nSubject: {subject}\n\nMessage:\n{message}\n"
    )

    try:
        asyncio.run(
            send_via_sendgrid(
                subject=f"[Where To?] {subject}",
                text=body,
                to_email=os.environ["EMAIL_TO"],
                from_email=os.environ["EMAIL_FROM"],
            )
        )
        # IMPORTANT: php-email-form expects plain "OK" on success
        return Response("OK", mimetype="text/plain")
    except Exception as e:
        app.logger.exception("Email send failed")
        return Response("Failed to send email.", status=502, mimetype="text/plain")

if __name__ == "__main__":
    app.run(debug=True)