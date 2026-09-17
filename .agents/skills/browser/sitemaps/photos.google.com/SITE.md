# Google Photos Sitemap Guide

Browser automation specification for Google Photos (`photos.google.com`).

## Overview

- **Service**: Google Photos Media Library & Search
- **Primary Use Case**: Querying timeline media, locating video footage, and downloading video files for local multimodal analysis.
- **Driver**: Browser Use CLI 3.0 / `browser-harness` via CDP port `9226`.
- **Keyboard Shortcuts**:
  - `Shift+D`: Download the active media item in the viewer.
  - `Escape`: Close viewer back to library grid.
  - `/`: Focus search bar.

## Authentication & Persistence

- **Profile Directory**: `sitemaps/photos.google.com/profiles/adithya/`
- **User Data Directory**: `/home/shakstzy/HADES/.agents/skills/browser/sitemaps/photos.google.com/profiles/adithya/user_data`
- **CDP Port**: `9226`
- **Session Persistence**: Chrome session cookies and Google OAuth tokens persist across restarts in `user_data_dir`.

## Navigation Paths

- **All Videos Category**: `https://photos.google.com/search/_m8_Videos`
- **Favorites**: `https://photos.google.com/faves`
- **Recent Uploads**: `https://photos.google.com/search/_tra_`
