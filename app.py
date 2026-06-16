"""
app.py  –  Gradio interface for the Scar Analysis Agent.

Run:
    python app.py
"""

import gradio as gr
from scar_agent import agent
from session_store import SCAR_SESSION_ID


def respond(message: str, image: str | None, history: list):
    # If an image was uploaded, pass its path to the agent
    if image:
        user_input = image
        display_message = f"[Image uploaded: {image}]"
    elif message.strip():
        user_input = message.strip()
        display_message = user_input
    else:
        return history, ""

    # Get agent response (synchronous)
    response = agent.run(user_input, session_id=SCAR_SESSION_ID)
    reply = response.content or "Sorry, I could not process that request."

    history.append({"role": "user",      "content": display_message})
    history.append({"role": "assistant", "content": reply})
    return history, ""


# ── Interface ─────────────────────────────────────────────────────────────────

with gr.Blocks(title="Scar Analysis Agent") as demo:
    gr.Markdown("## Scar Analysis Agent")
    gr.Markdown("Upload a scar image for analysis, or ask a question about wound healing.")

    chatbot = gr.Chatbot(height=450, label="Conversation")

    with gr.Row():
        with gr.Column(scale=1):
            image_input = gr.Image(
                type="filepath",
                label="Upload scar image",
            )
        with gr.Column(scale=2):
            msg_input = gr.Textbox(
                placeholder="Type a message...",
                label="Message",
                lines=3,
            )
            with gr.Row():
                send_btn   = gr.Button("Send", variant="primary")
                clear_btn  = gr.Button("Clear")

    # Send on button click or Enter
    send_btn.click(
        respond,
        inputs=[msg_input, image_input, chatbot],
        outputs=[chatbot, msg_input],
    )
    msg_input.submit(
        respond,
        inputs=[msg_input, image_input, chatbot],
        outputs=[chatbot, msg_input],
    )

    # Clear chat and inputs
    clear_btn.click(
        lambda: ([], "", None),
        outputs=[chatbot, msg_input, image_input],
    )


if __name__ == "__main__":
    demo.launch()
