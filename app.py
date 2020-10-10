import numpy as np
import pandas as pd
import operator
from flask import Flask, request, jsonify, render_template
import pickle

app = Flask(__name__)
#model = pickle.load(open('model.pkl', 'rb'))

#prepare and display location martix
matrix = [[0,1,2,3,4,5,5,4,3,4,5,4,4,4,3,4,4,3,2],[0,0,1,1,2,4,3,3,2,2,4,3,3,3,2,3,3,3,2],
 [0,0,0,1,2,3,3,2,1,1,2,1,1,2,1,2,2,2,1],[0,0,0,0,1,2,2,1,1,2,3,2,2,3,2,3,3,3,2],
 [0,0,0,0,0,1,1,1,1,2,2,2,2,3,3,4,4,4,4],[0,0,0,0,0,0,1,1,2,2,2,3,3,3,4,4,5,5,5],
 [0,0,0,0,0,0,0,1,2,2,1,2,3,3,4,4,4,5,5],[0,0,0,0,0,0,0,0,1,1,1,2,2,3,3,4,4,5,5],
 [0,0,0,0,0,0,0,0,0,1,2,1,1,2,1,3,3,4,3],[0,0,0,0,0,0,0,0,0,0,1,1,1,2,2,3,3,4,4],
 [0,0,0,0,0,0,0,0,0,0,0,1,2,1,2,2,3,4,4],[0,0,0,0,0,0,0,0,0,0,0,0,1,1,2,2,3,4,3],
 [0,0,0,0,0,0,0,0,0,0,0,0,0,1,1,2,2,3,3],[0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,1,2,2,3],
 [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,2,1,1],[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,1,2],
 [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,2],[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1],
         [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]]
for i in range(0,19):
    for j in range(0,i):
        matrix[i][j] = matrix[j][i]
        
#returns number corresponding to row/column of matrix
def locationCode(x):
    if x == "L’Île-Bizard—Sainte-Geneviève":
        return 0
    elif x == "Pierrefonds-Roxboro":
        return 1
    elif x == "Saint-Laurent":
        return 2
    elif x == "Ahuntsic-Cartierville":
        return 3
    elif x == "Montréal-Nord":
        return 4
    elif x == "Rivière-des-Prairies—Pointe-aux-Trembles":
        return 5
    elif x == "Anjou":
        return 6
    elif x == "Saint-Léonard":
        return 7
    elif x == "Villeray—Saint-Michel—Parc-Extension":
        return 8
    elif x == "Rosemont—La Petite-Patrie":
        return 9
    elif x == "Mercier—Hochelaga-Maisonneuve":
        return 10
    elif x == "Le Plateau-Mont-Royal":
        return 11
    elif x == "Outremont":
        return 12
    elif x == "Ville-Marie":
        return 13
    elif x == "Côte-des-Neiges—Notre-Dame-de-Grâce":
        return 14
    elif x == "Le Sud-Ouest":
        return 15
    elif x == "Verdun":
        return 16
    elif x == "LaSalle":
        return 17
    else:
        return 18
    
# transform available roles category from one string to a list of strings
def makeList(x):
    result = x.split(",")
    return result

#calculates distance between volunteer and organization
#gives highest importance to location
#second highest importance to service size
def distance(vol, org, location, matrix, rolePref):
    distance = 0.0
    for i in range(len(vol)-1):
        if (i>8) and (i<12):
            distance += (1.3*(vol[i] - org[i]))**2
        elif (i>4) and (i<9):    
            distance += (vol[i] - org[i])**2
    x = locationCode(location)
    y = locationCode(org[2])
    locDist = matrix[x][y]
    distance += (2*((2/5)*locDist))**2
    if rolePref not in org[4]:
        distance += 5
    return np.sqrt(distance)

#creates dictionary of all distances
def rank(volunteer, orgDf, rankings, location, matrix, rolePref):
    for i in range(0,len(orgDf)):
        dist = distance(volunteer, orgDf.iloc[i,:], location, matrix, rolePref)
        rankings[i]= dist
    return rankings

#returns the indices of the top 5 organizations
def getFiveKeys(x):
    result = []
    for i in range(5):
        result.append(x[i][0])
    return result

#returns the names of the top 5 indices
def getNames(indexList, orgDF):
    nameList = []
    for i in indexList:
        nameList.append(orgDF.iloc[i,1])
    return nameList

#main:
def finalRanking(location, serviceSizePref, orgSizePref, rolePref):
    orgs = pd.read_csv("Organizations_V2.csv")
    orgs = orgs.iloc[:,0:7]
    #dummify columns
    orgs = pd.get_dummies(orgs, columns = ["Org size", "Service size"])
    #create list of roles
    orgs["Available roles"] = orgs["Available roles"].apply(makeList)
    #create volunteer instance from user input
    testArr = [0,0,0,0,0,0,0,0,0,0,0,0]

    if serviceSizePref == "small":
        testArr[11] = 1
    elif serviceSizePref == "medium":
        testArr[10] = 1
    else:
        testArr[9] = 1

    if orgSizePref == "small":
        testArr[8] = 1
    elif orgSizePref == "medium":
        testArr[7] = 1
    else:
        testArr[5] = 1
    #rank organizations
    ranked = rank(testArr, orgs, {}, location, matrix, rolePref)

    #sort dictionary of ranked organizations
    sorted_d = sorted(ranked.items(), key=operator.itemgetter(1))

    #find and display the top 5
    finalFive = getFiveKeys(sorted_d)
    output = getNames(finalFive,orgs)
    return output



@app.route('/')
def home():
    return render_template('index.html')

@app.route('/predict',methods=['POST'])
def predict():

    int_features = [str(x) for x in request.form.values()]
    location = int_features[0]
    serviceSizePref = int_features[1]
    orgSizePref = int_features[2]
    rolePref = int_features[3]
    #final_features = [np.array(int_features)]
    #prediction = model.predict(final_features)

    output = finalRanking(location, serviceSizePref, orgSizePref,rolePref)
    out1 = output[0]
    out2 = output[1]
    out3 = output[2]
    out4 = output[3]
    out5 = output[4]

    output = "<p id='output'> Top 5 orgs:<br> 1.{} <br> 2.{} <br> 3.{} <br> 4.{} <br> 5.{} </p>".format(out1, out2, out3, out4, out5)

    return render_template('index.html', prediction_text=output)

# @app.route('/results',methods=['POST'])
# def results():

#     data = request.get_json(force=True)
#     prediction = model.predict([np.array(list(data.values()))])

#     output = prediction[0]
#     return jsonify(output)

# test comment

if __name__ == "__main__":
    app.run(debug=True)
