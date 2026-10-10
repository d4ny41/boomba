# Boomba

Boomba is an attempt at building a Letterboxd-style music rating platform. Users can authenticate with their Spotify accounts to rate their most recently played tracks and the songs they have been listening to most over the last four weeks. They can also add other Boomba users as friends to view and compare each other's ratings. This version of the app was made as a solo project to practise OAuth, relational schema design, and web security against a real third-party API with real platform constraints.

## Demo

Demo video coming soon.

The app is live at https://boomba-rc2r.onrender.com. Spotify only allows apps in development mode to be used by five approved accounts, so you will not be able to log in unless I have added your account. The video above shows the full flow for that reason. The site is on a free hosting plan, so the first visit after a quiet period can take a little while to load.

## Features

- Users sign in with their Spotify account. There is no separate username or password, so the app never stores a password.
- The home feed shows a user's top 20 tracks from the last four weeks with album art, and each one can be rated from 1 to 5 without leaving the page.
- The rating page pulls a user's 50 most recently played tracks and removes any repeats. Rating a song again updates the existing score rather than creating a second entry.
- Users can send, accept, decline, and cancel friend requests with other Boomba users, and remove friends.
- Each friend has a page listing their ratings from highest to lowest, with the user's own rating for the same song shown next to theirs.

## Tech Stack

- Backend: Python 3, Flask, and Jinja2 templates
- Spotify integration: spotipy
- Database: MySQL 8 through Flask-SQLAlchemy and PyMySQL, hosted on Aiven in production and run in Docker for local development
- Security and testing: Flask-WTF for CSRF protection and pytest for automated tests
- Deployment: gunicorn on Render

## How It Works

### Signing in with Spotify

Login uses Spotify's OAuth 2.0 authorisation code flow through the `/login` and `/callback` routes. By default, spotipy saves tokens to a `.cache` file on disk. On a server used by several people, this could lead to one user being handed another user's token. I noticed this during testing when a `.cache` file appeared in the project folder after logging in, so the app now uses spotipy's `MemoryCacheHandler`, which keeps tokens in memory only.

Each user's refresh token is stored on their row in the `users` table. Whenever a page needs Spotify data, the app uses that refresh token to get a new access token for that request. If Spotify issues a new refresh token in the process, the app saves it in place of the old one. If a user removes Boomba's access from their Spotify settings, they are logged out and sent back to the login page.

### Caching tracks

Every track a user sees is saved in the `tracks` table the first time it appears, along with its name, artists, album, and album art. Ratings point to these rows rather than to Spotify directly. This means two users who rate the same song are rating the same row, which is what allows ratings to be compared between friends. New tracks are added together with a single commit, and the friend ratings page reads only from the database without making any calls to Spotify.

### Database

The database has four tables: `users`, `tracks`, `ratings`, and `friendships`. The `ratings` table has a unique constraint on the combination of `user_id` and `track_id`, so a user can only have one rating per song. When a user rates a song they have already rated, the existing row is updated, and the constraint stops a duplicate from being saved even if that logic ever failed. A check constraint also keeps every score between 1 and 5.

Each row in `friendships` is a request from one user to another, marked as either pending or accepted. Since either person could have sent the original request, the app checks both directions whenever it needs to know whether two users are friends.

## Security

Since practising web security was one of the main goals of this project, I added the following protections.

- Every form that changes data, such as rating a song or accepting a friend request, sends a POST request protected by a Flask-WTF CSRF token. This stops another website from submitting forms on behalf of a logged-in user.
- The login flow sends Spotify a random `state` value and checks that the same value comes back, so a login can't be started by another site and finished in someone else's browser.
- The session cookie is signed, marked `HttpOnly` and `SameSite=Lax`, and marked `Secure` when the app runs in production.
- The logged-in user is always taken from the session and never from a form field, so nobody can rate songs or send requests as someone else.
- The server rejects any score that is not a whole number from 1 to 5, as well as ratings for tracks that do not exist. The database check constraint acts as a second line of defence.
- After a rating is submitted, the app only redirects to one of two known pages, which prevents open redirect attacks.
- Only the recipient of a friend request can accept or decline it, and only the sender can cancel it.
- The app checks for an accepted friendship before showing another user's ratings. Anyone who is not a friend gets a `404 Not Found` rather than a `403 Forbidden`, so the response does not reveal whether that user exists.
- All secrets are kept in environment variables and never committed to the repository. The production database connection is encrypted with SSL, and debug mode is turned off in production.

Some protection also comes from the tools themselves. SQLAlchemy uses parameterised queries, which guards against SQL injection, and Jinja2 escapes values like display names before adding them to a page, which guards against cross-site scripting.

## How It Was Built

I planned the features, the database design, and the security requirements myself. I used Claude Code to write much of the implementation. I reviewed the changes at each stage and tested every step by hand, which is how I caught the token cache problem described above.

## Running Locally

You will need Python 3, Docker, and a Spotify account. The account that owns the Spotify app needs an active Premium subscription.

1. Clone the repository and install the dependencies.

   ```
   git clone https://github.com/d4ny41/boomba.git
   cd boomba
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

2. Create an app on the Spotify Developer Dashboard. Set the redirect URI to `http://127.0.0.1:5000/callback` and add your Spotify account under User Management.

3. Start a MySQL container.

   ```
   docker run --name song-ratings-db \
     -e MYSQL_ROOT_PASSWORD=choose_a_root_password \
     -e MYSQL_DATABASE=song_ratings \
     -e MYSQL_USER=app_user \
     -e MYSQL_PASSWORD=choose_a_password \
     -p 3306:3306 \
     -d mysql:8
   ```

4. Copy `.env.example` to `.env` and fill in your Spotify credentials, a Flask secret key, and the MySQL details from the previous step.

   ```
   cp .env.example .env
   ```

5. Create the tables and start the app.

   ```
   python init_db.py
   python run.py
   ```

6. Open `http://127.0.0.1:5000` in your browser. Use `127.0.0.1` rather than `localhost`, since the address has to match the redirect URI registered with Spotify.

## Running Tests

```
pytest
```

The 18 tests run against a temporary in-memory SQLite database, so they never touch the MySQL data. They cover the friend request rules, who is allowed to see whose ratings, and the links on the landing page.

## Known Limitations

- Spotify's development mode limits the app to five approved accounts and requires the owner to have Premium. Opening it to the public would need extended access, which Spotify only grants to registered businesses with at least 250,000 monthly active users.
- Spotify no longer lets apps in development mode read its own charts and playlists or look up other users. This is why the feed shows each user's own top tracks rather than a global chart, and why friends are found among Boomba users rather than on Spotify.
- A new access token is requested on every page load. This keeps the code simple but adds an extra request to Spotify each time.
- Refresh tokens are stored in the database without encryption, there is no rate limiting, and logging out uses a link rather than a protected form.

## What I'd Do Next

- Add search so users can rate any song, not only ones they have played recently
- Add a feed showing the most popular tracks across a user's group of friends
- Let users write short reviews alongside their ratings
- Encrypt refresh tokens, add rate limiting, and move to proper database migrations with Flask-Migrate
- Add a messaging option between friends, where they can chat and share songs from Spotify among each other

## License

This project is licensed under the MIT License. See `LICENSE` for details.