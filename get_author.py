from bs4 import BeautifulSoup
from more_itertools import bucket
from connection import get
from database import *
import re
from urllib.parse import unquote

from utils import parse_date

def get_user_by_name(user_name):
    return get_user_by_url('/users/' + user_name)

def get_pseud_by_name(user_name, pseud_name):
    return get_pseud_by_url('/users/' + user_name, '/pseuds/' + pseud_name)

def get_pseud_by_url(url):
    q = re.search(r'/users/(.*)/pseuds/(.*)', url)
    user_name = q.group(1)
    pseud_name = q.group(2)
    user_name = unquote(user_name)
    pseud_name = unquote(pseud_name)
    pseud = Pseud.get_or_none(Pseud.name == pseud_name)
    if pseud is None:
        pseud = download_pseud(user_name, pseud_name)
    return pseud

def download_pseud(user_name, pseud_name):
    if pseud_name == 'orphan_account':
        # the orphan account is a special case
        return Pseud.create(name='orphan_account',
            user=get_user_by_name('orphan_account'),
            icon_url='https://s3.amazonaws.com/otw-ao3-icons/icons/8/standard.png',
            icon_alt_text='AO3 logo with text "orphan account"')

    if user_name == 'orphan_account':
        # the orphan account is a special case
        return Pseud.create(name=pseud_name,
            user=get_user_by_name('orphan_account'),
            icon_url='https://s3.amazonaws.com/otw-ao3-icons/icons/8/standard.png',
            icon_alt_text='AO3 logo with text "orphan account"')

    user = get_user_by_name(user_name)
    pseud_page = get('https://archiveofourown.org/users/' + user_name + '/pseuds/' + pseud_name, bucket='user').text
    soup = BeautifulSoup(pseud_page, 'html.parser')
    pseud = Pseud()
    pseud.name = pseud_name
    pseud.user = user
    if soup.find('img', {'class': 'icon'}):
        pseud.icon_url = soup.find('img', {'class': 'icon'})['src']
        if 'alt' in soup.find('img', {'class': 'icon'}).attrs:
            pseud.icon_alt_text = unquote(soup.find('img', {'class': 'icon'})['alt'])
    pseud.save(force_insert=True)
    UnresolvedPseud.delete().where(UnresolvedPseud.name == pseud_name, UnresolvedPseud.user == user).execute()
    return pseud

def get_user_by_url(url):
    q = re.search(r'/users/(.*)', url)
    user_name = q.group(1)
    user_name = unquote(user_name)
    user = User.get_or_none(User.username == user_name)
    if user is None:
        user = download_user(user_name)
    return user

def download_user(user_name):
    if user_name == 'orphan_account':
        # the orphan account is a special case
        return User.create(username='orphan_account',
            icon_url='https://s3.amazonaws.com/otw-ao3-icons/icons/8/standard.png',
            icon_alt_text='AO3 logo with text "orphan account"')

    user_page = get('https://archiveofourown.org/users/' + user_name + '/profile', bucket='user').text
    soup = BeautifulSoup(user_page, 'html.parser')
    user = User()

    user.username = user_name

    user_block = soup.find('div', {'class': 'primary header module'})

    user.id = int(
        user_block.find_next('dt', text='My user ID is:').find_next_sibling('dd').text.strip()
    )

    user.joined_at = parse_date(
        user_block.find_next('dt', text='I joined on:').find_next_sibling('dd').text.strip()
    )

    title_element = user_block.find_next('h3', {'class': 'heading'})
    if title_element:
        user.title = title_element.text.strip()
    
    location_element = user_block.find_next('dt', text='I live in:')
    if location_element:
        user.location = location_element.find_next_sibling('dd').text.strip()

    bio_element = user_block.find_next('div', {'class': 'bio module'})
    if bio_element:
        user.bio = bio_element.find('blockquote').encode_contents()


    birthday_element = user_block.find_next('dt', text='My birthday:')
    if birthday_element:
        user.birthday = parse_date(birthday_element.find_next_sibling('dd').text.strip())
    
    email_element = user_block.find_next('dt', text='My email address:')
    if email_element:
        user.email = email_element.find_next_sibling('dd').text.strip()
    

    user.icon_url = user_block.find_next('img', {'class': 'icon'})['src'].strip()
    if 'alt' in user_block.find('img', {'class': 'icon'}).attrs:
        user.icon_alt_text = unquote(user_block.find('img', {'class': 'icon'})['alt'].strip())
    user.save(force_insert=True)

    for pseud in user_block.find_next('dd', {'class': 'pseuds'}).find_all('a'):
        if Pseud.get_or_none(Pseud.name == pseud.text) is None:
            UnresolvedPseud.get_or_create(user=user, name=pseud.text.strip())
    return user