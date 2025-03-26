import streamlit as st
from agent.prompts import SYSTEM_PROMPT
from agent.agent import agent


#### Streamlit app
st.title("💬 Chatbot")
st.caption("🚀 A Streamlit chatbot powered by OpenAI")

#### Initialize the chat history
if "messages" not in st.session_state:
    st.session_state["messages"] = [{"role": "system",
                                     "content": SYSTEM_PROMPT},
                                     {"role": "assistant", 
                                     "content": "How can I help you?"}]

#### Display the chat history
for msg in st.session_state.messages[1:]:
    st.chat_message(msg["role"]).write(msg["content"])

#### Get user input
if prompt := st.chat_input():

    # Update the system prompt with memories
    st.session_state.messages[0]["content"] = SYSTEM_PROMPT

    # Add user message to the chat history
    st.session_state.messages.append({"role": "user", "content": prompt})

    # Display user message
    st.chat_message("user").write(prompt)

    # Generate assistant message
    msg = agent(st.session_state.messages)

    # Add assistant message to the chat history
    st.session_state.messages.append({"role": "assistant", "content": msg})

    # Display assistant message
    st.chat_message("assistant").write(msg)