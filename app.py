# -*- coding: utf-8 -*-F ,Z

import numpy as np
import pandas as pd
import operator
from flask import Flask, request, jsonify, render_template
import pickle

app = Flask(__name__)

locationID = {'L’Île-Bizard—Sainte-Geneviève': 0, 'Pierrefonds-Roxboro': 1, 'Saint-Laurent': 2, 'Ahuntsic-Cartierville': 3, 'Montréal-Nord': 4, 'Rivière-des-Prairies—Pointe-aux-Trembles': 5, 'Anjou': 6, 'Saint-Léonard': 7, 'Villeray—Saint-Michel—Parc-Extension': 8, 'Rosemont—La Petite-Patrie': 9, 'Mercier—Hochelaga-Maisonneuve': 10, 'Le Plateau-Mont-Royal': 11, 'Outremont': 12, 'Ville-Marie': 13, 'Côte-des-Neiges—Notre-Dame-de-Grâce': 14, 'Le Sud-Ouest': 15, 'Verdun': 16, 'LaSalle': 17, 'TO BE FOUND': 18}

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


# transform available roles category from one string to a list of strings
def makeList(x):
    result = x.split(",")
    return result


#calculates distance between volunteer and organization
#gives highest importance to location
#second highest importance to service size
def distance(vol, org, location, rolePref):
    distance = 0.0

    for i in range(len(vol)-1):
        if (i > 8) and (i < 12):
            distance += (1.3*(vol[i] - org[i]))**2
        elif (i > 4) and (i < 9):
            distance += (vol[i] - org[i])**2

    x = locationID[location]
    y = locationID[org[2]]
    if x < y:
        locDist = distMatrix[x][y]
    else:
        locDist = distMatrix[y][x]

    distance += (2*((2/5)*locDist))**2
    if rolePref not in org[4]:
        distance += 5

    return np.sqrt(distance)


#creates dictionary of all distances
def rank(vol, orgs, location, rolePref):
    weights = {}
    for i in range(0, len(orgs)):
        dist = distance(vol, orgs.iloc[i, :], location, rolePref)
        weights[i] = dist

    return weights


#returns the names of the top 5 corresponding organization
def getFiveNames(sortedOrgs, orgs):
    names = []
    for i in range(5):
        names.append(orgs.iloc[sortedOrgs[i][0], 1])

    return names


def finalRanking(location, serviceSizePref, orgSizePref, rolePref):
    orgs = pd.read_csv("Organizations_V2.csv")
    orgs = orgs.iloc[:, 0:7]
    #dummify columns
    orgs = pd.get_dummies(orgs, columns=["Org size", "Service size"])
    #create list of roles
    orgs["Available roles"] = orgs["Available roles"].apply(makeList)

    #create volunteer instance from user input
    testArr = [0 for _ in range(12)]
    if serviceSizePref == "small":
        testArr[11] = 1
    elif serviceSizePref == "medium":
        testArr[10] = 1
    else:  # large
        testArr[9] = 1

    if orgSizePref == "small":
        testArr[8] = 1
    elif orgSizePref == "medium":
        testArr[7] = 1
    else:  # large (should maybe be id: 6)
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

    input = [str(x) for x in request.form.values()]
    location = input[0]
    serviceSizePref = input[1]
    orgSizePref = input[2]
    rolePref = input[3]

    output = finalRanking(location, serviceSizePref, orgSizePref, rolePref)
    predText = 'Top 5 orgs:<br> 1.{} <br> 2.{} <br> 3.{} <br> 4.{} <br> 5.{}'.format(
        output[0], output[1], output[2], output[3], output[4])
    return render_template('index.html', prediction_text=predText)


if __name__ == "__main__":
    app.run(debug=True)
