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

# Chat input
if prompt := st.chat_input("Ask me anything about IT, technology, or current tech news..."):
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
        
        with st.spinner("🤔 Thinking..."):
            # Get conversation history
            conversation_context = get_conversation_history()
            
            # Get AI response using the new service
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                response, sources = loop.run_until_complete(
                    ai_service.get_enhanced_ai_response(prompt, conversation_context)
                )
            finally:
                loop.close()
            
            # Render response and persist it
            st.markdown(response)
            st.session_state.messages.append({"role": "assistant", "content": response})
            
            # Store sources for display
            if sources:
                st.session_state.last_sources = sources
    
    # Rerun to render full history
    st.rerun()

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #666; font-size: 0.9em;">
    <p>🔧 IT-Guru Assistant | Built with Streamlit & OpenAI | 
    <a href="https://github.com/your-username/it-chatbot" target="_blank">View on GitHub</a></p>
</div>
""", unsafe_allow_html=True)
