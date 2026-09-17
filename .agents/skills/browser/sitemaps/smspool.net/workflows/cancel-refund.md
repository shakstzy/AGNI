# Workflow: Cancel Order & Auto-Refund (SMSPool)

## Goal
Cancel an unfulfilled SMS verification order to release the number and immediately trigger an automated account credit/refund.

## Verified Action Sequence
1. Navigate to Order History (`https://www.smspool.net/history`).
2. Identify the pending order where the SMS did not arrive.
3. Click the **Cancel** button on the active order row.
4. Verify the order status transitions to `Cancelled` / `Refunded`.
5. Check account balance on `/deposit` to confirm the funds have been restored.
