"""
Streamlit Web Application for Repeated Calls Service Bus Integration

This application provides:
1. Send CallEvent messages to Azure Service Bus
2. Receive and display messages from Service Bus
3. Invoke the orchestrator to process CallEvents
4. View processing results

Flow:
1. WebApp creates CallEvent from scenario → Service Bus
2. WebApp invokes orchestrator to process CallEvent
3. Results are put back into Service Bus
4. WebApp reads and displays results
"""

import streamlit as st
import asyncio
import json
import os
import subprocess
from datetime import datetime
from typing import List, Dict, Any, Optional
import sys
from pathlib import Path

# Add the parent directory to the path so we can import our modules
sys.path.append(str(Path(__file__).parent.parent))

from repeated_calls.webapp.service_bus_operations import ServiceBusOperations
from repeated_calls.database.schemas import CallEvent

# Page configuration
st.set_page_config(
    page_title="Repeated Calls Service",
    page_icon="📞",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
if 'messages_sent' not in st.session_state:
    st.session_state.messages_sent = []
if 'messages_received' not in st.session_state:
    st.session_state.messages_received = []
if 'results_received' not in st.session_state:
    st.session_state.results_received = []
if 'processing_status' not in st.session_state:
    st.session_state.processing_status = {}

@st.cache_data
def load_scenarios() -> List[Dict[str, Any]]:
    """Load scenario specifications from JSON file."""
    try:
        scenarios_path = Path(__file__).parent.parent.parent / "data" / "scenarios" / "scenario_specifications.json"
        with open(scenarios_path, 'r') as file:
            return json.load(file)
    except FileNotFoundError:
        st.error(f"Scenario file not found at {scenarios_path}")
        return []
    except json.JSONDecodeError:
        st.error("Error parsing scenario JSON file")
        return []

def scenario_to_call_event(scenario: Dict[str, Any]) -> CallEvent:
    """Convert a scenario to a CallEvent object."""
    return CallEvent(
        id=scenario.get('call_event_id', 1),
        customer_id=scenario['customer']['customer_id'],
        sdc=scenario['scenario_details']['call_reason'],
        timestamp=datetime.now()
    )

async def send_call_event_async(call_event: CallEvent) -> bool:
    """Send a CallEvent to the Service Bus asynchronously."""
    try:
        message_data = {
            "id": call_event.id,
            "customer_id": call_event.customer_id,
            "sdc": call_event.sdc,
            "timestamp": call_event.timestamp.isoformat()
        }
        success = await ServiceBusOperations.send_message(message_data)
        if success:
            st.session_state.messages_sent.append({
                "timestamp": datetime.now(),
                "call_event": call_event,
                "status": "sent"
            })
        return success
    except Exception as e:
        st.error(f"Error sending message: {str(e)}")
        return False

async def receive_messages_async() -> List[Dict[str, Any]]:
    """Receive messages from the Service Bus asynchronously."""
    try:
        messages = await ServiceBusOperations.receive_messages()
        if messages:
            st.session_state.messages_received.extend([
                {
                    "timestamp": datetime.now(),
                    "content": msg,
                    "processed": False
                } for msg in messages
            ])
        return messages
    except Exception as e:
        st.error(f"Error receiving messages: {str(e)}")
        return []

async def receive_results_async() -> List[Dict[str, Any]]:
    """Receive result messages from the Service Bus asynchronously."""
    try:
        results = await ServiceBusOperations.receive_results()
        if results:
            st.session_state.results_received.extend([
                {
                    "timestamp": datetime.now(),
                    "content": result
                } for result in results
            ])
        return results
    except Exception as e:
        st.error(f"Error receiving results: {str(e)}")
        return []

def invoke_orchestrator() -> bool:
    """Invoke the main orchestrator to process CallEvents."""
    try:
        # Path to the main.py orchestrator
        orchestrator_path = Path(__file__).parent.parent / "orchestrator" / "main.py"
        
        # Run the orchestrator as a subprocess
        result = subprocess.run(
            [sys.executable, str(orchestrator_path)],
            capture_output=True,
            text=True,
            timeout=300  # 5 minute timeout
        )
        
        if result.returncode == 0:
            st.success("Orchestrator executed successfully!")
            st.session_state.processing_status[datetime.now().isoformat()] = {
                "status": "success",
                "stdout": result.stdout,
                "stderr": result.stderr
            }
            return True
        else:
            st.error(f"Orchestrator failed with return code {result.returncode}")
            st.error(f"Error output: {result.stderr}")
            st.session_state.processing_status[datetime.now().isoformat()] = {
                "status": "failed",
                "stdout": result.stdout,
                "stderr": result.stderr
            }
            return False
            
    except subprocess.TimeoutExpired:
        st.error("Orchestrator execution timed out (5 minutes)")
        return False
    except Exception as e:
        st.error(f"Error invoking orchestrator: {str(e)}")
        return False

def main():
    """Main Streamlit application."""
    st.title("📞 Repeated Calls Service Bus Integration")
    st.markdown("---")
    
    # Load scenarios
    scenarios = load_scenarios()
    
    # Sidebar navigation
    st.sidebar.title("Navigation")
    page = st.sidebar.selectbox(
        "Select Page",
        ["Send Messages", "Receive Messages", "Process Messages", "View Results", "Status Dashboard"]
    )
    
    if page == "Send Messages":
        st.header("📤 Send CallEvent Messages")
        
        if not scenarios:
            st.warning("No scenarios available. Please check the scenario file.")
            return
            
        # Scenario selection
        scenario_options = [f"Scenario {i+1}: {scenario['title']}" for i, scenario in enumerate(scenarios)]
        selected_scenario_idx = st.selectbox("Select a scenario:", range(len(scenario_options)), format_func=lambda x: scenario_options[x])
        
        selected_scenario = scenarios[selected_scenario_idx]
        
        # Display scenario details
        with st.expander("📋 Scenario Details", expanded=True):
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("Customer Information")
                st.write(f"**Name:** {selected_scenario['customer']['name']}")
                st.write(f"**ID:** {selected_scenario['customer']['customer_id']}")
                st.write(f"**CLV:** {selected_scenario['customer']['clv']}")
                
                st.subheader("Product Information")
                st.write(f"**Product:** {selected_scenario['product']['name']}")
                st.write(f"**Type:** {selected_scenario['product']['type']}")
                
            with col2:
                st.subheader("Call Details")
                st.write(f"**Call Reason:** {selected_scenario['scenario_details']['call_reason']}")
                st.write(f"**Primary Call Date:** {selected_scenario['dates']['primary_call_date']}")
                if selected_scenario['dates']['previous_call_dates']:
                    st.write(f"**Previous Calls:** {', '.join(selected_scenario['dates']['previous_call_dates'])}")
        
        # Send message button
        if st.button("📤 Send CallEvent to Service Bus", type="primary"):
            call_event = scenario_to_call_event(selected_scenario)
            
            with st.spinner("Sending message to Service Bus..."):
                success = asyncio.run(send_call_event_async(call_event))
                
            if success:
                st.success("✅ CallEvent sent successfully!")
                st.json({
                    "id": call_event.id,
                    "customer_id": call_event.customer_id,
                    "sdc": call_event.sdc,
                    "timestamp": call_event.timestamp.isoformat()
                })
            else:
                st.error("❌ Failed to send CallEvent")
                
    elif page == "Receive Messages":
        st.header("📥 Receive Messages from Service Bus")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("🔄 Refresh Messages", type="primary"):
                with st.spinner("Receiving messages from Service Bus..."):
                    messages = asyncio.run(receive_messages_async())
                    
                if messages:
                    st.success(f"✅ Received {len(messages)} new messages")
                else:
                    st.info("📭 No new messages in queue")
        
        with col2:
            if st.button("🧹 Clear Message History"):
                st.session_state.messages_received = []
                st.success("✅ Message history cleared")
        
        # Display received messages
        if st.session_state.messages_received:
            st.subheader("📨 Received Messages")
            for i, msg_info in enumerate(reversed(st.session_state.messages_received)):
                with st.expander(f"Message {len(st.session_state.messages_received) - i} - {msg_info['timestamp'].strftime('%Y-%m-%d %H:%M:%S')}"):
                    st.code(msg_info['content'], language="json")
        else:
            st.info("📭 No messages received yet")
            
    elif page == "Process Messages":
        st.header("⚙️ Process CallEvents with Orchestrator")
        
        st.markdown("""
        **Processing Flow:**
        1. Messages are retrieved from Service Bus
        2. Orchestrator processes the CallEvents
        3. Results are sent back to Service Bus
        4. You can view results in the 'View Results' tab
        """)
        
        if st.button("🚀 Run Orchestrator", type="primary"):
            with st.spinner("Running orchestrator... This may take a few minutes."):
                success = invoke_orchestrator()
                
            if success:
                st.success("✅ Processing completed successfully!")
                st.info("📝 Check the 'View Results' tab to see processing outcomes")
            else:
                st.error("❌ Processing failed - check the logs below")
                
        # Show recent processing status
        if st.session_state.processing_status:
            st.subheader("📊 Recent Processing Status")
            for timestamp, status in reversed(list(st.session_state.processing_status.items())):
                with st.expander(f"Processing run - {timestamp}"):
                    st.write(f"**Status:** {status['status']}")
                    if status['stdout']:
                        st.text_area("Standard Output:", status['stdout'], height=200)
                    if status['stderr']:
                        st.text_area("Error Output:", status['stderr'], height=100)
                        
    elif page == "View Results":
        st.header("📊 View Processing Results")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("🔄 Refresh Results", type="primary"):
                with st.spinner("Receiving results from Service Bus..."):
                    results = asyncio.run(receive_results_async())
                    
                if results:
                    st.success(f"✅ Received {len(results)} new results")
                else:
                    st.info("📭 No new results available")
        
        with col2:
            if st.button("🧹 Clear Results History"):
                st.session_state.results_received = []
                st.success("✅ Results history cleared")
        
        # Display results
        if st.session_state.results_received:
            st.subheader("🏆 Processing Results")
            for i, result_info in enumerate(reversed(st.session_state.results_received)):
                with st.expander(f"Result {len(st.session_state.results_received) - i} - {result_info['timestamp'].strftime('%Y-%m-%d %H:%M:%S')}"):
                    st.json(result_info['content'])
        else:
            st.info("📭 No results received yet")
            
    elif page == "Status Dashboard":
        st.header("📈 Status Dashboard")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Messages Sent", len(st.session_state.messages_sent))
            
        with col2:
            st.metric("Messages Received", len(st.session_state.messages_received))
            
        with col3:
            st.metric("Results Received", len(st.session_state.results_received))
        
        # Recent activity
        st.subheader("🕒 Recent Activity")
        
        # Combine all activities and sort by timestamp
        all_activities = []
        
        for msg in st.session_state.messages_sent:
            all_activities.append({
                "timestamp": msg["timestamp"],
                "type": "📤 Sent",
                "description": f"CallEvent for Customer {msg['call_event'].customer_id}"
            })
            
        for msg in st.session_state.messages_received:
            all_activities.append({
                "timestamp": msg["timestamp"],
                "type": "📥 Received",
                "description": "Message from Service Bus"
            })
            
        for result in st.session_state.results_received:
            all_activities.append({
                "timestamp": result["timestamp"],
                "type": "🏆 Result",
                "description": "Processing result received"
            })
        
        # Sort by timestamp (most recent first)
        all_activities.sort(key=lambda x: x["timestamp"], reverse=True)
        
        # Display recent activities
        if all_activities:
            for activity in all_activities[:10]:  # Show last 10 activities
                st.write(f"{activity['type']} - {activity['description']} ({activity['timestamp'].strftime('%H:%M:%S')})")
        else:
            st.info("No recent activity")

if __name__ == "__main__":
    main()
