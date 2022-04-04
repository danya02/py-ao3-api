import traceback
from connection import get
from database import *
import re
from bs4 import BeautifulSoup

from get_author import get_pseud_by_url
from get_tags import get_arch_warning_tag_by_url, get_category_tag_by_url, get_character_tag_by_url, get_fandom_tag_by_url, get_freeform_tag_by_url, get_rating_tag_by_url, get_relationship_tag_by_url
from utils import parse_date

@db.atomic()
def parse_work(work_id):
    print("Parsing work", work_id)
    work_url = "https://archiveofourown.org/works/{}".format(work_id)
    html = get(work_url, bucket='work').text
    soup = BeautifulSoup(html, 'html.parser')

    work = Work()
    work.id = work_id
    work.title = soup.find("h2", {"class": "title heading"}).text.strip()

    if soup.find("a", {"rel": "author"}):
        work.author = get_pseud_by_url(soup.find("a", {"rel": "author"})['href'])
    # Works can be marked as "Anonymous" with no links to the author page
    # example: https://archiveofourown.org/works/26530525

    work.has_coauthors = len(soup.find_all("a", {"rel": "author"})) > 1

    work.rating = get_rating_tag_by_url(
        soup.find("dd", {"class": "rating tags"}).find("a")['href']
    )

    work_archive_warnings = work_fandoms = work_categories = work_characters = work_relationships = work_additional_tags = []

    # archive warnings are required
    work_archive_warnings = [
        get_arch_warning_tag_by_url(a['href'])
        for a in soup.find("dd", {"class": "warning tags"}).find_all("a")
    ]

    if soup.find("dd", {"class": "category tags"}):
        work_categories = [
            get_category_tag_by_url(a['href'])
            for a in soup.find("dd", {"class": "category tags"}).find_all("a")
        ]

    # fandoms are required
    work_fandoms = [
        get_fandom_tag_by_url(a['href'])
        for a in soup.find("dd", {"class": "fandom tags"}).find_all("a")
    ]

    if soup.find("dd", {"class": "relationship tags"}):
        work_relationships = [
            get_relationship_tag_by_url(a['href'])
            for a in soup.find("dd", {"class": "relationship tags"}).find_all("a")
        ]

    if soup.find("dd", {"class": "character tags"}):
        work_characters = [
            get_character_tag_by_url(a['href'])
            for a in soup.find("dd", {"class": "character tags"}).find_all("a")
        ]
    
    if soup.find("dd", {"class": "freeform tags"}):
        work_additional_tags = [
            get_freeform_tag_by_url(a['href'])
            for a in soup.find("dd", {"class": "freeform tags"}).find_all("a")
        ]

    work.language, _ = Language.get_or_create(name=soup.find("dd", {"class": "language"}).text.strip())

    if soup.find('dd', {'class': 'series'}):
        work.is_in_series = True

    work.published_on = parse_date(soup.find("dd", {"class": "published"}).text)
    updated_block = soup.find("dd", {"class": "status"})  # yes, it's called "status" for some reason
    if updated_block:
        work.updated_on = parse_date(updated_block.text)
    work.words = int(soup.find("dd", {"class": "words"}).text)
    chapters_present, chapters_expected = soup.find("dd", {"class": "chapters"}).text.split("/")
    
    work.num_chapters = int(chapters_present)
    work.max_chapters = int(chapters_expected) if chapters_expected != '?' else None

    if soup.find("dd", {"class": "comments"}):
        work.comments_count = int(soup.find("dd", {"class": "comments"}).text)
    if soup.find("dd", {"class": "kudos"}):
        work.kudos_count = int(soup.find("dd", {"class": "kudos"}).text)
    if soup.find("dd", {"class": "bookmarks"}):
        work.bookmarks_count = int(soup.find("dd", {"class": "bookmarks"}).text)
    if soup.find("dd", {"class": "hits"}):
        work.hits_count = int(soup.find("dd", {"class": "hits"}).text)

    try:
        work.save(force_insert=True)
    except pw.IntegrityError as exc:
        if Work.get_or_none(id=work.id):
            print("Work", work.id, "already exists, trying to update")
            work.save()
        else:
            print("Work", work.id, "could not be saved")
            raise exc

    tag_kinds = [
        (WorkWarningTag, work_archive_warnings),
        (WorkCategoryTag, work_categories),
        (WorkFandomTag, work_fandoms),
        (WorkRelationshipTag, work_relationships),
        (WorkCharacterTag, work_characters),
        (WorkFreeformTag, work_additional_tags)
    ]

    for tag_kind, tags in tag_kinds:
        tag_kind.delete().where(tag_kind.work == work).execute()
        for index, tag in enumerate(tags):
            tag_match = tag_kind()
            tag_match.work = work
            tag_match.tag = tag
            if 'index' in tag_kind.__dict__:
                tag_match.index = index
            tag_match.save(force_insert=True)

    # Are there more than one chapters?
    next_chapter_btn = soup.find("li", {"class": "chapter next"})
    if next_chapter_btn:
        download_many_chapters(work, soup)
    else:
        download_single_chapter(work, soup)

    return work

def download_many_chapters(work, soup):
    chapter = Chapter()
    chapter.work = work

    current_chapter_id = soup.find("option", {'selected': 'selected'}).attrs['value']
    chapter.chapter_id = int(current_chapter_id)
    title_line = soup.find("h3", {"class": "title"}).text.strip()
    title_parse = re.search(r'Chapter (\d+): (.*)', title_line)
    if title_parse:
        chapter.index = int(title_parse.group(1))
        chapter.title = title_parse.group(2)
    else:
        title_parse = re.search(r'Chapter (\d+)', title_line)
        chapter.index = int(title_parse.group(1))
        chapter.title = None


    common_chapter_parse(soup, chapter)

    try:
        chapter.save(force_insert=True)
    except pw.IntegrityError as exc:
        existing_chapter = Chapter.get_or_none(chapter_id=chapter.chapter_id)
        if not existing_chapter:
            print("Chapter", chapter.chapter_id, "could not be saved")
            raise exc
        else:
            print("Chapter", chapter.chapter_id, "already exists, trying to update")
            chapter.id = existing_chapter.id
            for field in chapter.dirty_fields:
                if field.name == 'chapter_id': continue
                setattr(existing_chapter, field.name, getattr(chapter, field.name))
            existing_chapter.save()

    next_chapter_btn = soup.find("li", {"class": "chapter next"})
    if next_chapter_btn:
        next_chapter_url = next_chapter_btn.find_next("a")['href']
        next_chapter_source = get("https://archiveofourown.org" + next_chapter_url, bucket='work').text
        next_chapter_soup = BeautifulSoup(next_chapter_source, 'html.parser')
        download_many_chapters(work, next_chapter_soup)

def download_single_chapter(work, soup):
    chapter = Chapter()
    chapter.work = work

    chapter.chapter_id = None
    chapter.title = None  # single chapter works don't have titles

    chapter.index = 1

    chapter.published_on = parse_date(soup.find("dd", {"class": "published"}).text)

    common_chapter_parse(soup, chapter)

    try:
        chapter.save(force_insert=True)
    except pw.IntegrityError as exc:
        existing_chapter = Chapter.get_or_none(chapter_id=chapter.chapter_id)
        if not existing_chapter:
            print("Chapter", chapter.chapter_id, "could not be saved")
            raise exc
        else:
            print("Chapter", chapter.chapter_id, "already exists, trying to update")
            chapter.id = existing_chapter.id
            for field in chapter.dirty_fields:
                setattr(existing_chapter, field.name, getattr(chapter, field.name))
            existing_chapter.save()


def common_chapter_parse(soup, chapter):
    summary = soup.find("div", {"class": "summary module"})
    if summary:
        chapter.summary = summary.find_next("blockquote", {"class": "userstuff"}).encode_contents().strip()

    content_block = soup.find("div", {"class": "userstuff"})
    chapter.content = content_block.encode_contents().strip()

    notes_block = soup.find("div", {"class": "notes module"})
    if notes_block:
        notes_content = notes_block.find_next("blockquote", {"class": "userstuff"})
        if notes_content:
            chapter.notes = notes_content.encode_contents().strip()

    end_notes_block = soup.find("div", {"class": "end notes module"})
    if end_notes_block:
        chapter.end_notes = end_notes_block.find_next("blockquote", {"class": "userstuff"}).encode_contents().strip()



if __name__ == '__main__':
    #parse_work(35583634)
    parse_work(10057010)