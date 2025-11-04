# pdf_exporter.py
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from io import BytesIO
from datetime import datetime

# --- NEW IMPORTS FOR CHARTS ---
from reportlab.graphics.shapes import Drawing, String
from reportlab.graphics.charts.piecharts import Pie
from reportlab.graphics.charts.barcharts import VerticalBarChart
from reportlab.graphics.charts.axes import XCategoryAxis, YValueAxis
from reportlab.graphics.charts.legends import Legend

# ===================================
# HELPER FUNCTION: CREATE PIE CHART
# ===================================
def create_pie_chart(stats):
    """Creates a Pie chart for risk level distribution."""
    drawing = Drawing(300, 150)
    
    # Get stats, using .get() for safety
    high = stats.get('high_risk_txns', 0)
    medium = stats.get('medium_risk_txns', 0)
    low = stats.get('low_risk_txns', 0)
    
    data = [high, medium, low]
    labels = [f'High ({high})', f'Medium ({medium})', f'Low ({low})']
    
    # Filter out zero values
    non_zero_data = []
    non_zero_labels = []
    for d, l in zip(data, labels):
        if d > 0:
            non_zero_data.append(d)
            non_zero_labels.append(l)
    
    if not non_zero_data:
        drawing.add(String(150, 75, "No transaction data.", textAnchor='middle', fillColor=colors.gray))
        return drawing

    pie = Pie()
    pie.x = 0
    pie.y = 10
    pie.width = 130
    pie.height = 130
    pie.data = non_zero_data
    pie.labels = [l.split(' ')[0] for l in non_zero_labels] # Show "High", "Medium", "Low"
    pie.slices.strokeWidth = 0.5
    
    # Set colors for slices
    pie.slices[0].fillColor = colors.HexColor('#ef4444') # High
    if len(pie.data) > 1:
        pie.slices[1].fillColor = colors.HexColor('#f59e0b') # Medium
    if len(pie.data) > 2:
        pie.slices[2].fillColor = colors.HexColor('#10b981') # Low
        
    drawing.add(pie)
    
    # Add a legend
    legend = Legend()
    legend.x = 150
    legend.y = 110
    legend.columnMaximum = 10
    legend.colorNamePairs = [
        (colors.HexColor('#ef4444'), non_zero_labels[0])
    ]
    if len(non_zero_labels) > 1:
        legend.colorNamePairs.append((colors.HexColor('#f59e0b'), non_zero_labels[1]))
    if len(non_zero_labels) > 2:
        legend.colorNamePairs.append((colors.HexColor('#10b981'), non_zero_labels[2]))

    drawing.add(legend)
    
    title = String(150, 145, "Risk Level Distribution", textAnchor='middle', fontSize=12, fontName='Helvetica-Bold')
    drawing.add(title)
    
    return drawing

# ===================================
# HELPER FUNCTION: CREATE BAR CHART
# ===================================
def create_bar_chart(logs):
    """Creates a Bar chart for risk score trend."""
    drawing = Drawing(450, 180)
    
    # Get last 15 logs and reverse for chronological order
    logs_to_chart = logs[:15][::-1]
    
    if not logs_to_chart:
        drawing.add(String(225, 90, "No transaction data.", textAnchor='middle', fillColor=colors.gray))
        return drawing
        
    data = [(log.get('fraud_probability', 0) * 100) for log in logs_to_chart]
    
    bar_chart = VerticalBarChart()
    bar_chart.x = 50
    bar_chart.y = 40
    bar_chart.height = 125
    bar_chart.width = 380
    bar_chart.data = [data]
    bar_chart.groupSpacing = 10
    bar_chart.barSpacing = 2
    
    # Set bar colors based on risk
    for i, val in enumerate(data):
        if val > 75:
            bar_chart.bars[(0, i)].fillColor = colors.HexColor('#ef4444')
        elif val > 40:
            bar_chart.bars[(0, i)].fillColor = colors.HexColor('#f59e0b')
        else:
            bar_chart.bars[(0, i)].fillColor = colors.HexColor('#10b981')

    # X-Axis (Categories)
    bar_chart.categoryAxis = XCategoryAxis()
    bar_chart.categoryAxis.labels.boxAnchor = 'n'
    bar_chart.categoryAxis.labels.fontSize = 6
    bar_chart.categoryAxis.categoryNames = [f"Txn {i+1}" for i in range(len(data))]
    
    # Y-Axis (Values)
    bar_chart.valueAxis = YValueAxis()
    bar_chart.valueAxis.valueMin = 0
    bar_chart.valueAxis.valueMax = 100
    bar_chart.valueAxis.valueStep = 20
    bar_chart.valueAxis.labels.fontName = 'Helvetica'
    
    drawing.add(bar_chart)
    
    title = String(225, 170, "Risk Score Trend (Last 15 Txns)", textAnchor='middle', fontSize=12, fontName='Helvetica-Bold')
    drawing.add(title)
    drawing.add(String(20, 100, "Risk %", textAnchor='middle', angle=90))
    
    return drawing

# ===================================
# MAIN PDF GENERATION FUNCTION
# ===================================
def generate_investigation_report_with_llm(phone_number, logs, stats, llm_explanation=None):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=0.5*inch, bottomMargin=0.5*inch)
    
    elements = []
    styles = getSampleStyleSheet()
    
    # [Keep all existing styles from original function]
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#1a1f29'),
        spaceAfter=30,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=16,
        textColor=colors.HexColor('#4a9eff'),
        spaceAfter=12,
        spaceBefore=12,
        fontName='Helvetica-Bold'
    )
    
    body_style = ParagraphStyle(
        'CustomBody',
        parent=styles['BodyText'],
        fontSize=10,
        textColor=colors.HexColor('#1a1f29'),
        spaceAfter=6
    )
        
    # ===================================
    # TITLE PAGE
    # ===================================
    elements.append(Spacer(1, 1*inch))
    
    title = Paragraph("FRAUD INVESTIGATION REPORT", title_style)
    elements.append(title)
    elements.append(Spacer(1, 0.3*inch))
    
    # Investigation details box
    investigation_info = f"""
    <para align=center>
    <b>Phone Number:</b> {phone_number}<br/>
    <b>Report Generated:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}<br/>
    <b>Total Transactions:</b> {stats['total_txns']}<br/>
    <b>High Risk Alerts:</b> {stats['high_risk_txns']}<br/>
    <b>Medium Risk Alerts:</b> {stats.get('medium_risk_txns', 0)}
    </para>
    """
    
    info_para = Paragraph(investigation_info, body_style)
    elements.append(info_para)
    elements.append(Spacer(1, 0.5*inch))
    
    # --- *** FIXED RISK STATUS LOGIC *** ---
    if stats['high_risk_txns'] > 0:
        risk_status = "HIGH RISK"
        risk_color = colors.red
    elif stats.get('medium_risk_txns', 0) > 0:
        risk_status = "MEDIUM RISK"
        risk_color = colors.orange
    else:
        risk_status = "LOW RISK"
        risk_color = colors.green
    
    risk_summary = f"""
    <para align=center>
    <font size=14 color={risk_color.hexval()}><b>STATUS: {risk_status}</b></font><br/>
    <font size=12>Average Risk Score: {stats['avg_risk_score']*100:.1f}%</font>
    </para>
    """
    
    elements.append(Paragraph(risk_summary, body_style))
    elements.append(PageBreak())
    
    # ===================================
    # EXECUTIVE SUMMARY
    # ===================================
    elements.append(Paragraph("Executive Summary", heading_style))
    
    # Determine investigation status string
    investigation_status = "Normal Activity"
    if risk_status == "HIGH RISK":
        investigation_status = "REQUIRES IMMEDIATE ACTION"
    elif risk_status == "MEDIUM RISK":
        investigation_status = "ENHANCED MONITORING RECOMMENDED"

    summary_text = f"""
    This report provides a comprehensive analysis of transaction activity for phone number {phone_number}. 
    The investigation covered {stats['total_txns']} transactions with a total value of ${stats['total_amount']:.2f}. 
    
    <br/><br/>
    <b>Key Findings:</b><br/>
    • High Risk Transactions: {stats['high_risk_txns']}<br/>
    • Medium Risk Transactions: {stats.get('medium_risk_txns', 0)}<br/>
    • Average Risk Score: {stats['avg_risk_score']*100:.1f}%<br/>
    • Investigation Status: {investigation_status}
    """
    
    elements.append(Paragraph(summary_text, body_style))
    elements.append(Spacer(1, 0.3*inch))

    # ===================================
    # --- *** NEW: VISUAL ANALYSIS *** ---
    # ===================================
    elements.append(Paragraph("Visual Analysis", heading_style))

    # Create a table to hold the two charts side-by-side
    chart_table_data = [
        [create_pie_chart(stats), create_bar_chart(logs)]
    ]
    chart_table = Table(chart_table_data, colWidths=[3*inch, 4.5*inch])
    chart_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    
    elements.append(chart_table)
    elements.append(Spacer(1, 0.1*inch))

    # ===================================
    # TRANSACTION SUMMARY TABLE
    # ===================================
    elements.append(Paragraph("Transaction Summary", heading_style))

    # Prepare table data - LIMIT to first 10 transactions ONLY
    table_data = [
        ['Timestamp', 'Amount', 'Risk Score', 'Risk Level', 'CAMARA Flags']
    ]

    # Get only first 10 transactions
    transactions_to_show = logs[:10]

    # Add transaction rows
    for log in transactions_to_show:
        camara_flags = []
        if log.get('camara_data', {}).get('sim_swap', {}).get('swapped'):
            camara_flags.append('SIM')
        if not log.get('camara_data', {}).get('location', {}).get('verified', True):
            camara_flags.append('LOC')
        if log.get('camara_data', {}).get('roaming', {}).get('roaming'):
            camara_flags.append('ROAM')
        
        # Add Offline/SMS flags
        conn_status = log.get('camara_data', {}).get('device_status', {}).get('connection_status')
        if conn_status == 'NOT_CONNECTED':
            camara_flags.append('OFFLINE')
        elif conn_status == 'SMS':
            camara_flags.append('SMS_ONLY')
            
        table_data.append([
            log['timestamp'],
            f"${log['transaction_amount']:.2f}",
            f"{log['fraud_probability']*100:.1f}%",
            log['risk_level'],
            ', '.join(camara_flags) if camara_flags else 'None'
        ])

    # Add note if there are more transactions
    if len(logs) > 10:
        note_text = f"<i>Showing first 10 of {len(logs)} total transactions</i>"
        elements.append(Paragraph(note_text, body_style))
        elements.append(Spacer(1, 0.1*inch))

    # Create ONE table with all the data
    table = Table(table_data, colWidths=[1.5*inch, 1*inch, 1*inch, 1*inch, 1.5*inch], repeatRows=1)

    # Build table style dynamically
    table_style = [
        # Header row
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4a9eff')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        
        # Data rows - base styling
        ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 8),
        ('ALIGN', (0, 1), (-1, -1), 'LEFT'),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]

    # Add alternating row colors dynamically based on actual row count
    for i in range(1, len(table_data)):  # Start from row 1 (skip header at row 0)
        if i % 2 == 1:  # Odd rows (1, 3, 5, ...)
            table_style.append(('BACKGROUND', (0, i), (-1, i), colors.HexColor('#F5F5F5')))
        else:  # Even rows (2, 4, 6, ...)
            table_style.append(('BACKGROUND', (0, i), (-1, i), colors.HexColor('#E0E0E0')))

    table.setStyle(TableStyle(table_style))

    # Add the table ONCE
    elements.append(table)
    elements.append(Spacer(1, 0.3*inch))
    # ===================================
    # CAMARA NETWORK INTELLIGENCE
    # ===================================
    elements.append(PageBreak())
    elements.append(Paragraph("CAMARA Network Intelligence Analysis", heading_style))
    
    # Aggregate CAMARA data
    sim_swap_count = sum(1 for log in logs if log.get('camara_data', {}).get('sim_swap', {}).get('swapped'))
    location_mismatch_count = sum(1 for log in logs if not log.get('camara_data', {}).get('location', {}).get('verified', True))
    roaming_count = sum(1 for log in logs if log.get('camara_data', {}).get('roaming', {}).get('roaming'))
    offline_count = sum(1 for log in logs if log.get('camara_data', {}).get('device_status', {}).get('connection_status') == 'NOT_CONNECTED')
    
    camara_summary = f"""
    <b>Network Behavior Summary:</b><br/>
    <br/>
    • SIM Swap Detections: {sim_swap_count}<br/>
    • Location Mismatches: {location_mismatch_count}<br/>
    • Roaming Instances: {roaming_count}<br/>
    • Device Offline Instances: {offline_count}<br/>
    <br/>
    <b>Analysis:</b><br/>
    """
    
    has_anomaly = False
    if sim_swap_count > 0:
        camara_summary += "⚠️ <b>CRITICAL:</b> SIM swap activity detected. This is a strong indicator of account takeover fraud.<br/>"
        has_anomaly = True
    
    if location_mismatch_count > 0:
        camara_summary += "⚠️ <b>WARNING:</b> Device location does not match KYC records. Possible use of VPN or unauthorized remote access.<br/>"
        has_anomaly = True
    
    if offline_count > 0:
        camara_summary += "⚠️ <b>WARNING:</b> Device was offline for {offline_count} transaction(s). This is highly irregular and a common fraud tactic.<br/>"
        has_anomaly = True
        
    if roaming_count > 0:
        camara_summary += "⚠️ <b>NOTICE:</b> Device roaming detected. Verify if customer is traveling, as this can be used to mask location.<br/>"
        has_anomaly = True
    
    if not has_anomaly:
        camara_summary += "✅ All network behavior checks passed. No anomalies detected.<br/>"
    
    elements.append(Paragraph(camara_summary, body_style))
    elements.append(Spacer(1, 0.3*inch))
    
    # ===================================
    # DETAILED TRANSACTION ANALYSIS
    # ===================================
    high_risk_logs = [log for log in logs if log['risk_level'] == 'High Risk']
    
    if high_risk_logs:
        elements.append(Paragraph("High Risk Transaction Details", heading_style))
        
        for i, log in enumerate(high_risk_logs[:5], 1):  # Show first 5 high-risk
            detail_text = f"""
            <b>Transaction #{i}</b><br/>
            Timestamp: {log['timestamp']}<br/>
            Amount: ${log['transaction_amount']:.2f}<br/>
            Risk Score: {log['fraud_probability']*100:.1f}%<br/>
            """
            
            # Add CAMARA flags
            if log.get('camara_data'):
                detail_text += "<br/><b>CAMARA Flags:</b><br/>"
                if log['camara_data'].get('sim_swap', {}).get('swapped'):
                    detail_text += f"• SIM Swap: {log['camara_data']['sim_swap'].get('last_swap_date')}<br/>"
                if not log['camara_data'].get('location', {}).get('verified', True):
                    distance = log['camara_data']['location'].get('distance_meters', 0)
                    detail_text += f"• Location Mismatch: {distance/1000:.1f} km from KYC<br/>"
            
            elements.append(Paragraph(detail_text, body_style))
            elements.append(Spacer(1, 0.2*inch))
    
    # ===================================
    # RECOMMENDATIONS
    # ===================================
    elements.append(PageBreak())
    elements.append(Paragraph("Recommendations", heading_style))
    
    # --- *** FIXED RECOMMENDATION LOGIC *** ---
    if stats['high_risk_txns'] > 3:
        recommendation = """
        <b>IMMEDIATE ACTION REQUIRED</b><br/>
        <br/>
        This account shows multiple high-risk indicators and a pattern of abuse. Recommended actions:<br/>
        <br/>
        1. <b>SUSPEND</b> all transaction activity immediately.<br/>
        2. <b>Contact</b> customer through verified channel for identity verification.<br/>
        3. <b>Report</b> to fraud investigation team for immediate follow-up.<br/>
        4. Implement enhanced monitoring for 90 days if account is restored.<br/>
        """
    elif stats['high_risk_txns'] > 0:
        recommendation = """
        <b>ENHANCED MONITORING RECOMMENDED</b><br/>
        <br/>
        This account has triggered one or more high-risk alerts. Recommended actions:<br/>
        <br/>
        1. <b>Implement step-up authentication</b> (e.g., OTP) for high-value transactions.<br/>
        2. <b>Contact</b> customer to verify recent activity.<br/>
        3. <b>Monitor</b> account closely for the next 30 days.<br/>
        4. Consider temporary transaction limits until verification is complete.<br/>
        """
    elif stats.get('medium_risk_txns', 0) > 0:
        recommendation = """
        <b>REVIEW REQUIRED</b><br/>
        <br/>
        This account shows several medium-risk indicators. Recommended actions:<br/>
        <br/>
        1. <b>Review</b> medium-risk transactions for anomalies.<br/>
        2. <b>Monitor</b> account for the next 7 days for any escalation.<br/>
        3. No immediate customer contact required unless activity escalates.<br/>
        """
    else:
        recommendation = """
        <b>CONTINUE STANDARD MONITORING</b><br/>
        <br/>
        This account shows normal activity patterns. Recommended actions:<br/>
        <br/>
        1. Continue standard fraud monitoring.<br/>
        2. No additional action required at this time.<br/>
        """
    
    elements.append(Paragraph(recommendation, body_style))
    elements.append(Spacer(1, 0.3*inch))
    
    # ===================================
    # AI-POWERED ANALYSIS (LLM)
    # ===================================
    if llm_explanation:
        elements.append(PageBreak())
        elements.append(Paragraph("🤖 AI-Powered Investigation Analysis", heading_style))
        elements.append(Spacer(1, 0.2*inch))
        
        # Executive Summary
        if llm_explanation.get('executive_summary'):
            summary_box = f"""
            <para>
            <b>Executive Summary:</b><br/><br/>
            {llm_explanation['executive_summary']}
            </para>
            """
            elements.append(Paragraph(summary_box, body_style))
            elements.append(Spacer(1, 0.3*inch))
        
        # Detailed Analysis
        if llm_explanation.get('detailed_analysis'):
            elements.append(Paragraph("<b>Detailed Analysis:</b>", body_style))
            elements.append(Spacer(1, 0.1*inch))
            
            analysis_text = llm_explanation['detailed_analysis'].replace('\n', '<br/>')
            elements.append(Paragraph(analysis_text, body_style))
            elements.append(Spacer(1, 0.3*inch))
        
        # Risk Factors Table
        if llm_explanation.get('risk_factors') and len(llm_explanation['risk_factors']) > 0:
            elements.append(Paragraph("<b>Detected Risk Factors:</b>", body_style))
            elements.append(Spacer(1, 0.1*inch))
            
            risk_table_data = [
                ['Risk Factor', 'Severity', 'Explanation']
            ]
            
            for factor in llm_explanation['risk_factors']:
                risk_table_data.append([
                    factor.get('factor', 'Unknown'),
                    factor.get('severity', 'MEDIUM'),
                    factor.get('explanation', '')[:100] + '...' if len(factor.get('explanation', '')) > 100 else factor.get('explanation', '')
                ])
            
            risk_table = Table(risk_table_data, colWidths=[1.5*inch, 1*inch, 3.5*inch])
            risk_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#8b5cf6')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#F5F5F5')),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ]))
            
            elements.append(risk_table)
            elements.append(Spacer(1, 0.3*inch))
        
        # Recommendation
        if llm_explanation.get('recommendation'):
            rec = llm_explanation['recommendation']
            
            # --- FIXED: Use correct recommendation color ---
            rec_color = colors.green.hexval()
            if rec.get('action') in ["BLOCK", "REJECT", "SUSPEND"]:
                rec_color = colors.red.hexval()
            elif rec.get('action') in ["REVIEW", "STEP-UP"]:
                rec_color = colors.orange.hexval()

            recommendation_text = f"""
            <para>
            <b>AI Recommendation:</b><br/>
            <font size=12 color={rec_color}><b>{rec.get('action', 'REVIEW REQUIRED')}</b></font><br/><br/>
            """
            
            if rec.get('next_steps'):
                recommendation_text += "<b>Next Steps:</b><br/>"
                for i, step in enumerate(rec['next_steps'], 1):
                    recommendation_text += f"{i}. {step}<br/>"
            
            recommendation_text += "</para>"
            
            elements.append(Paragraph(recommendation_text, body_style))
            elements.append(Spacer(1, 0.3*inch))
        
        # AI Model Badge
        model_info = f"""
        <para align=center>
        <font size=8 color=gray>
        This analysis was generated by {llm_explanation.get('generation_method', 'AI').upper()}<br/>
        Analysis Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        </font>
        </para>
        """
        elements.append(Paragraph(model_info, body_style))

    # ===================================
    # FOOTER
    # ===================================
    footer_text = """
    <para align=center>
    <font size=8 color=gray>
    This report was generated by FraudGuard AI - Advanced Fraud Detection System<br/>
    Powered by Nokia CAMARA Network-as-Code APIs<br/>
    For questions contact: fraud-team@example.com<br/>
    <br/>
    CONFIDENTIAL - For internal use only
    </font>
    </para>
    """
    
    elements.append(Spacer(1, 0.5*inch))
    elements.append(Paragraph(footer_text, body_style))
    
    # Build PDF
    doc.build(elements)
    
    buffer.seek(0)
    return buffer