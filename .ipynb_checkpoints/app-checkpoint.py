import numpy as np
import pandas as pd
import operator
from flask import Flask, request, jsonify, render_template, url_for
import pickle

app = Flask(__name__)

# list of locations
locationID = ['L’Île-Bizard—Sainte-Geneviève', 'Pierrefonds-Roxboro', 'Saint-Laurent', 'Ahuntsic-Cartierville',
              'Montréal-Nord', 'Rivière-des-Prairies—Pointe-aux-Trembles', 'Anjou', 'Saint-Léonard',
              'Villeray—Saint-Michel—Parc-Extension', 'Rosemont—La Petite-Patrie', 'Mercier—Hochelaga-Maisonneuve',
              'Le Plateau-Mont-Royal', 'Outremont', 'Ville-Marie', 'Côte-des-Neiges—Notre-Dame-de-Grâce',
              'Le Sud-Ouest', 'Verdun', 'LaSalle']

# matrix that maps two locations to their physical distance
distMatrix = [[1, 2, 3, 4, 5, 5, 4, 3, 4, 5, 4, 4, 4, 3, 4, 4, 3, 2],
              [0, 1, 1, 2, 4, 3, 3, 2, 2, 4, 3, 3, 3, 2, 3, 3, 3, 2],
              [0, 0, 1, 2, 3, 3, 2, 1, 1, 2, 1, 1, 2, 1, 2, 2, 2, 1],
              [0, 0, 0, 1, 2, 2, 1, 1, 2, 3, 2, 2, 3, 2, 3, 3, 3, 2],
              [0, 0, 0, 0, 1, 1, 1, 1, 2, 2, 2, 2, 3, 3, 4, 4, 4, 4],
              [0, 0, 0, 0, 0, 1, 1, 2, 2, 2, 3, 3, 3, 4, 4, 5, 5, 5],
              [0, 0, 0, 0, 0, 0, 1, 2, 2, 1, 2, 3, 3, 4, 4, 4, 5, 5],
              [0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 2, 2, 3, 3, 4, 4, 5, 5],
              [0, 0, 0, 0, 0, 0, 0, 0, 1, 2, 1, 1, 2, 1, 3, 3, 4, 3],
              [0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 2, 2, 3, 3, 4, 4],
              [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 2, 1, 2, 2, 3, 4, 4],
              [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 2, 2, 3, 3],
              [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 2, 2, 3],
              [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 2, 1, 1],
              [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 2],
              [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 2],
              [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
              [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]]

# dictionary mapping input to index in volunteer sizes preference list
orgSizePreferenceMap = {'smallOrg': 2, 'mediumOrg': 1, 'largeOrg': 0}
serviceSizePreferenceMap = {'smallService': 2, 'mediumService': 1, 'largeService': 0}

def makeList(x):
    '''splits string into a list with elements separated by ', ' '''
    result = x.split(", ")
    return result

def getPhysicalDistance(location1, location2):
    ''' given 2 locations, return physical distance weight given in the distance matrix'''
    print("Form Location " + location1)
    print("Org Location " + location2)
    print(location1 in locationID)
    print(location2 in locationID)

    print( location1 == location2)

    if location1 in locationID and location2 in locationID:
        x = locationID.index(location1)
        y = locationID.index(location2)
        print("Form Location Index " + str(x))
        print("Org Location Index " + str(y))
    else:  # location doesn't exist
        return 10

    if x < y:
        print(distMatrix[x][y])
        return distMatrix[x][y]
    else:
        print(distMatrix[y][x])
        return distMatrix[y][x]

def getSizePrefDistance(orgSizePref, serviceSizePref, org):
    '''return a value that increases the less the org and the volunteers preferences are compatible'''
    
    result = 0.0
    orgSizeCompatible = False
    serviceSizeCompatible = False
    orgSizeSelected = True
    serviceSizeSelected = True

    if orgSizePref == [0, 0, 0]:
        orgSizeSelected = False
    if serviceSizePref == [0, 0, 0]:
        serviceSizeSelected = False

    sizePref = [orgSizePref, serviceSizePref]

    # checking if volunteer's size preferences are what the organisation can offer
    for i in range(len(sizePref)):
        for j in range(len(sizePref[i])):
            if sizePref[i][j] == 1 and org[(i*5 + j)] == 1:
                if i == 0:
                    orgSizeCompatible = True
                elif i == 1:
                    serviceSizeCompatible = True

    # increasing distance if org size doesn't correspond to preference or if no selection
    if not orgSizeCompatible and orgSizeSelected:
        result += 2
    # increasing distance if service size doesn't correspond to preference or if no selection
    if not serviceSizeCompatible and serviceSizeSelected:
        result += 2*((1.3)**2)

    return result
    # Ideas: could increase less if pref is small and vol is medium than when vol is large

def getRoleDistance(rolePref, org):
    '''returns a weight if roles wanted are not available'''
    # no roles selected
    if rolePref == []:
        return 0.0

    availableRoles = 0
    for role in rolePref:
        if role in org[4]:
            availableRoles += 1

    return ((1-availableRoles/len(rolePref))*5)

def distance(orgSizePref, serviceSizePref, org, location, rolePref):
    '''calculates distance between volunteer and organization
        pref: list of length 6 with 1 and zero corresponding to volunteer's preferences. 
            ex: [0, 0, 1, 0, 1, 0] org size: small, service size: medium
        gives highest importance to location
        second highest importance to service size'''

    distance = 0.0
    #increase distance if the org size properties aren't compatable with volunteer's preferences
    distance += getSizePrefDistance(orgSizePref, serviceSizePref, org)
    # increasing distance proportional to the physical distance between org's location and volunteer's location
    distance += ((4/5)*getPhysicalDistance(location, org[2]))**2
    # increasing distance if the prefered role isn't available
    distance += getRoleDistance(rolePref, org)

    return np.sqrt(distance) #not necessary to square root

def rank(orgSizePref, serviceSizePref, orgs, location, rolePref):
    '''creates a dictionary mapping org id to distance (weight) corresponding to the volunteer's preferences'''
    weights = {}
    for i in range(0, len(orgs)):
        weights[i] = distance(orgSizePref, serviceSizePref, orgs.iloc[i, :], location, rolePref)

    print(weights)

    return weights

def getFiveNames(sortedOrgs, orgs):
    '''returns the names of the top 5 corresponding organization'''
    names = []
    for i in range(5):
        names.append(orgs.iloc[sortedOrgs[i][0], 1])

    return names

def finalRanking(location, orgSizePref, serviceSizePref, rolePref):
    '''returns the top five orgs corresponding to the volunteers preference'''
    orgs = pd.read_excel("./Organizations_V3.xlsx", sheet_name= "org_list")
    #orgs = pd.read_csv("Organizations_V2.csv")
    orgs = orgs.iloc[:, 0:7]
    #dummify columns
    orgs = pd.get_dummies(orgs, columns=["Org size", "Service size"])
    #create list of roles
    orgs["Available roles"] = orgs["Available roles"].apply(makeList)

    #weight compatibility of organizations with preferences
    print("Location " + location)
    weighted = rank(orgSizePref, serviceSizePref, orgs, location, rolePref)
    sortedOrgs = sorted(weighted.items(), key=operator.itemgetter(1))

    #find and display the top 5
    output = getFiveNames(sortedOrgs, orgs)

    return output

def readDescription(orgName):
    '''returns description (string) of given organization'''

    descriptionAddress = 'static/media/description/' + orgName + '.txt'
    f = open(descriptionAddress, 'r')
    description = f.read()
    f.close()

    return description

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/predict', methods=['POST'])
def predict():
    '''receives inputs of preferences from POST, and outputs the top 5 orgs that best fits the preferences'''
    orgSizePref = [0, 0, 0]
    serviceSizePref = [0, 0, 0]
    location = ''
    rolePref = []

    # process input
    inp = request.form.values()
    input = [str(x) for x in inp]
    for i in input:
        if i in locationID:
            location = i
        elif i in orgSizePreferenceMap:
            orgSizePref[orgSizePreferenceMap[i]] = 1
        elif i in serviceSizePreferenceMap:
            serviceSizePref[serviceSizePreferenceMap[i]] = 1
        else: # roles
            rolePref.append(i)

    print(input)

    names = finalRanking(location, orgSizePref, serviceSizePref, rolePref)
    print(names)
    #extracting the description and link of rank orgs from organizations_V3.xlsx file
    descriptions = []
    links = []
    orgs = pd.read_excel("./Organizations_V3.xlsx", sheet_name= "org_list")
    for i in names:
        org_descr = orgs.loc[orgs['Name'] == i, 'Brief description' ].item()
        org_link = orgs.loc[orgs['Name'] == i, 'Link'].item()
        descriptions.append(org_descr)
        links.append(org_link)

    # replacing all spaces in names by underscore to open org file
    names_adress = names.copy()
    for i in range(len(names_adress)):
        temp = names_adress[i]
        temp = temp.lower()
        names_adress[i] = temp.replace(' ', '_')

    #descriptions = [readDescription(names[0]), readDescription(names[1]), readDescription(names[2]), readDescription(names[3]), readDescription(names[4])]
    
    return render_template('topOrgsPreset.html', orgNames = names, orgAdress = names_adress, descriptions = descriptions, links = links)
    
if __name__ == "__main__":
    app.run(debug=True)
