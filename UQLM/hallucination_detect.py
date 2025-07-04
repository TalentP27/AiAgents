import asyncio
import pandas as pd
from uqlm import BlackBoxUQ
from uqlm.utils import load_example_dataset, math_postprocessor
from langchain_openai import ChatOpenAI

async def main():
    # Load example dataset (SVAMP)
    svamp = load_example_dataset("svamp", n=5)
    print('--------------------------------Questions--------------------------------')
    for q in svamp['question']:
        print(q)
    print('-------------------------------------------------------------------------')

    # Define math problem prompts
    MATH_INSTRUCTION = "When you solve this math problem only return the answer with no additional text.\n"
    prompts = [MATH_INSTRUCTION + q for q in svamp.question]

    # Initialize OpenAI GPT-3.5 Turbo model
    llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0)

    # Create BlackBoxUQ object with the model
    bbuq = BlackBoxUQ(llm=llm)

    # Generate answers and uncertainty (confidence) estimates
    results = await bbuq.generate_and_score(prompts)

    # Convert results to a DataFrame
    df = results.to_df()

    print("Available columns:", df.columns.tolist())
    print(df.head())

    # Postprocess model output answers for cleaner results
    if "response" in df.columns:
        df['processed_output'] = df['response'].apply(math_postprocessor)
    elif "generation" in df.columns:
        df['processed_output'] = df['generation'].apply(math_postprocessor)
    else:
        print("No expected output column found.")

    # Print confidence scores (uncertainty quantification)
    if 'uncertainty' in df.columns:
        print("\nConfidence/Uncertainty scores:")
        print(df['uncertainty'])

if __name__ == "__main__":
    asyncio.run(main())
