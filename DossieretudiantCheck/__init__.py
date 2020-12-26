import datetime
import logging
import requests
from bs4 import BeautifulSoup
import hashlib
import os

import smtplib, ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders


import azure.functions as func
from azure.storage.blob import BlobClient

def __computeHash(fileBlob):
    # Compute sha256 for pdf file for the correct part
    content_pos = 0x138
    hasher = hashlib.sha256()
    hasher.update(fileBlob[content_pos:])
    return hasher.hexdigest()

def __send_email(file_content):
    sender_email = os.environ["DOSSIER_EMAIL_SENDER"]
    receiver_email = os.environ["DOSSIER_EMAIL_TO"]

    message = MIMEMultipart()
    message["Subject"] = "[POLYMTL] Changements sur le bulletin"
    message["From"] = sender_email
    message["To"] = receiver_email

    body = """\
Bonjour,

Des changements ont été détectés dans le bulletin. Vous pouvez le consutler, il est attaché dans ce courriel.

Un message d'une Azure Function :)
    """

    message.attach(MIMEText(body, "plain"))
    
    filename = "report.pdf"    
    part = MIMEBase("application", "octet-stream")
    part.set_payload(file_content)

    # Encode file in ASCII characters to send by email    
    encoders.encode_base64(part)

    # Add header as key/value pair to attachment part
    part.add_header(
        "Content-Disposition",
        f"attachment; filename= {filename}",
    )

    # Add attachment to message and convert message to string
    message.attach(part)
    text = message.as_string()

    # Log in to server using secure context and send email
    with smtplib.SMTP(os.environ["DOSSIER_EMAIL_SERVER"], int(os.environ["DOSSIER_EMAIL_PORT"])) as server:
        server.ehlo()
        server.starttls()
        server.ehlo()
        server.login(os.environ["DOSSIER_EMAIL_USERNAME"], os.environ["DOSSIER_EMAIL_PASSWORD"])
        server.sendmail(sender_email, receiver_email, text)

def main(mytimer: func.TimerRequest) -> None:
    utc_timestamp = datetime.datetime.utcnow().replace(
        tzinfo=datetime.timezone.utc).isoformat()

    logging.info('Python timer trigger function ran at %s', utc_timestamp)
    blob = BlobClient(account_url=os.environ["BLOB_URL"],
                  container_name=os.environ["BLOB_CONTAINER_NAME"],
                  blob_name="report.pdf",
                  credential=os.environ["BLOB_KEY"])

    data = {"code": os.environ["DOSSIER_USERNAME"], "nip": os.environ["DOSSIER_PASSWORD"], "naissance": os.environ["DOSSIER_DATEOFBIRTH"]}
    headers = requests.utils.default_headers()
    headers.update({
        "User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.88 Safari/537.36"
    })

    s = requests.Session()
    loginPage = ""

    rlogin = s.post("https://dossieretudiant.polymtl.ca/WebEtudiant7/ValidationServlet", data=data, headers=headers)
    if rlogin.status_code == requests.codes.ok:
        logging.info("Connected to dossieretudiant")
        loginPage = rlogin.text
    else:
        logging.error("Invalid response code login")
        return
    
    soup = BeautifulSoup(loginPage, "html.parser")
    pdfRequest = {}

    for element in soup.form.find_all("input", attrs={"type":"hidden"}):
        pdfRequest[element.attrs["name"]] = element.attrs["value"]

    rreport = s.post("https://dossieretudiant.polymtl.ca/WebEtudiant7/AfficheBulletinServlet", data=pdfRequest, headers=headers)
    if rreport.status_code == requests.codes.ok:
        report = rreport.content
    
        logging.info("Report card fetched from dossier etudiant.")

        # Read file from blob
        newFile = False
        if blob.exists():
            logging.info("Old report card fetched from the blob storage")
            oldReport = blob.download_blob().readall()

            if __computeHash(report) != __computeHash(oldReport):
                newFile = True
        else:
            newFile = True
        
        if newFile: 
            logging.info("New changes detected!")

            blob.upload_blob(report,overwrite=True)
            logging.info("File exported to blob.")
            __send_email(report)
            logging.info("Email sent.")

        else:
            logging.info("No new changes detected!")
    else:
        logging.error("Invalid response code pdf")
        return
