import streamlit as st
import requests

st.title("Machine Failure Prediction")

air_temperature = st.number_input("Air Temperature")
process_temperature = st.number_input("Process Temperature")
rotational_speed = st.number_input("Rotational Speed")

torque = st.number_input("Torque")
tool_wear = st.number_input("Tool Wear")

pressure = st.number_input("Pressure")
vibration = st.number_input("Vibration")
electrical_current = st.number_input("Electrical Current")

if st.button("Predict"):

    payload = {
        "air_temperature": air_temperature,
        "process_temperature": process_temperature,
        "rotational_speed": int(rotational_speed),
        "torque": torque,
        "tool_wear": int(tool_wear),
        "pressure": pressure,
        "vibration": vibration,
        "electrical_current": electrical_current
    }

    response = requests.post(
        "http://127.0.0.1:8000/predict",
        json=payload
    )

    result = response.json()

    if result["machine_failure"] == 1:
        st.error("Failure Predicted")
    else:
        st.success("Machine Operating Normally")

    st.json(result)