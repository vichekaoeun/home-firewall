import argparse
import subprocess
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
CONFIG_FILE = PROJECT_ROOT / "configs" / "nftables.conf"


def run_command(command, config=None):
    result = subprocess.run(
        command,
        input=config,
        text=True,
        capture_output=True
    )

    if result.stdout:
        print(result.stdout, end="")

    if result.stderr:
        print(result.stderr, end="")

    if result.returncode != 0:
        raise RuntimeError(
            f"Command failed with exit code {result.returncode}"
        )


def validate():
    config = CONFIG_FILE.read_text()

    print("Validating nftables configuration...")

    run_command(
        [
            "docker", "compose", "exec", "-T",
            "firewall", "nft", "-c", "-f", "-"
        ],
        config=config
    )

    print("Configuration is valid.")


def apply():
    validate()

    print("Applying firewall configuration...")

    run_command(
        [
            "docker", "compose", "exec", "-T",
            "firewall", "nft", "-f", "-"
        ],
        config=CONFIG_FILE.read_text()
    )

    print("Firewall configuration applied.")


def status():
    print("Current firewall forwarding rules:")

    run_command([
        "docker", "compose", "exec", "-T",
        "firewall", "nft",
        "list", "chain", "inet", "filter", "forward"
    ])


def main():
    parser = argparse.ArgumentParser(
        description="Network Security Gateway Manager"
    )

    parser.add_argument(
        "action",
        choices=["validate", "apply", "status"]
    )

    args = parser.parse_args()

    try:
        if args.action == "validate":
            validate()
        elif args.action == "apply":
            apply()
        elif args.action == "status":
            status()

    except (RuntimeError, OSError) as error:
        print(f"ERROR: {error}")
        raise SystemExit(1)


if __name__ == "__main__":
    main()
