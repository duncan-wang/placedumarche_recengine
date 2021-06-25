import numpy as np
import pandas as pd
import operator
from flask import Flask, request, jsonify, render_template
import pickle

app = Flask(__name__)

# list of locations
locationID = ['L’Île-Bizard—Sainte-Geneviève', 'Pierrefonds-Roxboro', 'Saint-Laurent', 'Ahuntsic-Cartierville',
              'Montréal-Nord', 'Rivière-des-Prairies—Pointe-aux-Trembles', 'Anjou', 'Saint-Léonard',
              'Villeray—Saint-Michel—Parc-Extension', 'Rosemont—La Petite-Patrie', 'Mercier—Hochelaga-Maisonneuve',
              'Le Plateau-Mont-Royal', 'Outremont', 'Ville-Marie', 'Côte-des-Neiges—Notre-Dame-de-Grâce',
              'Le Sud-Ouest', 'Verdun', 'LaSalle']

# matrix that maps two locations to their physical distance
distMatrix = [[0, 1, 2, 3, 4, 5, 5, 4, 3, 4, 5, 4, 4, 4, 3, 4, 4, 3, 2],
              [0, 0, 1, 1, 2, 4, 3, 3, 2, 2, 4, 3, 3, 3, 2, 3, 3, 3, 2],
              [0, 0, 0, 1, 2, 3, 3, 2, 1, 1, 2, 1, 1, 2, 1, 2, 2, 2, 1],
              [0, 0, 0, 0, 1, 2, 2, 1, 1, 2, 3, 2, 2, 3, 2, 3, 3, 3, 2],
              [0, 0, 0, 0, 0, 1, 1, 1, 1, 2, 2, 2, 2, 3, 3, 4, 4, 4, 4],
              [0, 0, 0, 0, 0, 0, 1, 1, 2, 2, 2, 3, 3, 3, 4, 4, 5, 5, 5],
              [0, 0, 0, 0, 0, 0, 0, 1, 2, 2, 1, 2, 3, 3, 4, 4, 4, 5, 5],
              [0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 2, 2, 3, 3, 4, 4, 5, 5],
              [0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 2, 1, 1, 2, 1, 3, 3, 4, 3],
              [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 2, 2, 3, 3, 4, 4],
              [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 2, 1, 2, 2, 3, 4, 4],
              [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 2, 2, 3, 3],
              [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 2, 2, 3],
              [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 2, 1, 1],
              [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 2],
              [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 2],
              [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
              [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]]

# dictionary mapping input to index in volunteer list
inputID = {'smallService': 2, 'mediumService': 1, 'largeService': 0, 'smallOrg': 5, 'mediumOrg': 4, 'largeOrg': 3}

def makeList(x):
    '''splits string into a list with elements separated by ', ' '''
    result = x.split(", ")
    return result

def getPhysicalDistance(location1, location2):
    ''' given 2 locations, return physical distance weight given in the distance matrix'''

    if location1 in locationID and location2 in locationID:
        x = locationID.index(location1)
        y = locationID.index(location2)
    else:  # location doesn't exist
        return 10

    if x < y:
        return distMatrix[x][y]
    else:
        return distMatrix[y][x]

def getSizesDistance(sizePref, org):
    '''return a value that increases the less the org and the volunteers preferences are compatible'''
    
    # if no preferences selected, return 0 since all posibilities are good
    if sizePref == [0, 0, 0, 0, 0, 0]:
        return 0.0

    result = 0.0

    orgSizeGood = False
    serviceSizeGood = False
    orgSizeSelected = False
    serviceSizeSelected = False

    for i in range(len(sizePref)):
        if i < 3:
            if sizePref[i] == 1:
                orgSizeSelected = True
            if sizePref[i] == 1 and org[5 + i] == 1:
                orgSizeGood = True
        else:
            if sizePref[i] == 1:
                serviceSizeSelected = True
            if sizePref[i] == 1 and org[5 + i] == 1:
                serviceSizeGood = True

    # increasing distance if org size doesn't correspond to preference or if no selection
    if not orgSizeGood and orgSizeSelected:
        result += 2
    # increasing distance if service size doesn't correspond to preference or if no selection
    if not serviceSizeGood and serviceSizeSelected:
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

def distance(sizePref, org, location, rolePref):
    '''calculates distance between volunteer and organization
        pref: list of length 6 with 1 and zero corresponding to volunteer's preferences. 
            ex: [0, 0, 1, 0, 1, 0] org size: small, service size: medium
        gives highest importance to location
        second highest importance to service size'''

    distance = 0.0
    #increase distance if the org size properties aren't compatable with volunteer's preferences
    distance += getSizesDistance(sizePref, org)
    # print('size: ', distance)
    # increasing distance proportional to the physical distance between org's location and volunteer's location
    distance += (2*((2/5)*getPhysicalDistance(location, org[2])))**2
    # print('distance: ', distance)
    # increasing distance if the prefered role isn't available
    distance += getRoleDistance(rolePref, org)
    # print('role: ', distance)

    return np.sqrt(distance) #not necessary to square root

def rank(sizePref, orgs, location, rolePref):
    '''creates a dictionary mapping org id to distance (weight) corresponding to the volunteer's preferences'''
    weights = {}
    for i in range(0, len(orgs)):
        weights[i] = distance(sizePref, orgs.iloc[i, :], location, rolePref)

    return weights

def getFiveOrgs(sortedOrgs, orgs):
    '''returns the top 5 corresponding organization'''
    topOrgs = []
    for i in range(5):
        topOrgs.append(orgs.iloc[sortedOrgs[i][0], :])

    return topOrgs

def getFiveNames(sortedOrgs, orgs):
    '''returns the names of the top 5 corresponding organization'''
    names = []
    for i in range(5):
        names.append(orgs.iloc[sortedOrgs[i][0], 1])

    return names

def finalRanking(location, sizePref, rolePref):
    '''returns the top five orgs corresponding to the volunteers preference'''
    orgs = pd.read_excel("./Organizations_V3.xlsx", sheet_name= "org_list")
    #orgs = pd.read_csv("Organizations_V2.csv")
    orgs = orgs.iloc[:, 0:7]
    #dummify columns
    orgs = pd.get_dummies(orgs, columns=["Org size", "Service size"])
    #create list of roles
    orgs["Available roles"] = orgs["Available roles"].apply(makeList)

    # print(location, sizePref, rolePref)

    #weight compatibility of organizations with preferences
    weighted = rank(sizePref, orgs, location, rolePref)
    sortedOrgs = sorted(weighted.items(), key=operator.itemgetter(1))

    # to pretty print top 5 orgs
    # output = getFiveOrgs(sortedOrgs, orgs)

    #find and display the top 5
    output = getFiveNames(sortedOrgs, orgs)
    print(sortedOrgs)

    return output

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/predict', methods=['POST'])
def predict():
    '''receives inputs of preferences from POST, and outputs the top 5 orgs that best fits the preferences'''
    sizePref = [0, 0, 0, 0, 0, 0]
    location = ''
    rolePref = []

    inp = request.form.values()
    input = [str(x) for x in inp]
    for i in input:
        if i in locationID:
            location = i
        elif i in inputID:
            sizePref[inputID[i]] = 1
        else: # roles
            rolePref.append(i)

    output = finalRanking(location, sizePref, rolePref)

    # make file result.html and find a way to output top 5 orgs in output
    # return render_template('result.html', ...)

    predText = 'Top 5 orgs:<br> 1.{} <br> 2.{} <br> 3.{} <br> 4.{} <br> 5.{}'.format(output[0], output[1], output[2], output[3], output[4])
    return render_template('index.html', prediction_text=predText)

if __name__ == "__main__":
    app.run(debug=True)
