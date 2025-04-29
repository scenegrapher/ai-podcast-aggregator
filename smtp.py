import smtplib
from email.mime.text import MIMEText


def send_email(episodes):
    if not episodes:
        return

    body = "\n".join(
        [f"{e['title']} - {e['podcast_title']} ({e['link']})" for e in episodes]
    )
    msg = MIMEText(body)
    msg["Subject"] = f"Daily AI Podcasts - {date.today()}"
    msg["From"] = "your_email@example.com"
    msg["To"] = "recipient@example.com"

    with smtplib.SMTP("smtp.gmail.com", 587) as server:
        server.starttls()
        server.login("your_email@example.com", "your_password")
        server.sendmail(msg["From"], msg["To"], msg.as_string())
