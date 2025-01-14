#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
@author: Ethan Frier
Streetview Covid19 Visualizer
ATLS 1300-5650 Final Project
December 2020

This script downloads streetview images from google maps static street view
API based on location data from the New York Times Covid19 github repo.

Humans respond more effectively to emotion as compared to information. In fact
too much information, regardless of quality or source, can sometimes have an
adverse effect. The goal of this project is to put these data into context.
By displaying a limited amount of high quality current data in a more human 
context, the hope is that this piece will make these data more digestible.

The most recent US covid data by county is retrieved from the New York Times
repo - https://github.com/nytimes/covid-19-data The data is then sorted by
the total number of cases by county and outputs today's top counties to a list.
Each list index contains a text string of 'County,State'. In order to best
communicate with the streetview api this data is converted to latitude and 
longitude  using the geopy library. Using these coordinates the StreetView 
class generates an API request and downloads images from those top counties.

The streetview images are downlaoded to a new directory for each day, created 
by the DailyDataManager class. This class also creates a csv file of relevant 
metadata for all images and saves it to the new directory as well. 

Attribution: 

The NYTCovidData class was modified from TowardsDataScience.com
https://towardsdatascience.com/analyze-ny-times-covid-19-dataset-86c802164210
I copied and modified 34 lines from: _init_(), today(), updateCounty(), 
dateUpdate(), process(). The total length without docstrings is 220 lines.

Future Improvements:

The top counties by raw case numbers are invariably almost all large cities.
I would like to modify this script further to sort by the highest number of
cases per capita. This will return the case rate, not the total number of cases.
The rate is a more effective way of looking at the velocity and impact of the
virus, and more accurately highlights the effect on less populous areas, which
are currently the hardest hit. This requires a dataset with each county's
population to compare total cases against. I'm not sure where to find best
or cleanest data for 1,929 counties, or if I should use the FIPS system?

Eventually, I would like to make this into a live viewer of the images which
will display on screen a tiled montage of the images from the top counties by
case rate, with the address text and current covid data overlaid. The speed at
which the images update will be relative to the current national caseload.

"""

import requests 
import pandas
import io
from datetime import date
import time
import urllib
from geopy.geocoders import Nominatim
import os
import csv


class NYTCovidData:
    """
    Manages data from New York Times Covid19 repository.

    Attributes
    ----------
    NYTcountiesData : str
        URL points to raw NYT counties CSV file
    _today : str
        current date from datetime library  
    numCounties : int
        number of counties to get images for
    topCounties : list
        stores text strings of 'County,State' limited to numCounties
    topCases : list 
        stores top case numbers in list
    countydf : DataFrame
        pandas DataFrame to store data from NYT CSV file
    _countyupdated : bool
        checks updateCounty()
    _processed : bool
        checks process()
    _sorted : bool
        checks sortByCases()
    countydict : dictionary
        stores data from countydf[DataFrame]
    countylist : list 
        list of every unique county in NYT CSV file

    Methods
    -------
    today():
        Prints today's date.
    updateCounty():
        Retrieves CSV data from NYT repo and stores it in countydf[DataFrame].
    dateUpdate():
        Checks that updateCounty() has been run and prints date of newest data.
    process():
        Processes countydf[DataFrame] using countydict{} and countylist[].
    sortByCases():
        Sorts countydf[DataFrame] by date then cases.    
    getTopCounties():
        Stores top counties in topCounties[].  
        
    """
    
    def __init__(self):
        """Initialize NYTCovidData class attributes. """
        self.NYTcountiesData = "https://raw.githubusercontent.com/nytimes/covid-19-data/master/us-counties.csv"
        self._today = date.today()
        self.numCounties = 20
        self.topCounties = []
        self.topCases = []
        self.countydf = None
        self._countyupdated = False
        self._processed = False
        self._sorted = False
    
    def today(self):
        """Prints today's date from datetime library."""
        print("Today's date is: ",self._today)
              
    def updateCounty(self):
        """ Retrieves most recent data from New York Times Covid19 repository.
        
        Uses requests library to get the CSV file at URL NYTcountiesData. 
        Uses pandas library to read the CSV and save in countydf[DataFrame].
        Formats the date axis of countydf. Sets _countyupdated = True. 
       
        Uses:
            countydf : DataFrame
                contains the data from NYT counties CSV file
            _countyupdated : bool
            
        """
        url = self.NYTcountiesData
        s = requests.get(url).content
        self.countydf = pandas.read_csv(io.StringIO(s.decode('utf-8')))
        self.countydf['date'] =  pandas.to_datetime(self.countydf['date'], format='%Y-%m-%d')
        self._countyupdated = True
    
    def dateUpdate(self):
        """ Checks for most recent data.
        
        If updateCounty() has been run, it checks for the most recent date
        of data in the newly created countydf[DataFrame]. Prints date. 
            
        """
        if self._countyupdated:
            print("Most recent data:",self.countydf.iloc[-1]['date'].date())
        else:
            print("Data has not been updated!")
               
    def process(self):
        """Processes NYT data.
        
        Usually takes 60-120 seconds to run. 

        Creates a dictionary to store data from countydf[DataFrame]. Creates a
        list of all counties, and uses it to traverse countydf[DataFrame]. 
        Calculates new cases and new deaths in each county and stores in 
        countydict{}. Prints time it took to process once complete. 
        
        Uses:
            countydict : dictionary
                contains data from countydf[DataFrame]
            countylist : list 
                all unique counties 
            _processed : bool
            
        """
        pandas.set_option('mode.chained_assignment', None)
        self.countydict= {}
        t1 = time.time()
        
        if self._countyupdated:
            self.countylist = list(self.countydf['county'].unique())
            print('')
            print(f'Processing {str(len(self.countylist))} counties...')
            
            for c in self.countylist:
                county_df=self.countydf[self.countydf['county']==c]
                county_df['newcases'] = county_df['cases'].diff()
                county_df['newdeaths'] = county_df['deaths'].diff()
                self.countydict[c]=county_df       
        
        self._processed = True
        t2 = time.time()
        delt = round(t2-t1,3)
        print("Finished. Took {} seconds".format(delt))
                    
    def sortByCases(self):
        """ Sorts counties by date and total cases
        
        Checks that process() has been run. Sorts countydf[DataFrame] by most 
        recent, then total cases in descending order. Prints to terminal.
        
        Returns:
            countydf : DataFrame
            _sorted : bool
        
        """
        if self._processed:
            self.countydf = self.countydf.sort_values(by=['date','cases'], ascending=False)
            self._sorted = True
            print('Sorted by recent number of cases per county.')
            print('')
        else:
            print('Not processed yet!')
                            
    def getTopCounties(self):
        """ Creates list of counties with most cases today.

        Checks that countydf[DataFrame] has been sorted. Extracts the county 
        and state from the DataFrame and formats each into a single string 
        as 'county,state'. Saves each location string to topCounties[].
        Prints the number of counties, sorting method, and each county name.

        Uses:
            topCounties : list 
            
        """
        if self._sorted:       
            for c in range(self.numCounties):
                county_ = self.countydf.iloc[c]['county']
                state_ = self.countydf.iloc[c]['state']
                location_ = str(f'{county_},{state_}')
                self.topCounties.append(location_)
            
            print(f'Top {covid.numCounties} counties by total cases:')
            for location in covid.topCounties:
                print(f'   {location}')
                
    def getTopCases(self):
        """ Creates list of only the case numbers per county.
        
        Uses:
            topCases : list 
            
        """
        if self._sorted:       
            for c in range(self.numCounties):
                cases_ = self.countydf.iloc[c]['cases']
                self.topCases.append(cases_)


class StreetView:
    """ Uses NYT covid data to request images from google streetview API.

    Attributes
    ----------
    apiKey : str
        unique and private key used to verify API requests 
    locations : list
        top locations formated as 'latitude,longitude'
    headings : list
        direction (0-360) of camera at each location
    fov : int
        field of view (0-120) of camera for all images
    radius : int
        distance in meters from location API will look for an image (best when > 100000)
    size : str
        size of image - max free size is 640x640 
    filename : str
        name of each file downloaded 
    numImages : int
        number of images processed 
    numLocations : int
        number of locations processed 

    Methods
    -------
    getKey():
        Pulls API key from keys.txt.
    getStreetView(lat_, lon_, heading_, fileName_, saveFolder_):
        Compiles URL and downloads image from streetview API.
    makeLatLon():
        Generates locations['float(lat),float(lon)'] from topCounties['County,State'].
    execute():
        Generates filename and calls getStreetView(parameters).
    """    
    
    def __init__(self):
        """ Initialize StreetView class attributes. """
        self.apiKey = ''
        self.locations = []
        self.headings = [0, 120, 240]    
        self.fov = 90               
        self.radius = 100000        
        self.size = '640x500'   
        self.filename = ''
        self.numImages = 0
        self.numLocations = 1
        # self.localFolder = '/Users/ethanfrier/Desktop/covid19_streetview/downloadImages/'

    def getKey(self):
        """ Pulls API key from keys.txt.

        API keys should be kept secret. This method gets a key string from 
        keys.txt file which only contains the API key string. This text 
        file is included in the gitignore file so it stays private. Prints
        obfuscated API key to terminal.

        Uses:
            apiKey : str 
            
        """
        keyDoc = open('keys.txt', 'r')
        self.apiKey = keyDoc.read()
        printKeyA, printKeyB = self.apiKey[0:5],self.apiKey[-6:-1]
        print(f'Recieved API key: {printKeyA}xxxxxxxxxxxxxxxxxx{printKeyB}')
        print('')

    def getStreetView(self, lat_, lon_, heading_, fileName_, saveFolder_):
        """ Compiles unique URL and downloads images from streetview API.
        
        Generates unique URL using: size, lat_, lon_, fov, heading_, radius, apiKey.
        Uses urllib library to send request to API. Downloads images to 
        designated folder and saves as .jpg using filename_ 

        Parameters:
            lat_ : float
            lon_ : float
            heading_ : int
            fileName_ : str
            saveFolder : str
            
        Uses:
            urllib request
                urllib.request.urlretrieve()
            streetview image download to localFolder
                
        """
        base = r'https://maps.googleapis.com/maps/api/streetview?'
        imageSize = r'&size={}'.format(self.size) 
        imageLocation = r'&location={0},{1}'.format(lat_, lon_)
        imageHeading = r'&fov={0}&heading={1}'.format(self.fov, heading_)
        searchRadius = r'&radius={}'.format(self.radius)
        useKey = r'&key={}'.format(self.apiKey)
       
        myUrl = base + imageSize + imageLocation + imageHeading + searchRadius + useKey 
        urllib.request.urlretrieve(myUrl, os.path.join(saveFolder_,fileName_))
   
    def makeLatLon(self):
        """ Generates list of locations as latitude and longitude.

        This method uses the geopy library to convert a text string location 
        into a latitude and longitude. It uses topCounties[] as an input. It
        also generates an address for each location which is stored in 
        locationText (unused).

        Uses:
            locations[] : list 
                formated as ['float(latitude),float(longitude)']
            locationText : str
            
        """
        geolocator = Nominatim(user_agent="covid_streetview")
        print('')
        print(f'Using geopy, converting {len(covid.topCounties)} locations:')
        
        for L in covid.topCounties:
            convertLocation = geolocator.geocode(L) 
            # locationText = convertLocation.address 
            latLon = (convertLocation.latitude,convertLocation.longitude)
            
            self.locations.append(latLon)
            print(f'   {latLon}')

    def execute(self):
        """ Formats filename and parameters for streetview API request

        Loops through each location in locations[] and generates a unique 
        filename and parameters for getStreetView(). It then calls 
        getStreetView() and prints each time an image has been downloaded. 
        
        The variables and structurs for generating each image: 
            location[i] (i = 'float(lat),float(lon)')
                heading[i] (direction camera is pointing)
                    lat (extracted from locations[i])
                    lon (extracted from locations[i])
                    numLocations (ranking of county and order it is processed)
        
        Calls Method:
            getStreetView(float(lat), float(lon), int(headings[i]), str(filename), str(self.localFolder).    
            
        Uses:
            lat : float 
                extracted from locations[i]
            lon : float 
                extracted from locations[i]
            filename : str 
                ending in .jpg using: numLocations, headings[i], lat, lon
            numImages : int
                number of images processed
            numLocations : int 
                number of locations processed
                
        """  
        print('')
        print('Downloading from Streetview static API:')
        
        for location in self.locations:
            for heading in self.headings:
                
                lat, lon = location    
                NYTlocation =  covid.topCounties[((self.numLocations)-1)].replace(" ","")
                
                self.filename = "{0}_{1}_{2}_({3},{4},h{5}).jpg".format(str(self.numLocations).zfill(3), covid._today, NYTlocation, lat, lon, heading)        
                self.getStreetView(lat, lon, heading, self.filename, go.todayPath)  
                
                print(f'   Got {self.filename}')      
                self.numImages += 1      
            
            self.numLocations += 1
               

class DailyDataManager:
    """ Manages the processed data and saves to a new local directory.

    This class creates a local directory for each day, which is used to save 
    all street view images and relevant metadata.

    Attributes
    ----------
    todayPath : str
        path to the newly created directory
    nameCSV : str
        name for csv file created by createCSV()
    nameFolder : str
        name of new folder formatted as '2020-12-31'
    rootFolder : str
        uses os library to get the current working directory
    saveFolder : str
        path used for todayPath
        
    Methods
    -------
    createFolder():
        makes new directoy using todayPath
    createCSV:
        makes csv file of relevant meta data for images
    
    """

    def __init__(self):
        """Initialize DailyDataManager class attributes. """
        self.todayPath = ''
        self.nameCSV = '_' + str(covid._today) + '_byTopCases.csv'
        self.nameFolder = str(covid._today)
        self.rootFolder =  os.getcwd()
        self.saveFolder = '/Users/ethanfrier/Desktop/covid19_streetview/dailyData/'

    def createFolder(self):
        """ Creates a new directoy using todayPath in the root directory.

        Checks to see if the directoy to be created already exists. If it does 
        not then it creates it, if it does it passes. If it passes, the script 
        will still re-save any new data to existing directory.

        Uses:
            todayPath : str 
            saveFolder : str
            nameFolder : str
            
        """
        # this should refrence rootFolder instead of saveFolder (I could not 
        # figure out how to do it right and am scared of messing with directories)
        self.todayPath = os.path.join(self.saveFolder, self.nameFolder)
        try:
            os.mkdir(self.todayPath)
            print('')
            print(f'New folder /dailyData/{self.nameFolder} created')
        except Exception:
            pass
            print('')
            print(f'Folder /dailyData/{self.nameFolder} already exists!')

    def createCSV(self):
        """ Creates a CSV file of data used to get streetview images.

        rank = ranking of counties tracked by NYT (1,930 as of 2020-12-15)
        cases = total number of cases in that county 
        county = name and state of county 
        latLon = latitude and longitude coordinates of today's photo

        Uses:
            todayPath : str 
                path to the newly created directory
            nameCSV : str
                name for csv file set by _init_
            NYTCovidData.topCounties : list 
                list of strings of 'County,State'
            NYTCovidData.topCases : list
                list of ints of the number of cases in each county
            StreetView.locations
                list of strings of top counties formated as 'latitude,longitude'
            
        """
        os.chdir(self.todayPath)
        with open(self.nameCSV,'w', newline='') as newCSV:
            CSVwriter = csv.writer(newCSV)  
            CSVwriter.writerow(['rank', 'cases', 'county', 'latLon'])
            for idx, data in enumerate(covid.topCounties):
                CSVwriter.writerow( [idx+1, covid.topCases[idx], data, geo.locations[idx]])
            print(f'Saved {self.nameCSV} to /{self.nameFolder}')
        os.chdir(self.rootFolder)
            
            
if __name__ == "__main__":
    covid = NYTCovidData()
    geo = StreetView()
    go = DailyDataManager()

    geo.getKey()
    covid.today()
    covid.updateCounty()
    covid.dateUpdate()

    covid.process()
    covid.sortByCases()
    covid.getTopCounties()
    covid.getTopCases()
    geo.makeLatLon()      
    
    go.createFolder()
    go.createCSV()
    
    geo.execute()
    
    print('')
    print(f'Processed {str(geo.numImages)} images.')
    print('Done.')




