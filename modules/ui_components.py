"""
UI Components Module - Handles Streamlit UI components and interactions
"""
import json
import streamlit as st
import requests
from typing import Dict, List, Any
from modules.ai_service import AIService


class ModelManager:
    """Manages AI model selection and display"""
    
    @staticmethod
    @st.cache_data(ttl=3600)
    def fetch_openrouter_models() -> Dict[str, List[str]]:
        """Fetch available models from OpenRouter API"""
        try:
            response = requests.get("https://openrouter.ai/api/v1/models")
            if response.status_code == 200:
                models_data = response.json()
                
                # Categorize models by pricing - more inclusive
                free_models = []
                affordable_models = []
                premium_models = []
                all_models = []
                
                for model in models_data.get('data', []):
                    model_id = model.get('id', '')
                    pricing = model.get('pricing', {})
                    prompt_cost = float(pricing.get('prompt', '0'))
                    
                    all_models.append(model_id)
                    
                    if prompt_cost == 0:
                        free_models.append(model_id)
                    elif prompt_cost < 0.01:  # Increased threshold for affordable
                        affordable_models.append(model_id)
                    else:
                        premium_models.append(model_id)
                
                return {
                    "All Models": sorted(all_models),  # Show all models
                    "Free": sorted(free_models),
                    "Affordable": sorted(affordable_models), 
                    "Premium": sorted(premium_models)
                }
            else:
                return {"Error": ["Failed to fetch models"]}
        except Exception as e:
            st.error(f"Error fetching models: {str(e)}")
            return {"Default": ["google/gemini-2.5-flash-lite"]}
    
    @staticmethod
    def render_model_selector():
        """Render the model selection UI"""
        st.markdown("### 🤖 AI Model Selection")
        
        models = ModelManager.fetch_openrouter_models()
        default_from_secrets = st.secrets.get("OPENROUTER_MODEL", "meta-llama/llama-3.1-8b-instruct:free")
        
        # Add configured model to appropriate category if not present
        configured_model_added = False
        for category, model_list in models.items():
            if default_from_secrets in model_list:
                configured_model_added = True
                break
        
        if not configured_model_added and default_from_secrets:
            # Add configured model to "Configured" category
            models["Configured"] = [default_from_secrets]
        
        # Model category selection
        selected_category = st.selectbox(
            "Choose Model Category:",
            options=list(models.keys()),
            help="Free models have no cost, Affordable models cost <$0.001 per 1K tokens, Configured shows your secrets.toml model"
        )
        
        # Model selection within category
        if selected_category in models and models[selected_category]:
            # Pre-select the configured model if in current category
            current_model = st.session_state.get("selected_model", default_from_secrets)
            default_index = 0
            if current_model in models[selected_category]:
                default_index = models[selected_category].index(current_model)
            
            selected_model = st.selectbox(
                f"Select {selected_category} Model:",
                options=models[selected_category],
                index=default_index,
                help=f"Choose from available {selected_category.lower()} models"
            )
        else:
            selected_model = None
            st.warning("No models available in this category")
        
        # Update selected model
        if selected_model:
            st.session_state.selected_model = selected_model
            st.success(f"✅ Selected: {selected_model}")
        
        # Show current model with secrets.toml fallback
        current_model = st.session_state.get("selected_model", default_from_secrets)
        st.info(f"🤖 Current Model: {current_model}")
        
        # Show if using configured model
        if current_model == default_from_secrets:
            st.caption(f"💡 Using model from secrets.toml")
        
        # Reset to default button
        if st.button("🔄 Reset to secrets.toml Default", help="Reset to model configured in secrets.toml"):
            st.session_state.selected_model = default_from_secrets
            st.rerun()
        
        return current_model


class IntentDetectionUI:
    """Manages intent detection UI components"""
    
    @staticmethod
    def render_settings():
        """Render intent detection settings"""
        st.markdown("### 🧠 Intent Detection")
        use_ai_intent = st.checkbox("Use AI-Powered Intent Detection", value=True, 
                                   help="Uses AI to classify queries with higher accuracy")
        st.session_state.use_ai_intent = use_ai_intent
        
        if not use_ai_intent:
            st.info("Using semantic similarity matching")
        else:
            st.success("Using AI classification + semantic fallback")
        
        # (Feedback metrics removed)
    
    @staticmethod
    def render_intent_details():
        """Render intent detection details for the last response"""
        if hasattr(st.session_state, 'last_intent_info') and st.session_state.last_intent_info:
            intent_info = st.session_state.last_intent_info
            with st.expander("🔍 Intent Detection Details", expanded=False):
                st.write(f"**Method:** {intent_info.get('method', 'unknown').title()}")
                st.write(f"**Confidence:** {intent_info.get('confidence', 0):.1%}")
                st.write(f"**Source:** {intent_info.get('source', 'unknown').replace('_', ' ').title()}")
                if intent_info.get('reasoning'):
                    st.write(f"**AI Reasoning:** {intent_info['reasoning']}")
                if intent_info.get('multi_source'):
                    st.info("🔄 Multi-source search used due to low confidence")




class SidebarManager:
    """Manages the sidebar content"""
    
    @staticmethod
    def render_sidebar():
        """Render the complete sidebar"""
        with st.sidebar:
            # Secrets-driven visibility flags
            hide_settings_bar = bool(st.secrets.get("HIDE_SETTINGS_BAR", False))
            hide_model_selector = bool(st.secrets.get("HIDE_MODEL_SELECTOR", False))

            if not hide_settings_bar:
                st.markdown("# ⚙️ Settings")

                # Model selection (optional)
                if not hide_model_selector:
                    ModelManager.render_model_selector()
                else:
                    # Force default model from secrets when selector is hidden
                    default_model = st.secrets.get("OPENROUTER_MODEL", "meta-llama/llama-3.1-8b-instruct:free")
                    st.session_state.selected_model = default_model
                    st.info(f"🤖 Current Model (locked by admin): {default_model}")

                # Intent detection settings (only when settings bar is visible)
                IntentDetectionUI.render_settings()
            else:
                # If the whole settings bar is hidden, still ensure model is locked to default
                default_model = st.secrets.get("OPENROUTER_MODEL", "meta-llama/llama-3.1-8b-instruct:free")
                st.session_state.selected_model = default_model
            
            # Scope reminder
            if bool(st.secrets.get("ENFORCE_IT_SCOPE", True)):
                allow_career = bool(st.secrets.get("ALLOW_IT_CAREER_TOPICS", True))
                career_msg = " IT career topics (resume, interviews, certifications) are allowed." if allow_career else " IT career topics are currently disabled."
                st.info("""
                🔒 Scope: This assistant only handles IT infrastructure, cybersecurity, cloud, DevOps, and system administration topics.
                """ + career_msg)

            # Refresh button only when settings bar is visible and model selector is enabled
            if not hide_settings_bar and not hide_model_selector:
                if st.button("🔄 Refresh Models"):
                    st.cache_data.clear()
                    st.rerun()
            
            # Capabilities info
            st.markdown("### 🎯 What I Can Help With")
            st.markdown("""
            <div class="sidebar-info">
            <strong>Networking:</strong><br>
            • Firewalls, VPNs, DNS<br>
            • Load balancing, routing<br><br>
            
            <strong>Cloud Platforms:</strong><br>
            • AWS, Azure, GCP services<br>
            • Infrastructure as Code<br><br>
            
            <strong>Security:</strong><br>
            • Threat analysis & response<br>
            • Compliance frameworks<br><br>
            
            <strong>DevOps:</strong><br>
            • CI/CD pipelines<br>
            • Container orchestration<br><br>
            
            <strong>Real-time Info:</strong><br>
            • Latest security threats<br>
            • Current best practices
            </div>
            """, unsafe_allow_html=True)
            
            # (Feedback stats removed)


class ChatInterface:
    """Manages the main chat interface"""
    
    @staticmethod
    def render_chat_history():
        """Render the chat message history"""
        for i, message in enumerate(st.session_state.messages):
            with st.chat_message(message["role"]):
                st.markdown(message["content"])
                
                # Show intent detection details and sources for each assistant message
                if message["role"] == "assistant":
                    # Prefer per-message intent info if present
                    intent_info = message.get("intent_info")
                    if intent_info:
                        with st.expander("🔍 Intent Detection Details", expanded=False):
                            method = intent_info.get('method', 'unknown')
                            confidence = intent_info.get('confidence', 0)
                            source = intent_info.get('source', 'unknown')
                            reasoning = intent_info.get('reasoning')
                            multi_source = intent_info.get('multi_source', False)
                            st.write(f"**Method:** {str(method).title()}")
                            try:
                                st.write(f"**Confidence:** {float(confidence):.1%}")
                            except Exception:
                                st.write(f"**Confidence:** {confidence}")
                            st.write(f"**Source:** {str(source).replace('_', ' ').title()}")
                            if reasoning:
                                st.write(f"**AI Reasoning:** {reasoning}")
                            if multi_source:
                                st.info("🔄 Multi-source search used due to low confidence")

                    # Show sources under assistant messages (prefer markdown, fallback to list)
                    sources_list = message.get("sources_list") or []
                    sources_md = message.get("sources_md")
                    if sources_md:
                        st.markdown(sources_md, unsafe_allow_html=False)
                    elif sources_list:
                        # Simple bullet list fallback
                        st.markdown("**Sources**")
                        for src in sources_list:
                            title = src.get("title") or src.get("url", "Source")
                            url = src.get("url", "")
                            excerpt = src.get("excerpt")
                            if excerpt:
                                st.markdown(f"- [{title}]({url}) — {excerpt}")
                            else:
                                st.markdown(f"- [{title}]({url})")

                    # Reformat controls removed per request

                    # Follow-up suggestions: only on the last assistant message (avoid blocking calls during render)
                    if (
                        i == len(st.session_state.messages) - 1
                        and not message.get("is_welcome", False)
                    ):
                        followups = message.get("followups") or []
                        if followups:
                            st.markdown("**💡 Follow-up suggestions:**")
                            for idx, sug in enumerate(followups):
                                if st.button(sug, key=f"follow_btn_{i}_{idx}", use_container_width=True):
                                    st.session_state["queued_prompt"] = sug
                                    st.rerun()

                    # Export / Share (only on last non-welcome assistant message)
                    if i == len(st.session_state.messages) - 1 and not message.get("is_welcome", False):
                        with st.expander("📤 Export / Share", expanded=False):
                            try:
                                lines = ["# IT-Guru Assistant Chat Transcript\n"]
                                for m in st.session_state.messages:
                                    role = m["role"].title()
                                    content = m.get("content", "")
                                    lines.append(f"## {role}\n\n{content}\n")
                                    if role == "Assistant":
                                        smd = m.get("sources_md")
                                        if smd:
                                            lines.append("### Sources\n\n" + smd + "\n")
                                md_blob = "\n".join(lines)
                                st.download_button("⬇️ Download Markdown", data=md_blob, file_name="it-guru-transcript.md", mime="text/markdown")

                                json_blob = json.dumps(st.session_state.messages, ensure_ascii=False, indent=2)
                                st.download_button("⬇️ Download JSON", data=json_blob, file_name="it-guru-transcript.json", mime="application/json")
                            except Exception as e:
                                st.error(f"Export failed: {e}")
                
                # (Feedback buttons removed)
    
    @staticmethod
    def initialize_session_state():
        """Initialize session state variables"""
        if "messages" not in st.session_state:
            # Add welcome message
            welcome_message = """👋 **Welcome to IT-Guru Assistant!**

I'm your specialized AI assistant for IT infrastructure and cybersecurity. I can help you with:

🔧 **Infrastructure & Systems**
- Network troubleshooting and configuration
- Server administration and DevOps practices
- Cloud platforms (AWS, Azure, GCP)

🛡️ **Cybersecurity**
- Security best practices and threat analysis
- Vulnerability assessments and CVE information
- Compliance and governance guidance

💡 **Real-time Information**
- Current tech news and trends
- Latest security advisories
- Up-to-date documentation from Microsoft Learn and AWS

**Try asking me:**
- "How do I set up an AWS EC2 instance?"
- "What are the latest CVE vulnerabilities?"
- "Explain Azure Active Directory best practices"
- "Compare Docker vs Kubernetes"

I use real-time sources including Microsoft Learn, AWS documentation, and current security feeds to provide you with accurate, up-to-date information."""

            st.session_state.messages = [
                {"role": "assistant", "content": welcome_message, "is_welcome": True}
            ]
        if "selected_model" not in st.session_state:
            # Use model from secrets.toml as default
            default_model = st.secrets.get("OPENROUTER_MODEL", "meta-llama/llama-3.1-8b-instruct:free")
            st.session_state.selected_model = default_model
        if "use_ai_intent" not in st.session_state:
            st.session_state.use_ai_intent = True
        # (Feedback session variables removed)
