"""
IT-Guru Assistant - Main Streamlit Application
A specialized AI assistant for IT infrastructure and cybersecurity
"""
import streamlit as st
import asyncio
from datetime import datetime
from modules.ai_service import AIService
from modules.ui_components import SidebarManager, ChatInterface
from config import *

st.set_page_config(
    page_title="IT-Guru Assistant",
    page_icon="🔧",
    layout="wide",
    initial_sidebar_state="expanded"
)


def is_it_related(query: str) -> bool:
    """Always return True since we now handle all queries with AI + real-time search"""
    return True

def get_conversation_history() -> str:
    """Get formatted conversation history"""
    if not st.session_state.messages:
        return ""
    
    # Get last 6 messages for context (3 exchanges)
    recent_messages = st.session_state.messages[-6:]
    
    context_parts = []
    for msg in recent_messages:
        role = "Human" if msg["role"] == "user" else "Assistant"
        context_parts.append(f"{role}: {msg['content'][:200]}...")
    
    return "\n".join(context_parts)






# Initialize session state
ChatInterface.initialize_session_state()

# Initialize AI service
ai_service = AIService()

# Main interface
st.markdown("""
<div class="main-header">
    <h1>🔧 IT-Guru Assistant</h1>
    <p>Your specialized AI assistant for IT infrastructure and cybersecurity</p>
</div>
""", unsafe_allow_html=True)

# Render sidebar
SidebarManager.render_sidebar()

# Chat interface
st.markdown("### 💬 Chat with IT-Guru")

# Display chat history
ChatInterface.render_chat_history()

# Chat input (also handle queued follow-up suggestions)
placeholder = "Ask about IT infrastructure, cybersecurity, cloud, DevOps, or IT careers (resume, interviews, certs)"
prompt = None
if st.session_state.get("queued_prompt"):
    prompt = st.session_state.pop("queued_prompt")
else:
    prompt = st.chat_input(placeholder)

if prompt:
    # Show user message immediately and store it
    st.chat_message("user").markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    # Scroll to bottom after user message so it's visible
    st.markdown(
        """
        <script>
            setTimeout(function() {
                window.scrollTo(0, document.body.scrollHeight);
            }, 100);
        </script>
        """,
        unsafe_allow_html=True,
    )
    
    # Assistant response container
    with st.chat_message("assistant"):
        # Marker to scroll to the start of AI reply
        st.markdown('<div id="ai-response-start"></div>', unsafe_allow_html=True)
        
        # Scroll to the start of the AI response (not the bottom)
        st.markdown(
            """
            <script>
                setTimeout(function() {
                    var el = document.getElementById('ai-response-start');
                    if (el) {
                        el.scrollIntoView({ behavior: 'smooth', block: 'start' });
                    }
                }, 200);
            </script>
            """,
            unsafe_allow_html=True,
        )
        
        # Manual status so we can clear it on first token
        status_ph = st.empty()
        status_ph.info("🤔 Thinking...")

        # Conversation context
        conversation_context = get_conversation_history()

        try:
            # Try streaming response
            token_iter, _ = ai_service.stream_ai_response(prompt, conversation_context)

            # Placeholder for progressive rendering
            placeholder = st.empty()
            # Seed with a typing indicator to show activity immediately
            accumulated = ""
            placeholder.markdown("…")

            first_visible = False
            for chunk in token_iter:
                if chunk:
                    accumulated += chunk
                    placeholder.markdown(accumulated)
                    if not first_visible:
                        status_ph.empty()  # clear "Thinking..." once first content arrives
                        first_visible = True

            # Persist final message with sources and intent info
            intent_info = st.session_state.get("last_intent_info")
            sources_md_final = st.session_state.get("last_sources", "")
            sources_list_final = st.session_state.get("last_sources_list", [])
            msg = {
                "role": "assistant",
                "content": accumulated,
                "sources_md": sources_md_final,
                "sources_list": sources_list_final,
                "intent_info": intent_info or {}
            }
            # Precompute follow-up suggestions to avoid blocking in UI render
            try:
                ctx_text = "\n".join([f"{s.get('title','')}: {s.get('url','')}" for s in (sources_list_final or [])])
                followups = ai_service.generate_followups(
                    user_query=prompt,
                    answer=accumulated,
                    context_text=ctx_text,
                )
                msg["followups"] = followups
            except Exception:
                msg["followups"] = []
            st.session_state.messages.append(msg)

            # Show sources under the assistant message if available
            if sources_md_final:
                st.markdown(sources_md_final, unsafe_allow_html=False)
        except AttributeError:
            # Fallback to non-streaming behavior
            try:
                response, sources = ai_service._run_async(
                    ai_service.get_enhanced_ai_response(prompt, conversation_context)
                )
            except Exception as _:
                # As a last resort, create a temporary loop
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    response, sources = loop.run_until_complete(
                        ai_service.get_enhanced_ai_response(prompt, conversation_context)
                    )
                finally:
                    loop.close()
            status_ph.empty()
            st.markdown(response)
            intent_info = st.session_state.get("last_intent_info")
            sources_list_final = st.session_state.get("last_sources_list", [])
            msg = {
                "role": "assistant",
                "content": response,
                "sources_md": sources,
                "sources_list": sources_list_final,
                "intent_info": intent_info or {}
            }
            # Precompute follow-ups
            try:
                ctx_text = "\n".join([f"{s.get('title','')}: {s.get('url','')}" for s in (sources_list_final or [])])
                followups = ai_service.generate_followups(
                    user_query=prompt,
                    answer=response,
                    context_text=ctx_text,
                )
                msg["followups"] = followups
            except Exception:
                msg["followups"] = []
            st.session_state.messages.append(msg)

            # Show sources under the assistant message if available; also persist
            if sources:
                st.markdown(sources, unsafe_allow_html=False)
                st.session_state.last_sources = sources
    
    # Rerun to render full history
    st.rerun()

# Footer
st.markdown("---")
st.markdown(
    """
<div style="text-align: center; color: #666; font-size: 0.9em; line-height: 1.6;">
  <p><strong>🔧 IT-Guru Assistant</strong></p>
  <p>
    Built by <strong>Han Yong Lim</strong>
    · <a href="https://github.com/leroylim" target="_blank">GitHub</a>
    · <a href="https://www.linkedin.com/in/han-yong-lim-312b88a7/" target="_blank">LinkedIn</a>
  </p>
  <p>
    Credits: <a href="https://streamlit.io/" target="_blank">Streamlit</a> ·
    <a href="https://openrouter.ai/" target="_blank">OpenRouter</a> ·
    <a href="https://exa.ai/" target="_blank">Exa</a> ·
    <a href="https://learn.microsoft.com/" target="_blank">Microsoft Learn</a> ·
    <a href="https://docs.aws.amazon.com/" target="_blank">AWS Documentation</a>
  </p>
  <p>
    <a href="https://github.com/leroylim/it-guru-assistant-chatbot.git" target="_blank">View on GitHub</a>
  </p>
  <p style="font-size: 0.85em; color: #888;">© 2025 Han Yong Lim. MIT License.</p>
  </div>
""",
    unsafe_allow_html=True,
)
