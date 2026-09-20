# Phase 2 — Database and Models

**Goal of this phase:** a running MySQL instance with four tables, reachable from Flask via SQLAlchemy, that you can insert into and query from a Python shell before you build any UI around them.

## Step 1 — Run MySQL locally via Docker

Don't install MySQL natively for a weekend project — a container is faster to set up and trivial to wipe and restart if your schema needs changing.

```
docker run --name song-ratings-db \
  -e MYSQL_ROOT_PASSWORD=your_root_password \
  -e MYSQL_DATABASE=song_ratings \
  -e MYSQL_USER=app_user \
  -e MYSQL_PASSWORD=your_app_password \
  -p 3306:3306 \
  -d mysql:8
```

Fill in the matching values in your `.env` file:

```
MYSQL_HOST=127.0.0.1
MYSQL_PORT=3306
MYSQL_USER=app_user
MYSQL_PASSWORD=your_app_password
MYSQL_DATABASE=song_ratings
```

Verify it's running with `docker ps`, and confirm you can connect with a MySQL client (`docker exec -it song-ratings-db mysql -u app_user -p`) before moving on.

## Step 2 — The four tables

Define these as SQLAlchemy models in `models.py`. Specification below — implement the actual class syntax yourself so the model layer is something you understand line by line, not copy-pasted.

**`users`**
| Column | Type | Constraints |
|---|---|---|
| `id` | Integer | Primary key, autoincrement |
| `spotify_id` | String(64) | Unique, not null |
| `display_name` | String(128) | Not null |
| `profile_image_url` | String(512) | Nullable |
| `spotify_refresh_token` | String(512) | Not null |
| `created_at` | DateTime | Default: current timestamp |

**`tracks`**
| Column | Type | Constraints |
|---|---|---|
| `id` | Integer | Primary key, autoincrement |
| `spotify_track_id` | String(64) | Unique, not null |
| `name` | String(256) | Not null |
| `artist_name` | String(256) | Not null |
| `album_name` | String(256) | Nullable |
| `album_art_url` | String(512) | Nullable |
| `cached_at` | DateTime | Default: current timestamp |

**`ratings`**
| Column | Type | Constraints |
|---|---|---|
| `id` | Integer | Primary key, autoincrement |
| `user_id` | Integer | Foreign key → `users.id`, not null |
| `track_id` | Integer | Foreign key → `tracks.id`, not null |
| `score` | Integer | Not null, check constraint `score BETWEEN 1 AND 5` |
| `rated_at` | DateTime | Default: current timestamp, updated on change |

Add a **unique constraint on `(user_id, track_id)`** — this is what makes "rate a song" naturally become "update the existing rating" instead of creating duplicates, without you having to check for that manually every time.

**`friendships`**
| Column | Type | Constraints |
|---|---|---|
| `id` | Integer | Primary key, autoincrement |
| `user_id` | Integer | Foreign key → `users.id`, not null |
| `friend_id` | Integer | Foreign key → `users.id`, not null |
| `status` | String(16) | Not null, e.g. `'pending'` / `'accepted'` |
| `created_at` | DateTime | Default: current timestamp |

Model this as directional (a request from A to B is a row with `user_id=A, friend_id=B`), not as an automatically-mutual relationship — you'll query in both directions depending on whether you're showing "my friends" or "pending requests I've sent."

## Step 3 — Wire SQLAlchemy to Flask

In your `config.py`, build the SQLAlchemy connection string from the env vars:

```
SQLALCHEMY_DATABASE_URI = f"mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DATABASE}"
```

Initialize `Flask-SQLAlchemy` in your app factory with this config, and import your models so they're registered with the SQLAlchemy metadata.

## Step 4 — Create the tables

For a weekend project, `db.create_all()` run once from a Python shell (or a small one-off script) is enough — you don't need Flask-Migrate's full migration history for something this size, since the schema is fixed going in.

## Step 5 — Verify from the database side, not just Python

Connect with the MySQL client and run `SHOW TABLES;` then `DESCRIBE users;` (and the others) to confirm the columns, types, and constraints actually landed the way you specified — SQLAlchemy defaults don't always map to the exact type you expect, and it's much better to catch a mismatch now than after you've written rating logic against it.

## Checkpoint — before moving to Phase 3

- [ ] `docker ps` shows the MySQL container running
- [ ] All four tables exist with the columns specified above (confirmed via `DESCRIBE`, not just assumed)
- [ ] The `(user_id, track_id)` unique constraint exists on `ratings`
- [ ] From a Python shell, you can manually insert a test user row and query it back
- [ ] Your Phase 1 `/callback` route is updated to actually create/look up the user row here, instead of the placeholder from Phase 1
