from email.policy import default
import peewee as pw
import logging
#logging.basicConfig(level=logging.DEBUG)

db = pw.SqliteDatabase('ao3.db')

class MyModel(pw.Model):
    class Meta:
        database = db

def create_table(cls):
    db.create_tables([cls])
    return cls

@create_table
class User(MyModel):
    # These can be found at https://archiveofourown.org/users/<username>/profile
    id = pw.IntegerField(primary_key=True)
    username = pw.CharField(unique=True)
    title = pw.CharField(null=True)
    location = pw.CharField(null=True)
    joined_at = pw.DateField(null=True)
    bio = pw.TextField(null=True)
    birthday = pw.DateField(null=True)
    email = pw.CharField(null=True)

    updated_at = pw.DateTimeField(default=pw.datetime.datetime.now)
    exists_anymore = pw.BooleanField(default=True)

@create_table
class UnresolvedPseud(MyModel):
    user = pw.ForeignKeyField(User, backref='unresolved_pseuds')
    name = pw.CharField(unique=True)

@create_table
class Pseud(MyModel):
    # These can be found at https://archiveofourown.org/users/<username>/pseuds
    id = pw.IntegerField(primary_key=True)
    name = pw.CharField(unique=True)
    user = pw.ForeignKeyField(User, backref='pseuds')
    # The pseud description is only available from https://archiveofourown.org/users/<username>/pseuds/
    #description = pw.TextField(null=True)
    icon_url = pw.CharField(null=True)
    icon_alt_text = pw.CharField(null=True)

    updated_at = pw.DateTimeField(default=pw.datetime.datetime.now)
    exists_anymore = pw.BooleanField(default=True)

@create_table
class TagKind(MyModel):
    name = pw.CharField(unique=True)

    @classmethod
    def get(cls, name):
        try:
            return cls.select(cls.name == name).get()
        except cls.DoesNotExist:
            return cls.create(name=name)

@create_table
class Tag(MyModel):
    name = pw.CharField(unique=True)  # not case sensitive
    kind = pw.ForeignKeyField(TagKind, backref='tags')

    # TODO: implement tag relationships, like parent tags, metatags, etc.

    updated_at = pw.DateTimeField(default=pw.datetime.datetime.now)

@create_table
class Language(MyModel):
    name = pw.CharField(unique=True)

@create_table
class Work(MyModel):
    id = pw.IntegerField(primary_key=True)
    title = pw.CharField()

    author = pw.ForeignKeyField(Pseud, backref='works', null=True)
    has_coauthors = pw.BooleanField(default=False)  # TODO: replace with data

    rating = pw.ForeignKeyField(Tag)
    #archive_warnings = pw.ManyToManyField(Tag)
    #category = pw.ManyToManyField(Tag)
    #fandoms = pw.ManyToManyField(Tag)
    #relationships = pw.ManyToManyField(Tag)
    #characters = pw.ManyToManyField(Tag)
    #additional_tags = pw.ManyToManyField(Tag)
    language = pw.ForeignKeyField(Language)
    # TODO: add series support
    is_in_series = pw.BooleanField(default=False)

    published_on = pw.DateField()
    updated_on = pw.DateField(default=pw.datetime.datetime.now)

    words = pw.IntegerField()
    num_chapters = pw.IntegerField()
    max_chapters = pw.IntegerField(null=True)
    comments_count = pw.IntegerField(null=True)
    kudos_count = pw.IntegerField(null=True)
    bookmarks_count = pw.IntegerField(null=True)
    hits_count = pw.IntegerField(null=True)

    values_updated_at = pw.DateTimeField(default=pw.datetime.datetime.now)

@create_table
class WorkWarningTag(MyModel):
    work = pw.ForeignKeyField(Work, backref='warnings')
    tag = pw.ForeignKeyField(Tag, backref='warnings')

@create_table
class WorkCategoryTag(MyModel):
    work = pw.ForeignKeyField(Work, backref='category_tags')
    tag = pw.ForeignKeyField(Tag, backref='category_tags')


@create_table
class WorkFandomTag(MyModel):
    work = pw.ForeignKeyField(Work, backref='fandoms')
    tag = pw.ForeignKeyField(Tag, backref='fandoms')
    index = pw.IntegerField()

@create_table
class WorkRelationshipTag(MyModel):
    work = pw.ForeignKeyField(Work, backref='relationships')
    tag = pw.ForeignKeyField(Tag, backref='relationships')
    index = pw.IntegerField()

@create_table
class WorkCharacterTag(MyModel):
    work = pw.ForeignKeyField(Work, backref='characters')
    tag = pw.ForeignKeyField(Tag, backref='characters')
    index = pw.IntegerField()

@create_table
class WorkFreeformTag(MyModel):
    work = pw.ForeignKeyField(Work, backref='freeform_tags')
    tag = pw.ForeignKeyField(Tag, backref='freeform_tags')
    index = pw.IntegerField()



@create_table
class Chapter(MyModel):
    chapter_id = pw.IntegerField(unique=True, null=True)
    work = pw.ForeignKeyField(Work, backref='chapters')
    index = pw.IntegerField()
    title = pw.CharField(null=True)
    published_on = pw.DateField(null=True)

    content = pw.TextField()

    summary = pw.TextField(null=True)
    notes = pw.TextField(null=True)
    end_notes = pw.TextField(null=True)

    updated_at = pw.DateTimeField(default=pw.datetime.datetime.now)


@create_table
class Bookmark(MyModel):
    what = pw.ForeignKeyField(Work, backref='bookmarks')
    by_whom = pw.ForeignKeyField(User, backref='bookmarks')
    is_rec = pw.BooleanField(default=False)
    created_at = pw.DateTimeField(default=pw.datetime.datetime.now)
    note = pw.TextField(null=True)

    updated_at = pw.DateTimeField(default=pw.datetime.datetime.now)
    exists_anymore = pw.BooleanField(default=True)

    is_part_of_collection = pw.BooleanField(default=False)  # TODO: replace this with a proper Collection model

@create_table
class BookmarkTag(MyModel):
    bookmark = pw.ForeignKeyField(Bookmark, backref='tags')
    tag = pw.ForeignKeyField(Tag)

    class Meta:
        primary_key = pw.CompositeKey('bookmark', 'tag')

