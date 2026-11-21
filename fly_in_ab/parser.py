"""Read the map once and reject malformed input with a line number."""

from graph import Connection, MapData, Zone


class Parser:
    """Validate the text format independently of pathfinding."""

    def parse(self, filename: str) -> MapData:
        """Return validated map data or raise a descriptive ValueError."""
        data = MapData()
        seen_links: set[frozenset[str]] = set()
        line_number = 0
        with open(filename, encoding="utf-8-sig") as source:
            for line_number, raw in enumerate(source, 1):
                line = raw.split("#", 1)[0].strip()
                if not line:
                    continue
                try:
                    self.parse_line(line, data, seen_links)
                except ValueError as error:
                    raise ValueError(
                        f"line {line_number}: {error}"
                    ) from error
        for name, value in (("nb_drones", data.nb_drones),
                            ("start_hub", data.start),
                            ("end_hub", data.end)):
            if not value:
                raise ValueError(
                    f"end of file (after line {line_number}): missing {name}"
                )
        return data

    def parse_line(self, line: str, data: MapData,
                   seen_links: set[frozenset[str]]) -> None:
        """Dispatch one meaningful line to its matching parser."""
        key, separator, value = line.partition(":")
        key, value = key.strip(), value.strip()
        if not separator:
            raise ValueError("expected 'key: value'")
        if data.nb_drones == 0 and key != "nb_drones":
            raise ValueError("first meaningful line must define nb_drones")
        if key == "nb_drones":
            if data.nb_drones:
                raise ValueError("duplicate nb_drones")
            data.nb_drones = self.positive_integer(value, key)
        elif key in ("start_hub", "end_hub", "hub"):
            self.parse_zone(key, value, data)
        elif key == "connection":
            self.parse_connection(value, data, seen_links)
        else:
            raise ValueError(f"unknown directive '{key}'")

    @staticmethod
    def integer(value: str, field: str) -> int:
        """Accept decimal integers, including signed coordinates."""
        digits = value.lstrip("+-")
        if (not digits or not digits.isascii() or not digits.isdecimal()
                or value.count("+") + value.count("-") > 1):
            raise ValueError(f"{field} must be an integer")
        return int(value)

    def positive_integer(self, value: str, field: str) -> int:
        """Reject non-integer, zero and negative counts."""
        number = self.integer(value, field)
        if number <= 0:
            raise ValueError(f"{field} must be positive")
        return number

    @staticmethod
    def metadata(raw: str, allowed: set[str]) -> dict[str, str]:
        """Parse one optional bracket block containing key=value tags."""
        if not raw:
            return {}
        if (not raw.startswith("[") or not raw.endswith("]")
                or raw.count("[") != 1 or raw.count("]") != 1):
            raise ValueError("metadata must be one complete [...] block")
        tags: dict[str, str] = {}
        for token in raw[1:-1].split():
            if token.count("=") != 1:
                raise ValueError("metadata must use key=value")
            key, value = token.split("=")
            if key not in allowed:
                raise ValueError(f"unknown metadata key '{key}'")
            if key in tags:
                raise ValueError(f"duplicate metadata key '{key}'")
            if not value:
                raise ValueError(f"missing value for '{key}'")
            tags[key] = value
        return tags

    def parse_zone(self, key: str, value: str, data: MapData) -> None:
        """Validate a zone and register its optional start/end role."""
        parts = value.split(maxsplit=3)
        if len(parts) < 3:
            raise ValueError("zone needs a name and integer x/y coordinates")
        name, x_text, y_text = parts[:3]
        if "-" in name:
            raise ValueError("zone names cannot contain dashes")
        if name in data.zones:
            raise ValueError(f"duplicate zone '{name}'")
        if key == "start_hub" and data.start:
            raise ValueError("duplicate start_hub")
        if key == "end_hub" and data.end:
            raise ValueError("duplicate end_hub")
        tags = self.metadata(parts[3] if len(parts) == 4 else "",
                             {"zone", "color", "max_drones"})
        kind = tags.get("zone", "normal")
        if kind not in ("normal", "restricted", "priority", "blocked"):
            raise ValueError(f"invalid zone type '{kind}'")
        # Subject v3 explicitly ignores max_drones on both endpoints.
        capacity = data.nb_drones
        if key == "hub":
            capacity = self.positive_integer(
                tags.get("max_drones", "1"), "max_drones"
            )
        data.zones[name] = Zone(
            name, self.integer(x_text, "x"), self.integer(y_text, "y"),
            kind, tags.get("color", "none"), capacity
        )
        if key == "start_hub":
            data.start = name
        elif key == "end_hub":
            data.end = name

    def parse_connection(self, value: str, data: MapData,
                         seen: set[frozenset[str]]) -> None:
        """Require defined endpoints and reject reversed duplicate edges."""
        parts = value.split(maxsplit=1)
        if not parts or parts[0].count("-") != 1:
            raise ValueError("connection needs 'zone1-zone2'")
        first, second = parts[0].split("-")
        if first not in data.zones or second not in data.zones:
            raise ValueError("connection references an undefined zone")
        edge = frozenset((first, second))
        if edge in seen:
            raise ValueError(f"duplicate connection '{first}-{second}'")
        tags = self.metadata(parts[1] if len(parts) == 2 else "",
                             {"max_link_capacity"})
        capacity = self.positive_integer(
            tags.get("max_link_capacity", "1"), "max_link_capacity"
        )
        data.connections.append(Connection(first, second, capacity))
        seen.add(edge)
