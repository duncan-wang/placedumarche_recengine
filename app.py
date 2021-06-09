# -*- coding: utf-8 -*-F ,Z

import numpy as np
import pandas as pd
import operator
from flask import Flask, request, jsonify, render_template
import pickle

app = Flask(__name__)

locationID = {'L’Île-Bizard—Sainte-Geneviève': 0, 'Pierrefonds-Roxboro': 1, 'Saint-Laurent': 2, 'Ahuntsic-Cartierville': 3,
              'Montréal-Nord': 4, 'Rivière-des-Prairies—Pointe-aux-Trembles': 5, 'Anjou': 6, 'Saint-Léonard': 7,
              'Villeray—Saint-Michel—Parc-Extension': 8, 'Rosemont—La Petite-Patrie': 9, 'Mercier—Hochelaga-Maisonneuve': 10,
              'Le Plateau-Mont-Royal': 11, 'Outremont': 12, 'Ville-Marie': 13, 'Côte-des-Neiges—Notre-Dame-de-Grâce': 14,
              'Le Sud-Ouest': 15, 'Verdun': 16, 'LaSalle': 17, 'TO BE FOUND': 18}

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

def makeList(x):
    '''splits string into a list with elements separated by ',' '''
    result = x.split(",")
    return result

def getPhysicalDistance(location1, location2):
    ''' given 2 locations, return physical distance weight given in the distance matrix'''
    if locationID[location1] < locationID[location2]:
        return distMatrix[locationID[location1]][locationID[location2]]
    else:
        return distMatrix[locationID[location2]][locationID[location1]]

def distance(vol, org, location, rolePref):
    '''calculates distance between volunteer and organization
        vol: list of length 6 with 1 and zero corresponding to volunteer's preferences. 
            ex: [0, 0, 1, 0, 1, 0] org size: small, service size: medium
        gives highest importance to location
        second highest importance to service size'''
    
    distance = 0.0

    # increasing distance if org size doesn't correspond to preference
    distance += (vol[0] - org[5])**2
    distance += (vol[1] - org[6])**2
    distance += (vol[2] - org[7])**2

    # increasing distance if service size doesn't correspond to preference
    distance += (1.3*(vol[3] - org[8]))**2
    distance += (1.3*(vol[4] - org[9]))**2
    distance += (1.3*(vol[5] - org[10]))**2

    # increasing distance based on the physical distance between org's location and volunteer's location
    distance += (2*((2/5)*getPhysicalDistance(location, org[2])))**2

    # increasing distance if the prefered role isn't available
    if rolePref not in org[4]:
        distance += 5

    return np.sqrt(distance) #not necessary to square root

def rank(vol, orgs, location, rolePref):
    '''creates a dictionary mapping org id to distance (weight) corresponding to the volunteer's preference'''
    weights = {}
    for i in range(0, len(orgs)):
        dist = distance(vol, orgs.iloc[i, :], location, rolePref)
        weights[i] = dist

    return weights

def getFiveNames(sortedOrgs, orgs):
    '''returns the names of the top 5 corresponding organization'''
    names = []
    for i in range(5):
        names.append(orgs.iloc[sortedOrgs[i][0], 1])

    return names

def finalRanking(location, serviceSizePref, orgSizePref, rolePref):
    '''returns the top five orgs corresponding to the volunteers preference'''
    orgs = pd.read_csv("Organizations_V2.csv")
    orgs = orgs.iloc[:, 0:7]
    #dummify columns
    orgs = pd.get_dummies(orgs, columns=["Org size", "Service size"])
    #create list of roles
    orgs["Available roles"] = orgs["Available roles"].apply(makeList)

    #create volunteer instance from user input
    testArr = [0 for _ in range(6)]

    if orgSizePref == "large":
        testArr[0] = 1
    elif orgSizePref == "medium":
        testArr[1] = 1
    elif orgSizePref == "small":
        testArr[2] = 1
    if serviceSizePref == "large":
        testArr[3] = 1
    elif serviceSizePref == "medium":
        testArr[4] = 1
    elif orgSizePref == "small":
        testArr[5] = 1

    #weight compatibility of organizations with preferences
    weighted = rank(testArr, orgs, location, rolePref)
    sortedOrgs = sorted(weighted.items(), key=operator.itemgetter(1))

    #find and display the top 5
    output = getFiveNames(sortedOrgs, orgs)
    return output

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/predict', methods=['POST'])
def predict():
    '''receives inputs of preferences from POST, and outputs the top 5 orgs that best fits the preferences'''
    input = [str(x) for x in request.form.values()]
    location = input[0]
    serviceSizePref = input[1]
    orgSizePref = input[2]
    rolePref = input[3]

    output = finalRanking(location, serviceSizePref, orgSizePref, rolePref)
    predText = 'Top 5 orgs:<br> 1.{} <br> 2.{} <br> 3.{} <br> 4.{} <br> 5.{}'.format(output[0], output[1], output[2], output[3], output[4])
    return render_template('index.html', prediction_text=predText)

if __name__ == "__main__":
    app.run(debug=True)