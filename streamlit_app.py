import streamlit as st
from playwright.sync_api import sync_playwright
from playwright_stealth import stealth_sync
from supabase import create_client, Client
import json
import time
import random
from datetime import datetime
import pandas as pd
from extraction_profiles import PROFILES, get_profile_choices
from enhanced_extractor import enhanced_crawl_with_extraction

# Initialize Supabase
@st.cache_resource
def init_supabase():
    return create_client(
        st.secrets["SUPABASE_URL"],
        st.secrets["SUPABASE_KEY"]
    )

supabase = init_supabase()

# Session state
if 'user' not in st.session_state:
    st.session_state.user = None

def signup_user(email, password, company_name, industry):
    """Register new user"""
    try:
        response = supabase.auth.sign_up({
            "email": email,
            "password": password,
            "options": {
                "data": {
                    "company_name": company_name,
                    "industry": industry
                }
            }
        })
        return response.user
    except Exception as e:
        st.error(f"Signup failed: {str(e)}")
        return None

def login_user(email, password):
    """Login user"""
    try:
        response = supabase.auth.sign_in_with_password({
            "email": email,
            "password": password
        })
        return response.user
    except Exception as e:
        st.error(f"Login failed: {str(e)}")
        return None

def logout_user():
    """Logout"""
    supabase.auth.sign_out()
    st.session_state.user = None

def save_crawl(user_id, url, profile, results):
    """Save crawl results to database"""
    data = {
        "user_id": user_id,
        "target_url": url,
        "profile_used": profile,
        "results": results,
        "page_count": len(results),
        "crawled_at": datetime.now().isoformat()
    }
    supabase.table("crawls").insert(data).execute()

def get_user_crawls(user_id, limit=10):
    """Get user's crawl history"""
    response = supabase.table("crawls")\
        .select("*")\
        .eq("user_id", user_id)\
        .order("crawled_at", desc=True)\
        .limit(limit)\
        .execute()
    return response.data

def login_page():
    """Login/Signup page"""
    st.title("🔍 SEO Site Crawler")
    
    tab1, tab2 = st.tabs(["Login", "Sign Up"])
    
    with tab1:
        with st.form("login_form"):
            email = st.text_input("Email")
            password = st.text_input("Password", type="password")
            submit = st.form_submit_button("Login")
            
            if submit:
                user = login_user(email, password)
                if user:
                    st.session_state.user = user
                    st.rerun()
    
    with tab2:
        with st.form("signup_form"):
            email = st.text_input("Email", key="signup_email")
            password = st.text_input("Password (min 6 chars)", type="password", key="signup_pass")
            company = st.text_input("Company Name")
            industry = st.selectbox("Industry", list(get_profile_choices().values()))
            submit = st.form_submit_button("Sign Up")
            
            if submit:
                if len(password) < 6:
                    st.error("Password must be at least 6 characters")
                else:
                    user = signup_user(email, password, company, industry)
                    if user:
                        st.success("Account created! Please log in.")

def main_app():
    """Main application"""
    st.set_page_config(page_title="SEO Crawler", page_icon="🔍", layout="wide")
    
    # Header
    col1, col2 = st.columns([6, 1])
    with col1:
        st.title("🔍 SEO Site Crawler")
        st.caption(f"Logged in as: {st.session_state.user.email}")
    with col2:
        if st.button("Logout"):
            logout_user()
            st.rerun()
    
    # Tabs
    tab1, tab2 = st.tabs(["🚀 New Crawl", "📊 History"])
    
    with tab1:
        with st.sidebar:
            st.header("Configuration")
            
            # Profile selection
            profile_key = st.selectbox(
                "Extraction Profile",
                options=list(PROFILES.keys()),
                format_func=lambda x: PROFILES[x]["name"]
            )
            
            st.info(PROFILES[profile_key]["description"])
            
            start_url = st.text_input("Website URL", "https://example.com")
            max_pages = st.number_input("Max Pages", 1, 500, 50)
            delay_min = st.slider("Min Delay (sec)", 1, 10, 3)
            delay_max = st.slider("Max Delay (sec)", 2, 15, 6)
        
        if st.button("🚀 Start Crawl", type="primary", use_container_width=True):
            if not start_url.startswith('http'):
                st.error("Enter valid URL")
            else:
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                with st.spinner("Crawling..."):
                    start_time = time.time()
                    results = enhanced_crawl_with_extraction(
                        start_url, max_pages, profile_key, 
                        delay_min, delay_max, progress_bar, status_text
                    )
                    elapsed = time.time() - start_time
                
                status_text.empty()
                progress_bar.empty()
                
                if results:
                    # Save to database
                    save_crawl(st.session_state.user.id, start_url, profile_key, results)
                    
                    st.success(f"✅ Crawled {len(results)} pages in {elapsed:.1f}s")
                    
                    # Display
                    df = pd.DataFrame(results)
                    st.dataframe(df, use_container_width=True)
                    
                    # Download
                    csv = df.to_csv(index=False).encode('utf-8')
                    st.download_button(
                        "📥 Download CSV",
                        csv,
                        f"crawl_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                        use_container_width=True
                    )
    
    with tab2:
        st.header("Your Crawl History")
        history = get_user_crawls(st.session_state.user.id)
        
        if history:
            for crawl in history:
                with st.expander(f"📄 {crawl['target_url']} - {crawl['crawled_at'][:10]} ({crawl['page_count']} pages)"):
                    st.write(f"**Profile used:** {PROFILES[crawl['profile_used']]['name']}")
                    st.write(f"**Pages crawled:** {crawl['page_count']}")
                    
                    df = pd.DataFrame(crawl['results'])
                    csv = df.to_csv(index=False).encode('utf-8')
                    st.download_button(
                        "Download CSV",
                        csv,
                        f"crawl_{crawl['id']}.csv",
                        key=crawl['id']
                    )
        else:
            st.info("No crawls yet!")

# Entry point
if st.session_state.user is None:
    login_page()
else:
    main_app()
