import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

def notificacion_de_mensaje(Sender, Reciver, password, data):
    sender_email = Sender
    reciver_email = Reciver
    password = password

    # creamos el contenido del correo

    subject = "Reporte de Outlier"
    body = data

    message = MIMEMultipart()
    message['From'] = sender_email
    message['To'] = reciver_email
    message['Subject'] = subject

    message.attach(MIMEText(body, "plain"))

    with smtplib.SMTP("smtp.gmail.com",587) as server:
        server.starttls()
        server.login(sender_email, password)
        server.send_message(message)
    print("Mensaje Enviado")