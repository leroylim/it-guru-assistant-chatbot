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

# Fixed-position credits below the chat input (sit at the very bottom)
st.markdown(
    """
<style>
  .credits-bar { position: fixed; left: 0; right: 0; bottom: 0; text-align: center; color: #777; font-size: 0.9em; line-height: 1.35; z-index: 999; pointer-events: auto; background: rgba(255,255,255,0.9); backdrop-filter: blur(2px); padding: 6px 8px; border-top: 1px solid #eee; }
  .credits-bar a { color: inherit; text-decoration: underline; }
</style>
<div class=\"credits-bar\" id=\"credits-bar\">
  <div>
    Built by <strong>Han Yong Lim</strong>
    · <a href=\"https://github.com/leroylim\" target=\"_blank\">GitHub</a>
    · <a href=\"https://www.linkedin.com/in/han-yong-lim-312b88a7/\" target=\"_blank\">LinkedIn</a>
  </div>
  <div>
    © 2025 MIT ·
    <a href=\"https://github.com/leroylim/it-guru-assistant-chatbot#credits\" target=\"_blank\">Credits</a> ·
    <a href=\"https://github.com/leroylim/it-guru-assistant-chatbot.git\" target=\"_blank\">View on GitHub</a>
  </div>
</div>
<script>
  (function() {
    function positionChatInputAboveCredits() {
      try {
        var bar = document.getElementById('credits-bar');
        var chat = document.querySelector('[data-testid="stChatInput"]');
        if (!bar || !chat) return;
        var barRect = bar.getBoundingClientRect();
        var barH = barRect.height || bar.offsetHeight || 32;
        var gap = 6; // small gap between credits and chat input
        // Move chat input above the credits bar
        chat.style.bottom = (barH + gap) + 'px';
      } catch (e) { /* noop */ }
    }

    // Initial and periodic updates
    positionChatInputAboveCredits();
    window.addEventListener('resize', positionChatInputAboveCredits);

    // Observe DOM changes to reposition when Streamlit rerenders
    var obs = new MutationObserver(function() { positionChatInputAboveCredits(); });
    obs.observe(document.body, { childList: true, subtree: true });
    setInterval(positionChatInputAboveCredits, 1000);
  })();
  </script>
""",
    unsafe_allow_html=True,
)

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

# Minimal footer (no extra links; credits bar already includes GitHub link)
st.markdown("---")
