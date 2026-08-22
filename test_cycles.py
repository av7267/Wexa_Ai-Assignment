from detector.cycles import detect_cycles


def main():
    print("=" * 60)
    print("CYCLE DETECTION TEST")
    print("=" * 60)

    cycles = detect_cycles()

    print(f"Cycles found: {len(cycles)}")
    print()

    for cycle in cycles:
        accounts = cycle["account_sequence"]

        print(
            f"{cycle['hop_count']}-hop: "
            f"{' -> '.join(accounts)}"
            f" -> {accounts[0]}"
        )


if __name__ == "__main__":
    main()