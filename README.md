# Amber SmartShift Status for Home Assistant

A custom component for Home Assistant that scrapes the [Amber SmartShift Status page](https://help.amber.com.au/hc/en-us/articles/35922375367181-SmartShift-Status) and provides a sensor indicating the health of your battery brand's SmartShift integration.

## Features
- Bypasses Cloudflare protection using `cloudscraper`.
- Provides a Config Flow so you can select your specific battery brand from the Home Assistant UI.
- Updates every 30 minutes.
- Provides 6 sensors for comprehensive status tracking:
  - **Status**: Indicates the overall health (`Healthy` or `Issue`).
  - **First Reported**: Displays when the active issue was first identified (multiple issues are separated by ` / `).
  - **Last Updated**: Shows when the active issue description was last updated (multiple issues are separated by ` / `).
  - **Date Resolved**: Displays the resolution date/time for the most recently resolved issue.
  - **Error Details**: Shows a summary of the active issue details (multiple issues are separated by two newlines).
  - **Last Polled**: Indicates the timestamp of the last successful scrape from the Amber Status page.

## Installation

### HACS (Home Assistant Community Store)
1. Open HACS in your Home Assistant instance.
2. Click on the 3 dots in the top right corner and select **Custom repositories**.
3. Add the URL to this repository and select **Integration** as the category.
4. Click **Add**.
5. Once added, you can find "Amber SmartShift Status" in HACS and click **Download**.
6. Restart Home Assistant.
7. Go to **Settings** > **Devices & Services** > **Add Integration** and search for "Amber SmartShift Status".
8. Follow the prompts to select your battery type.

### Manual Installation
1. Download the repository.
2. Copy the `custom_components/amber_smartshift_status` folder to your Home Assistant's `custom_components` directory.
3. Restart Home Assistant.
4. Go to **Settings** > **Devices & Services** > **Add Integration** and search for "Amber SmartShift Status".
5. Follow the prompts to select your battery type.

## Requirements
- Python requirements: `beautifulsoup4`, `cloudscraper` (These are installed automatically by Home Assistant).
