# Dossier Étudiant Notify
Periodically check the Polytechnique Montreal DossierEtudiant to alert me of any new grades or any modifications to my report card.

## Installation and usage
This is an Azure Function, it can be adapted to run on other plateforms. It does not need a database. It only needs access to an SMTP server to send an email and a blob storage to save the report card.

## Environnement variables
The following environnement variable must be set in order to configure the azure function.

*Email settings*
- `DOSSIER_EMAIL_SENDER` Email address for the sender
- `DOSSIER_EMAIL_TO` Email address for the receiver of the email
- `DOSSIER_EMAIL_SERVER` Hostname of the SMTP server. The server must use STARTTLS. The function is configured with sendgrid.
- `DOSSIER_EMAIL_PORT` Port of the SMTP server.
- `DOSSIER_EMAIL_USERNAME` Username to connect to the SMTP server
- `DOSSIER_EMAIL_PASSWORD` Password to connect to the SMTP server

*Blob storage settings*
- `BLOB_URL` URL of the Azure blob storage container
- `BLOB_CONTAINER_NAME` Name of the Azure storage container.
- `BLOB_KEY` Access key to the storage container.

*Polymtl settings*
- `DOSSIER_USERNAME` Username to connect to the Dossier etudiant
- `DOSSIER_PASSWORD` Password to connect to the Dossier etudiant
- `DOSSIER_DATEOFBIRTH` Date of birth used to connect to the Dossier etudiant. Yes, polymtl follows the NIST 800-63 🙄.
