import databases
import sqlalchemy
from sqlalchemy.schema import Table

# At this point is where the config is readed from the specified environment
from mediaapi.config import config

# Setting up the DB
metadata = sqlalchemy.MetaData()

post_table: Table = sqlalchemy.Table(
    "posts",
    metadata,
    sqlalchemy.Column("id", sqlalchemy.Integer, primary_key=True),
    sqlalchemy.Column("body", sqlalchemy.String),
    sqlalchemy.Column(
        "user_id", sqlalchemy.ForeignKey(column="users.id"), nullable=False
    ),
)

users_table: Table = sqlalchemy.Table(
    "users",
    metadata,
    sqlalchemy.Column("id", sqlalchemy.Integer, primary_key=True),
    sqlalchemy.Column(
        "email", sqlalchemy.String, unique=True
    ),  # The email address is unique
    sqlalchemy.Column("password", sqlalchemy.String),
)

comments_table: Table = sqlalchemy.Table(
    "comments",
    metadata,
    sqlalchemy.Column("id", sqlalchemy.Integer, primary_key=True),
    sqlalchemy.Column("body", sqlalchemy.String),
    sqlalchemy.Column(
        "post_id", sqlalchemy.ForeignKey(column="posts.id"), nullable=False
    ),
    sqlalchemy.Column(
        "user_id", sqlalchemy.ForeignKey(column="users.id"), nullable=False
    ),
)

engine = sqlalchemy.create_engine(
    url=config.DATABASE_URL,
    connect_args={
        "check_same_thread": False
    },  # Required for sqlite (default: Single thread)
)

metadata.create_all(engine)
database = databases.Database(
    url=config.DATABASE_URL, force_rollback=config.DB_FORCE_ROLL_BACK
)
