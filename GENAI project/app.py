import streamlit as st
from planner import graph

st.set_page_config(
    page_title="AI Health & Fitness Planner",
    page_icon="💪",
    layout="wide"
)

st.title("AI powered Health & Fitness Planner 💪 ")
st.write("Generate Your general fitness and nutrition plan here"
         " Using this AI powered Planner.")

st.sidebar.header("Your Profile")

goal = st.sidebar.text_input(
    "Fitness Goal",
    placeholder="Example: Build general fitness"
    )

age = st.sidebar.number_input(
    "Age",
    min_value=13,
    max_value=75,
    value=24,
    step=1
)

gender = st.sidebar.selectbox(
    "Gender",
    ["Male","Female","Other"]
)

experience = st.sidebar.selectbox(
    "Experience Level",
    ["Beginner","Intermediate","Advanced"]
    )

days_per_week = st.sidebar.slider(
    "Training Days per week",
    min_value=1,
    max_value=7,
    value=4
    )

equipment = st.sidebar.multiselect(
    "Available Equipment",
    ["No Equipment",
     "Dumbbells",
     "Barbell",
     "Resistance Bands",
     "Treadmill",
     "Exercise Mat"]
)

generate = st.sidebar.button("Generate plan",type="primary")

if generate:

    if not goal:
        st.warning("Please enter your fitness goal.")

    elif not equipment:
        st.warning("Please select your available equipment.")

    else:

        equipment_text = ", ".join(equipment)

        initial_state = {
            "goal": goal,
            "age": age,
            "gender": gender,
            "experience": experience,
            "days_per_week": days_per_week,
            "equipment": equipment_text,
            "workout_plan": "",
            "nutrition_plan": "",
            "validation_status": "",
            "feedback": "",
            "revision_count": 0,

            "final_plan": ""
        }

        with st.spinner("Creating and validating your plan..."):
            result = graph.invoke(initial_state)

        st.success("Your plan has been generated.")

        tab1, tab2 = st.tabs(["🏋️ Workout Plan","🥗 Nutrition Plan"])

        with tab1:
            st.subheader("Workout Plan")
            st.markdown(result["workout_plan"])

        with tab2:
            st.subheader("Nutrition Guidance")
            st.markdown(result["nutrition_plan"])

        st.divider()
        st.subheader("Plan Validation")

        if result["validation_status"] == "valid":
            st.success("Plan passed validation.")

        else:
            st.warning(
                "The plan reached the maximum "
                "revision limit. Review it carefully.")

        st.caption(
            f"Planner revisions: "
            f"{result['revision_count']}")