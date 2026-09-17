# SMSPool Login Reference

- **Profile**: Use `adithya` profile under `profiles/adithya/` (`profiles/adithya/metadata.json`).
- **Vault Reference**: Query `SMSPool` in Bitwarden folder `HADES`.
- **Retrieval Command**:
  ```bash
  bw get item "SMSPool"
  ```
- **Session Persistence**: Session cookies and local storage persist in `profiles/adithya/user_data/`.
- **Checkpoint Rule**: Stop on Cloudflare Turnstile, CAPTCHA, or human verification challenges. Never attempt brute-force password retries.
