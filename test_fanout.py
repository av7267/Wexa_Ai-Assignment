from detector.fanout import detect_fanout, print_fanout

def main():
    flagged = detect_fanout()
    print_fanout(flagged)

if __name__ == "__main__":
    main()