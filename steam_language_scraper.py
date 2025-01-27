# Author:   Alec Tutin
# Date:     2025-01-27

import csv, os
from argparse import ArgumentParser
from bs4 import BeautifulSoup
from pathlib import Path
from typing import List, Optional
from urllib import request

class SoftwareDetails:
    @property
    def software_name() -> str:
        return 'steam_language_scraper'
    
    @property
    def software_version() -> str:
        return 'v1.1'
    
    @property
    def software_tag() -> str:
        return f'{SoftwareDetails.software_name} {SoftwareDetails.software_version}'


class Options:
    def __init__(self) -> None:
        parser = ArgumentParser(SoftwareDetails.software_name, description='Scrape Steam game search results for language support.')
        parser.add_argument('-o', '--output-directory', help='File to write the .csv output(s) to.', required=True)
        parser.add_argument('-l', '--language', action='append', help='Name of a language to look for.', required=True)
        parser.add_argument('-c', '--max-games', type=int, help='Number of search game pages to check.', required=True)
        args = parser.parse_args()

        self.__output_directory: Path = Path(args.output_directory)
        self.__languages: List[str] = [language.lower() for language in args.language]
        self.__max_games_to_scan: int = args.max_games

    @property
    def output_directory(self) -> Optional[Path]:
        return self.__output_directory
    
    @property
    def languages(self) -> List[str]:
        return self.__languages
    
    @property
    def max_games_to_scan(self) -> int:
        return self.__max_games_to_scan


class LanguageResult:
    def __init__(self, interface: bool, audio: bool, subtitles: bool):
        self.interface: bool = interface
        self.audio: bool = audio
        self.subtitles: bool = subtitles


class ScrapeResult:
    def __init__(self, accessible: bool, name: str = ''):
        self.accessible: bool = accessible
        self.name: str = name
        self.results: dict[str, LanguageResult] = {}

    def add_language_result(self, language: str, result: LanguageResult) -> None:
        self.results[language] = result


def to_language_file(output_directory: Path, language: str) -> Path:
    return output_directory.joinpath(f'{language}.csv')

def to_search_url(languages: List[str], page_index: int) -> str:
    language_search_str: str = languages[0].lower()

    for i in range(1, len(languages)):
        language_search_str += f'%2C{languages[i].lower()}'

    return f'https://store.steampowered.com/search/?category1=998&supportedlang={language_search_str}&page={page_index}'

def scrape_game_page(uri: str, languages: List[str]) -> ScrapeResult:
    print(f'Checking {uri}...')

    with request.urlopen(uri) as response:
        game_page = BeautifulSoup(response.read(), 'html.parser')
        game_languages = game_page.find('table', class_='game_language_options')

        if game_languages is None: #TODO: We need to bypass the age check
            return ScrapeResult(False)
        
        name: str = game_page.find('div', id='appHubAppName').string

        page_result = ScrapeResult(True, name)

        table_rows = game_languages.find_all('tr')

        for row in table_rows:
            data = row.find_all('td')

            if len(data) == 0:
                continue

            language: str = data[0].string.strip().lower()

            if language not in languages:
                continue

            interface: bool = data[1].find('span') is not None
            audio: bool = data[2].find('span') is not None
            subtitles: bool = data[3].find('span') is not None

            page_result.add_language_result(language, LanguageResult(interface, audio, subtitles))

        return page_result

def append_result_to_file(language_file: Path, name: str, uri: str, language_result: LanguageResult) -> None:
    with open(language_file, 'a', encoding='utf8') as file:
        writer = csv.writer(file)
        writer.writerow([name, str(language_result.interface), str(language_result.audio), str(language_result.subtitles), uri])

def append_inaccessible_game(file: Path, uri: str) -> None:
    with open(file, 'a', encoding='utf8') as file:
        writer = csv.writer(file)
        writer.writerow([uri])

def main() -> None:
    options = Options()

    if len(options.languages) == 0:
        raise ValueError('No languages to search for!')
    
    if options.max_games_to_scan <= 0:
        raise ValueError('Must scan at least 1 game!')
    
    if not os.access(options.output_directory, os.W_OK):
        raise SystemError('Cannot write to directory: {options.output_directory}!')
    
    print(f'Scanning the first {options.max_games_to_scan} games for the languages: {options.languages}...')

    for language in options.languages:
        with open(to_language_file(options.output_directory, language), 'w') as file:
            writer = csv.writer(file)
            writer.writerow(['Game', 'Interface', 'Audio', 'Subtitles', 'URI'])

    inaccessible_page_file: Path = options.output_directory.joinpath('inaccessible.csv')

    with open(inaccessible_page_file, 'w') as file:
        writer = csv.writer(file)
        writer.writerow(['Link'])
    
    games_scanned: int = 0
    page_index: int = 0

    while games_scanned < options.max_games_to_scan:
        with request.urlopen(to_search_url(options.languages, page_index)) as response:
            search_page = BeautifulSoup(response.read(), 'html.parser')
            results_container = search_page.find(id='search_result_container')
            game_links = results_container.find_all('a', class_='search_result_row')

            if len(game_links) == 0:
                break
            
            for link_element in game_links:
                uri: str = link_element['href']

                if '/app/' not in uri:
                    continue

                scrape_result: ScrapeResult = scrape_game_page(uri, options.languages)
                
                if not scrape_result.accessible:
                    append_inaccessible_game(inaccessible_page_file, uri)
                else:
                    for language, result in scrape_result.results.items():
                        append_result_to_file(to_language_file(options.output_directory, language), scrape_result.name, uri, result)
                
                games_scanned += 1

                if games_scanned >= options.max_games_to_scan:
                    break
        
        page_index += 1

    print('Done!')

if __name__ == '__main__':
    main()
