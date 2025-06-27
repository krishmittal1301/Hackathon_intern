import os
import sys
import pandas as pd
import numpy as np
from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential
from pathlib import Path
from datetime import datetime
from scipy import stats
from json_to_csv import json_to_dataframe

# Global DataFrames - load once at module level from CSV

merged_df = pd.read_csv("final_merged_with_questions.csv")

# Create KPI scores dataframe (equivalent to the Excel KPI_Scores sheet)
kpi_columns = ['Sales_and_Marketing', 'Cloud_Strategy', 'Business_model', 'Solution_Area_Focus', 
               'Cloud_Services', 'Cloud_Tooling', 'KPI_Strat', 'KPI_AI', 'KPI_Copilot', 'KPI_SEC', 
               'KPI_Scale', 'KPI_Data', 'AIDW_AI_Index', 'AIDW_DB_Index', 'AIDW_Inno_Index', 
               'Business_Capability', 'Technical_Capability', 'AIDW_Index', 'Partner_PTI', 'AIDW_ready']
kpi_scores_df = merged_df[['Partner_ID'] + kpi_columns].set_index('Partner_ID')

# Create question scores dataframe (equivalent to the Excel Question_Scores sheet)
question_answer_columns = [col for col in merged_df.columns if col.endswith('_Answer') and not col.endswith('_Answer_text') and not col.endswith('_Answer_question')]
question_scores_df = merged_df[['Partner_ID', 'TPID'] + question_answer_columns].copy()

# Create question mapping dictionary from the CSV data
question_text_columns = [col for col in merged_df.columns if col.endswith('_Answer_question')]
question_dict = {}
for col in question_text_columns:
    question_code = col.replace('_Answer_question', '_Answer')
    # Get the first non-null question text for this question code
    question_text = merged_df[col].dropna().iloc[0] if not merged_df[col].dropna().empty else question_code
    question_dict[question_code] = question_text

# Function to reload data from CSV file
def reload_data():
    """Reload all data from CSV file"""
    global merged_df, kpi_scores_df, question_scores_df, question_dict
    merged_df = pd.read_csv("final_merged_with_questions.csv")
    
    # Recreate KPI scores dataframe
    kpi_columns = ['Sales_and_Marketing', 'Cloud_Strategy', 'Business_model', 'Solution_Area_Focus', 
                   'Cloud_Services', 'Cloud_Tooling', 'KPI_Strat', 'KPI_AI', 'KPI_Copilot', 'KPI_SEC', 
                   'KPI_Scale', 'KPI_Data', 'AIDW_AI_Index', 'AIDW_DB_Index', 'AIDW_Inno_Index', 
                   'Business_Capability', 'Technical_Capability', 'AIDW_Index', 'Partner_PTI', 'AIDW_ready']
    kpi_scores_df = merged_df[['Partner_ID'] + kpi_columns].set_index('Partner_ID')
    
    # Recreate question scores dataframe
    question_answer_columns = [col for col in merged_df.columns if col.endswith('_Answer') and not col.endswith('_Answer_text') and not col.endswith('_Answer_question')]
    question_scores_df = merged_df[['Partner_ID', 'TPID'] + question_answer_columns].copy()
    
    # Recreate question mapping dictionary
    question_text_columns = [col for col in merged_df.columns if col.endswith('_Answer_question')]
    question_dict = {}
    for col in question_text_columns:
        question_code = col.replace('_Answer_question', '_Answer')
        question_text = merged_df[col].dropna().iloc[0] if not merged_df[col].dropna().empty else question_code
        question_dict[question_code] = question_text

# function for getting response from CSV data
def prepare_partner_summary(partner_id: int):
    try:
        # Get the partner's KPI scores
        partner_kpis = kpi_scores_df.loc[partner_id]
    except KeyError:
        print("Available Partner IDs:", kpi_scores_df.index.tolist())
        raise ValueError(f"Partner ID {partner_id} not found in KPI scores. Please check the available IDs above.")
    
    # Get the partner's question scores
    partner_questions = question_scores_df[question_scores_df['Partner_ID'] == partner_id]
    if partner_questions.empty:
        raise ValueError(f"Partner ID {partner_id} not found in Question scores")
    partner_questions = partner_questions.iloc[0]
    
    # Get TPID from question scores
    tpid = partner_questions['TPID']
    
    # Prepare the summary text in the requested format
    summary_text = f"""Chosen Partner: {partner_id} with TPID: {tpid}

KPI Scores:"""
    
    # Add KPI scores to summary, ensuring AIDW_ready is included
    for kpi, score in partner_kpis.items():
        if kpi == 'AIDW_ready':
            # Handle AIDW_ready as a string value
            summary_text += f"\n{kpi}: {score}"
        elif isinstance(score, (int, float)) and not np.isnan(score):   # here we check if the score is a number(!) and not NaN
            summary_text += f"\n{kpi}: {score:.2f}"
    
    summary_text += "\n\nQuestion replies:"
    
    # Add question scores to summary with full question text and numbering
    for i, (question_code, score) in enumerate(partner_questions.items(), 1):
        if question_code not in ['Partner_ID', 'TPID']:
            # Get the full question text from mapping, if available
            full_question = question_dict.get(question_code, question_code)  # Use code as fallback
            summary_text += f"\n{i}. {full_question}: {score}"
    
    return summary_text

project_client = AIProjectClient(
    credential=DefaultAzureCredential(),
    endpoint=os.getenv("AZURE_ENDPOINT")
)

# Function to initialize that specific Azure AI agent
def initialize_agent():
    """Initialize the Azure AI agent and verify its existence"""
    project_client = AIProjectClient(
        credential=DefaultAzureCredential(),
        endpoint=os.getenv("AZURE_ENDPOINT")
    )
    agent_id = os.getenv("AZURE_AGENT_ID")

    return project_client, agent_id

class ResponseWrapper:
    def __init__(self, text):
        self.text = type("TextValue", (), {"value": text})()

# Function to send a message to the agent and get the response
def send_message_to_agent(project_client, thread_id: str, agent_id: str, content: str):
    """Send a message to the agent and get the response"""
    message = project_client.agents.messages.create(
        thread_id=thread_id,
        role="user",
        content=content
    )
    print(f"Sent message, ID: {message.id}")
    
    run = project_client.agents.runs.create_and_process(thread_id=thread_id, agent_id=agent_id)
    print(f"Run finished with status: {run.status}")
    
    if run.status == "failed":
        raise RuntimeError(f"Run failed: {run.last_error}")
    
    messages = project_client.agents.messages.list(thread_id=thread_id)
    for message in messages:
        if message.text_messages:
            # print(f"{message.role}: {message.text_messages[-1].text.value}")
            return message.text_messages[-1]
    return None




# Function to save the conversation history to a text file
def save_conversation_to_text(conversation_history, partner_id: int) -> Path:
    """Save the conversation history to a single text file in output directory"""
    # Create output directory if it doesn't exist
    output_dir = Path.cwd() / "output"
    output_dir.mkdir(exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    output_file = output_dir / f"partner_{partner_id}_analysis_{timestamp}.txt"
    
    with output_file.open('w', encoding='utf-8') as f:
        f.write(f"Analysis for Partner {partner_id}\n")
        f.write(f"Generated on: {timestamp}\n")
        f.write("="*80 + "\n\n")
        
        # Write initial summary first (it's in the first conversation turn)
        if conversation_history:
            f.write("=== Initial Summary ===\n\n")
            f.write(conversation_history[0]["user"])  # This contains prepare_partner_summary output
            f.write("\n\n" + "="*80 + "\n\n")
        
        # Write only assistant responses for subsequent turns
        for turn in conversation_history[1:]:  # Skip the first turn as we already handled it
            section_name = turn.get('name', 'Analysis')  # Get the specific name from the turn
            f.write(f"=== {section_name} ===\n\n")
            f.write(turn["assistant"])
            f.write("\n\n" + "="*80 + "\n\n")
    
    print(f"\nAnalysis saved to: {output_file.absolute()}")
    return output_file

# Function to prepare comparison statistics for a specific partner
def prepare_comparison_stats(partner_id: int) -> str:
    """
    Prepares comparison statistics text including the percentile of the chosen partner for each KPI.
    Returns formatted string ready to be used in the prompts.
    """
    # Get partner's scores
    try:
        partner_scores = kpi_scores_df.loc[partner_id]
    except KeyError:
        raise ValueError(f"Partner ID {partner_id} not found in KPI scores")
    
    comparison_text = "Statistics of all partners:\n"
    
    # List of KPIs to analyze
    kpis = [
        'Sales_and_Marketing', 'Cloud_Strategy', 'Business_model', 
        'Solution_Area_Focus', 'Cloud_Tooling', 'KPI_Strat',
        'KPI_AI', 'KPI_Copilot', 'KPI_Scale', 'KPI_Data',
        'AIDW_AI_Index', 'AIDW_DB_Index', 'AIDW_Inno_Index',
        'Business_Capability', 'AIDW_Index', 'Partner_PTI'
    ]
    
    for kpi in kpis:
        if kpi not in kpi_scores_df.columns:
            continue
            
        # Calculate statistics
        mean = kpi_scores_df[kpi].mean()
        std = kpi_scores_df[kpi].std()
        p25 = kpi_scores_df[kpi].quantile(0.25)
        p75 = kpi_scores_df[kpi].quantile(0.75)
        
        # Calculate partner's percentile
        partner_value = partner_scores[kpi]
        partner_percentile = int(stats.percentileofscore(kpi_scores_df[kpi].dropna(), partner_value))
        
        # Format the text
        comparison_text += (
            f" {kpi}: Mean - {mean:.2f}, "
            f"Standard Deviation - {std:.2f}, "
            f"25th percentile - {p25:.2f}, "
            f"75th percentile - {p75:.2f}, "
            f"Partner Score - {partner_value:.2f} "
            f"(at {partner_percentile}th percentile)\n"
        )
    
    return comparison_text

######### Getting the resoponce from the agent and saving it #########

# step before running the code:
# 1. activate the environment .venv\scripts\activate
# 2. in powershell run the command: az login     and then, select the subscription you want to use (or press enter to use the default one)
# 3. set the environment variable AZURE_CONNECTION_STRING with the connection string of your project
#    i.e. code to run: $env:AZURE_CONNECTION_STRING = "" set here the connection string of your project
# 4. run the script in powershell: python chat_paiti.py

def main():
    try:
        # Optionally reload data before processing
        reload_data()     # uncomment this line if you want to reload data from Excel files (e.g. when data is updated). Cuz data is saved in global variables, you can use it without reloading
        
        project_client, agent_id = initialize_agent()
        
        # Initialize conversation history
        conversation_history = []
        partner_id = 1  # Replace with your partner ID

        # Prepare summary before entering context
        summary = prepare_partner_summary(partner_id)
        
        # All Azure client operations within a single context manager
        with project_client:
            # Create thread
            thread_id = os.getenv("AZURE_THREAD_ID")
            thread = project_client.agents.threads.get(thread_id)
            print(f"Created thread, ID: {thread.id}")
            
            # Define all prompts
            prompts = [
                {"name": "Initial Summary", "content": f"""For this prompt, just consume the text. I need your output from the next prompt.
                {summary}"""},
                
                {"name": "Strength Analysis", "content": """
                [Response Language: German (just like mentioned in instructions)]
                Based on the previous evaluation summary, generate a detailed analysis of the customer's strengths. Your response must include exactly 5-6 distinct strengths. 

                For each strength:
                - Start with a bolded headline stating the name of the strength (use Markdown formatting: **Strength Name**)
                - Follow this with a single, well-developed paragraph (5-7 sentences) explaining:
                - What this strength is
                - What it means having this strength
                - What it enables them to do
                - How it impacts partner's customers or business performance
                - Market relevance of this strength
                - How transformative is this strength manifested in the partner's answers
                - How disruptive is this strength manifested in the partner's answers
                

                Do not use bullet points, line breaks, or numbered lists within paragraphs. Ensure each paragraph covers a unique aspect without repeating the same ideas.
                Use the following format:
                 
                **Strength #1 headline**:  
                [Paragraph about this strength.]

                **Strength #2 headline**:  
                [Paragraph about this strength.]
                 
                (and so on until Strength #5)
                """},
                
                {"name": "Weakness Analysis", "content": """
                [Response Language: German (just like mentioned in instructions)]
                Based on the previous evaluation summary, generate a detailed analysis of the customer's weaknesses. Your response must include exactly 5-6 distinct weaknesses. 

                For each weakness:
                - Start with a bolded headline stating the name of the weakness (use Markdown formatting: **Weakness Name**)
                - Follow this with a single, well-developed paragraph (5-7 sentences) explaining:
                - What this weakness is
                - What it means having this weakness
                - What it limits them to do
                - How it impacts their customers or business performance

                Do not use bullet points, line breaks, or numbered lists within paragraphs. Ensure each paragraph covers a unique aspect without repeating the same ideas.
                Use the following format:
                 
                **Weakness #1 headline**:  
                [Paragraph about this weakness.]

                **Weakness #2 headline**:  
                [Paragraph about this weakness.]
                 
                (and so on until Weakness #5)
                """},

                {"name": "Opportunity Assessment", "content": """
                [Response Language: German (just like mentioned in instructions)]
                Based on the previous evaluation summary, generate a detailed analysis of the customer's business opportunities emerging from their identified strengths. Your response must include exactly same amount of distinct opportunities as strengths.

                For each opportunity:
                - Start with a bolded headline stating the name of the opportunity (use Markdown formatting: **Opportunity Name**)
                - Follow this with a single, well-developed paragraph (5-7 sentences) explaining:
                - What business opportunity arises from the corresponding strength
                - What it would enable the partner to achieve if they effectively exploit this strength
                - How it could positively impact partner's customers or overall business performance after leveraging this strength

                Do not use bullet points, line breaks, or numbered lists within paragraphs. Ensure each paragraph covers a unique aspect without repeating the same ideas.

                Use the following format:

                **Opportunity #1 headline**:  
                [Paragraph about this opportunity.]

                **Opportunity #2 headline**:  
                [Paragraph about this opportunity.]

                (and so on until Opportunity #5)
                """},

                {"name": "Comparison to other partners", "content": f"""
                [Response Language: German (just like mentioned in instructions)]
                {prepare_comparison_stats(partner_id)}

                Based on the summary statistics of all partner results and selected partner, generate a detailed analysis focusing on the partner's top 3 best-performing and bottom 3 worst-performing KPIs. 
                Focus primarily on the following KPIs: KPI_Strat, KPI_AI, KPI_Copilot, KPI_SEC, KPI_Scale, KPI_Data, AIDW_Index and AIDW_ready, Business_Capability, Technical_Capability. Avoid focusing on AIDW_AI_Index, AIDW_DB_Index and AIDW_Inno_Index as seperate area of focus.
                Keep the language simple avoiding statistics jargon, and focus on clear, simple comparison. E.g. instead of specific percentile, say in top x% performers.

                First analyze the 3 strongest KPIs (where the partner performs best relative to other partners), then the 3 weakest KPIs (where the partner shows the most room for improvement). For each KPI:
                - Start with a bolded headline stating the KPI name (use Markdown formatting: **KPI Name - Strong/Weak Performance**)
                - Follow this with a single, well-developed paragraph (5-7 sentences) explaining:
                - The partner's performance in this KPI relative to other partners
                - What this performance level means for the partner's business
                - How this impacts their market position
                - Specific recommendations for maintaining strength or improving weakness
                - General maturity level in this area

                Do not use bullet points, line breaks, or numbered lists within paragraphs. Ensure each paragraph covers a unique aspect without repeating the same ideas.
                Use the following format:

                ### Top 3 Strongest KPIs:

                **KPI #1 - Area of Excellence**:  
                [Paragraph about this KPI's strong performance.]

                **KPI #2 - Area of Excellence**:  
                [Paragraph about this KPI's strong performance.]

                **KPI #3 - Area of Excellence**:  
                [Paragraph about this KPI's strong performance.]

                ### Top 3 Areas for Improvement:

                **KPI #1 - Development Area**:  
                [Paragraph about this KPI's weak performance.]

                **KPI #2 - Development Area**:  
                [Paragraph about this KPI's weak performance.]

                **KPI #3 - Development Area**:  
                [Paragraph about this KPI's weak performance.]
                """},

                {"name": "Recommendation Assessment", "content": """
                [Response Language: German (just like mentioned in instructions)]                
                Based on the previous evaluation summary, generate a detailed set of actionable recommendations for the customer. Your recommendations must be divided into two distinct sections:

                1. **Recommendations for Weaknesses**  
                2. **Recommendations for Opportunities**

                The number of recommendations in each section must directly correspond to the number of weaknesses and opportunities identified in the previous analysis. For example, if five weaknesses were identified, provide five recommendations in the 'Recommendations for Weaknesses' section. If six opportunities were identified, provide six recommendations in the 'Recommendations for Opportunities' section.

                For each recommendation:
                - Clearly state which specific weakness or opportunity it addresses (or both, if applicable)
                - Start with a bolded headline naming the recommendation (use Markdown formatting: **Recommendation Name**)
                - Follow this with a single, well-developed paragraph (5-7 sentences) explaining:
                    - What the recommendation involves
                    - Why it is relevant for the customer, based on the identified weakness or opportunity
                    - How it will help address that weakness or exploit that opportunity
                    - The expected business or customer impact after implementation
                    - Give me estimated effort and time to implement this recommendation in terms of short-term (1 month), mid-term (3-6 months) or long-term (6-12 months) horizon
                    - Give me estimation on how sales relevant this recommendation is, in terms of high, medium or low sales relevance

                 
                Each recommendation must include **at least one specific, concrete suggestion**, such as:
                - Relevant Microsoft training programs
                - Microsoft Certification courses
                - Microsoft Workshops
                - Microsoft Internal process improvements
                - Microsoft Strategic initiatives

                You have access to the connected knowledge base of available programs, certificates, and resources, and should suggest the most relevant and up-to-date options in each case.

                Do not use bullet points, line breaks, or numbered lists within paragraphs. Ensure each paragraph covers a unique recommendation without repeating ideas.

                Use the following format:

                ### Recommendations for Weaknesses:

                **Recommendation #1 headline**:  
                [Paragraph about this recommendation.]

                **Recommendation #2 headline**:  
                [Paragraph about this recommendation.]

                (Continue until a recommendation is provided for each identified weakness.)

                ### Recommendations for Opportunities:

                **Recommendation #1 headline**:  
                [Paragraph about this recommendation.]

                **Recommendation #2 headline**:  
                [Paragraph about this recommendation.]

                (Continue until a recommendation is provided for each identified opportunity.)

                """},

                {"name": "Summary Assessment", "content": """
                [Response Language: German (just like mentioned in instructions)]                
                Generate a detailed strategic assessment for the partner regarding its current position and future potential as a partner in the Microsoft ecosystem. The document should be titled as 'Summary of [partner ID]', and discuss the following key elements in precise and formal German language:
                 
                 A summary of partner's current performance and positioning, highlighting its strengths and unique differentiators within the market and the Microsoft partner ecosystem.
                 Five strategic dimensions with separate paragraphs – People, AI, Innovation, Transformation, and Impact (PAITI) – described in detail as a framework for the company's necessary AI transformation. Under each dimension, provide actionable recommendations tailored for achieving leadership and excellence. Include insights on relevant Microsoft programs, technologies, and opportunities to develop competitive advantage.
                 Performance metrics: Summarize the company's KPIs. Compare these to other partners benchmark and specify areas where the company excels or falls short.
                 A concluding summary, emphasizing partner's potential to emerge as a leading Microsoft partner in the AI & Cloud space. Include a motivational call to action, supported by previously discussed points, that encourages the company to capitalize on its strengths and actively pursue the outlined recommendations.
                 
                 Use clear and concise language with a professional tone. Ensure the text acknowledges partner's current achievements while providing a constructive critique of areas for improvement, backed by data. Close with an optimistic outlook that inspires confidence in partner's future success.

                 Also, consider the following context (ignore if no bulletpoints below):
                 -
                """}
            ]
            
            # Send all messages within the same context
            # Batch file writing instead of writing after each response
            responses_buffer = []
            for prompt in prompts:
                response = send_message_to_agent(project_client, thread.id, agent_id, prompt['content'])
                # Add to responses_buffer for backup
                responses_buffer.append({
                    "name": prompt['name'],
                    "content": response.text.value,
                    "timestamp": datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
                })
                # Add to conversation history
                conversation_history.append({
                    "name": prompt['name'],
                    "user": prompt['content'],
                    "assistant": response.text.value
                })

            # Write all responses at once
            timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

            # Create output and backup directories
            output_dir = Path.cwd() / "output"
            backup_dir = output_dir / "backup"
            output_dir.mkdir(exist_ok=True)
            backup_dir.mkdir(exist_ok=True)

            # Create backup file in the backup directory
            backup_file = backup_dir / f"backup_responses_{partner_id}_{timestamp}.txt"
            with open(backup_file, "w", encoding='utf-8') as f:
                for resp in responses_buffer:
                    f.write(f"\n=== {resp['name']} at {resp['timestamp']} ===\n")
                    f.write(resp['content'])
                    f.write("\n\n" + "="*80 + "\n\n")
            print(f"Response backed up to: {backup_file.absolute()}")
            
            # After all responses are collected, save complete conversation to text
            txt_file = save_conversation_to_text(conversation_history, partner_id)
            print(f"Complete conversation saved to: {txt_file.resolve()}")
            
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()