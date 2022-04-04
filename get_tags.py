from database import *
import re
from urllib.parse import unquote
from functools import partial

def get_tag_by_url(url, tag_type):
    tag_name = re.search(r'/tags/([^/]*)(/works)?', url).group(1)
    tag_name = unquote(tag_name).replace('*s*', '/').replace('*q*', '?')
    tag = Tag.get_or_none(Tag.name == tag_name)
    if tag is None:
        tag_kind, _ = TagKind.get_or_create(name = tag_type)
        tag = Tag.create(name=tag_name, kind=tag_kind)
    return tag

get_rating_tag_by_url = partial(get_tag_by_url, tag_type='Rating')
get_arch_warning_tag_by_url = partial(get_tag_by_url, tag_type='Archive Warning')
get_category_tag_by_url = partial(get_tag_by_url, tag_type='Category')
get_fandom_tag_by_url = partial(get_tag_by_url, tag_type='Fandom')
get_relationship_tag_by_url = partial(get_tag_by_url, tag_type='Relationship')
get_character_tag_by_url = partial(get_tag_by_url, tag_type='Character')
get_freeform_tag_by_url = partial(get_tag_by_url, tag_type='Additional Tags')
