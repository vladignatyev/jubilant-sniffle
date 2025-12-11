# Manual testing instructions

Follow these steps to validate the Telegram bot address-checking flow:

1. **Start the bot**
   - Set environment variables for `BOT_TELEGRAM_API_TOKEN`, `BOT_AMLBOT_API_ID`, and `BOT_AMLBOT_API_KEY`.
   - Run `python run.py` in a terminal to launch the bot.

2. **Verify invalid address handling**
   - Send a short or non-alphanumeric message (e.g., `hello`).
   - Expect the bot to reply with `The address you provided isn't recognized`.

3. **Trigger the blockchain selection prompt**
   - Send any alphanumeric string 26–64 characters long to simulate an address (e.g., `1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa`).
   - The bot should respond to the same message with `Which blockchain to check this address across?` and display inline buttons for all supported blockchains.

4. **Immediate response path**
   - Click any blockchain button.
   - The keyboard prompt disappears entirely, and the bot replies to your original address message with `immediate_response`.

5. **Postponed response path**
   - Send another valid-looking address that contains the word `wait` (for example, `waitADDRESS1234567890123456789`).
   - Choose any blockchain option.
   - The keyboard message is removed, and a new status reply is added to your address message saying `Checking the address <address> on blockchain <blockchain>` (with your specific values). After one polling iteration, the status message disappears and the bot replies to your address message with `immediate_response`.

6. **Parallel request handling**
   - Send two different valid addresses before pressing any blockchain button.
   - Choose blockchains for each in any order; each selection should process independently with its own response or polling status tied to the specific address message.
