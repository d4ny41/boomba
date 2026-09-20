# Phase 4 — Friends and Stretch Features

**Only start this phase once Phase 3's checkpoint is fully complete.** This is explicitly stretch scope — if you're running low on weekend, skip straight to Phase 5 and note this as "Roadmap" in your README rather than rushing it and shipping something broken.

## Step 1 — Understand the constraint that shapes this feature

Spotify's current API restrictions mean you can't look up arbitrary Spotify users by ID or search Spotify's user directory (`GET /users/{id}` for looking up other people has been withdrawn, and other-user profile access generally is restricted in Development Mode). This isn't a gap in your implementation — it's a platform limit. The consequence: "adding a friend" has to mean searching **your own app's `users` table** (people who have already logged into your app), not searching Spotify itself. Given you're capped at 5 allowlisted testers anyway, this isn't a real limitation in practice for a weekend demo — your "friends" are the same small group you already allowlisted in Phase 1.

## Step 2 — Friend request flow

Using the `friendships` table from Phase 2:
1. A "find friends" view lists other users already in your `users` table (simple — you have at most 4 other people to show).
2. Sending a request inserts a row: `user_id` = the sender, `friend_id` = the recipient, `status` = `'pending'`.
3. The recipient sees pending requests (query `friendships` where `friend_id` = them and `status` = `'pending'`) with accept/decline actions.
4. Accepting updates that row's `status` to `'accepted'`. Declining either deletes the row or sets it to `'declined'` — your call, but be consistent.
5. To check "are these two people friends" anywhere else in the app, query for an accepted row in **either** direction (`user_id`/`friend_id` could be either way round depending on who sent the original request) — don't assume the direction.

## Step 3 — Viewing a friend's rated list

Route: something like `/friends/<user_id>/ratings`. Before rendering anything, verify an accepted friendship exists between the current session user and that `user_id` — don't let a logged-in user view an arbitrary stranger's ratings just because they guessed a URL. Then it's the same query pattern as your own rating page: join `ratings` to `tracks` for that user, render.

## Step 4 — Stretch: combined "friend group top tracks"

Only attempt this if Phase 4 Steps 1–3 are done with time to spare. Approach: for each accepted friend (plus yourself), pull their cached top tracks (you may already have them cached from when they used their own feed — otherwise fetch fresh), combine into one list, and rank by however many of the group have it in their top tracks, or by average rating if enough of the group has rated it. Keep the ranking logic simple — this is a bonus feature, not the part of the project anyone will judge closely.

## Checkpoint — before moving to Phase 5

- [ ] Friend requests can be sent, seen by the recipient, and accepted
- [ ] A user can view an accepted friend's rated list, but a direct URL guess to a non-friend's list is rejected
- [ ] If you didn't get to the combined feed, it's clearly marked as future work rather than left half-built in the UI
