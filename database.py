import peewee as pw

db = pw.SqliteDatabase('ao3.db')

class MyModel(pw.Model):
    class Meta:
        database = db

def create_table(cls):
    db.create_tables([cls])
    return cls
