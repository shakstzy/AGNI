# Workflow: Download Video from Google Photos

Automated sequence to open Google Photos videos view, pick the latest video, and trigger a download.

## Steps

1. Navigate to `https://photos.google.com/search/_m8_Videos`.
2. Wait for media items to load in the DOM.
3. Click the first video thumbnail to open the viewer (`/photo/...`).
4. Dispatch keyboard shortcut `Shift+D` or click `More options` -> `Download`.
5. Monitor `~/Downloads` for the newly created video file (`*.mp4` or `*.mov`).
