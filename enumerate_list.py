from bs4 import BeautifulSoup
from connection import get
import re
from database import *

from get_work import parse_work

def enumerate_search_results(search_url, page=1):
    print('-----------')
    print('Page', page)
    print('-----------')
    search_page = get("https://archiveofourown.org" + search_url, bucket='search').text
    soup = BeautifulSoup(search_page, 'html.parser')
    for result in soup.find_all('li', {'role': 'article'}):
        work_url = result.find_next('h4', {'class': 'heading'}).find_next('a')['href']
        yield work_url
    next_url = soup.find('a', {'rel': 'next'}, string="Next →")['href']
    yield from enumerate_search_results(next_url, page=page+1)

def save_all_works_from_search_query(search_url):
    for work_url in enumerate_search_results(search_url):
        print('---', work_url, '---')
        parsed_url = re.search(r'/works/(\d+)', work_url)
        work_id = parsed_url.group(1)
        if Work.get_or_none(Work.id == work_id):
            print('Work', work_id, 'already exists')
            continue
        parse_work(work_id)
    
if __name__ == '__main__':
    save_all_works_from_search_query(
        "/works/search?work_search%5Bquery%5D=&work_search%5Btitle%5D=&work_search%5Bcreators%5D=&work_search%5Brevised_at%5D=&work_search%5Bcomplete%5D=&work_search%5Bcrossover%5D=&work_search%5Bsingle_chapter%5D=0&work_search%5Bword_count%5D=&work_search%5Blanguage_id%5D=&work_search%5Bfandom_names%5D=&work_search%5Brating_ids%5D=&work_search%5Bcharacter_names%5D=&work_search%5Brelationship_names%5D=&work_search%5Bfreeform_names%5D=&work_search%5Bhits%5D=&work_search%5Bkudos_count%5D=&work_search%5Bcomments_count%5D=&work_search%5Bbookmarks_count%5D=&work_search%5Bsort_column%5D=_score&work_search%5Bsort_direction%5D=&commit=Search"
    )