# Workflow: Upload Single Release

1. Navigate to `https://distrokid.com/new/`.
2. Dismiss cookie banner (`.osano-cm-deny`) and upgrade modal if present.
3. Select 1 song release.
4. Set artist name: `Shak STZY`.
5. Upload cover art (3000x3000px JPEG) to `input#file_art`.
6. Select language English, primary genre Hip Hop/Rap.
7. Enter track title into `input[name="trackTitle1"]`.
8. Upload WAV audio file into `input[name="file_track1"]`.
9. Set songwriter as original music, real name `Adithya Shakthi Kumar`.
10. Check mandatory confirmation checkboxes (`input.areyousure[type="checkbox"]`).
11. Submit via `#saveAndContinue`.
12. Verify landing on `/new/done/?albumuuid=...`.
