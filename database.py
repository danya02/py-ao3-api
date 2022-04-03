from email.policy import default
import peewee as pw

db = pw.SqliteDatabase('ao3.db')

class MyModel(pw.Model):
    class Meta:
        database = db

def create_table(cls):
    db.create_tables([cls])
    return cls

class User(MyModel):
    # These can be found at https://archiveofourown.org/users/<username>/profile
    id = pw.IntegerField(primary_key=True)
    username = pw.CharField(unique=True)
    title = pw.CharField(null=True)
    location = pw.CharField(null=True)
    joined_at = pw.DateField(null=True)
    bio = pw.TextField(null=True)

    updated_at = pw.DateTimeField(default=pw.datetime.datetime.now)
    exists_anymore = pw.BooleanField(default=True)

class Pseud(MyModel):
    # These can be found at https://archiveofourown.org/users/<username>/pseuds
    id = pw.IntegerField(primary_key=True)
    name = pw.CharField(unique=True)
    user = pw.ForeignKeyField(User, backref='pseuds')
    description = pw.TextField(null=True)
    icon_url = pw.CharField(null=True)
    icon_alt_text = pw.CharField(null=True)

    updated_at = pw.DateTimeField(default=pw.datetime.datetime.now)
    exists_anymore = pw.BooleanField(default=True)

class TagKind:
    FREEFORM = 0
    FANDOM = 1
    CHARACTER = 2
    CATEGORY = 3
    UNSORTEDTAG = 4

class Tag(MyModel):
    name = pw.CharField(unique=True)  # not case sensitive
    kind = pw.IntegerField(null=True)

    # TODO: implement tag relationships, like parent tags, metatags, etc.

    updated_at = pw.DateTimeField(default=pw.datetime.datetime.now)

class Language(MyModel):
    name = pw.CharField(unique=True)

    @classmethod
    def get(cls, name):
        try:
            return cls.get(cls.name == name)
        except cls.DoesNotExist:
            return cls.create(name=name)

class Work(MyModel):
    id = pw.IntegerField(primary_key=True)
    title = pw.CharField()

    author = pw.ForeignKeyField(User, backref='works')
    has_coauthors = pw.BooleanField(default=False)  # TODO: replace with data

    rating = pw.ForeignKeyField(Tag)
    archive_warnings = pw.ManyToManyField(Tag)
    fandoms = pw.ManyToManyField(Tag)
    relationships = pw.ManyToManyField(Tag)
    characters = pw.ManyToManyField(Tag)
    additional_tags = pw.ManyToManyField(Tag)
    language = pw.ForeignKeyField(Language)
    published_on = pw.DateField()
    updated_on = pw.DateField(default=pw.datetime.datetime.now)

    words = pw.IntegerField()
    chapters = pw.IntegerField()
    max_chapters = pw.IntegerField(null=True)
    comments = pw.IntegerField()
    kudos = pw.IntegerField()
    bookmarks = pw.IntegerField()
    hits = pw.IntegerField()

    has_work_skin = pw.BooleanField(default=False)  # TODO: replace with WorkSkin table

    values_updated_at = pw.DateTimeField(default=pw.datetime.datetime.now)


class Chapter(MyModel):
    chapter_id = pw.IntegerField(unique=True, null=True)
    work = pw.ForeignKeyField(Work, backref='chapters')
    index = pw.IntegerField()
    title = pw.CharField()

    content = pw.TextField()

    front_notes = pw.TextField(null=True)
    back_notes = pw.TextField(null=True)


class Bookmark(MyModel):
    what = pw.ForeignKeyField(Work, backref='bookmarks')
    by_whom = pw.ForeignKeyField(User, backref='bookmarks')
    is_rec = pw.BooleanField(default=False)
    created_at = pw.DateTimeField(default=pw.datetime.datetime.now)
    note = pw.TextField(null=True)

    updated_at = pw.DateTimeField(default=pw.datetime.datetime.now)
    exists_anymore = pw.BooleanField(default=True)

    is_part_of_collection = pw.BooleanField(default=False)  # TODO: replace this with a proper Collection model

class BookmarkTag(MyModel):
    bookmark = pw.ForeignKeyField(Bookmark, backref='tags')
    tag = pw.ForeignKeyField(Tag)

    class Meta:
        primary_key = pw.CompositeKey('bookmark', 'tag')

