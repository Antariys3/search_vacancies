"""
Search for vacancies with the word Python in the city of Lviv
To change the city, change the name in "base_url"
To change the number of parsing pages, change the variable "number_of_pages_to_search"
"""

import concurrent.futures
import json

import requests
from bs4 import BeautifulSoup

base_url = "https://www.work.ua/jobs-lviv/"
headers = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}
vacancies_list = []
# search for professions by keywords
KEY_WORLD = ["Python", "python", "PYTHON"]
number_of_pages_to_search = 5


def next_page(url):
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, "html.parser")
    next_page = soup.find("li", class_="no-style add-left-default")
    if next_page is not None:
        href = next_page.a["href"]
        return "https://www.work.ua" + href
    return next_page


def search_for_vacancies(url) -> list:
    response = requests.get(url, headers=headers)
    page = BeautifulSoup(response.text, "html.parser")
    vacancy_cards = page.find_all("div",
                                  class_="card card-hover card-search card-visited wordwrap job-link js-hot-block")
    if not vacancy_cards:
        vacancy_cards = page.find_all("h2", class_="cut-top cut-bottom")
        # print("vacancy_cards: ", len(vacancy_cards))
    url_cards = []
    for job in vacancy_cards:
        href = job.find("a").get("href")
        url_cards.append("https://www.work.ua" + href)
    return url_cards


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
    if any(python in title for python in KEY_WORLD):
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


def process_pool_executor(url_cards: list):
    with concurrent.futures.ProcessPoolExecutor(max_workers=15) as executor:
        future_to_url = {executor.submit(get_vacancies, url): url for url in url_cards}
        result_list = []
        for future in concurrent.futures.as_completed(future_to_url):
            url = future_to_url[future]
            try:
                result = future.result()
                if result:
                    result_list.extend(result)
            except Exception as e:
                print(f"{url} generated an expection {e}")
        return result_list


def write_to_json(data):
    try:
        with open("vacancies_python.json", "r", encoding="utf-8") as file:
            existing_data = json.load(file)
    except FileNotFoundError:
        existing_data = []

    existing_data.extend(data)

    with open("vacancies_python.json", "w", encoding="utf-8") as file:
        json.dump(existing_data, file, ensure_ascii=False, indent=4)


if __name__ == "__main__":

    pages = 1
    vacancies = 0

    while base_url and number_of_pages_to_search >= 0:
        card_urls = search_for_vacancies(base_url)
        vacancies_list = process_pool_executor(card_urls)
        write_to_json(vacancies_list)
        base_url = next_page(base_url)
        number_of_pages_to_search -= 1

        # statistics
        print("pages", pages)
        pages += 1
        vacancies += len(card_urls)

    print(f"Просмотрено страниц {pages}, \nПросмотрено вакансий {vacancies}. Проверьте файл 'vacancies_python.json'")
