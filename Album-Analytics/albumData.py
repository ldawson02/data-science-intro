import gspread
import numpy as np
import pandas as pd
import pitchfork
from google.oauth2.service_account import Credentials


# Call the PITCHFORK API to get information on the album
def get_score(album, artist):
    try:
        rec = pitchfork.search(artist, album)
        return rec.score()
    except IndexError:
        print(f"Cannot find album \"{album}\" by {artist}")


def get_sheet(ss_name, sheet_name="Sheet1"):
    # Use creds to create a client to interact with the Google Drive API
    scope = ['https://spreadsheets.google.com/feeds',
             'https://www.googleapis.com/auth/drive']
    creds = Credentials.from_service_account_file('client_secret.json', scopes=scope)
    client = gspread.authorize(creds)

    # Find a workbook by name and open the first sheet
    # Make sure you use the right name here.
    sheet = client.open(ss_name).worksheet(sheet_name)
    return sheet


# Extract and print all of the values
sheet = get_sheet("Album Rankings", "Main")
all_data = sheet.get_all_records()

# Convert to dataframe and get Pitchfork score
df = pd.DataFrame(all_data)[['Album', 'Artist']]
df['Score'] = df.apply(lambda tmp: get_score(tmp['Album'], tmp['Artist']), axis=1).fillna("")

data = df['Score'].to_numpy()[np.newaxis].T.tolist()

# Update the spreadsheet
header = sheet.find("Pitchfork Rating")
first_cell = sheet.cell(row=header.row+1, col=header.col).address
last_cell = sheet.cell(row=header.row+1+len(data), col=header.col).address
sheet.update(f'{first_cell}:{last_cell}', data, value_input_option='RAW')
