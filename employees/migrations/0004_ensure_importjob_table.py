from django.db import migrations


CREATE_SQL = """
CREATE TABLE IF NOT EXISTS "employees_importjob" (
    "id"            UUID PRIMARY KEY,
    "status"        VARCHAR(10) NOT NULL DEFAULT 'running',
    "total"         INTEGER NOT NULL DEFAULT 0,
    "done"          INTEGER NOT NULL DEFAULT 0,
    "ok"            INTEGER NOT NULL DEFAULT 0,
    "failed"        INTEGER NOT NULL DEFAULT 0,
    "skipped"       INTEGER NOT NULL DEFAULT 0,
    "stop_requested" BOOLEAN NOT NULL DEFAULT FALSE,
    "log"           JSONB NOT NULL DEFAULT '[]',
    "errors"        JSONB NOT NULL DEFAULT '[]',
    "created_at"    TIMESTAMP WITH TIME ZONE NOT NULL,
    "updated_at"    TIMESTAMP WITH TIME ZONE NOT NULL
);
"""


class Migration(migrations.Migration):

    dependencies = [
        ('employees', '0003_add_address_score_field'),
    ]

    operations = [
        migrations.RunSQL(CREATE_SQL, migrations.RunSQL.noop),
    ]
