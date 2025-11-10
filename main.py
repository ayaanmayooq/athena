from agent.core import run_agent

def main():
    print("athena ready. Type 'exit' to quit.")
    while True:
        user_input = input("\nYou: ").strip()
        if user_input.lower() in {"exit", "quit"}:
            print("Athena: disengaged.")
            break
        result = run_agent(user_input)
        print(f"\nAgent: {result}")

if __name__ == "__main__":
    main()
