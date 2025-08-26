import streamlit as st
import pandas as pd
import psycopg2
from datetime import datetime
import plotly.express as px
import plotly.graph_objects as go

# Set page config - No changes needed here
st.set_page_config(
    page_title="E-Commerce Analysis Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling - No changes needed here
st.markdown("""
<style>
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
    .stSelectbox {
        margin-bottom: 1rem;
    }
</style>
""", unsafe_allow_html=True)

# Main app
def main():
    st.title("🛒 E-Commerce Data Analysis Dashboard")
    st.markdown("---")
    
    # --- SIMPLIFIED DATABASE CONNECTION ---
    # st.connection handles secrets, caching, and retries automatically.
    try:
        conn = st.connection("postgresql", type="sql")
        st.success("✅ Connected to database successfully!")
    except Exception as e:
        st.error(f"❌ Unable to connect to database. Please check your connection settings in .streamlit/secrets.toml", icon="🚨")
        st.stop() # Stop the app if connection fails

    # Sidebar navigation - No changes needed here
    st.sidebar.title(" Navigation")
    analysis_type = st.sidebar.selectbox(
        "Choose Analysis Type:",
        [
            " Overview",
            " Customer Analysis", 
            " Order Analysis",
            " Sales & Revenue",
            " Time Series Analysis",
        ]
    )
    
    if analysis_type == " Overview":
        st.header("Dashboard Overview")
        
        # Key Metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            df = conn.query("SELECT COUNT(customer_id) FROM customers", ttl=600)
            st.metric("Total Customers", f"{df.iloc[0,0]:,}")
        
        with col2:
            df = conn.query("SELECT COUNT(DISTINCT order_id) FROM orders", ttl=600)
            st.metric("Unique Orders", f"{df.iloc[0,0]:,}")
        
        with col3:
            df = conn.query("SELECT COUNT(*) FROM orders", ttl=600)
            st.metric("Order Records", f"{df.iloc[0,0]:,}")
        
        with col4:
            df = conn.query("SELECT ROUND(SUM(payment_value)::NUMERIC, 2) FROM payments", ttl=600)
            st.metric("Total Revenue", f"${df.iloc[0,0]:,.2f}")
        
        st.markdown("---")
        
        st.info(" *Data Note*: 'Unique Orders' shows distinct business transactions, while 'Order Records' shows total database rows (including duplicates).")
        
        col_a, col_b = st.columns(2)
        
        with col_a:
            df = conn.query("SELECT COUNT(DISTINCT customer_id) FROM orders", ttl=600)
            st.metric("Active Customers", f"{df.iloc[0,0]:,}")
        
        with col_b:
            df = conn.query("SELECT ROUND(AVG(payment_value)::NUMERIC, 2) FROM payments", ttl=600)
            st.metric("Avg Order Value", f"${df.iloc[0,0]:,.2f}")
        
        # --- UI Section - Unchanged ---
        st.markdown("###  About This Dashboard")
        st.markdown("This dashboard analyzes e-commerce data including:")
        st.markdown("• *Customer Demographics*: Cities, states, and customer distribution")
        st.markdown("• *Order Patterns*: Monthly trends, seasonal analysis")
        st.markdown("• *Sales Performance*: Category-wise sales, revenue analysis") 
        st.markdown("• *Business Metrics*: Growth rates, retention, top performers")
        st.markdown("Navigate through different sections using the sidebar to explore various aspects of the data.")
    
    elif analysis_type == " Customer Analysis":
        st.header("Customer Analysis")
        
        query = """
        SELECT customer_state AS "State", COUNT(*) AS "Customer Count"
        FROM customers
        GROUP BY customer_state
        ORDER BY "Customer Count" DESC
        LIMIT 10
        """
        df = conn.query(query, ttl=600)
        
        if not df.empty:
            fig = px.bar(df, x='State', y='Customer Count', title="Top 10 States by Customer Count")
            st.plotly_chart(fig, use_container_width=True)
            st.dataframe(df)
    
    elif analysis_type == " Order Analysis":
        st.header("Order Analysis")
        st.subheader("Order Statistics")
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            df = conn.query("SELECT COUNT(DISTINCT order_id) FROM orders", ttl=600)
            st.metric("Unique Orders", f"{df.iloc[0,0]:,}")
        
        with col2:
            query = "SELECT ROUND((COUNT(DISTINCT order_id) * 1.0 / COUNT(DISTINCT customer_id))::NUMERIC, 2) FROM orders"
            df = conn.query(query, ttl=600)
            st.metric("Orders per Customer", f"{df.iloc[0,0]:.2f}")
        
        with col3:
            df = conn.query("SELECT ROUND(AVG(payment_value)::NUMERIC, 2) FROM payments", ttl=600)
            st.metric("Avg Order Value", f"${df.iloc[0,0]:,.2f}")
        
        with col4:
            df = conn.query("SELECT COUNT(DISTINCT product_id) FROM products", ttl=600)
            st.metric("Total Products", f"{df.iloc[0,0]:,}")
        
        st.subheader(" Data Quality")
        col_a, col_b = st.columns(2)
        
        with col_a:
            df = conn.query("SELECT COUNT(*) FROM orders", ttl=600)
            st.metric("Order Records", f"{df.iloc[0,0]:,}")
        
        with col_b:
            query = "SELECT ROUND((COUNT(*) * 1.0 / COUNT(DISTINCT order_id))::NUMERIC, 1) FROM orders"
            df = conn.query(query, ttl=600)
            st.metric("Duplicate Factor", f"{df.iloc[0,0]}x")
        
        st.info(" *Note*: Each order appears multiple times in the database. This could be due to order updates, multiple items, or data import issues.")
        
        st.subheader(" Orders by Status")
        query = """
        SELECT order_status AS "Status", COUNT(DISTINCT order_id) AS "Count" 
        FROM orders 
        GROUP BY order_status 
        ORDER BY "Count" DESC
        """
        df = conn.query(query, ttl=600)
        if not df.empty:
            fig = px.bar(df, x='Status', y='Count', title="Unique Orders by Status")
            fig.update_xaxes(tickangle=45)
            st.plotly_chart(fig, use_container_width=True)
        
        st.subheader("📅 Orders Over Time")
        query = """
        SELECT 
            TO_CHAR(order_purchase_timestamp::TIMESTAMP, 'YYYY-MM') AS "Month",
            COUNT(DISTINCT order_id) AS "Order Count"
        FROM orders
        GROUP BY "Month"
        ORDER BY "Month"
        """
        df = conn.query(query, ttl=600)
        if not df.empty:
            fig = px.line(df, x='Month', y='Order Count', title="Unique Orders Over Time")
            st.plotly_chart(fig, use_container_width=True)
    
    elif analysis_type == " Sales & Revenue":
        st.header("Sales & Revenue Analysis")
        
        query = """
        SELECT 
            p."product category" AS "Category",
            ROUND(SUM(pay.payment_value)::NUMERIC, 2) AS "Revenue"
        FROM products p
        JOIN order_items oi ON p.product_id = oi.product_id
        JOIN payments pay ON oi.order_id = pay.order_id
        GROUP BY "Category"
        ORDER BY "Revenue" DESC
        LIMIT 10
        """
        df = conn.query(query, ttl=600)
        if not df.empty:
            fig = px.bar(df, x='Category', y='Revenue', title="Revenue by Product Category")
            fig.update_xaxes(tickangle=45)
            st.plotly_chart(fig, use_container_width=True)
            st.dataframe(df)
    
    elif analysis_type == " Time Series Analysis":
        st.header("Time Series Analysis")
        
        query = """
        SELECT 
            TO_CHAR(o.order_purchase_timestamp::TIMESTAMP, 'YYYY-MM') AS "Month",
            ROUND(SUM(p.payment_value)::NUMERIC, 2) AS "Revenue",
            COUNT(DISTINCT o.order_id) AS "Order Count"
        FROM (SELECT DISTINCT order_id, order_purchase_timestamp FROM orders) o
        JOIN payments p ON o.order_id = p.order_id
        GROUP BY "Month"
        ORDER BY "Month"
        """
        df = conn.query(query, ttl=600)
        if not df.empty:
            col1, col2 = st.columns(2)
            with col1:
                fig1 = px.line(df, x='Month', y='Revenue', title="Monthly Revenue Trend")
                st.plotly_chart(fig1, use_container_width=True)
            with col2:
                fig2 = px.line(df, x='Month', y='Order Count', title="Monthly Order Count")
                st.plotly_chart(fig2, use_container_width=True)
            st.dataframe(df)
    
    # --- Footer and Links Section - Unchanged ---
    st.markdown("---")
    st.markdown("### 📊 Dashboard created using Streamlit")
    st.markdown("Data source: E-commerce PostgreSQL Database")
    
    st.markdown("---")
    st.markdown("### 👨‍💻 Created by Punarbasu Chakraborty")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("🔗 *LinkedIn*")
        st.markdown("[Connect with me](https://linkedin.com/in/punarbasu-chakraborty-628566252/)")
    with col2:
        st.markdown("🐙 *GitHub*")
        st.markdown("[View my projects](https://github.com/punarchakra02)")
    with col3:
        st.markdown("📧 *Email*")
        st.markdown("[Contact me](mailto:punarbasu02chakra@gmail.com)")
    
    st.markdown("---")
    st.markdown("Built with ❤ using Python, SQL & Streamlit")

if _name_ == "_main_":
    main()