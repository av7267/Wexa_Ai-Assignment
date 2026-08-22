from detector.cycles import detect_cycles


def main():
    cycles = detect_cycles()

    print("=" * 60)
    print("CYCLE DETECTION TEST")
    print("=" * 60)

    print(f"Cycles found: {len(cycles)}")
    print()

    for cycle in cycles:
        accounts = cycle["account_sequence"]
        hop_count = cycle["hop_count"]

        print(
            f"{hop_count}-hop: "
            + " -> ".join(accounts)
            + f" -> {accounts[0]}"
        )


if __name__ == "__main__":
    main()