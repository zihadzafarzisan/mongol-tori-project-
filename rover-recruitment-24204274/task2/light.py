"""Print rover status lights: python light.py mission_log.csv targets.csv.

Only Python's standard library is needed. See README.md for anomaly policies.
"""

import argparse
import csv
import math
import sys

EARTH_RADIUS_M = 6_371_000.0
ARRIVAL_RADIUS_M = 3.0
STOP_SPEED_MPS = 0.5
GREEN_SECONDS = 5.0


def haversine(a, b):
    """Great-circle distance in meters between two (latitude, longitude) pairs."""
    lat1, lon1 = map(math.radians, a)
    lat2, lon2 = map(math.radians, b)
    value = (math.sin((lat2 - lat1) / 2) ** 2
             + math.cos(lat1) * math.cos(lat2) * math.sin((lon2 - lon1) / 2) ** 2)
    # Floating-point rounding must not put the square roots outside their domain.
    value = min(1.0, max(0.0, value))
    return 2 * EARTH_RADIUS_M * math.atan2(math.sqrt(value), math.sqrt(1 - value))


def position(row):
    """Return a valid coordinate pair, or None for missing/invalid GPS data."""
    try:
        lat, lon = float(row['lat']), float(row['lon'])
    except (KeyError, TypeError, ValueError):
        return None
    if math.isfinite(lat) and math.isfinite(lon) and -90 <= lat <= 90 and -180 <= lon <= 180:
        return lat, lon
    return None


def csv_rows(stream, required):
    """Read a headered CSV, accepting a BOM and surrounding header whitespace."""
    reader = csv.DictReader(stream, strict=True)
    if reader.fieldnames is None:
        raise ValueError('CSV is empty or has no header')
    headers = [name.lstrip('\ufeff').strip().lower() for name in reader.fieldnames]
    if len(set(headers)) != len(headers):
        raise ValueError('CSV contains duplicate column names')
    missing = set(required) - set(headers)
    if missing:
        raise ValueError('CSV is missing columns: ' + ', '.join(sorted(missing)))
    reader.fieldnames = headers
    for row in reader:
        yield reader.line_num, row


def load_targets(stream):
    """Preserve target file order; never silently skip an invalid objective."""
    targets = []
    for line, row in csv_rows(stream, ('lat', 'lon')):
        target = position(row)
        if target is None or None in row:
            raise ValueError(f'targets line {line}: invalid target record')
        targets.append(target)
    return targets


class LightController:
    """Track the current target and a latched five-second arrival indication."""

    def __init__(self, targets):
        self.targets = targets
        self.target_index = 0
        self.green_until = None
        self.previous_fix = None
        self.latest_time = None
        self.last_mode = 'MANUAL'

    def update(self, timestamp, mode, coordinates):
        if mode in ('AUTO', 'MANUAL'):
            self.last_mode = mode
        baseline = 'red' if self.last_mode == 'AUTO' else 'blue'

        # Emit duplicate/backward records, but never rewind timers or GPS history.
        if self.latest_time is not None and timestamp <= self.latest_time:
            return 'green' if self.green_until is not None else baseline
        self.latest_time = timestamp

        speed = None
        if coordinates is not None:
            if self.previous_fix is not None:
                previous_time, previous_position = self.previous_fix
                speed = haversine(previous_position, coordinates) / (timestamp - previous_time)
            self.previous_fix = timestamp, coordinates

        if self.green_until is not None:
            if timestamp < self.green_until:
                return 'green'
            self.green_until = None
            self.target_index += 1
            # Display the required standard indication when a green period ends.
            # A new target may trigger arrival on a subsequent sample.
            return baseline

        if (mode == 'AUTO'
                and coordinates is not None
                and speed is not None and speed < STOP_SPEED_MPS
                and self.target_index < len(self.targets)
                and haversine(coordinates, self.targets[self.target_index]) <= ARRIVAL_RADIUS_M):
            self.green_until = timestamp + GREEN_SECONDS
            return 'green'
        return baseline


def process_log(stream, targets, output, diagnostics):
    controller = LightController(targets)
    for line, row in csv_rows(stream, ('time_s', 'mode', 'lat', 'lon')):
        raw_time = (row.get('time_s') or '').strip()
        try:
            timestamp = float(raw_time)
            if not math.isfinite(timestamp) or timestamp < 0:
                raise ValueError
        except ValueError:
            print(f'log line {line}: invalid time_s; record omitted', file=diagnostics)
            continue

        mode = (row.get('mode') or '').strip().upper()
        if mode not in ('AUTO', 'MANUAL'):
            print(f'log line {line}: unknown mode; retaining last known mode', file=diagnostics)
            mode = None
        coordinates = position(row)
        if coordinates is None:
            print(f'log line {line}: missing or invalid GPS fix', file=diagnostics)
        if None in row:
            print(f'log line {line}: extra CSV fields; GPS fix ignored', file=diagnostics)
            coordinates = None
        if controller.latest_time is not None and timestamp <= controller.latest_time:
            print(f'log line {line}: non-increasing time; mission state not advanced', file=diagnostics)
        light = controller.update(timestamp, mode, coordinates)
        print(f'{raw_time},{light}', file=output)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mission_log', help='CSV with time_s,mode,lat,lon')
    parser.add_argument('targets', help='CSV with ordered lat,lon targets')
    args = parser.parse_args(argv)
    try:
        with open(args.targets, encoding='utf-8-sig', newline='') as stream:
            targets = load_targets(stream)
        with open(args.mission_log, encoding='utf-8-sig', newline='') as stream:
            process_log(stream, targets, sys.stdout, sys.stderr)
    except (OSError, UnicodeError, csv.Error, ValueError) as error:
        parser.exit(2, f'light.py: {error}\n')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
