from detector.convergence import detect_convergence, print_convergence

def main():
    flagged = detect_convergence()
    print_convergence(flagged)

if __name__ == "__main__":
    main()