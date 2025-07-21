"""
Results Page Module for CreditRisk AI Suite
Enhanced results display with comprehensive reporting and export capabilities
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import plotly.subplots as sp
import json
import base64
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import io
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
import matplotlib.pyplot as plt
import seaborn as sns

def generate_risk_explanation(result: Dict[str, Any]) -> str:
    """Generate natural language explanation of risk assessment"""
    
    risk_score = result.get('risk_score', 0)
    risk_level = result.get('risk_level', 'Unknown')
    approval_probability = result.get('approval_probability', 0)
    recommendation = result.get('recommendation', 'Unknown')
    
    # Base explanation
    explanation = f"""
## Risk Assessment Summary

**Overall Risk Score: {risk_score}/100**

Based on our comprehensive analysis, this application has been assigned a risk score of **{risk_score}/100**, which corresponds to a **{risk_level.lower()}** risk level. 

### Key Findings

**Risk Level Assessment:**
"""
    
    if risk_score >= 80:
        explanation += """
- **Excellent Credit Profile**: The applicant demonstrates exceptional creditworthiness
- **Strong Financial Position**: Income, assets, and debt ratios are all favorable
- **Low Default Risk**: Historical payment behavior indicates high reliability
- **Recommended Action**: **Approve** with competitive terms
"""
    elif risk_score >= 70:
        explanation += """
- **Good Credit Profile**: The applicant shows strong creditworthiness
- **Solid Financial Foundation**: Income and debt ratios are within acceptable ranges
- **Moderate Default Risk**: Payment history shows good reliability
- **Recommended Action**: **Approve** with standard terms
"""
    elif risk_score >= 60:
        explanation += """
- **Fair Credit Profile**: The applicant meets basic credit requirements
- **Adequate Financial Position**: Income and debt ratios are acceptable
- **Moderate-High Default Risk**: Some concerns in payment history
- **Recommended Action**: **Approve with Conditions** or higher rates
"""
    elif risk_score >= 50:
        explanation += """
- **Poor Credit Profile**: The applicant has significant credit concerns
- **Weak Financial Position**: Income and debt ratios are concerning
- **High Default Risk**: Poor payment history indicates reliability issues
- **Recommended Action**: **Deny** or require significant collateral
"""
    else:
        explanation += """
- **Very Poor Credit Profile**: The applicant has severe credit issues
- **Critical Financial Position**: Income and debt ratios are problematic
- **Very High Default Risk**: Poor payment history and financial instability
- **Recommended Action**: **Deny** - does not meet minimum requirements
"""
    
    # Add approval probability explanation
    explanation += f"""
### Approval Probability: {approval_probability:.1%}

The system calculates a **{approval_probability:.1%}** probability of approval based on:
- Historical data analysis
- Industry benchmarks
- Current market conditions
- Applicant-specific factors

### Final Recommendation: {recommendation}

**{recommendation.upper()}** - This recommendation is based on:
- Risk score analysis
- Financial ratio evaluation
- Credit history assessment
- Market condition analysis
"""
    
    return explanation

def generate_detailed_analysis(result: Dict[str, Any]) -> str:
    """Generate detailed analysis explanation"""
    
    app_data = result.get('application_data', {})
    
    explanation = """
## Detailed Analysis Breakdown

### Financial Health Assessment
"""
    
    # Credit score analysis
    credit_score = app_data.get('credit_score', 0)
    if credit_score is None:
        explanation += "- **Credit Score**: Not available\n"
    elif credit_score >= 750:
        explanation += f"- **Credit Score ({credit_score})**: Excellent - Indicates exceptional credit management\n"
    elif credit_score >= 700:
        explanation += f"- **Credit Score ({credit_score})**: Good - Shows responsible credit behavior\n"
    elif credit_score >= 650:
        explanation += f"- **Credit Score ({credit_score})**: Fair - Some concerns but generally acceptable\n"
    else:
        explanation += f"- **Credit Score ({credit_score})**: Poor - Significant credit management issues\n"
    
    # Income analysis
    annual_income = app_data.get('annual_income', 0)
    loan_amount = app_data.get('loan_amount', 0)
    if annual_income is None:
        explanation += "- **Income Analysis**: Not available\n"
    elif annual_income > 0:
        income_ratio = (loan_amount / annual_income) * 100
        explanation += f"- **Income Analysis**: ${annual_income:,.2f} annual income\n"
        explanation += f"- **Loan-to-Income Ratio**: {income_ratio:.1f}% "
        if income_ratio <= 20:
            explanation += "(Excellent - Very manageable)\n"
        elif income_ratio <= 40:
            explanation += "(Good - Within acceptable range)\n"
        else:
            explanation += "(Concerning - May strain finances)\n"
    else:
        explanation += "- **Income Analysis**: Not available\n"
    
    # Employment analysis
    employment_years = app_data.get('employment_years', 0)
    explanation += f"- **Employment Stability**: {employment_years} years at current job\n"
    if employment_years >= 5:
        explanation += "  - Strong employment stability\n"
    elif employment_years >= 2:
        explanation += "  - Adequate employment history\n"
    else:
        explanation += "  - Limited employment history - may be a concern\n"
    
    # Risk indicators analysis
    if 'risk_indicators' in app_data:
        indicators = app_data['risk_indicators']
        explanation += "\n### Risk Indicators Analysis\n"
        
        dti_ratio = indicators.get('debt_to_income_ratio', 0)
        explanation += f"- **Debt-to-Income Ratio**: {dti_ratio:.1f}% "
        if dti_ratio <= 30:
            explanation += "(Excellent - Low debt burden)\n"
        elif dti_ratio <= 50:
            explanation += "(Acceptable - Manageable debt level)\n"
        else:
            explanation += "(Concerning - High debt burden)\n"
        
        net_worth = indicators.get('net_worth', 0)
        explanation += f"- **Net Worth**: ${net_worth:,.2f} "
        if net_worth >= 0:
            explanation += "(Positive - Good financial position)\n"
        else:
            explanation += "(Negative - Financial concerns)\n"
    
    return explanation

def create_risk_radar_chart(result: Dict[str, Any]) -> go.Figure:
    """Create radar chart for risk assessment"""
    
    app_data = result.get('application_data', {})
    
    # Calculate risk factors
    credit_score = app_data.get('credit_score', 0)
    credit_risk = max(0, 100 - (credit_score / 850 * 100))  # Invert credit score
    
    annual_income = app_data.get('annual_income', 0)
    loan_amount = app_data.get('loan_amount', 0)
    income_risk = min(100, (loan_amount / max(annual_income, 1)) * 100 * 2)  # Loan-to-income ratio
    
    employment_years = app_data.get('employment_years', 0)
    employment_risk = max(0, 100 - (employment_years * 10))  # More years = lower risk
    
    # Get risk indicators if available
    if 'risk_indicators' in app_data:
        indicators = app_data['risk_indicators']
        dti_risk = min(100, indicators.get('debt_to_income_ratio', 0))
        net_worth_risk = max(0, 100 - (indicators.get('net_worth', 0) / 100000 * 100))
    else:
        dti_risk = 50  # Default value
        net_worth_risk = 50  # Default value
    
    # Create radar chart
    categories = ['Credit Risk', 'Income Risk', 'Employment Risk', 'Debt-to-Income Risk', 'Net Worth Risk']
    values = [credit_risk, income_risk, employment_risk, dti_risk, net_worth_risk]
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatterpolar(
        r=values,
        theta=categories,
        fill='toself',
        name='Risk Assessment',
        line_color='red',
        fillcolor='rgba(255, 0, 0, 0.3)'
    ))
    
    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 100]
            )),
        showlegend=False,
        title="Risk Assessment Radar Chart",
        height=400
    )
    
    return fig

def create_risk_score_gauge(result: Dict[str, Any]) -> go.Figure:
    """Create gauge chart for risk score"""
    
    risk_score = result.get('risk_score', 0)
    
    fig = go.Figure(go.Indicator(
        mode = "gauge+number+delta",
        value = risk_score,
        domain = {'x': [0, 1], 'y': [0, 1]},
        title = {'text': "Risk Score"},
        delta = {'reference': 50},
        gauge = {
            'axis': {'range': [None, 100]},
            'bar': {'color': "darkblue"},
            'steps': [
                {'range': [0, 20], 'color': "lightgray"},
                {'range': [20, 40], 'color': "yellow"},
                {'range': [40, 60], 'color': "orange"},
                {'range': [60, 80], 'color': "lightgreen"},
                {'range': [80, 100], 'color': "green"}
            ],
            'threshold': {
                'line': {'color': "red", 'width': 4},
                'thickness': 0.75,
                'value': 90
            }
        }
    ))
    
    fig.update_layout(height=300)
    return fig

def create_financial_breakdown_chart(result: Dict[str, Any]) -> Optional[go.Figure]:
    """Create financial breakdown visualization"""
    
    app_data = result.get('application_data', {})
    
    if 'assets' in app_data and 'liabilities' in app_data:
        assets = app_data['assets']
        liabilities = app_data['liabilities']
        
        # Prepare data for visualization
        asset_data = {
            'Checking': assets.get('checking', 0),
            'Savings': assets.get('savings', 0),
            'Investments': assets.get('investments', 0),
            'Real Estate': assets.get('real_estate', 0)
        }
        
        liability_data = {
            'Credit Cards': liabilities.get('credit_cards', 0),
            'Other Loans': liabilities.get('loans', 0),
            'Mortgage': liabilities.get('mortgage', 0),
            'Other Debt': liabilities.get('other_debt', 0)
        }
        
        # Create subplot
        fig = sp.make_subplots(
            rows=1, cols=2,
            subplot_titles=('Assets Breakdown', 'Liabilities Breakdown'),
            specs=[[{"type": "pie"}, {"type": "pie"}]]
        )
        
        # Assets pie chart
        fig.add_trace(
            go.Pie(labels=list(asset_data.keys()), values=list(asset_data.values()), name="Assets"),
            row=1, col=1
        )
        
        # Liabilities pie chart
        fig.add_trace(
            go.Pie(labels=list(liability_data.keys()), values=list(liability_data.values()), name="Liabilities"),
            row=1, col=2
        )
        
        fig.update_layout(height=400, title_text="Financial Position Breakdown")
        
        return fig
    
    return None

def create_approval_probability_chart(result: Dict[str, Any]) -> go.Figure:
    """Create approval probability visualization"""
    
    approval_probability = result.get('approval_probability', 0)
    
    fig = go.Figure(go.Indicator(
        mode = "gauge+number",
        value = approval_probability * 100,
        domain = {'x': [0, 1], 'y': [0, 1]},
        title = {'text': "Approval Probability"},
        gauge = {
            'axis': {'range': [None, 100]},
            'bar': {'color': "darkgreen"},
            'steps': [
                {'range': [0, 30], 'color': "red"},
                {'range': [30, 60], 'color': "orange"},
                {'range': [60, 80], 'color': "yellow"},
                {'range': [80, 100], 'color': "green"}
            ],
            'threshold': {
                'line': {'color': "red", 'width': 4},
                'thickness': 0.75,
                'value': 50
            }
        }
    ))
    
    fig.update_layout(height=300)
    return fig

def generate_pdf_report(result: Dict[str, Any]) -> bytes:
    """Generate PDF report"""
    
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    styles = getSampleStyleSheet()
    story = []
    
    # Title
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        spaceAfter=30,
        alignment=1  # Center alignment
    )
    story.append(Paragraph("Credit Risk Analysis Report", title_style))
    story.append(Spacer(1, 20))
    
    # Customer Information
    app_data = result.get('application_data', {})
    story.append(Paragraph("Customer Information", styles['Heading2']))
    
    customer_info = [
        ['Customer ID', app_data.get('customer_id', 'N/A')],
        ['Name', app_data.get('name', 'N/A')],
        ['Email', app_data.get('email', 'N/A')],
        ['Phone', app_data.get('phone', 'N/A')],
        ['Age', str(app_data.get('age', 'N/A'))],
        ['Annual Income', f"${app_data.get('annual_income', 0):,.2f}"],
        ['Credit Score', str(app_data.get('credit_score', 'N/A'))]
    ]
    
    customer_table = Table(customer_info, colWidths=[2*inch, 3*inch])
    customer_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    story.append(customer_table)
    story.append(Spacer(1, 20))
    
    # Analysis Results
    story.append(Paragraph("Analysis Results", styles['Heading2']))
    
    results_info = [
        ['Risk Score', f"{result.get('risk_score', 0)}/100"],
        ['Risk Level', result.get('risk_level', 'N/A')],
        ['Approval Probability', f"{result.get('approval_probability', 0):.1%}"],
        ['Recommendation', result.get('recommendation', 'N/A')],
        ['Recommended Rate', f"{result.get('recommended_rate', 0):.2f}%"],
        ['Recommended Amount', f"${result.get('recommended_amount', 0):,.2f}"],
        ['Execution Time', f"{result.get('execution_time', 0):.2f} seconds"]
    ]
    
    results_table = Table(results_info, colWidths=[2*inch, 3*inch])
    results_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    story.append(results_table)
    story.append(Spacer(1, 20))
    
    # Analysis Explanation
    story.append(Paragraph("Analysis Explanation", styles['Heading2']))
    explanation = generate_risk_explanation(result)
    story.append(Paragraph(explanation, styles['Normal']))
    
    # Footer
    story.append(Spacer(1, 30))
    footer_style = ParagraphStyle(
        'Footer',
        parent=styles['Normal'],
        fontSize=10,
        alignment=1,
        textColor=colors.grey
    )
    story.append(Paragraph(f"Report generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", footer_style))
    
    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()

def render_results_page():
    """Render the enhanced results page"""
    st.markdown('<h1 class="sub-header">📊 Risk Assessment Results</h1>', unsafe_allow_html=True)
    
    if not st.session_state.analysis_results:
        st.info("No analysis results available. Please complete an analysis first.")
        if st.button("Go to Application"):
            st.session_state.current_page = 'Application'
            st.rerun()
        return
    
    # Display latest result
    latest_result = st.session_state.analysis_results[-1]
    
    # Risk Assessment Overview
    st.markdown("### 🎯 Risk Assessment Overview")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown('<div class="metric-card success-metric">', unsafe_allow_html=True)
        st.metric("Risk Score", f"{latest_result['risk_score']}/100")
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col2:
        risk_level = latest_result['risk_level']
        if risk_level == 'Low':
            risk_color = "success-metric"
            risk_icon = "🟢"
        elif risk_level == 'Medium':
            risk_color = "warning-metric"
            risk_icon = "🟡"
        else:
            risk_color = "error-metric"
            risk_icon = "🔴"
        
        st.markdown(f'<div class="metric-card {risk_color}">', unsafe_allow_html=True)
        st.metric("Risk Level", f"{risk_icon} {risk_level}")
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col3:
        approval_prob = latest_result['approval_probability']
        if approval_prob >= 0.8:
            approval_color = "success-metric"
            approval_icon = "✅"
        elif approval_prob >= 0.6:
            approval_color = "warning-metric"
            approval_icon = "⚠️"
        else:
            approval_color = "error-metric"
            approval_icon = "❌"
        
        st.markdown(f'<div class="metric-card {approval_color}">', unsafe_allow_html=True)
        st.metric("Approval Probability", f"{approval_icon} {approval_prob:.1%}")
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col4:
        recommendation = latest_result['recommendation']
        if 'Approve' in recommendation:
            rec_color = "success-metric"
            rec_icon = "✅"
        elif 'Deny' in recommendation:
            rec_color = "error-metric"
            rec_icon = "❌"
        else:
            rec_color = "warning-metric"
            rec_icon = "⚠️"
        
        st.markdown(f'<div class="metric-card {rec_color}">', unsafe_allow_html=True)
        st.metric("Recommendation", f"{rec_icon} {recommendation}")
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Risk Visualizations
    st.markdown("### 📈 Risk Assessment Visualizations")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Risk Score Gauge
        risk_gauge = create_risk_score_gauge(latest_result)
        st.plotly_chart(risk_gauge, use_container_width=True)
    
    with col2:
        # Approval Probability Gauge
        approval_gauge = create_approval_probability_chart(latest_result)
        st.plotly_chart(approval_gauge, use_container_width=True)
    
    # Risk Radar Chart
    st.markdown("#### Risk Factor Analysis")
    radar_chart = create_risk_radar_chart(latest_result)
    st.plotly_chart(radar_chart, use_container_width=True)
    
    # Financial Breakdown
    financial_chart = create_financial_breakdown_chart(latest_result)
    if financial_chart:
        st.markdown("#### Financial Position Breakdown")
        st.plotly_chart(financial_chart, use_container_width=True)
    
    # Natural Language Explanation
    st.markdown("### 📝 Analysis Explanation")
    
    with st.expander("View Detailed Analysis", expanded=True):
        explanation = generate_risk_explanation(latest_result)
        st.markdown(explanation)
        
        detailed_analysis = generate_detailed_analysis(latest_result)
        st.markdown(detailed_analysis)
    
    # Loan Terms and Recommendations
    st.markdown("### 💰 Loan Terms & Recommendations")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Recommended Terms**")
        st.info(f"**Interest Rate:** {latest_result['recommended_rate']:.2f}%")
        st.info(f"**Loan Amount:** ${latest_result['recommended_amount']:,.2f}")
        st.info(f"**Term:** {latest_result.get('application_data', {}).get('term_months', 'N/A')} months")
        
        if 'application_data' in latest_result:
            app_data = latest_result['application_data']
            monthly_payment = (latest_result['recommended_amount'] * 
                             (latest_result['recommended_rate'] / 100 / 12)) / (1 - (1 + latest_result['recommended_rate'] / 100 / 12) ** (-app_data.get('term_months', 36)))
            st.info(f"**Estimated Monthly Payment:** ${monthly_payment:,.2f}")
    
    with col2:
        st.markdown("**Analysis Performance**")
        st.info(f"**Execution Time:** {latest_result['execution_time']:.2f} seconds")
        st.info(f"**Agents Used:** {latest_result['agents_used']}")
        st.info(f"**Tasks Completed:** {latest_result['tasks_completed']}")
        st.info(f"**Analysis Date:** {latest_result['analysis_time'][:19]}")
    
    # Document Download Section
    st.markdown("### 📄 Download Reports")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        # JSON Export
        json_data = json.dumps(latest_result, indent=2, default=str)
        st.download_button(
            label="📄 JSON Report",
            data=json_data,
            file_name=f"credit_analysis_{latest_result.get('customer_id', 'unknown')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            mime="application/json",
            help="Download detailed analysis data in JSON format"
        )
    
    with col2:
        # PDF Report
        try:
            pdf_data = generate_pdf_report(latest_result)
            st.download_button(
                label="📋 PDF Report",
                data=pdf_data,
                file_name=f"credit_analysis_report_{latest_result.get('customer_id', 'unknown')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
                mime="application/pdf",
                help="Download comprehensive PDF report"
            )
        except Exception as e:
            st.error(f"PDF generation failed: {str(e)}")
    
    with col3:
        # Summary Report
        summary_report = f"""
# Credit Risk Analysis Summary

**Customer:** {latest_result.get('application_data', {}).get('name', 'Unknown')}
**Analysis Date:** {latest_result['analysis_time'][:19]}

## Key Results
- **Risk Score:** {latest_result['risk_score']}/100
- **Risk Level:** {latest_result['risk_level']}
- **Approval Probability:** {latest_result['approval_probability']:.1%}
- **Recommendation:** {latest_result['recommendation']}
- **Recommended Rate:** {latest_result['recommended_rate']:.2f}%
- **Recommended Amount:** ${latest_result['recommended_amount']:,.2f}

## Analysis Summary
{generate_risk_explanation(latest_result)}
"""
        st.download_button(
            label="📝 Summary Report",
            data=summary_report,
            file_name=f"credit_analysis_summary_{latest_result.get('customer_id', 'unknown')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
            mime="text/markdown",
            help="Download summary report in Markdown format"
        )
    
    with col4:
        # All Results CSV
        if len(st.session_state.analysis_results) > 1:
            df = pd.DataFrame(st.session_state.analysis_results)
            csv_data = df.to_csv(index=False)
            st.download_button(
                label="📊 All Results CSV",
                data=csv_data,
                file_name=f"all_credit_analyses_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv",
                help="Download all analysis results in CSV format"
            )
        else:
            st.info("Only one analysis available")
    
    # Analysis History
    if len(st.session_state.analysis_results) > 1:
        st.markdown("### 📊 Analysis History")
        
        df = pd.DataFrame(st.session_state.analysis_results)
        df['analysis_time'] = pd.to_datetime(df['analysis_time'])
        
        # Risk score trend
        fig = px.line(df, x='analysis_time', y='risk_score', 
                     title='Risk Score Trend Over Time',
                     labels={'analysis_time': 'Analysis Time', 'risk_score': 'Risk Score'})
        fig.update_layout(xaxis_title="Analysis Time", yaxis_title="Risk Score")
        st.plotly_chart(fig, use_container_width=True)
        
        # Risk level distribution
        col1, col2 = st.columns(2)
        
        with col1:
            risk_counts = df['risk_level'].value_counts()
            fig = px.pie(values=risk_counts.values, names=risk_counts.index,
                        title='Risk Level Distribution')
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Approval probability vs risk score
            fig = px.scatter(df, x='risk_score', y='approval_probability',
                            title='Risk Score vs Approval Probability',
                            labels={'risk_score': 'Risk Score', 'approval_probability': 'Approval Probability'})
            fig.update_layout(xaxis_title="Risk Score", yaxis_title="Approval Probability")
            st.plotly_chart(fig, use_container_width=True)
    
    # Action Buttons
    st.markdown("### 🎯 Next Steps")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🔄 New Analysis", type="primary"):
            st.session_state.current_page = 'Application'
            st.rerun()
    
    with col2:
        if st.button("📈 View Analytics"):
            st.session_state.current_page = 'Analytics'
            st.rerun()
    
    with col3:
        if st.button("⚙️ Processing Details"):
            st.session_state.current_page = 'Processing'
            st.rerun() 