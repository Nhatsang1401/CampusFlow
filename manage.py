#!/usr/bin/env python
"""Command-line utility for Django project management."""

import os
import sys


def main():
    """Run administrative tasks."""
    os.environ.setdefault(
        "DJANGO_SETTINGS_MODULE",
        "config.settings.development",
    )

    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Không thể tải Django. Hãy kiểm tra môi trường ảo và cài đặt dependencies."
        ) from exc

    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
