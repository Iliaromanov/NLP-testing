###########################################################
# Goal: parse block of text and extract categorical data  #
#       eg: "Address 123 Lester, Suite 567" =>            #
#             {'Address': "123 Lester", 'Suite': "567"}   #
###########################################################

text = "Suite 08 Condominium Plot aBGH-1234 Lot 123 Leslie St. Size 45km^2, Unit 512; High elevation on walls and damp asphalt around building makes cleanup difficult during times of disturbance in the nature"

import spacy
from spacy.matcher import PhraseMatcher
# python -m spacy download en_core_web_sm

nlp = spacy.load('en_core_web_sm')
doc = nlp(text)

for token in doc:
    print(token)

matcher = PhraseMatcher(nlp.vocab, attr='LOWER')
categories = ['Address', 'Suite', 'Condominium Unit', 'Unit', 'Plot', 'Lot', 'Condominium Plot', 'Size']

patterns = [nlp(category) for category in categories]
matcher.add('Categories', patterns)

matches = matcher(doc)
print(matches)

for match in matches:
    match_id, start, end = match
    print(nlp.vocab.strings[match_id], doc[start:end])