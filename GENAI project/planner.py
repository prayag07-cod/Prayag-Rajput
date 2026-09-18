from dotenv import load_dotenv
from typing import TypedDict, Literal
from pydantic import BaseModel, Field
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.output_parsers import StrOutputParser
from langgraph.graph import StateGraph, START, END

load_dotenv()

model = ChatGoogleGenerativeAI(model="gemini-3.6-flash")

parser = StrOutputParser()

class ValidationResult(BaseModel):
    status: Literal["valid", "invalid"] = Field(description="Whether the plan is valid")

    feedback: str = Field(description="Explanation of validation result")

structured_validator = model.with_structured_output(ValidationResult)

class PlannerState(TypedDict):

    goal: str
    age: int
    gender: str
    experience: str
    days_per_week: int
    equipment: str

    workout_plan: str
    nutrition_plan: str

    validation_status: str
    feedback: str

    revision_count: int

    final_plan: str

def create_workout(state: PlannerState):

    prompt = f"""
    Create a general fitness workout plan based on the user's profile.

    User Profile:

    Age: {state['age']}
    Gender: {state['gender']}
    Goal: {state["goal"]}
    Experience: {state["experience"]}
    Days per week: {state["days_per_week"]}
    Equipment: {state["equipment"]}

    Design the workout plan according to the user's 
    age, gender, experience level, goal, available days,
    and equipment.

    Keep the recommendations general and educational.
    Do not diagnose medical conditions or prescribe medical treatment.
    """

    if state["feedback"]:

        prompt += f"""

        The previous plan was reviewed and received
        the following feedback:

        {state["feedback"]}

        Create a revised plan that addresses this feedback.
        """

    result = model.invoke(prompt)
    response = parser.invoke(result)

    return {"workout_plan": response,
            "revision_count": state["revision_count"] + 1}


def create_nutrition(state: PlannerState):

    prompt = f"""
    Create general nutrition guidance to complement
    the user's fitness goal and workout plan.

    User Profile:

    Age: {state["age"]}
    Gender: {state["gender"]}
    Fitness Goal: {state["goal"]}
    Experience Level: {state["experience"]}
    Days Available Per Week: {state["days_per_week"]}

    Workout Plan:

    {state["workout_plan"]}

    Provide general educational nutrition guidance
    appropriate to the user's profile.

    Do not diagnose medical conditions.
    Do not prescribe medical treatment.
    Do not make unsupported medical claims.
    """

    result = model.invoke(prompt)
    response = parser.invoke(result)

    return {"nutrition_plan": response}

def validate_plan(state: PlannerState):

    prompt = f"""
    Evaluate this generated fitness plan.

    WORKOUT:
    {state["workout_plan"]}

    NUTRITION:
    {state["nutrition_plan"]}

    Check:

    - completeness
    - consistency with the goal
    - consistency with available equipment
    - consistency with requested training days
    - clarity
    - unsupported medical claims

    Mark the plan as valid only if it satisfies
    the requirements reasonably well.
    """
    result = structured_validator.invoke(prompt)

    return {"validation_status": result.status,
            "feedback": result.feedback}


def decide_next_step(state: PlannerState):

    if state["validation_status"] == "valid":
        return "finish"

    if state["revision_count"] >= 3:
        return "finish"

    return "revise"


def finalize_plan(state: PlannerState):

    final_plan = f"""
    FINAL FITNESS PLAN

    Goal:{state["goal"]}
    Age: {state['age']}
    Gender:{state["gender"]}
    Experience:{state["experience"]}
    Days per week:{state["days_per_week"]}
    Equipment:{state["equipment"]}

    WORKOUT PLAN
    ------------
    {state["workout_plan"]}

    NUTRITION PLAN
    --------------
    {state["nutrition_plan"]}

    VALIDATION
    ----------
    {state["feedback"]}
    """

    return {"final_plan": final_plan}

g_b = StateGraph(PlannerState)

g_b.add_node("workout", create_workout)
g_b.add_node("nutrition", create_nutrition)
g_b.add_node("validator", validate_plan)
g_b.add_node("finalize", finalize_plan)

g_b.add_edge(START,"workout")
g_b.add_edge("workout","nutrition")
g_b.add_edge("nutrition","validator")
g_b.add_conditional_edges("validator",decide_next_step,
                                    {"finish": "finalize","revise": "workout"})
g_b.add_edge("finalize",END)

graph = g_b.compile()