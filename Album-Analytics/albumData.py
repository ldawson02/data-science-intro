import pitchfork
import gspread
from google.oauth2.service_account import Credentials


# use creds to create a client to interact with the Google Drive API
scope = ['https://spreadsheets.google.com/feeds',
         'https://www.googleapis.com/auth/drive']
creds = Credentials.from_service_account_file('client_secret.json', scopes=scope)
client = gspread.authorize(creds)

# Find a workbook by name and open the first sheet
# Make sure you use the right name here.
sheet = client.open("Album Rankings").worksheet("Main")

# Extract and print all of the values
list_of_hashes = sheet.get_all_records()
print(list_of_hashes)

p = pitchfork.search("the national","i am easy to find")

print(p.score())