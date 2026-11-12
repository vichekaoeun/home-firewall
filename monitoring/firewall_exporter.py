import json
import subprocess
from http.server import BaseHTTPRequestHandler, HTTPServer


def collect_metrics():
    command = [
        "nft", "-j", "list", "chain",
        "inet", "filter", "forward"
    ]

    result = subprocess.run(
        command,
        capture_output=True,
        text=True,
        check=True,
        timeout=3
    )

    data = json.loads(result.stdout)

    totals = {
        "accept": {"packets": 0, "bytes": 0},
        "drop": {"packets": 0, "bytes": 0}
    }

    rule_metrics = []

    rule_number = 0

    for item in data["nftables"]:
        rule = item.get("rule")

        if not rule:
            continue

        rule_number += 1
        expressions = rule.get("expr", [])

        action = next(
            (
                action
                for expression in expressions
                for action in ("accept", "drop")
                if action in expression
            ),
            None
        )

        counter = next(
            (
                expression["counter"]
                for expression in expressions
                if "counter" in expression
            ),
            None
        )

        if action is None or counter is None:
            continue

        packets = counter["packets"]
        byte_count = counter["bytes"]

        totals[action]["packets"] += packets
        totals[action]["bytes"] += byte_count

        rule_metrics.append(
            f'firewall_nftables_rule_packets_total'
            f'{{chain="forward",rule="rule_{rule_number:02}",'
            f'action="{action}"}} {packets}'
        )

    lines = [
        "# HELP firewall_nftables_packets_total Packets accepted or dropped",
        "# TYPE firewall_nftables_packets_total counter",
    ]

    for action, values in totals.items():
        lines.append(
            f'firewall_nftables_packets_total'
            f'{{chain="forward",action="{action}"}} '
            f'{values["packets"]}'
        )

    lines.extend([
        "# HELP firewall_nftables_bytes_total Bytes accepted or dropped",
        "# TYPE firewall_nftables_bytes_total counter",
    ])

    for action, values in totals.items():
        lines.append(
            f'firewall_nftables_bytes_total'
            f'{{chain="forward",action="{action}"}} '
            f'{values["bytes"]}'
        )

    lines.extend([
        "# HELP firewall_nftables_rule_packets_total Packets processed by individual rules",
        "# TYPE firewall_nftables_rule_packets_total counter",
    ])

    lines.extend(rule_metrics)

    lines.extend([
        "# HELP firewall_nftables_exporter_up Whether nftables metrics were collected successfully",
        "# TYPE firewall_nftables_exporter_up gauge",
        "firewall_nftables_exporter_up 1",
    ])

    return "\n".join(lines) + "\n"


class MetricsHandler(BaseHTTPRequestHandler):

    def do_GET(self):
        if self.path != "/metrics":
            self.send_error(404)
            return

        try:
            metrics = collect_metrics().encode()

            self.send_response(200)
            self.send_header(
                "Content-Type",
                "text/plain; version=0.0.4"
            )
            self.send_header("Content-Length", str(len(metrics)))
            self.end_headers()
            self.wfile.write(metrics)

        except Exception:
            self.send_error(500, "Failed to collect nftables metrics")

    def log_message(self, format, *args):
        pass


if __name__ == "__main__":
    server = HTTPServer(("0.0.0.0", 9101), MetricsHandler)

    print("Firewall exporter listening on port 9101")

    server.serve_forever()
