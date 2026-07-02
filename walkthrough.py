import requests
import bs4
from termcolor import colored
import json
import re
import csv
from unidecode import unidecode
import subprocess
import webbrowser
import urllib.parse

# selenium shit
# options = webdriver.ChromeOptions()
# options.add_argument('--headless')
# driver = webdriver.Chrome(options=options)

print("""
                  ███
                 ███████  █████
                  █████  ███████
 █               █████    █████        ██
  ███          ██████    ███         ████
   ██████    ████████    ████      ██████████
    ████████████████    █████  ███ ███████████
     ███████████████   █████████████████████
      ██████████████████████████████████████
       ████████████████████████████████  █████
        ████████ ██████████████████ ███ █████
         ██████ ██████         ███  ███ ███
           ███  ██              ██  ██ ██
            █                        █
 """)

print("         Vidiots VHS Digitization Tool")
print("           By Quinn Patwardhan - v0.1")
print("")

print("Loading Files...")

basics_dataset = open("data/title.basics-sorted.tsv").readlines()

principals_dataset = open("data/title.principals-sorted-directors.tsv").readlines()

names_dataset = open("data/name.basics-sorted.tsv").readlines()

cinefile_dataset = "data/cinefile.csv"

print("Files Loaded!")
print("")


# https://tamarisk.it/manipulating-the-clipboard-using-python3
def set_clipboard_data(data):
    p = subprocess.Popen(['pbcopy'], stdin=subprocess.PIPE)
    p.stdin.write(data.encode('utf-8'))
    p.stdin.close()
    retcode = p.wait()


def binary_search_file(file: list[str], target: int) -> str:
    left = 0
    right = len(file) - 1

    while left <= right:
        mid = (left + right) // 2
        arr_mid = imdb_to_int(file[mid].split("\t")[0])
        if arr_mid == target:
            return file[mid]
        if arr_mid < target:
            left = mid + 1
        else:
            right = mid - 1

    return "Not Found"


def process_title(title: str) -> str:
    out = unidecode(title.strip().lower())
    return out


def imdb_to_int(imdb_id: str) -> int:
    if "nm" in imdb_id:
        out = imdb_id.replace('nm', '')
        return int(out)
    out = imdb_id.replace('tt', '')
    return int(out)


def print_array(array: list):
    for line in array:
        print(line)
    if len(array) != 0:
        print("")


def print_boolean(value: bool):
    if value:
        print(colored('✓', "green"))
    else:
        print(colored('x', "red"))


def resolve_name_id(name_id: str) -> str:
    line = binary_search_file(names_dataset, imdb_to_int(name_id))
    return line.split("\t")[1]


def find_director(imdb_id: str) -> str:
    line = binary_search_file(principals_dataset, imdb_to_int(imdb_id))
    if len(line.split("\t")) < 4:
        return "Not Found"
    director = resolve_name_id(line.split("\t")[2])
    return director


def find_metadata(imdb_id: str) -> [str, str, str]:
    # year, primary_title, original_title
    line = binary_search_file(basics_dataset, imdb_to_int(imdb_id))
    year = process_title(line.split("\t")[5])
    primary_title = process_title(line.split("\t")[2])
    original_title = process_title(line.split("\t")[3])
    return (year, primary_title, original_title)


def check_cinefile(metadata: [str, str, str]) -> [bool, list]:
    results = []
    with open(cinefile_dataset, newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            title = process_title(row["Title"])
            if len(row["Year"]) == 4 and row["Year"] != metadata[0]:
                continue
            if process_title(metadata[1]) == title:
                results.append(title)
                return (True, results)
            if process_title(metadata[2]) == title:
                results.append(title)
                return (True, results)
            if metadata[1][0:4] == "the ":
                formatted_title = metadata[1].replace("the ", "").strip() + ", the"
                if formatted_title == title:
                    results.append(title)
                    return (True, results)
            if process_title(metadata[1]) in title or process_title(metadata[2]) in title:
                results.append(row["Title"])
    return (False, results)


def check_whammy(metadata: [str, str, str]) -> [bool, list]:
    primary_query = metadata[1].replace(" ", "+")
    original_query = metadata[2].replace(" ", "+")
    queries = [primary_query, original_query]
    results = []

    for query in queries:
        r = requests.get(f"https://shop.whammyanalog.com/search?q={query}")
        if "No results found" in r.text:
            continue
        soup = bs4.BeautifulSoup(r.text, features="lxml")
        elements = soup.select(".card__content h3 a")
        items = []
        for element in elements:
            items.append(process_title(element.encode_contents().decode("utf-8")))
        for item in items:
            results.append(item)
            if metadata[1].lower() == item or metadata[2].lower() == item:
                return (True, results)
    return (False, results)


def check_vidtheque(metadata: [str, str, str]) -> [bool, list]:
    primary_query = metadata[1].replace(" ", "+")
    original_query = metadata[2].replace(" ", "+")
    queries = [primary_query, original_query]
    results = []

    for query in queries:
        r = requests.get(f"https://www.vidtheque.com/Search.aspx?tt={query}")
        if "There were no titles found containing" in r.text:
            continue
        soup_1 = bs4.BeautifulSoup(r.text, features="lxml")
        elements = soup_1.select(".resultodd, .resulteven")
        items = []
        for element in elements:
            items.append(process_title(element.select_one(".resultitem a span").encode_contents().decode("utf-8")))
        for item in items:
            results.append(item)
            if metadata[1].lower() == item or metadata[2].lower() == item:
                return (True, results)
    return (False, results)


def check_ucla(metadata: [str, str, str], director) -> bool:
    primary_query = metadata[1].replace(" ", "+")
    original_query = metadata[2].replace(" ", "+")
    queries = [primary_query, original_query]

    for query in queries:
        url = f"https://search.library.ucla.edu/primaws/rest/pub/pnxs?acTriggered=false&blendFacetsSeparately=false&citationTrailFilterByAvailability=true&disableCache=false&getMore=0&inst=01UCS_LAL&isCDSearch=false&lang=en&limit=10&mode=advanced&newspapersActive=false&newspapersSearch=false&offset=0&otbRanking=false&pcAvailability=true&q=any,contains,{query},AND;any,contains,{metadata[0]},AND&qExclude=&qInclude=&rapido=false&refEntryActive=false&rtaLinks=true&scope=FTVA&searchInFulltextUserSelection=true&skipDelivery=Y&sort=rank&tab=FTVA_slot&vid=01UCS_LAL:UCLA"
        r = requests.get(url)
        text = json.dumps(r.json())
        strings = re.findall(r"\"title\"([^\]]*);", text)
        for string in strings:
            if metadata[1].lower() not in string.lower() and metadata[2].lower() not in string.lower():
                continue
            if len(director.split(" ")) < 2:
                return True
            if director.split(" ")[0].lower() not in string.lower() and director.split(" ")[1].lower() not in string.lower():
                return False
            return True
    return False


def check_justwatch(metadata) -> str:
    primary_query = metadata[1].replace(" ", "%20")
    original_query = metadata[2].replace(" ", "%20")
    queries = [primary_query, original_query]

    streams = False
    rents = False

    for query in queries:
        url = f"https://www.justwatch.com/us/search?q={query}"
        r = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'})
        soup_1 = bs4.BeautifulSoup(r.text, features="lxml")
        containers = soup_1.select(".title-list-row__row__search")
        for container in containers:
            title = process_title(container.select_one(".title-list-row__column-header").encode_contents().decode("utf-8"))

            if metadata[1].lower() in title:
                int_year = int(metadata[0])
                txt = process_title(container.encode_contents().decode("utf-8"))
                soup_2 = bs4.BeautifulSoup(container.encode_contents().decode("utf-8"), features="lxml")
                labels = soup_2.select(".offer__label")

                #print(txt)
                if str(int_year-1) not in title and str(int_year+1) not in title and metadata[0] not in title:
                    continue
                if "is not available" in txt:
                    return "Not Available"
                if "stream" in txt:
                    streams = True
                if "rent" in txt:
                    rents = True
                if streams and rents:
                    return "Both"
                if streams:
                    return "Streams"
                only_dvd = True
                for label in labels:
                    formatted_label = process_title(label.encode_contents().decode("utf-8"))
                    if "dvd" not in label and "blu-ray" not in label:
                        only_dvd = False
                        break
                if only_dvd:
                    return "Not Available"
                return "Rents"
    query = urllib.parse.quote_plus(metadata[1])
    webbrowser.open(f"https://www.justwatch.com/us/search?q={query}")
    return "Not Available (not found)"


while True:
    imdb_link = input('IMDB Link: ')
    # imdb_link = "https://www.imdb.com/title/tt0048190/?ref_=fn_all_ttl_1"
    imdb_id = imdb_link.split("/")[4]
    director = find_director(imdb_id)
    print("\nDirector: " + director)
    if director == "Not Found":
        director = ""
    set_clipboard_data(director)

    metadata = find_metadata(imdb_id)
    print(metadata)

    print("Cinefile: ", end="")
    cinefile = check_cinefile(metadata)
    print_boolean(cinefile[0])
    print_array(cinefile[1][0:5])

    print("Whammy: ", end="")
    whammy = check_whammy(metadata)
    print_boolean(whammy[0])
    print_array(whammy[1][0:5])

    print("Vidtheque: ", end="")
    vidtheque = check_vidtheque(metadata)
    print_boolean(vidtheque[0])
    print_array(vidtheque[1][0:5])

    print("UCLA: ", end="")
    print_boolean(check_ucla(metadata, director))
    print("JustWatch: " + check_justwatch(metadata))
    print("")

    query = urllib.parse.quote_plus(metadata[1])
    webbrowser.open(f"https://www.ebay.com/sch/i.html?_nkw={query}&_sacat=11232")
    webbrowser.open(f"https://www.amazon.com/s?k={query}&i=movies-tv")

    print("==============================\n")
