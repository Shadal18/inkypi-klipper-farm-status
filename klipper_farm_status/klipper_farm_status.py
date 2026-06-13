from plugins.base_plugin.base_plugin import BasePlugin
from datetime import datetime
import requests
import json
import base64
import logging

logger = logging.getLogger(__name__)


def to_bool(value, default=False):
    if value is None:
        return default
    return str(value).strip().lower() in ("1", "true", "yes", "on")


def safe_float(value, default=0):
    try:
        if value is None or value == "":
            return default
        return float(value)
    except Exception:
        return default


def safe_int(value, default=0):
    try:
        if value is None or value == "":
            return default
        return int(float(value))
    except Exception:
        return default


def format_seconds(seconds):
    seconds = safe_int(seconds, 0)
    if seconds <= 0:
        return "—"
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    if hours > 0:
        return f"{hours}h {minutes}m"
    return f"{minutes}m"


def format_temp(current, target):
    c = safe_float(current, 0)
    t = safe_float(target, 0)
    if t > 0:
        return f"{round(c)}° / {round(t)}°"
    return f"{round(c)}°"


class KlipperFarmStatus(BasePlugin):
    JSON_TIMEOUT = 8
    IMAGE_TIMEOUT = 12

    def _fetch_json(self, url, timeout=8):
        response = requests.get(url, timeout=timeout)
        response.raise_for_status()
        return response.json()

    def _build_stream_url(self, moonraker_url):
        base = (moonraker_url or "").strip().rstrip("/")
        if not base:
            return ""
        return f"{base}/webcam/?action=stream"

    def _build_snapshot_url(self, moonraker_url):
        base = (moonraker_url or "").strip().rstrip("/")
        if not base:
            return ""
        return f"{base}/webcam/?action=snapshot"

    def _fetch_snapshot_parts(self, snapshot_url):
        if not snapshot_url:
            logger.info("KFS_IMAGE_DEBUG snapshot_url missing")
            return "", ""

        try:
            response = requests.get(snapshot_url, timeout=self.IMAGE_TIMEOUT)
            response.raise_for_status()
            content_type = response.headers.get("content-type", "image/jpeg").strip().lower()
            if not content_type.startswith("image/"):
                content_type = "image/jpeg"
            encoded = base64.b64encode(response.content).decode("ascii")

            logger.info(
                "KFS_IMAGE_DEBUG snapshot ok | url=%s | status=%s | mime=%s | bytes=%s | b64_len=%s",
                snapshot_url,
                response.status_code,
                content_type,
                len(response.content),
                len(encoded),
            )

            return encoded, content_type
        except Exception as e:
            logger.info(
                "KFS_IMAGE_DEBUG snapshot failed | url=%s | error=%s",
                snapshot_url,
                str(e),
            )
            return "", ""

    def _empty_printer(self, name, base="", status_label="Offline", state_class="offline", message=""):
        return {
            "name": name,
            "url": base,
            "stream_url": self._build_stream_url(base),
            "snapshot_url": self._build_snapshot_url(base),
            "snapshot_base64": "",
            "snapshot_mime": "image/jpeg",
            "connected": False,
            "state": "offline",
            "status_label": status_label,
            "state_class": state_class,
            "progress": 0,
            "filename": "",
            "print_duration": 0,
            "total_duration": 0,
            "remaining_seconds": 0,
            "eta": "—",
            "current_layer": None,
            "total_layer": None,
            "extruder_temp": "—",
            "bed_temp": "—",
            "message": message,
            "spool_id": None,
            "spool_name": "",
            "spool_vendor": "",
            "spool_material": "",
            "spool_remaining": None,
            "spool_color": "",
        }

    def _fetch_printer(self, name, moonraker_url, include_spool=True, include_image=True):
        base = (moonraker_url or "").strip().rstrip("/")

        printer = self._empty_printer(name=name, base=base, status_label="Offline", state_class="offline", message="")

        if not base:
            printer["status_label"] = "Missing URL"
            printer["state_class"] = "error"
            printer["message"] = "Moonraker URL not configured"
            logger.info("KFS_PRINTER_DEBUG name=%s | missing moonraker url", name)
            return printer

        query_url = (
            f"{base}/printer/objects/query?"
            "print_stats&display_status&toolhead&extruder&heater_bed&virtual_sdcard&webhooks"
        )

        try:
            data = self._fetch_json(query_url, timeout=12)
            status = data.get("result", {}).get("status", {})
            print_stats = status.get("print_stats", {}) or {}
            display_status = status.get("display_status", {}) or {}
            extruder = status.get("extruder", {}) or {}
            heater_bed = status.get("heater_bed", {}) or {}
            virtual_sdcard = status.get("virtual_sdcard", {}) or {}
            webhooks = status.get("webhooks", {}) or {}

            raw_state = (
                print_stats.get("state")
                or webhooks.get("state")
                or webhooks.get("state_message")
                or "standby"
            )
            raw_state = str(raw_state).strip().lower()

            printer["connected"] = True
            printer["state"] = raw_state

            if raw_state == "printing":
                printer["status_label"] = "Printing"
                printer["state_class"] = "printing"
            elif raw_state == "paused":
                printer["status_label"] = "Paused"
                printer["state_class"] = "paused"
            elif raw_state in ("complete", "completed"):
                printer["status_label"] = "Complete"
                printer["state_class"] = "complete"
            elif raw_state in ("error", "shutdown"):
                printer["status_label"] = "Error"
                printer["state_class"] = "error"
            else:
                printer["status_label"] = "Idle"
                printer["state_class"] = "idle"

            printer["filename"] = (print_stats.get("filename") or "").split("/")[-1]
            printer["progress"] = round(safe_float(virtual_sdcard.get("progress"), 0) * 100)
            printer["print_duration"] = safe_int(print_stats.get("print_duration"), 0)
            printer["total_duration"] = safe_int(print_stats.get("total_duration"), 0)

            total_estimated = safe_int(display_status.get("total_duration"), 0)
            if total_estimated <= 0:
                total_estimated = printer["total_duration"]

            if total_estimated > 0 and printer["print_duration"] > 0:
                remaining = max(total_estimated - printer["print_duration"], 0)
                printer["remaining_seconds"] = remaining
                printer["eta"] = format_seconds(remaining)
            else:
                printer["eta"] = "—"

            current_layer = None
            total_layer = None

            if isinstance(print_stats.get("info"), dict):
                current_layer = print_stats.get("info", {}).get("current_layer")
                total_layer = print_stats.get("info", {}).get("total_layer")

            if current_layer is None and isinstance(display_status.get("info"), dict):
                current_layer = display_status.get("info", {}).get("current_layer")
            if total_layer is None and isinstance(display_status.get("info"), dict):
                total_layer = display_status.get("info", {}).get("total_layer")

            printer["current_layer"] = current_layer
            printer["total_layer"] = total_layer

            printer["extruder_temp"] = format_temp(
                extruder.get("temperature"), extruder.get("target")
            )
            printer["bed_temp"] = format_temp(
                heater_bed.get("temperature"), heater_bed.get("target")
            )
            printer["message"] = (
                webhooks.get("state_message")
                or display_status.get("message")
                or ""
            )

            if include_spool:
                try:
                    spool_data = self._fetch_json(f"{base}/server/spoolman/spool_id", timeout=6)
                    spool_id = spool_data.get("result", {}).get("spool_id")
                    printer["spool_id"] = spool_id

                    if spool_id:
                        spool_detail = self._fetch_json(
                            f"{base}/server/spoolman/proxy/request?method=GET&path=/api/v1/spool/{spool_id}",
                            timeout=8,
                        )
                        result = spool_detail.get("result", {})
                        spool = result if isinstance(result, dict) else {}
                        filament = spool.get("filament", {}) or {}
                        vendor = filament.get("vendor", {}) or {}

                        printer["spool_name"] = filament.get("name") or f"Spool #{spool_id}"
                        printer["spool_vendor"] = vendor.get("name") or filament.get("vendor_name") or ""
                        printer["spool_material"] = filament.get("material") or ""
                        printer["spool_remaining"] = safe_int(spool.get("remaining_weight"), 0)
                        printer["spool_color"] = filament.get("color_hex") or ""
                except Exception as e:
                    logger.info("KFS_SPOOL_DEBUG name=%s | error=%s", name, str(e))

            if include_image:
                snapshot_base64, snapshot_mime = self._fetch_snapshot_parts(printer["snapshot_url"])
                printer["snapshot_base64"] = snapshot_base64
                printer["snapshot_mime"] = snapshot_mime or "image/jpeg"

                if not printer["snapshot_base64"]:
                    cam_msg = f"cam fetch failed: {printer['snapshot_url']}"
                    printer["message"] = f"{printer['message']} | {cam_msg}".strip(" |")

            logger.info(
                "KFS_PRINTER_DEBUG name=%s | state=%s | status_label=%s | snapshot_url=%s | snapshot_len=%s | message=%s",
                name,
                printer["state_class"],
                printer["status_label"],
                printer["snapshot_url"],
                len(printer.get("snapshot_base64") or ""),
                printer.get("message", ""),
            )

        except Exception as e:
            printer["status_label"] = "Error"
            printer["state_class"] = "error"
            printer["message"] = str(e)

            logger.info(
                "KFS_PRINTER_DEBUG name=%s | fetch failed | query_url=%s | error=%s",
                name,
                query_url,
                str(e),
            )

        return printer

    def generate_image(self, settings, device_config):
        title = (settings.get("title") or "Klipper Farm").strip()
        updated_label = datetime.now().strftime("%-I:%M %p")

        raw_printers = settings.get("printers_json", "[]")
        try:
            configured_printers = json.loads(raw_printers)
            if not isinstance(configured_printers, list):
                configured_printers = []
        except Exception:
            configured_printers = []

        printers = []
        include_spool = to_bool(settings.get("show_spool"), True)
        include_image = to_bool(settings.get("show_image"), True)

        logger.info(
            "KFS_RENDER_DEBUG title=%s | printers_configured=%s | include_spool=%s | include_image=%s",
            title,
            len(configured_printers),
            include_spool,
            include_image,
        )

        for idx, printer_cfg in enumerate(configured_printers, start=1):
            enabled = to_bool(printer_cfg.get("enabled"), True)
            if not enabled:
                logger.info("KFS_RENDER_DEBUG skipping disabled printer idx=%s", idx)
                continue

            name = (printer_cfg.get("name") or f"Printer {idx}").strip()
            url = (printer_cfg.get("url") or "").strip()

            printers.append(
                self._fetch_printer(
                    name=name,
                    moonraker_url=url,
                    include_spool=include_spool,
                    include_image=include_image,
                )
            )

        total = len(printers)
        printing = sum(1 for p in printers if p["state_class"] == "printing")
        paused = sum(1 for p in printers if p["state_class"] == "paused")
        offline = sum(1 for p in printers if p["state_class"] == "offline")

        width, height = device_config.get_resolution()
        if device_config.get_config("orientation") == "vertical":
            width, height = height, width

        logger.info(
            "KFS_RENDER_DEBUG total=%s | printing=%s | paused=%s | offline=%s | dimensions=%sx%s",
            total,
            printing,
            paused,
            offline,
            width,
            height,
        )

        return self.render_image(
            dimensions=(width, height),
            html_file="klipper_farm_status.html",
            css_file="klipper_farm_status.css",
            template_params={
                "title": title,
                "updated_label": updated_label,
                "printers": printers,
                "total": total,
                "printing": printing,
                "paused": paused,
                "offline": offline,
                "show_image": include_image,
                "show_progress": to_bool(settings.get("show_progress"), True),
                "show_filename": to_bool(settings.get("show_filename"), True),
                "show_eta": to_bool(settings.get("show_eta"), True),
                "show_layers": to_bool(settings.get("show_layers"), True),
                "show_temps": to_bool(settings.get("show_temps"), True),
                "show_spool": to_bool(settings.get("show_spool"), True),
                "show_spool_vendor": to_bool(settings.get("show_spool_vendor"), True),
                "show_spool_material": to_bool(settings.get("show_spool_material"), True),
                "show_spool_remaining": to_bool(settings.get("show_spool_remaining"), True),
                "show_message": to_bool(settings.get("show_message"), True),
                "plugin_settings": settings,
            },
        )

    def generate_settings_template(self):
        template_params = super().generate_settings_template()
        template_params["style_settings"] = True
        return template_params