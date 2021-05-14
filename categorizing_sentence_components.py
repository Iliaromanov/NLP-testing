###########################################################
# Goal: parse block of text and extract categorical data  #
#       eg: "Address 123 Lester, Suite 567" =>            #
#             {'Address': "123 Lester", 'Suite': "567"}   #
###########################################################

text = "Suite 08 Condominium Plot aBGH-1234 Lot 123 Leslie St. Size 45km^2, Unit 512; High elevation on walls and damp asphalt around building makes cleanup difficult during times of disturbance in the nature"
features_to_extract = ['plan', 'block', 'lot', 'condoplan', 'unit'] # Must be all lower

import pyodbc
import pandas as pd
import numpy as np
import spacy
import wordninja
from spacy.matcher import PhraseMatcher

import time

# Connect to db and create cursor object
# conn = () #connect to a db if needed
# cursor = conn.cursor()

data_to_clean = pd.read_sql_query(query_for_data, conn)

# Loading the NLP model for breaking up words and getting indexes of features to extract
nlp = spacy.load('en_core_web_sm')


# Description containing 'no' are unparsable for now
for row_num, row_data in data_to_clean.iterrows():

    if row_num > 28:
        break
    
    if row_num != 26:
        tic = time.time()
        continue

    # Text preprocessing. (THIS PART REALLY DEPENDS ON WHAT FEATURES YOU WANT TO EXTRACT AND YOUR DATA)
    text = row_data['legal desc']
    text = text.lower().replace('plt', '').replace('blk', 'block')
    separated = wordninja.split(text)
    text = ' '.join(separated)
    text = text.replace('condominium plan', 'condoplan').replace('condo plan', 'condoplan').replace('lots', 'lot')
    doc = nlp(text)

    print(f"row_num {row_num + 1}:")
    print(text)

    # Creating a matcher object to get info on indexes of desired fields in text
    matcher = PhraseMatcher(nlp.vocab)
    matcher.add("Categories", [nlp(s) for s in features_to_extract])
    matches = matcher(doc)
    #print(matches)

    categ_start_indexes = [match[1] for match in matches]
    
    parsed_result = {'PLAN': None, 'BLOCK': None, 'LOT': None, 'CONDOPLAN': None, 'UNIT': None, 'AdditionalText': None} # AGAIN DEPENDS ON features_to_extract

    # Saving the parsed feature data to the parsed_result dict
    for i, match in enumerate(matches):
        if i < len(categ_start_indexes) - 1:
            value = str(doc[match[2]:categ_start_indexes[i + 1]])
            
            # uppercase and remove spaces
            value = value.replace(' ', '').upper()

            # If value is too long, then select only numeric data from it
            #   allowing 9 chars max eg. 123and456 is valid
            if len(value) >= 10:
                new_value = ""
                j = match[2]
                while j <= len(doc) - 1: # Error prone when value is much longer than doc
                    print(doc[j])
                    if str(doc[j]) in ' '.join(features_to_extract):
                        break
                    if str(doc[j]).isnumeric():
                        new_value += str(doc[j])
                    j += 1
                value = new_value

            # NULL if not found
            if value == '':
                value = None

            parsed_result[str(doc[match[1]:match[2]]).upper()] = value
        else:
            value = ""
            j = match[2]
            while j <= len(doc) - 1 and (str(doc[j]).isnumeric() or str(doc[j]) == "and"):
                value += str(doc[j])
                j += 1
            parsed_result[str(doc[match[1]:match[2]]).upper()] = value

            # Additional Text parsing
            additional = str(doc[j:])
            if additional == '':
                additional = None
            parsed_result['AdditionalText'] = additional
            
    print(parsed_result)
    
    # UPDATING DB
    for field in list(parsed_result.keys()):
        update_extracted_features = f"""
                                     UPDATE {db_name}
                                         SET [{field}] = ?
                                     WHERE FILERECORDID = ?
                                    """
        cursor.execute(update_extracted_features, [parsed_result[field], row_data['id']])
        conn.commit()

    if row_num < 105:
        toc = time.time()
        print(f"time: {toc - tic}s")
    #print('\n~~~~\n')

print("DONE")
