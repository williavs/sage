import streamlit as st

# Must be the first Streamlit command
st.set_page_config(
    page_title="Setup Guide - SlackSage",
    page_icon="assets/logo.png",
    layout="wide"
)

def show_footer():
    """Display the footer with links."""
    st.divider()
    footer_cols = st.columns([1, 4, 1])
    
    with footer_cols[1]:
        st.markdown("""
        <div style="text-align: center;">
            <a href="https://github.com/williavs" target="_blank">
                <img src="https://img.shields.io/badge/GitHub-100000?style=for-the-badge&logo=github&logoColor=white" height="28px"/>
            </a>&nbsp;
            <a href="https://www.linkedin.com/in/willyv3/" target="_blank">
                <img src="https://img.shields.io/badge/LinkedIn-0077B5?style=for-the-badge&logo=linkedin&logoColor=white" height="28px"/>
            </a>&nbsp;
            <a href="https://v3-ai.com" target="_blank">
                <img src="https://img.shields.io/badge/V3_AI-FF4B4B?style=for-the-badge&logo=safari&logoColor=white" height="28px"/>
            </a>&nbsp;
            <a href="https://pmfeels.com" target="_blank">
                <img src="https://img.shields.io/badge/PM_Feels-4A154B?style=for-the-badge&logo=slack&logoColor=white" height="28px"/>
            </a>
        </div>
        """, unsafe_allow_html=True)

# Move logo to sidebar
st.sidebar.image("../assets/logo.png", use_container_width=True)
st.sidebar.markdown("---")

st.title("🔧 Setup Guide")

st.markdown("""
Welcome to the SlackSage setup guide! Follow these steps to get your AI-powered knowledge assistant up and running.
""")

# Step 1: Create Slack App
with st.expander("Step 1: Create Your Slack App", expanded=True):
    st.markdown("""
    ### 1. Create a New Slack App
    1. Go to [Slack API Dashboard](https://api.slack.com/apps)
    2. Click "Create New App"
    3. Choose "From scratch"
    4. Name your app "SlackSage" and select your workspace
    
    ### 2. Configure Socket Mode
    1. Navigate to "Socket Mode" in the sidebar
    2. Enable Socket Mode
    3. Generate and save your App-Level Token
    4. This will be your `SLACK_APP_TOKEN` (starts with `xapp-`)
    """)

# Step 2: Configure Bot Permissions
with st.expander("Step 2: Configure Bot Permissions"):
    st.markdown("""
    ### Add Required Bot Scopes
    Navigate to "OAuth & Permissions" and add these Bot Token Scopes:
    - `app_mentions:read` - Allow bot to see when it's mentioned
    - `channels:history` - View messages in channels
    - `chat:write` - Send messages as the bot
    - `mpim:read` - Access group messages
    
    After adding scopes:
    1. Click "Install to Workspace"
    2. Copy the "Bot User OAuth Token" (starts with `xoxb-`)
    3. This will be your `SLACK_BOT_TOKEN`
    """)

# Step 3: Enable Events
with st.expander("Step 3: Enable Event Subscriptions"):
    st.markdown("""
    ### Configure Event Subscriptions
    1. Go to "Event Subscriptions"
    2. Toggle "Enable Events"
    3. Under "Subscribe to bot events" add:
        - `app_mentions` - To respond when @mentioned
        - `message.channels` - To process channel messages
    
    Note: With Socket Mode enabled, you don't need to configure a Request URL
    """)

# Step 4: Final Configuration
with st.expander("Step 4: Final Configuration Steps"):
    st.markdown("""
    ### Complete Setup
    1. Get your OpenAI API key:
        - Go to [OpenAI API Keys](https://platform.openai.com/api-keys)
        - Click "Create new secret key"
        - Copy your key immediately (you won't be able to see it again!)
    2. Return to the main SlackSage interface
    3. Enter your credentials:
        - Paste your OpenAI API Key in the Credentials tab
        - Add your Slack Bot Token (`xoxb-` token from Step 2)
        - Add your Slack App Token (`xapp-` token from Step 1)
    4. Upload your documents
    5. Start the bot!
    
    ### Testing the Bot
    1. Invite @SlackSage to a channel using `/invite @SlackSage`
    2. Mention the bot using `@SlackSage` followed by your question
    3. The bot will respond with relevant information from your documents
    """)

# Troubleshooting Section
with st.expander("Troubleshooting"):
    st.markdown("""
    ### Common Issues
    
    **Bot Not Responding**
    - Verify all tokens are correct
    - Ensure bot is invited to the channel
    - Check that Socket Mode is enabled
    - Confirm all required scopes are added
    
    **Permission Errors**
    - Reinstall the app to update permissions
    - Verify all required scopes are added
    
    **Document Processing Issues**
    - Ensure documents are in supported formats
    - Check that documents are properly uploaded
    - Verify OpenAI API key is valid
    """)

st.divider()

st.markdown("""
### Need Help?
If you encounter any issues not covered here, please reach out:
- Check the [GitHub repository](https://github.com/williavs) for updates
- Connect on [LinkedIn](https://www.linkedin.com/in/willyv3/) for support
- Visit [V3 AI](https://v3-ai.com) for custom solutions
""")

# Add footer at the end
show_footer() 