# InkyPi Crypto Price

An InkyPi plugin that shows a crypto price with a clean, glanceable layout and configurable symbol settings.

## Install

Use the InkyPi plugin installer with the plugin ID and this repository URL, following the install pattern shown by the official InkyPi plugin template.

```bash
inkypi plugin install crypto_price https://github.com/shadal18/inkypi-crypto-price
```

## Update

To update the plugin on your InkyPi device:

1. SSH into your InkyPi host.
2. Change into the plugin directory:
   ```bash
   cd ~/InkyPi/src/plugins/crypto_price
   ```
3. Run this update command:
   ```bash
   git pull origin main && \
   if [ -d crypto_price ]; then \
     rsync -a crypto_price/ ./ && \
     rm -rf crypto_price; \
   fi && \
   sudo systemctl restart inkypi.service
   ```

If you don’t see your changes after updating:

- Confirm you are in the correct plugin folder.
- Clear your browser cache or hard refresh the InkyPi web UI.
- Check the InkyPi logs for any plugin errors.

## Requirements

- An API Ninjas account with a configured API key for crypto price requests.
- A valid InkyPi environment key named `API_NINJAS_KEY`.
- Network access from the InkyPi device to the API Ninjas API endpoint.

## Features

This plugin is an extension for the InkyPi e-paper display frame and includes the following features.

- Shows the current price for a configured crypto symbol pair such as `BTCUSD` or `BTCUSDT`.
- Displays the base and quote symbols in a large, glanceable format.
- Displays the latest returned timestamp from the API.
- Supports common fiat and crypto quote pairs.
- Clean layout optimized for quick glance reading on e-paper.
- Simple settings with a configurable header text and symbol pair.

## Settings

The plugin settings page lets you customize:

- Header text.
- Crypto symbol pair.

## API Key Setup

This plugin requires one API key from API Ninjas.

### Create the API key

1. Create or log into your API Ninjas account at [https://api-ninjas.com](https://api-ninjas.com).
2. Open your API Ninjas dashboard.
3. Generate or copy your API key for use with the [Crypto Price API](https://api-ninjas.com/api/cryptoprice).

### Add the key in InkyPi

1. Open the InkyPi front page.
2. Click the **key icon**.
3. Add a new key named `API_NINJAS_KEY`.
4. Paste in your API Ninjas API key.
5. Save it.
6. Restart InkyPi if needed.

## API Endpoint Used

This plugin currently reads data from the following API Ninjas endpoint:

- `/v1/cryptoprice`

This endpoint returns the current price and current UNIX timestamp for a cryptocurrency symbol pair, and fiat-quoted pairs require the appropriate API plan level.

## Repository

GitHub repository:

[https://github.com/shadal18/inkypi-crypto-price](https://github.com/shadal18/inkypi-crypto-price)

## Screenshots

- Main plugin display showing crypto price data.
- Plugin settings screen.

<p align="center">
  <img src="screenshots/example.png" width="45%" />
  <img src="screenshots/settings.png" width="45%" />
</p>
