import urllib.request
from bs4 import BeautifulSoup

lastPage = 60
language = 'swedish'
searchUrl = 'https://store.steampowered.com/search/?supportedlang=' + language.lower() + '&page='

languageSupported = []
unableToCheck = []

for currentPage in range(1, lastPage):
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
                if gameLanguages is None: #We need to bypass the age check
                    unableToCheck.append(link)
                    print('This game requires an age-gate bypass.')
                else:
                    tableRows = gameLanguages.find_all('tr')
                    for row in tableRows:
                        data = row.find_all('td')
                        if len(data) > 0:
                            if data[0].string.strip().lower() == language:
                                if data[2].find('img') is not None:
                                    gameName = gamePage.find('div', class_='apphub_AppName').string.strip()
                                    languageSupported.append(gameName)
                                    print(gameName + ' supports the audio in the language ' + language)
                                    break

print('Language support was found in the following games:')
print(lanuageSupported)

print('Unable to check the following links due to content age-gating.')
print(unableToCheck)
