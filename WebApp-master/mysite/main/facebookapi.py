import requests 
from bs4 import BeautifulSoup
from json import JSONDecoder
import json
import re

'''
process
facebook source doesn't have traditional html to grab data
must grab embeded json

first tryed to regex to grab any json patteren in page sourse as "string"
    didn't work due to nested json objects

then used a json decoder
    returned too many json objects to be resonable

filtered out page sourse to only show a list of <script> tags becuase all json object are in strip tags

filtered out to useful script tags at indexes 16,18

then ran the json decoder, but is only returning properly formatted json for python being

{
    "key" : "object"
}
vs
{
    key : "object"
}

need to add quotes to make it work correctly
'''

def getEntries(location, query):
    URL = 'https://www.facebook.com/marketplace/' + location + '/search/?query=' + query
    r = requests.get(URL)
    
    soup = BeautifulSoup(r.content, 'html5lib')
    code = soup.find_all('script')
    # code index 16 and 18 have useful information

    jsonFix16 = re.sub("(\{|,)(\w*):", "\g<1>\"\g<2>\":", str(code[16]))
    #jsonFix18 = re.sub("(\{|,)(\w*):", "\g<1>\"\g<2>\":", str(code[18]))

    def checkKey(dict, key): 
        if key in dict.keys(): 
            return True
        else: 
            return False

    def extract_json_objects(text, decoder=JSONDecoder()):
        pos = 0
        while True:
            match = text.find('{', pos)
            if match == -1:
                break
            try:
                result, index = decoder.raw_decode(text[match:])
                yield result
                pos = match + index
            except ValueError:
                pos = match + 1

    for i,result in enumerate(extract_json_objects(jsonFix16)):
        if i == 0:
            test = json.dumps(result)

            # fixQuote = re.sub("\'", "\"", str(result))
            # fixNone = re.sub("None", "null", fixQuote)
            # fixLeftBracket = re.sub("\"\{", "{", fixNone)
            # fixRightBracket = re.sub("\}\"", "}", fixLeftBracket)
            # fixSlashes = re.sub("\\\\", "", fixRightBracket)
            # fixTrue = re.sub("True", "true", fixSlashes)
            # fixFalse = re.sub("False", "false", fixTrue)
            # fixQuote = re.sub("(: \".*)\"(.+\"(,|}))", "\g<1>'\g<2>",  fixFalse)
            # print(fixFalse)

            pageObjTotal = json.loads(test)
    pageEntryies = pageObjTotal['jsmods']['pre_display_requires'][0][3][1]['__bbox']['result']['data']['marketplace_search']['feed_units']['edges']
    finalObj = {}
    for e in pageEntryies:
        if (checkKey(e['node'], 'listing')):
            finalObj[e['node']['listing']['id']] = {
                'title' : e['node']['listing']['marketplace_listing_title'],
                'imageUrl' : e['node']['listing']['primary_listing_photo']['image']['uri'],
                'price' : e['node']['listing']['formatted_price']['text'],
                'location' : e['node']['listing']['location']['reverse_geocode']['city_page'],
                'delivery' : e['node']['listing']['delivery_types'][0],
                'itemUrl' : e['node']['listing']['story']['url']
            }
    return finalObj

'''
Example:

# search gtx from denver
entry = getEntries('denver', 'gtx')

# grab the first entry at index 0
index = list(entry.keys())[0] 

print(entry[index])

'''