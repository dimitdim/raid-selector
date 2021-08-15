"""RAID Drive Selector"""
import argparse
import json
from dataclasses import asdict
from dataclasses import dataclass
from pathlib import Path
from typing import Dict
from typing import List

DEFAULT_RAID_LEVEL = "RAID5"


@dataclass
class Combo:
    """Combination of drives for RAID"""

    drive_count: int
    unit_capacity: float
    unit_price: float
    raid_level: str = DEFAULT_RAID_LEVEL

    @property
    def total_capacity(self) -> float:
        """Total RAID  Capacity"""

        if self.raid_level in ["RAID0"]:
            return self.unit_capacity * self.drive_count
        if self.raid_level in ["RAID1"]:
            return self.unit_capacity
        if self.raid_level in ["RAID3", "RADI4", "RAID5"]:
            return self.unit_capacity * (self.drive_count - 1)
        if self.raid_level in ["RAID6"]:
            return self.unit_capacity * (self.drive_count - 2)
        raise ValueError(f"Unknown RAID Level {self.raid_level}")

    @property
    def total_price(self) -> float:
        """Total price of all drives"""

        return self.unit_price * self.drive_count


def parse_args() -> argparse.Namespace:
    """Parse arguments"""

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "input_filepath", type=Path, help="Path to JSON of pricing information"
    )
    parser.add_argument("max_drive_count", type=int, help="Maximum number of drives")
    parser.add_argument(
        "-o",
        "--output_filepath",
        default=None,
        type=Path,
        help="Path for JSON of ranked combinations",
    )
    parser.add_argument(
        "-m", "--min_drive_count", default=3, type=int, help="Minimum number of drives"
    )
    parser.add_argument(
        "-r", "--raid_level", default=DEFAULT_RAID_LEVEL, type=str, help="RAID Leve"
    )

    return parser.parse_args()


def rank_combinations(
    prices: Dict[float, float],
    min_drive_count: int,
    max_drive_count: int,
    raid_level: str = DEFAULT_RAID_LEVEL,
) -> List[Combo]:
    """Find best combinations of drives for RAID"""

    all_combos: Dict[float, List[Combo]] = {}
    for drive_count in range(min_drive_count, max_drive_count + 1):
        for unit_capacity, unit_price in prices.items():
            combo = Combo(drive_count, unit_capacity, unit_price, raid_level)
            total_capacity = combo.total_capacity
            if total_capacity not in all_combos:
                all_combos[total_capacity] = []
            all_combos[total_capacity].append(combo)

    ranked_combos: List[Combo] = []
    for total_capacity, combos in sorted(all_combos.items(), reverse=True):
        min_price = min([combo.total_price for combo in combos])
        if len(ranked_combos) > 0 and min_price > ranked_combos[-1].total_price:
            continue
        cheapest_combos = [combo for combo in combos if combo.total_price == min_price]
        min_drive_count = min([combo.drive_count for combo in cheapest_combos])
        tightest_combos = [
            combo for combo in cheapest_combos if combo.drive_count == min_drive_count
        ]
        ranked_combos.append(tightest_combos[0])  # List will always be of length 1

    return ranked_combos


def main() -> None:
    """Main function"""

    args = parse_args()

    with args.input_filepath.open("r") as input_file:
        prices = {
            float(unit_capacity_str): unit_price
            for unit_capacity_str, unit_price in json.load(input_file).items()
        }

    ranked_combos = rank_combinations(
        prices, args.min_drive_count, args.max_drive_count, args.raid_level
    )

    if args.output_filepath is not None:
        with args.output_filepath.open("w") as output_file:
            json.dump([asdict(combo) for combo in ranked_combos], output_file)

    for combo in ranked_combos:
        print(
            f"{combo.drive_count}x {combo.unit_capacity}TB Drives = "
            f"{combo.total_capacity}TB:\t${round(combo.total_price, 2)} "
            f"(${round(combo.total_price/combo.total_capacity, 2)}/TB)"
        )


if __name__ == "__main__":
    main()
