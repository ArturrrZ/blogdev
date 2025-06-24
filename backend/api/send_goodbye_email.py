from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string


def send_goodbye_email(fromemail, toemail, creator_username):
    
    # First, render the plain text content.
    text_content = render_to_string(
        "emails/goodbye.txt",
        context={"my_variable": 42},
    )
    
    # Secondly, render the HTML content.
    html_content = render_to_string(
        "emails/goodbye.html",
        context={"my_variable": 42},
    )
    # Then, create a multipart email instance.
    msg = EmailMultiAlternatives(
        f"{creator_username}'s subscription cancellation",
        text_content,
        fromemail,
        toemail,
        headers={"List-Unsubscribe": "<mailto:unsub@example.com>"},
    )
    
    # Lastly, attach the HTML content to the email instance and send.
    msg.attach_alternative(html_content, "text/html")
    msg.send()