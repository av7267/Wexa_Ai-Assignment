from detector.queries import detect_cycles


results = detect_cycles()

print(f"Cycles found: {len(results)}")

for cycle in results:
    print(
        f"{cycle['hop_count']}-hop: "
        f"{' -> '.join(cycle['account_sequence'])}"
        f" -> {cycle['account_sequence'][0]}"
    )