from pydantic import BaseModel, Field
from langchain_core.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
from typing import List
from typing_extensions import TypedDict

llm = ChatGoogleGenerativeAI(
    model="gemini-2.0-flash",  # or gemini-1.5-pro
    google_api_key="AIzaSyBxHic-gcYoj8TZuELjq1OGwprpUCkwE7w",

)

class employee(BaseModel):
    """Schema for employee information"""
    employee_id: int = Field(description="Employee ID of the employee")
    name: str = Field(description="Name of the employee")
    age: int = Field(description="Age of the employee")
    department: str = Field(description="Department of the employee")
    salary: int = Field(description="Salary of the employee")
    position: str = Field(description="Position of the employee")
    hire_date: str = Field(description="Hire date of the employee")
    gender: str = Field(description="Gender of the employee")
    years_of_experience: int = Field(description="Years of experience of the employee")

class employees(BaseModel):
    """Schema for employees information"""
    employees: List[employee] = Field(description="List of employees")
    action: str = Field(description="Action to be taken by the user")
    total_extracted: int = Field(description="Number of employees actually extracted")
    expected_total: int = Field(description="Expected number of employees (should match total_extracted)")
    is_complete: bool = Field(description="True if total_extracted == expected_total")

system_prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            """
            You are an expert data extraction specialist. Your mission is to extract EVERY SINGLE employee from the CSV file provided.
            CRITICAL INSTRUCTIONS:
                - The CSV contains EXACTLY 30 employee records
                - Read through the ENTIRE CSV file carefully.
                - Extract EVERY employee row - do not skip any.
                - Continue until you reach the last employee in the file
                - Map 'years_experience' column to 'years_of_experience' field

                QUALITY CHECK:
                - Scan from the first employee_id to the last employee_id
                - Make sure no employee is missing between first and last
                - Double-check that you processed the entire CSV content

                Your reputation depends on extracting EVERY employee without missing any!
            """,
        ),
        (
            "placeholder", "{messages}"
        ),

    ]
)

employee_agent_chain = system_prompt | llm.with_structured_output(employees)

messages = [("user", """
             The user wants to complete this task: From the dataset located at: employees.csv.
             IMPORTANT REMINDERS:
                - Process the ENTIRE file from top to bottom.
                - Extract EVERY employee record.
                - Don't stop until you reach the end of the data.
             """)]

result = employee_agent_chain.invoke({"messages": messages})
print(result)






