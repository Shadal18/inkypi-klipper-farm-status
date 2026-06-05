# InkyPi Klipper Farm Status

An InkyPi plugin that shows the status of multiple Klipper printers with a clean, glanceable layout and configurable display options for Moonraker and Spoolman data.

_Klipper Farm Status_ is a plugin for [InkyPi](https://github.com/fatihak/InkyPi) that surfaces the live state of your Klipper printer farm directly on your Inky display.

## Install

Use the InkyPi plugin installer with the plugin ID and this repository URL, following the install pattern shown by the official InkyPi plugin template.

```bash
inkypi plugin install klipper_farm_status https://github.com/shadal18/inkypi-klipper-farm-status
```

## Update

To update the plugin on your InkyPi device:

1. SSH into your InkyPi host.
2. Change into the plugin directory:
   ```bash
   cd ~/InkyPi/src/plugins/klipper_farm_status
   ```
3. Run this update command:
   ```bash
   git pull origin main && \
   if [ -d klipper_farm_status ]; then \
     rsync -a klipper_farm_status/ ./ && \
     rm -rf klipper_farm_status; \
   fi && \
   sudo systemctl restart inkypi.service
   ```

If you don’t see your changes after updating:

- Confirm you are in the correct plugin folder.
- Clear your browser cache or hard refresh the InkyPi web UI.
- Check the InkyPi logs for any plugin errors.

## Requirements

- One or more reachable Moonraker instances for your Klipper printers.
- Network access from the InkyPi device to each Moonraker host.
- Optional Spoolman integration configured in Moonraker if you want active spool data displayed.
- A working InkyPi installation with plugin support.

## Features

This plugin is an extension for the InkyPi e-paper display frame and includes the following features.

- Shows the live status of multiple Klipper printers from Moonraker.
- Displays printer state such as printing, paused, idle, complete, offline, or error.
- Displays print progress percentage for each printer.
- Displays the active filename when available.
- Displays estimated remaining time when available.
- Displays current and total layer counts when available.
- Displays nozzle and bed temperatures.
- Displays the currently active spool when Moonraker is linked to Spoolman.
- Optionally displays spool brand, material, and remaining grams.
- Includes per-printer enable or disable controls.
- Clean layout optimized for quick glance reading on e-paper.
- Uses InkyPi display dimensions and orientation handling for proper rendering.

## Settings

The plugin settings page lets you customize:

- Header text.
- Printer 1 name.
- Printer 1 Moonraker URL.
- Enable or disable Printer 1.
- Printer 2 name.
- Printer 2 Moonraker URL.
- Enable or disable Printer 2.
- Show or hide progress.
- Show or hide filename.
- Show or hide ETA.
- Show or hide layers.
- Show or hide temperatures.
- Show or hide active spool.
- Show or hide spool brand.
- Show or hide spool material.
- Show or hide spool remaining grams.
- Show or hide status messages.

## Moonraker Data Used

This plugin reads printer information from Moonraker printer object queries and related endpoints.

It can display values such as:

- Print state.
- Current file.
- Virtual SD progress.
- Nozzle temperature.
- Bed temperature.
- Print duration.
- Estimated remaining time.
- Current and total layers when present.
- Active spool ID through Moonraker’s Spoolman integration.

Layer counts may not always be available, depending on slicer metadata and printer configuration.

## Spoolman Support

If your Moonraker instance is configured with Spoolman support, the plugin can also display the currently active spool for each printer.

That can include:

- Spool name.
- Vendor or brand.
- Material.
- Remaining grams.
- Color swatch when available.

If Spoolman is not configured, the rest of the printer status display will still work normally.

## Repository

GitHub repository:

[https://github.com/shadal18/inkypi-klipper-farm-status](https://github.com/shadal18/inkypi-klipper-farm-status)

## Screenshots

- Main plugin display showing printer farm status.
- Plugin settings screen.

<p align="center">
  <img src="screenshots/example.png" width="45%" />
  <img src="screenshots/settings.png" width="45%" />
</p>
