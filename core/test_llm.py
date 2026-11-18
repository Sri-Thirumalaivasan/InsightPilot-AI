from core.llm_engine import ask_ai


def main():
    print("Starting InsightPilot AI local model test...")

    question = "Explain data analytics in two simple sentences."
    context = (
        "Example dataset: retail sales with Date, Product, Category, "
        "Sales and Profit columns."
    )

    try:
        answer = ask_ai(question, context)
        print("\nINSIGHTPILOT AI RESPONSE:\n")
        print(answer)
        print("\nConnection test completed.")
    except Exception as error:
        print(f"\nOllama connection failed: {error}")
        raise


if __name__ == "__main__":
    main()
