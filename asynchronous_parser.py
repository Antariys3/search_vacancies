"""
Search for vacancies with the word Python in the city of Lviv
To change the city, change the name in "base_url"
"""

import concurrent.futures
import json

import requests
from bs4 import BeautifulSoup

base_url = "https://www.work.ua/jobs-lviv/?page="
headers = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

# search for professions by keywords
KEY_WORLD = ["Python", "python", "PYTHON"]
# It is recommended to go through no more than 200 pages at a time.
FROM_PAGE_SEARCH = 1
PAGES_TO_SEARCH = 200


def get_vacancies(url):
    teg_h = "h1"
    class_span = "strong-500"
    result = []
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, "html.parser")
    title = soup.find(name=teg_h, class_="cut-top cut-bottom")
    if not title:
        teg_h = "h2"
        class_span = "strong-600"
        title = soup.find(name=teg_h, class_="cut-top cut-bottom")

    title = title.text.strip()
    price = soup.find("span", class_=class_span).text
    if "грн" in price:
        price = price.replace("\u2009", "").replace("\u202f", "").replace("\xa0", "").strip()
        employer = soup.find_all("span", class_=class_span)[1].text
    else:
        employer = price
        price = None
    items = {"title": title, "price": price, "employer": employer}
    result.append(items)
    print(title, price, employer)
    return result


def write_to_json(data):
    try:
        with open("vacancies_python_asynch.json", "r", encoding="utf-8") as file:
            existing_data = json.load(file)
    except FileNotFoundError:
        existing_data = []

    existing_data.extend(data)

    with open("vacancies_python_asynch.json", "w", encoding="utf-8") as file:
        json.dump(existing_data, file, ensure_ascii=False, indent=4)


def make_request(url):
    # the function goes through all the headings from vacancies and searches for suitable professions using keywords
    response = requests.get(url, headers=headers)
    page = BeautifulSoup(response.text, "html.parser")
    title_cards = page.find_all("h2", class_="cut-top cut-bottom")
    if not title_cards:
        print("Блокировка от Work.ua")
    for title_card in title_cards:
        title = title_card.text.strip()
        if title:
            if any(python in title for python in KEY_WORLD):
                href = title_card.find("a").get("href")
                url = "https://www.work.ua" + href
                print(url)
                result = get_vacancies(url)
                write_to_json(result)


def process_pool_executor():
    with concurrent.futures.ProcessPoolExecutor(max_workers=50) as executor:
        future_to_url = {
            executor.submit(make_request, base_url + str(page) + "/"): page
            for page in range(FROM_PAGE_SEARCH, PAGES_TO_SEARCH + 1)
        }
        for future in concurrent.futures.as_completed(future_to_url):
            url = future_to_url[future]
            try:
                name = future.result()
            except Exception as e:
                print(f"{url} generated an expection {e}")


if __name__ == "__main__":
    process_pool_executor()
