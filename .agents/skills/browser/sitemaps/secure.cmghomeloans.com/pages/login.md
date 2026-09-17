# CMG Home Loans Login Page

- **Route**: `https://secure.cmghomeloans.com/`
- **Fields**:
  - `user_field`: Username or registered email (`adithya@outerscope.xyz`)
  - `password_field`: Account password retrieved from Bitwarden
  - `login_btn`: Sign-in submit button
- **Behavior**:
  - Direct entry of credentials via Browser Use CLI.
  - Halt if SMS/email OTP, reCAPTCHA, or security questions are presented.
