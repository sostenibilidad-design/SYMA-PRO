from google.oauth2 import service_account
from googleapiclient.discovery import build

# Lee las credenciales del bot
creds = service_account.Credentials.from_service_account_file(
    'credentials.json', 
    scopes=["https://www.googleapis.com/auth/drive"]
)
service = build("drive", "v3", credentials=creds)

print("Vaciando papelera del bot...")
service.files().emptyTrash().execute()
print("¡Papelera vaciada con éxito! El bot ya tiene sus 15 GB libres.")