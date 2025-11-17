from __future__ import annotations

from athena.core.agent import get_default_agent


def main() -> None:
    agent = get_default_agent()
    user_id = "default"
    print("Athena v1 CLI. Type 'exit' to quit.")

    while True:
        try:
            text = input("you > ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break

        if text.lower() in {"exit", "quit"}:
            break

        if not text:
            continue

        reply = agent.run(user_id=user_id, new_user_message=text)
        print(f"athena > {reply}")


if __name__ == "__main__":
    main()

