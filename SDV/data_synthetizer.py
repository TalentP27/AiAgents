import pandas as pd
import warnings
from sdv.metadata import Metadata
from sdv.evaluation.single_table import run_diagnostic
from sdv.single_table import GaussianCopulaSynthesizer
from sdv.evaluation.single_table import get_column_plot
from sdv.evaluation.single_table import evaluate_quality

# Suppress warnings
warnings.filterwarnings("ignore")

# Load the data
real_data = pd.read_csv('Data/E-Commerce Dataset.csv', nrows=500)

# Initialize variables
metadata = None
synthetic_data = None
quality_report_result = None

def synthetize_data():
    # Automatically detects and creates metadata (structure & types) from the data.
    global metadata
    metadata = Metadata.detect_from_dataframe(real_data)

    # Initializes the synthetic data generator using Gaussian Copula model.
    synthesizer = GaussianCopulaSynthesizer(metadata)

    # Trains the synthesizer to learn patterns from the real data.
    synthesizer.fit(real_data)

    # Generates new synthetic rows based on the learned data patterns.
    global synthetic_data
    synthetic_data = synthesizer.sample(num_rows=500)

    # Saves the synthetic data to a CSV file without row indices.
    synthetic_data.to_csv('Data/synthetic_data.csv', index=False)

def diagnostic_report():
    # Run a diagnostic to ensure that the data is valid
    diagnostic = run_diagnostic(
        real_data=real_data,
        synthetic_data=synthetic_data,
        metadata=metadata
    )

def quality_report():
    # Measure the data quality or the statistical similarity between the real and synthetic data
    global quality_report_result
    quality_report_result = evaluate_quality(
        real_data,
        synthetic_data,
        metadata
    )

def column_plot():
    global quality_report_result
    if quality_report_result is None:
        print("Quality report not generated yet. Generating now...")
        quality_report()
    print('Columns from highest to lowest quality score:')
    print('-----------------------------------------------------------')
    print(quality_report_result.get_details('Column Shapes'))

def visualize_data():
    # Visualize comparing a column (PreferedOrderCat) of the real data to the synthetic data.
    fig = get_column_plot(
        real_data=real_data,
        synthetic_data=synthetic_data,
        column_name='PreferedOrderCat',
        metadata=metadata
    )

    fig.show()

if __name__ == "__main__":
    print("""
        What is the objective of the Data you want to synthetize (Type the number of the objective):
            1. Schema replication
            2. Realism + variety
            3. Narrative fields (e.g., reviews, support tickets)
        Want to know the difference between the objectives? Type 'help'
    """)
    while True:
        user_input = input("Type your choice: ")
        if user_input == 'help':
            print("""
                1. Schema replication: Ensures the synthetic data matches the structure (columns, data types, constraints) of the original dataset.

                2. Realism + variety: Focuses on making the synthetic data look realistic and diverse, capturing patterns and variability seen in real data.

                3. Narrative fields: Involves generating coherent, human-like text for fields such as reviews or support tickets, requiring natural language understanding and generation.

            """)
        elif user_input == '1':
            synthetize_data()
            print("Data synthetized successfully, view file 'Data/synthetic_data.csv'")
            print("""
                What do you want to do next?
                    1. View the diagnostic report
                    2. View the quality report
                    3. View the column plot
                    4. Visualize the data
            """)
            while True:
                user_input = input("Type your choice: ")
                if user_input == '1':
                    diagnostic_report()
                elif user_input == '2':
                    quality_report()
                elif user_input == '3':
                    column_plot()
                elif user_input == '4':
                    visualize_data()
                else:
                    print("Invalid input")
        else:
            print("Invalid input")