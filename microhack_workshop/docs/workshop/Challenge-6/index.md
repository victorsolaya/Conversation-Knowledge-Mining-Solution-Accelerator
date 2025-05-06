# Evaluation

## Content Safety Evaluation

This notebook demonstrates how to evaluate content safety using Azure AI's evaluation tools. It includes steps to:

* Simulate content safety and grounded scenarios.
* Evaluate content for safety metrics such as violence, sexual content, hate/unfairness, and self-harm.
* Generate evaluation reports in JSON format.

### Prerequisites
- Azure AI project credentials.
- [Python 3.9+](https://www.python.org/downloads/)
- Python environment with required libraries installed (`azure-ai-evaluation`, `pandas`, etc.).
- Access to the Azure API endpoint.

If you already set up a virtual environment in **Challenge 3-4**, skip to step 4 below. Otherwise, please follow the steps below to set up your virtual environment and run the notebook. 
1. Navigate to the `workshop` folder in the terminal in your local repository and run the following commands 
2. Open the `.env.sample` to update the variables with the details of your solution. Remeber to save the file after filling in the details.  
    - Rename the file to `.env` and save it.

3. In the terminal run the following commands 

* Create a virtual environment
```shell
python -m venv .venv
```
* Activate the virtual environment
```shell
.venv\Scripts\activate
```
* Install the requirements
```shell
pip install -r requirements.txt
```
4. In the `Challenge-6` folder open the [Content_safety_evaluation notebook](./Content_safety_evaluation.ipynb) 
5. In the first cell, update your `api_url`. This can be found by going to the [Azure Portal](https://portal.azure.com/) and navigating to the resource group you are using for this workshop. 
    - Find the App Service ending in `-api`. Open the app service and copy the default domain. Past the default domain in the `api_url` variable in the first cell. 
        - Your `api_url` should look like the following `api_url = "<default domain>/api/chat"`
6. Run the first cell to create a folder for the output file of the evaluations.
7. Run cells 2-4 to initialize your Azure AI Project, the call streaming function and callback function. 
8. Cell 5 run the Adversarial Scenario to generate questions, run the questions against your AI solution and write these results to a local file. Cell 6 will format the output of the results.  
    - The Adversarial Scenario will run content safety evaluation tests on your AI solution 
9. Cell 7 and 8 initialize the model configuration and the Groundedness Evaluator. The groundedness measure assesses the correspondence between claims in an AI-generated answer and the source context, making sure that these claims are substantiated by the context. 
    - Learn more about the groundedness evaluator [here](https://learn.microsoft.com/en-us/azure/ai-foundry/how-to/develop/evaluate-sdk#performance-and-quality-evaluator-usage)
