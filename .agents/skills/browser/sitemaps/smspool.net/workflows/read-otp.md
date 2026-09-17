# Workflow: Retrieve SMS OTP Verification Code (SMSPool)

## Goal
Monitor and extract the incoming SMS verification OTP code for an active order on smspool.net.

## Verified Action Sequence
1. Navigate to the Order History / Active Orders page (`https://www.smspool.net/history`).
2. Locate the active row corresponding to the ordered phone number and service.
3. Poll the order row every 3-5 seconds until the status changes from `Pending` to `Completed` or the verification code appears.
4. Extract the 4-to-8 digit OTP verification code from the SMS text message.
5. Provide the code to the downstream verification flow or input form.
6. Stop if order times out without SMS arrival (usually 5 to 10 minutes depending on service).
