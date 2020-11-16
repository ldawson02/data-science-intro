import gspread
import numpy as np
import pandas as pd
from fuzzywuzzy import fuzz
from fuzzywuzzy import process

import pitchfork
from google.oauth2.service_account import Credentials

pd.set_option("display.max_rows", None, "display.max_columns", None)


# Call the PITCHFORK API to get information on the album
def get_score(album, artist):
    try:
        rec = pitchfork.search(artist, album)
        return rec.score()
    except IndexError:
        print(f"Cannot find album \"{album}\" by {artist}")


def clean_col(col):
    res = col.split(", ", 1)
    res.reverse()
    return " ".join(res)


def find_match(match1_options, search1_options, match2_options, search2_options, cutoff=50):
    names_array = []
    artists_array = []
    ratio_array = []
    s2_dict = {s1: s2 for s1, s2 in zip(search1_options, search2_options)}

    for m1, m2 in zip(match1_options, match2_options):
        if m1 in s2_dict and m2 == s2_dict[m1]:
            # Exact match found
            names_array.append(m1)
            artists_array.append(m2)
            ratio_array.append(100)
        elif m1 in search1_options:
            # Exact match on album, check artist
            y = process.extractOne(m2, [s2_dict[m1]])
            if y[1] > cutoff:
                names_array.append(m1)
                artists_array.append(y[0])
                names_array.append(y[1])
            else:
                names_array.append('')
                artists_array.append('')
                ratio_array.append('')
        else:
            x = process.extractOne(m1, search1_options, scorer=fuzz.token_set_ratio)
            y = process.extractOne(m2, [s2_dict[x[0]]])
            if x[1]*y[1]/100 > cutoff:
                names_array.append(x[0])
                artists_array.append(y[0])
                ratio_array.append(x[1]*y[1]/100)
            else:
                names_array.append('')
                artists_array.append('')
                ratio_array.append('')

    df = pd.DataFrame()
    df['rs_albums'] = pd.Series(names_array)
    df['rs_art'] = pd.Series(artists_array)
    df['match'] = pd.Series(ratio_array)
    return df


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


# Extract sheet ref and all of the values from Album Rankings sheet
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


# Get Rolling Stone's top 500 albums data
rs_data = get_sheet("Rolling Stone's 500 Greatest Albums", "Main").get_all_records()
tmp_df = pd.DataFrame(rs_data)[['2020 #', 'Artist', 'Album']]
tmp_df['Artist_clean'] = tmp_df.apply(lambda tmp: clean_col(tmp['Artist']), axis=1)
rs_df = tmp_df[(tmp_df['2020 #'].notnull()) & (tmp_df['2020 #'] != '')]

# Use fuzzy match to find album/artist in RS list
df1 = find_match(df['Album'], rs_df['Album'], df['Artist'], rs_df['Artist_clean'], 75)
df1['sheet_albums'] = pd.Series(df['Album'].tolist())

data = df1.merge(rs_df, 'left', left_on=['rs_albums', 'rs_art'], right_on=['Album', 'Artist_clean'])['2020 #']\
    .fillna('').to_numpy()[np.newaxis].T.tolist()

# Update the spreadsheet
header = sheet.find("RS Top 500")
first_cell = sheet.cell(row=header.row+1, col=header.col).address
last_cell = sheet.cell(row=header.row+1+len(data), col=header.col).address
sheet.update(f'{first_cell}:{last_cell}', data, value_input_option='RAW')
