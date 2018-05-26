#Last Updated - 2018/05/26

import os
import urllib.request
from bs4 import BeautifulSoup

def ScrapeSearch():
    for currentPage in range(1, lastPage + 1):
        print('Scanning page: ' + str(currentPage))
        with urllib.request.urlopen(searchUrl + str(currentPage)) as searchResponse:
            searchPage = BeautifulSoup(searchResponse.read(), 'html.parser')
            searchContainer = searchPage.find(id='search_result_container')
            gameLinks = searchContainer.find_all('a', class_='search_result_row')
            if len(gameLinks) == 0:
                break
            for linkElement in gameLinks:
                link = linkElement['href']
                print('Checking ' + link)
                with urllib.request.urlopen(link) as gameResponse:
                    gamePage = BeautifulSoup(gameResponse.read(), 'html.parser')
                    gameLanguages = gamePage.find('table', class_='game_language_options')
                    if gameLanguages is None: #TODO: We need to bypass the age check
                        gameName = linkElement.find('span').string.strip()
                        unableToCheck.append(gameName)
                        print(gameName + ' requires an age-gate bypass. :(')
                    else:
                        tableRows = gameLanguages.find_all('tr')
                        for row in tableRows:
                            data = row.find_all('td')
                            if len(data) > 0:
                                if data[0].string.strip().lower() == language:
                                    if data[2].find('img') is not None:
                                        gameName = gamePage.find('div', class_='apphub_AppName').string.strip()
                                        languageSupported.append(gameName)
                                        print(gameName + ' supports audio in the language ' + language + '!')
                                        break
        WriteResultsToFile()

def WriteResultsToFile():
    with open(pathToFile + '/' + outputFileName, 'w') as outputFile:
        outputFile.write('The language ' + language + ' was supported in the following games:\r\n')
        supportedGameString = '';
        for game in languageSupported:
            supportedGameString += game + '\r\n'
        outputFile.write(supportedGameString)
        outputFile.write('\nUnable to check the following games due to age-gating:\r\n')
        uncheckedGameString = '';
        for game in unableToCheck:
            uncheckedGameString += game + '\r\n'
        outputFile.write(uncheckedGameString)



pathToFile = input('Enter a directory to output the results to: ')
if not os.access(pathToFile, os.W_OK):
    print('Cannot write to the path at: ' + pathToFile);
    exit()

outputFileName = input('Enter the name of the output file (existing contents will be overwritten): ')
language = input('Enter the name of a Steam supported language: ').strip().lower();
lastPage = int(input('Enter the number of search pages to scan: '))
searchUrl = 'https://store.steampowered.com/search/?category1=998&supportedlang=' + language.lower() + '&page='

languageSupported = []
unableToCheck = []

ScrapeSearch();

print('Operation completed! Check for output in ' + pathToFile + '/' + outputFileName)
