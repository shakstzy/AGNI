# Workflow: Order Temporary SMS Number (SMSPool)

## Goal
Order a non-VoIP temporary phone number for SMS verification on smspool.net using Browser Use CLI 3.0.

## Verified Action Sequence
1. Attach to SMSPool profile 'adithya' on port 9200:
   ```bash
   ./.agents/skills/browser/cli/browser opencli --site smspool.net --profile adithya --url https://www.smspool.net/order
   ```
2. In the Order interface, select the target Country (e.g., United States) from `#country`.
3. Select the target Service (e.g., Tinder, OpenAI, Google) from `#service`.
4. Check estimated pricing and verify sufficient account balance.
5. Click **Quick Order** to allocate the phone number.
6. Extract and copy the allocated non-VoIP phone number (e.g., `+1XXXXXXXXXX`) for use in the target service verification screen.
