# 🔧 IT-Guru Assistant

An AI-powered chatbot specialized in IT infrastructure and cybersecurity, built with Streamlit and OpenRouter. The app uses AI intent detection plus real-time web search (Exa) and selective MCP integrations (AWS docs, Microsoft Learn) — no local knowledge base or RAG.

## 🌟 Features

### Core Capabilities
- **AI Intent Detection**: Routes queries to AWS docs MCP, Microsoft Learn MCP, or Exa real-time search
- **Context-Aware Conversations**: Maintains conversation history for natural interactions
- **Real-time Coverage**: Searches authoritative IT/security sources with vendor boosting
- **OpenRouter Models**: Select and use models via UI/secrets

### Advanced Features
- **Multiple Response Formats**: Definitions, step-by-step guides, troubleshooting, comparisons
- **Professional UI**: Modern design with custom CSS and responsive layout
- **Session Management**: Persistent conversation state across interactions
- **Performance Monitoring**: Response quality and usage metrics

## 🛠️ Technology Stack

- **Frontend**: Streamlit
- **Backend**: Python using OpenRouter Chat Completions API
- **Real-time Search**: Exa Search API with domain filters and vendor boosting
- **MCP Integrations**: AWS docs (HTTP API), Microsoft Learn (SSE streaming implemented)
- **Deployment**: Streamlit Community Cloud (free hosting)

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- OpenRouter API key (get one free at [openrouter.ai](https://openrouter.ai))
- Git

### Local Development

1. **Clone the repository**
```bash
git clone https://github.com/leroylim/it-guru-assistant-chatbot.git
cd it-guru-assistant-chatbot
```

2. **Install dependencies**
```bash
pip install -r requirements.txt
```

3. **Configure API keys**
Create `.streamlit/secrets.toml` and add your keys:
```toml
OPENROUTER_API_KEY = "your-openrouter-api-key-here"
OPENROUTER_MODEL = "google/gemini-2.5-flash-lite"  # or any available model id

# Exa real-time search
EXA_API_KEY = "your-exa-api-key-here"
EXA_START_DAYS = 180          # rolling window, overrides EXA_START_DATE if > 0
# EXA_START_DATE = "2025-02-01" # optional fixed date
EXA_MAX_RESULTS = 5

# IT scope guardrails (enable strict IT-only scope)
ENFORCE_IT_SCOPE = true                   # default true; set false to disable scope enforcement
ALLOW_IT_CAREER_TOPICS = true             # allow resume/interviews/certifications (career-only)
OUT_OF_SCOPE_MESSAGE = "Sorry, I’m focused on IT infrastructure, cybersecurity, cloud, DevOps, and IT careers. Please rephrase your question within this scope."

# Admin UI controls
HIDE_SETTINGS_BAR = false                 # set true to hide entire Settings sidebar section
HIDE_MODEL_SELECTOR = false               # set true to hide model selector and lock to OPENROUTER_MODEL
```

4. **Run the application**
```bash
streamlit run app.py
```

5. **Open your browser**
Navigate to `http://localhost:8501`

## 🌐 Deployment to Streamlit Community Cloud

### Step-by-Step Deployment

1. **Prepare Repository**
   - Ensure all code is in a public GitHub repository
   - Verify `requirements.txt` includes all dependencies
   - Remove any hardcoded API keys

2. **Deploy to Streamlit Cloud**
   - Visit [share.streamlit.io](https://share.streamlit.io)
   - Connect your GitHub account
   - Select your repository and `app.py` as the main file
   - Configure secrets in the Streamlit dashboard:
     ```
     OPENROUTER_API_KEY = "your-actual-api-key"
     OPENROUTER_MODEL = "google/gemini-2.5-flash-lite"
     EXA_API_KEY = "exa_..."
     EXA_START_DAYS = 180
     EXA_MAX_RESULTS = 5

     # IT scope guardrails
     ENFORCE_IT_SCOPE = true
     ALLOW_IT_CAREER_TOPICS = true
     OUT_OF_SCOPE_MESSAGE = "Sorry, I’m focused on IT infrastructure, cybersecurity, cloud, DevOps, and IT careers. Please rephrase your question within this scope."

     # Admin UI controls
     HIDE_SETTINGS_BAR = false
     HIDE_MODEL_SELECTOR = false
     ```

## ⚙️ Configuration Reference

### Required secrets
- **OPENROUTER_API_KEY**: OpenRouter API key for LLM responses and small classification calls
- **OPENROUTER_MODEL**: Default model ID (e.g., `meta-llama/llama-3.1-8b-instruct:free`)
- **EXA_API_KEY**: Exa search API key (for real-time web results)

### Optional secrets
- **EXA_START_DAYS**: Integer rolling window for recency filtering (e.g., `7`, `30`, `180`)
- **EXA_START_DATE**: ISO date (`YYYY-MM-DD`) as fixed earliest crawl date (ignored if `EXA_START_DAYS > 0`)
- **EXA_MAX_RESULTS**: Number of results to return (default 3 in code; example above uses 5)

- **LLM_SCOPE_CHECK**: `true|false` (default `false`) — when `true`, an inexpensive LLM check runs only on ambiguous queries that contain both a non‑IT term and an IT anchor. If the LLM says out-of-scope, the query is refused.
- **LLM_SCOPE_MODEL**: Optional model ID to use for the scope check (defaults to `OPENROUTER_MODEL` if not provided). Example: `meta-llama/llama-3.1-8b-instruct:free`.

### IT scope guardrails (secrets)
- **ENFORCE_IT_SCOPE**: `true|false` (default `true`) — when `true`, non‑IT topics get a polite refusal
- **ALLOW_IT_CAREER_TOPICS**: `true|false` (default `true`) — allows resume/interviews/certs topics
- **OUT_OF_SCOPE_MESSAGE**: Custom refusal message shown to the user

### IT scope keywords (externalized JSON)
- The scope guard keywords are editable in `modules/mcp/scope_keywords.json`:
  - `non_it_patterns`: topics to treat as out-of-scope (uses word-boundary regex for single words; substring for phrases)
  - `it_career_whitelist`: career-related whitelisted terms
  - `it_anchors`: strong IT indicators; presence of any anchor prevents false positives and may trigger the optional LLM scope check when ambiguous

If the JSON cannot be read, the app falls back to built-in defaults.

### Admin UI controls (secrets)
- **HIDE_SETTINGS_BAR**: `true|false` (default `false`) — hides the entire “Settings” section in the sidebar
- **HIDE_MODEL_SELECTOR**: `true|false` (default `false`) — hides the model selector and locks the app to `OPENROUTER_MODEL`

### Environment variables
- **OPENROUTER_API_KEY**: The app will also read this from environment as a fallback if not in secrets
  - Example: `export OPENROUTER_API_KEY=sk-or-...`

Notes:
- Exa keys (`EXA_*`) are read from Streamlit secrets in this app; prefer secrets over env for those.
- See `modules/ai_service.py`, `modules/mcp/intent_detector.py`, `modules/mcp/exa_client.py`, and `modules/mcp/router.py` for how these settings are used.

3. **Go Live**
   - Click "Deploy" - your app goes live immediately
   - Get your custom URL: `your-app-name.streamlit.app`

## 📊 Project Structure

```
it-chatbot/
├── app.py                          # Main Streamlit application
├── requirements.txt                # Python dependencies
├── config.py                       # App config (max_tokens, temperature)
├── modules/
│   ├── ai_service.py               # OpenRouter calls and response formatting
│   ├── ui_components.py            # Streamlit UI components
│   └── mcp/
│       ├── exa_client.py           # Exa search integration
│       ├── exa_domains.json        # Editable domain categories and vendor map
│       ├── scope_keywords.json     # Editable scope keywords (non-IT, IT anchors, career whitelist)
│       └── intent_detector.py      # AI-powered intent routing
├── .streamlit/
│   └── secrets.toml                # API keys and Exa settings (local dev)
└── README.md
```

## 🎯 What IT-Guru Can Help With

### 🔧 Networking
- Firewalls, VPNs, DNS configuration
- Routing and switching concepts
- Network troubleshooting procedures
- Load balancing and traffic management

### 🔒 Cybersecurity
- Security best practices and frameworks
- SSL/TLS certificates and encryption
- Incident response procedures
- Vulnerability management

### 💻 System Administration
- Active Directory management
- Server administration (Windows/Linux)
- Backup and disaster recovery
- PowerShell and automation

### ☁️ Cloud & Infrastructure
- AWS, Azure, Google Cloud concepts
- Container orchestration (Kubernetes)
- Infrastructure as Code (Terraform)
- DevOps practices and CI/CD

## 🔧 Technical Implementation

### Intent Routing
The system classifies queries and routes them to the best source:
- **Definitions**: "What is a firewall?"
- **Step-by-step**: "How to configure DNS?"
- **Troubleshooting**: "Network connectivity issues"
- **Comparisons**: "VPN vs proxy"

### Conversation Management
Maintains context across interactions while managing memory efficiently:
```python
def manage_conversation_context(chat_history, max_context=10):
    # Keep recent exchanges for context continuity
    recent_history = chat_history[-max_context*2:]
    return format_context_for_ai(recent_history)
```

## 📈 Performance & Analytics

### Built-in Metrics
- **Query Classification**: Automatic categorization of user requests
- **Response Quality**: Context relevance scoring
- **Usage Analytics**: Session duration and interaction depth

<!-- Feedback loop removed: no feedback collection in current version -->

## 🎨 UI/UX Features

### Professional Design
- **Modern Interface**: Clean, intuitive chat layout
- **Responsive Design**: Works on desktop and mobile
- **Custom Styling**: Professional color scheme and typography
- **Loading States**: Visual feedback during processing

### User Experience
- **Smart Suggestions**: Contextual help in sidebar
- **Error Handling**: Graceful handling of API failures
- **Accessibility**: Screen reader friendly components
- **Performance**: Optimized for fast response times

## 🔐 Security Considerations

### API Key Management
- Never commit API keys to version control
- Use Streamlit secrets for secure key storage
- Environment variable fallback for local development

### Rendering Safety
- Titles and text are sanitized; sources rendered via Markdown with `unsafe_allow_html=False`.

### Data Privacy
- No persistent storage of user conversations
- Session-based data only
- No personal information collection

## 🚀 Future Enhancements

### Planned Features
- [ ] Multi-modal support (document analysis)
- [ ] Advanced analytics dashboard
- [ ] Custom knowledge base upload
- [ ] Integration with ticketing systems

### Scalability Options
- [ ] Database backend for conversation history
- [ ] Redis caching for improved performance
- [ ] Kubernetes deployment configuration
- [ ] Load balancing for high availability

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 👤 Author

Built by **Han Yong Lim**  
GitHub: https://github.com/leroylim  
LinkedIn: https://www.linkedin.com/in/han-yong-lim-312b88a7/

## 🙏 Acknowledgments

- Built following best practices from the comprehensive IT Assistant documentation
- Inspired by modern RAG architectures and conversational AI patterns
- Designed for portfolio demonstration and real-world applicability

## 🧾 Credits

- UI framework: [Streamlit](https://streamlit.io/)
- LLM platform: [OpenRouter](https://openrouter.ai/)
- Real-time web search: [Exa](https://exa.ai/)
- Microsoft documentation: [Microsoft Learn](https://learn.microsoft.com/)
- AWS documentation: [AWS Docs](https://docs.aws.amazon.com/)

## 📞 Support

For questions or support, please:
1. Check the [Issues](https://github.com/leroylim/it-guru-assistant-chatbot/issues) page
2. Create a new issue with detailed description
3. Contact the maintainer through GitHub

---

**🔧 IT-Guru Assistant** - Demonstrating professional AI development skills through practical IT solutions.
