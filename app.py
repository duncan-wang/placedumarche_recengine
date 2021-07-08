import numpy as np
import pandas as pd
import operator
from flask import Flask, request, jsonify, render_template, url_for
import pickle
import mysql.connector

app = Flask(__name__)


#define credentials
host_name = "50.87.170.37"
port_name = '3306'
username = "myplaced_myplacedumarche"
password = "Mcfac_2020_mma"
db_name = "myplaced_WP1DL"

#establish db connection 
db = mysql.connector.connect(
   host = host_name,
   port = port_name,
   user = username,
   password = password,
   database = db_name
)

cursor = db.cursor()

#query from each db and fetch all results in raw format 
cursor.execute("SELECT * FROM Organizations_DB")
organizations_results = cursor.fetchall()

cursor.execute("SELECT * FROM Locations_DB")
locations_results = cursor.fetchall()

cursor.execute("SELECT * FROM Roles_DB")
roles_results = cursor.fetchall()

#create new dfs to store queried results from SQL
orgs_columns = ['OrgID', 'Name', 'Address Line 1', 'Address Line 2', 'Zip Code', 'Location', 'Coordinates', 'Org Size', 'Service Size', 'Target Demographic', 'Services Provided', 'Available Roles', 'Brief Description', 'Link', 'General Contact', 'Internal Contact', 'Consent']
organizations_df = pd.DataFrame(columns = orgs_columns)

locations_columns = ['LocationID', 'Organization Location']
locations_df = pd.DataFrame(columns = locations_columns)

roles_columns = ['RoleID', 'Available Roles']
roles_df = pd.DataFrame(columns = roles_columns)

df_list = [organizations_df, locations_df, roles_df]
results_list = [organizations_results, locations_results, roles_results]

for i in range(len(df_list)):
    for j in range(len(results_list[i])): 
        to_series = pd.Series(results_list[i][j], index = df_list[i].columns)
        df_list[i] = df_list[i].append(to_series,  ignore_index = True)

organizations_df = df_list[0]
locations_df = df_list[1]
roles_df = df_list[2]

organizations_df.replace('\xa0', ' ', regex=True, inplace=True)
locations_df = locations_df['Organization Location'].tolist()
all_locations = [i.replace('\xa0',' ') for i in locations_df]
all_roles = list(roles_df['Available Roles'])


# dictionary mapping input to index in volunteer sizes preference list
all_org_sizes = ['smallOrg', 'mediumOrg' ,'largeOrg']
all_service_sizes = ['smallService', 'mediumService' ,'largeService']

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

def getPhysicalDistance(location_pref, org_location):
    #if there is no location input or if the user selected no preference, then penalty is 0
    if location_pref == [] or location_pref == 'NoLocationPref':
        return 0
    #otherwise, loop through the user's selected locations, calculate the distance penalty for each location, and take the smallest one
    else:
        penalty = []
        for i in range(len(location_pref)): 
            x = all_locations.index(location_pref[i])
            y = all_locations.index(org_location)
            if x < y:
                penalty.append(distMatrix[x][y])
            else:
                penalty.append(distMatrix[y][x]) 
    return min(penalty)

def getRoleDistance(role_pref, org_roles):

    # if there is no role input or if the user selected no preference, then penalty is 0
    if role_pref == [] or role_pref == 'NoRolePref':
        return 0.0
    
    #for each of the user's specified roles, if the role is found in the organization, increase a counter
    #return the proportion of matched roles in relation to the number of roles specified as a score out of 5
    #ex: 2/3 matched roles = 1.66 
    available_roles = 0
    for i in role_pref:
        if i in org_roles:
            available_roles += 1

    return ((1-available_roles/len(role_pref))*5)


def getOrgSizePrefDistance(org_size_pref, org_size):
   
    # if there is no size input or if the user selected no preference, then penalty is 0
    if org_size_pref == [] or org_size_pref == 'NoOrgPref':
        return 0.0

    orgSizeMap = {'small': 'smallOrg', 'medium': 'mediumOrg', 'large': 'largeOrg'}

    #if the organization's size is contained in one of the user's preference(s), return 0
    if orgSizeMap[org_size] in org_size_pref:
        return 0.0 
    
    org_pref_penalty = 0 
    
    #increase the penalty by 2.5 if either the user's choice contains 'medium' or if the organization's size is medium -- since no matter what then the user's preference will only be 1 step away from organization's
    #otherwise increase penalty by 5 (max)
    if 'mediumOrg' in org_size_pref or org_size == 'medium':
        org_pref_penalty += 2.5 
    else:
        org_pref_penalty += 5
        
    return org_pref_penalty

def getServiceSizePrefDistance(service_size_pref, service_size):
   
    # if there is no size input or if the user selected no preference, then penalty is 0
    if service_size_pref == [] or service_size_pref == 'NoServicePref':
        return 0.0

    serviceSizeMap = {'small': 'smallService', 'medium': 'mediumService', 'large': 'largeService'}

    #if the service's size is contained in one of the user's preference(s), return 0
    if serviceSizeMap[service_size] in service_size_pref:
        return 0.0 
    
    service_pref_penalty = 0 
    
    #increase the penalty by 2.5 if either the user's choice contains 'medium' or if the organization's size is medium -- since no matter what then the user's preference will only be 1 step away from organization's
    #otherwise increase penalty by 5 (max)
    if 'mediumService' in service_size_pref or service_size == 'medium':
        service_pref_penalty += 2.5 
    else:
        service_pref_penalty += 5
        
    return service_pref_penalty

def distance(location_pref, role_pref, org_size_pref, service_size_pref, organizations_df):
    distance = 0.0
    distance += getPhysicalDistance(location_pref, organizations_df['Location'])
    distance += getRoleDistance(role_pref, organizations_df['Available Roles'])
    distance += getOrgSizePrefDistance(org_size_pref, organizations_df['Org Size'])
    distance += getServiceSizePrefDistance(service_size_pref, organizations_df['Service Size'])

    return distance

def finalRanking(location_pref, role_pref, org_size_pref, service_size_pref, organizations_df):
    
    weights = {}
    for i in range(0, len(organizations_df)):
        weights[i] = distance(location_pref, role_pref, org_size_pref, service_size_pref, organizations_df.iloc[i])
    sorted_orgs = sorted(weights.items(), key=operator.itemgetter(1))

    #find and display the top 5
    output = []
    for i in range(5):
        output.append(organizations_df.iloc[sorted_orgs[i][0], 1])
        
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
    
    #blank if no input is received 
    location_pref = []
    role_pref = []
    org_size_pref = []
    service_size_pref = []


    #placeholder for now, later this will come from the user inputs
    inp = ['Verdun', 'Saint-Laurent', 'Ville-Marie','smallOrg', 'mediumOrg', 'smallService', 'mediumService', 'Cooking' ,'Gardening/Harvesting' ,'Cleaning']

    # verify and process inputs - this step is not strictly necessary 
    inp = request.form.values()
    input = [str(x) for x in inp]
    for i in input:
        if i in all_locations or i == 'NoLocationPref': #location
            location_pref.append(i)
        elif i in all_roles or i == 'NoRolePref': #role
            role_pref.append(i)
        elif i in all_org_sizes or i == 'NoOrgPref': #org size
            org_size_pref.append(i)
        elif i in all_service_sizes or i == 'NoServicePref': #service size
            service_size_pref.append(i)


    names = finalRanking(location_pref, role_pref, org_size_pref, service_size_pref, organizations_df)

    #extracting the description and link of rank orgs from organizations_V3.xlsx file
    descriptions = []
    links = []
    
    for i in names:
        org_descr = organizations_df.loc[organizations_df['Name'] == i, 'Brief Description' ].item()
        org_link = organizations_df.loc[organizations_df['Name'] == i, 'Link'].item()
        descriptions.append(org_descr)
        links.append(org_link)

    # replacing all spaces in names by underscore to open org file
    names_address = names.copy()
    for i in range(len(names_address)):
        temp = names_address[i]
        temp = temp.lower()
        names_address[i] = temp.replace(' ', '_')
    
        return render_template('topOrgsPreset.html', orgNames = names, orgAdress = names_address, descriptions = descriptions, links = links)

if __name__ == "__main__":
    app.run(debug=True)