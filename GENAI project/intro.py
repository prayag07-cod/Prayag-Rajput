from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langgraph.graph import StateGraph, START, END
from typing import TypedDict

load_dotenv()

model = ChatGoogleGenerativeAI(model="gemini-3.6-flash")

parser = StrOutputParser()

# creating the state
class PlannerState(TypedDict):
    goal: str
    experience: str
    days_per_week: str
    equipment: str

    workout_plan: str
    nutrition_plan: str

    validation_status: str
    feedback: str
    revision_count: str


workout_prompt = ChatPromptTemplate.from_template("""
Yout are a planning fiteness assistant.
Create a general beginner-friendly workout plan.


Goal:{goal}

Experience: {experience}

Days per week: {days_per_week}

Equipment: {equipment}

Keep the paln practical and clearly structured.
Do not Provide medical diagnosis or treatment.
If the user may nedd medical clearance, recommend 
consulting an appropriate healthcare professionals.
""")

workout_chain = workout_prompt | model | parser

def create_workout(state: PlannerState):

    response = workout_chain.invoke({

        "goal": state["goal"],

        "experience": state["experience"],

        "days_per_week": state["days_per_week"],

        "equipment": state["equipment"]
    })

    return {"workout_plan": response}    

nutrition_prompt = ChatPromptTemplate.from_template("""
You are a general nutrition planning assistant.
Create general nutrition guidance for this goal:

Goal:{goal}

Experience: {experience}

Days per week: {days_per_week}

Provide practical, general guidance.
Do not diagnosis medical condition or prescibe
medical deits or tratement.
""")

nutrition_chain = nutrition_prompt | model | parser

def create_nutrition(state: PlannerState):

    response = nutrition_chain.invoke({

        "goal": state["goal"],

        "experience": state["experience"],

        "days_per_week": state["days_per_week"],

        "equipment": state["equipment"]
    })

    return {"nutrition_plan": response}    


def validate_plan(state: PlannerState):

    workout = state["workout_plan"]
    nutrition = state["nutrition_plan"]

    if not workout or not nutrition:
        return {"validation_status": "invalid",
                "feedback": "Workout or nutrition plan is missing."}

    if len(workout) < 200:
        return {"validation_status": "invalid",
                "feedback": "Workout plan is too short"}
    
    if len(nutrition) < 200:
        return {"validation_status": "invalid",
                "feedback": "Nutrition plan is too short"}

    return {"validation_status": "valid",
            "feedback": "Plan passed validation."}

def decide_next_step(state: PlannerState):

    if state["validation_status"] == "valid":
        return "finish"

    if state["revision_count"] >= 2:
        return "finish"
    return "revise"

gb = StateGraph(PlannerState)

gb.add_node("workout", create_workout)
gb.add_node("nutrition", create_nutrition)
gb.add_node("validation", validate_plan)

gb.add_edge(START,"workout")
gb.add_edge("workout","nutrition")
gb.add_edge("nutrition","validation")

gb.add_conditional_edges("validation", decide_next_step, 
                         {"finish": END, "revise": "workout"})

graph = gb.compile()

result = graph.invoke({
    "goal": "improve general fitness",
    "experience":"begineer",
    "days_per_week": 4,
    "equipment":"bodyweight and dumbbells",
    "workout_plan":"",
    "nutrition_plan":""
    
})

print("\n============================")
print("WORKOUT PLAN")
print("============================")
print(result["workout_plan"])

print("============================")
print("Nutrition Plan:")
print("============================")
print(result["nutrition_plan"])