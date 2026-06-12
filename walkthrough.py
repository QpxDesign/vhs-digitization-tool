import requests
import bs4
from termcolor import colored
import json
import re

basics_dataset = "data/title.basics.tsv"
principals_dataset = "data/title.principals.tsv"
names_dataset = "data/name.basics.tsv"
cinefile_dataset = open("data/cinefile.csv", "r").read()


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

def print_boolean(value: bool):
    if value:
        print(colored('✓', "green"))
    else:
        print(colored('x', "red"))

def resolve_name_id(name_id: str) -> str:
    with open(names_dataset) as file:
        for line in file:
            if line.split("\t")[0] == name_id:
                return line.split("\t")[1]
    assert("UNABLE TO RESOLVE NAME ID - " + name_id)


def find_director(imdb_id: str) -> str:
    director = ""
    with open(principals_dataset) as file:
        for line in file:
            if len(line.split("\t")) < 4:
                continue
            if line.split("\t")[0] == imdb_id and line.split("\t")[3] == "director":
                director = resolve_name_id(line.split("\t")[2])
                return director
    return "No Director Found"


def find_metadata(imdb_id: str) -> [str, str, str]:
    # year, primary_title, original_title
    with open(basics_dataset) as file:
        for line in file:
            if line.split("\t")[0] == imdb_id:
                return (line.split("\t")[5], line.split("\t")[2], line.split("\t")[3])
    assert "UNABLE TO FIND METADATA - " + imdb_id


def check_cinefile(metadata: [str, str, str]) -> bool:
    for line in cinefile_dataset.split("\n"):
        if metadata[1].lower() in line.lower() or metadata[2].lower() in line.lower():
            return True
        if metadata[1].lower().replace("the", "").strip() in line.lower():
            return True
    return False


def check_whammy(metadata: [str, str, str]) -> bool:
    primary_query = metadata[1].replace(" ", "+")
    original_query = metadata[2].replace(" ", "+")
    queries = [primary_query, original_query]

    for query in queries:
        r = requests.get(f"https://shop.whammyanalog.com/search?q={query}")
        if "No results found" in r.text:
            continue
        soup = bs4.BeautifulSoup(r.text, features="lxml")
        elements = soup.select(".card__content h3 a")
        items = []
        for element in elements:
            items.append(element.encode_contents().decode("utf-8").strip().lower())
        for item in items:
            if metadata[1].lower() in item or metadata[2].lower() in item:
                return True
            if metadata[1].lower().replace("the", "") in item:
                return True
        return False


def check_vidtheque(metadata: [str, str, str]) -> bool:
    primary_query = metadata[1].replace(" ", "+")
    original_query = metadata[2].replace(" ", "+")
    queries = [primary_query, original_query]

    for query in queries:
        r = requests.get(f"https://www.vidtheque.com/Search.aspx?tt={query}")
        if "There were no titles found containing" in r.text:
            continue
        soup_1 = bs4.BeautifulSoup(r.text, features="lxml")
        elements = soup_1.select(".resultodd")
        items = []
        for element in elements:
            items.append(element.select_one(".resultitem a span").encode_contents().decode("utf-8").strip().lower())
        for item in items:
            if metadata[1].lower() in item or metadata[2].lower() in item:
                return True
            if metadata[1].lower().replace("the", "") in item:
                return True
        return False


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
    queries = [primary_query]

    streams = False
    rents = False

    for query in queries:
        url = f"https://www.justwatch.com/us/search?q={query}"
        r = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'})
        soup_1 = bs4.BeautifulSoup(r.text, features="lxml")
        containers = soup_1.select(".title-list-row__row__search")
        for container in containers:
            title = container.select_one(".title-list-row__column-header").encode_contents().decode("utf-8").strip().lower()
            if metadata[1].lower() in title and metadata[0] in title:
                if "is not available" in container.encode_contents().decode("utf-8").lower():
                    return "Not Available"
                if "stream" in container.encode_contents().decode("utf-8").lower():
                    streams = True
                if "rent" in container.encode_contents().decode("utf-8").lower():
                    rents = True
                if streams and rents:
                    return "Both"
                if streams:
                    return "Streams"
                if "dvd" in container.encode_contents().decode("utf-8").lower():
                    print(colored("⚠ DVDs Included in JustWatch Listing", "yellow"))
                return "Rents"
    return "Not Available (not found)"


def tests():
    a =  check_justwatch(('1955', 'I Died a Thousand Times', 'I Died a Thousand Times')) # "Both"
    b = check_justwatch(("1956", "The Steel Jungle", "The Steel Jungle")) # "Not Available"
    c = check_justwatch(("2025", "A Thousand Blows", "A Thousand Blows")) # "Streams"
    d = check_justwatch(("1978", "Battlestar Galactica", "Battlestar Galactica")) # "Rents"
    print(a)
    print(b)
    print(c)
    print(d)

while True:
    imdb_link = input('IMDB Link: ')
    # imdb_link = "https://www.imdb.com/title/tt0048190/?ref_=fn_all_ttl_1"
    imdb_id = imdb_link.split("/")[4]
    director = find_director(imdb_id)
    if director is not None:
        print("Director: " + director)
    else:
        director = ""

    metadata = find_metadata(imdb_id)
    print(metadata)

    print("Cinefile: ", end="")
    print_boolean(check_cinefile(metadata))
    print("Whammy: ", end="")
    print_boolean(check_whammy(metadata))
    print("Vidtheque: ", end="")
    print_boolean(check_vidtheque(metadata))
    print("UCLA: ", end="")
    print_boolean(check_ucla(metadata, director))
    print("JustWatch: " + check_justwatch(metadata))
    print("")

# amazon
# webbrowser.open(f"https://www.amazon.com/s?k={long_query_1}&i=movies-tv")

# ebay
# webbrowser.open(f"https://www.ebay.com/sch/i.html?_nkw={long_query_1}")
