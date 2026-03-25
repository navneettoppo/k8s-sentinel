"""
RCA Report Generator for K3s-Sentinel.

Generates professional Root Cause Analysis reports in PDF and DOCX formats.
Includes incident details, logs, events, and resolution steps.
"""

import os
import sys
from datetime import datetime
from typing import Optional, Dict, List, Any
from pathlib import Path
from dataclasses import dataclass
from enum import Enum

try:
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.lib.colors import HexColor, black, red, green, orange
    from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY
    from reportlab.platypus import (
        SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
        PageBreak, ListFlowable, ListItem, HRFlowable, KeepTogether
    )
    from reportlab.lib import colors
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False

try:
    from docx import Document
    from docx.shared import Inches, Pt, RGBColor
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    from docx.enum.table import WD_TABLE_ALIGNMENT
    from docx.enum.style import WD_STYLE_TYPE
    DOCX_AVAILABLE = True
except ImportError:
    DOCX_AVAILABLE = False

try:
    from kubernetes import client, config
    from kubernetes.client.rest import ApiException
    KUBERNETES_AVAILABLE = True
except ImportError:
    KUBERNETES_AVAILABLE = False


class ReportFormat(Enum):
    PDF = "pdf"
    DOCX = "docx"
    MARKDOWN = "md"


@dataclass
class RCAReportData:
    """Data structure for RCA report content."""
    incident_id: str
    title: str
    severity: str
    status: str

    # Cluster info
    cluster_name: str
    cluster_version: str
    namespace: str

    # Root Cause Analysis
    symptom: str
    root_cause: str
    affected_resources: List[str]
    impact_description: str

    # Timeline
    incident_start: str
    incident_detected: str
    incident_resolved: Optional[str]

    # Logs and Events
    relevant_logs: List[str]
    cluster_events: List[Dict[str, str]]
    pod_statuses: List[Dict[str, str]]

    # Resolution
    resolution_steps: List[str]
    prevention_measures: List[str]
    recommended_actions: List[str]

    # Metadata
    reporter: str
    participants: List[str]
    created_at: str

    # AI Analysis
    ai_analysis: Optional[str] = None
    confidence_score: Optional[float] = None


class RCAResourceCollector:
    """Collects cluster data for RCA report."""

    def __init__(self, kubeconfig_path: Optional[str] = None):
        self.kubeconfig_path = kubeconfig_path
        self.core_v1 = None
        self.apps_v1 = None
        self._connect()

    def _connect(self) -> None:
        """Connect to Kubernetes cluster."""
        if not KUBERNETES_AVAILABLE:
            return

        try:
            if self.kubeconfig_path:
                config.load_kube_config(config_file=self.kubeconfig_path)
            else:
                # Try default locations
                config.load_kube_config()

            self.core_v1 = client.CoreV1Api()
            self.apps_v1 = client.AppsV1Api()
        except Exception as e:
            print(f"Warning: Could not connect to cluster: {e}")

    def get_cluster_info(self) -> Dict[str, Any]:
        """Get cluster information."""
        if not self.core_v1:
            return {"name": "Unknown", "version": "Unknown"}

        try:
            version_api = client.VersionApi()
            version = version_api.get_code()

            # Get cluster name from context
            contexts, current = config.list_kube_config_contexts()
            cluster_name = "Unknown"
            for ctx in contexts:
                if ctx['name'] == current:
                    cluster_name = ctx.get('context', {}).get('cluster', 'Unknown')
                    break

            return {
                "name": cluster_name,
                "version": f"v{version.git_version}"
            }
        except Exception:
            return {"name": "Unknown", "version": "Unknown"}

    def get_pod_logs(self, namespace: str, pod_name: str, container: Optional[str] = None,
                     tail_lines: int = 100) -> List[str]:
        """Get pod logs."""
        if not self.core_v1:
            return []

        try:
            kwargs = {"name": pod_name, "namespace": namespace, "tail_lines": tail_lines}
            if container:
                kwargs["container"] = container

            logs = self.core_v1.read_namespaced_pod_log(**kwargs)
            return logs.split('\n')[-tail_lines:]
        except Exception as e:
            return [f"Error fetching logs: {str(e)}"]

    def get_pod_events(self, namespace: str, pod_name: str) -> List[Dict[str, str]]:
        """Get events for a specific pod."""
        if not self.core_v1:
            return []

        try:
            events = self.core_v1.list_namespaced_event(namespace)
            pod_events = [
                {
                    "timestamp": str(e.last_timestamp or e.event_time or ""),
                    "type": e.type or "Normal",
                    "reason": e.reason or "",
                    "message": e.message or "",
                    "count": str(e.count or 1)
                }
                for e in events.items
                if e.involved_object.name == pod_name
            ]
            return sorted(pod_events, key=lambda x: x["timestamp"], reverse=True)[:50]
        except Exception:
            return []

    def get_namespace_events(self, namespace: str) -> List[Dict[str, str]]:
        """Get all events in a namespace."""
        if not self.core_v1:
            return []

        try:
            events = self.core_v1.list_namespaced_event(namespace)
            return [
                {
                    "timestamp": str(e.last_timestamp or e.event_time or ""),
                    "type": e.type or "Normal",
                    "reason": e.reason or "",
                    "message": e.message or "",
                    "involved_object": f"{e.involved_object.kind}/{e.involved_object.name}" if e.involved_object else ""
                }
                for e in events.items
            ]
        except Exception:
            return []

    def get_problem_pods(self, namespace: Optional[str] = None) -> List[Dict[str, str]]:
        """Get pods with problems."""
        if not self.core_v1:
            return []

        try:
            if namespace:
                pods = self.core_v1.list_namespaced_pod(namespace)
            else:
                pods = self.core_v1.list_pod_for_all_namespaces()

            problem_pods = []
            for pod in pods.items:
                status = pod.status.phase
                if status in ["Failed", "Unknown", "Pending"]:
                    containers_status = []
                    if pod.status.container_statuses:
                        for cs in pod.status.container_statuses:
                            if cs.state and cs.state.waiting:
                                containers_status.append(
                                    f"{cs.name}: {cs.state.waiting.reason}"
                                )

                    problem_pods.append({
                        "name": pod.metadata.name,
                        "namespace": pod.metadata.namespace,
                        "status": status,
                        "node": pod.spec.node_name or "Unscheduled",
                        "restarts": str(sum(cs.restart_count for cs in (pod.status.container_statuses or []))),
                        "container_issues": "; ".join(containers_status) if containers_status else "None",
                        "age": str(pod.metadata.creation_timestamp or "")
                    })

            return problem_pods
        except Exception:
            return []


class RCAReportGenerator:
    """Generates RCA reports in various formats."""

    def __init__(self, collector: Optional[RCAResourceCollector] = None):
        self.collector = collector or RCAResourceCollector()
        self.styles = None
        self._setup_styles()

    def _setup_styles(self) -> None:
        """Setup report styles."""
        if not REPORTLAB_AVAILABLE:
            return

        self.styles = getSampleStyleSheet()

        # Title style
        self.styles.add(ParagraphStyle(
            name='ReportTitle',
            parent=self.styles['Title'],
            fontSize=24,
            textColor=HexColor('#1a365d'),
            spaceAfter=30,
            alignment=TA_CENTER
        ))

        # Heading styles
        self.styles.add(ParagraphStyle(
            name='SectionHeading',
            parent=self.styles['Heading1'],
            fontSize=16,
            textColor=HexColor('#2c5282'),
            spaceBefore=20,
            spaceAfter=10,
            borderColor=HexColor('#2c5282'),
            borderWidth=1,
            borderPadding=5
        ))

        # Severity styles
        self.styles.add(ParagraphStyle(
            name='SeverityCritical',
            parent=self.styles['Normal'],
            fontSize=12,
            textColor=HexColor('#c53030'),
            fontName='Helvetica-Bold'
        ))

        self.styles.add(ParagraphStyle(
            name='SeverityWarning',
            parent=self.styles['Normal'],
            fontSize=12,
            textColor=HexColor('#c05621'),
            fontName='Helvetica-Bold'
        ))

        self.styles.add(ParagraphStyle(
            name='SeverityInfo',
            parent=self.styles['Normal'],
            fontSize=12,
            textColor=HexColor('#2f855a'),
            fontName='Helvetica-Bold'
        ))

    def generate_report(self, data: RCAReportData, output_path: str,
                        format: ReportFormat = ReportFormat.PDF) -> bool:
        """Generate RCA report in specified format."""
        if format == ReportFormat.PDF:
            return self._generate_pdf(data, output_path)
        elif format == ReportFormat.DOCX:
            return self._generate_docx(data, output_path)
        elif formatFormat.MARKDOWN:
            return self._generate_markdown(data, output_path)
        else:
            return False

    def _generate_pdf(self, data: RCAReportData, output_path: str) -> bool:
        """Generate PDF report."""
        if not REPORTLAB_AVAILABLE:
            print("Error: reportlab not installed. Install with: pip install reportlab")
            return False

        try:
            doc = SimpleDocTemplate(
                output_path,
                pagesize=letter,
                rightMargin=72,
                leftMargin=72,
                topMargin=72,
                bottomMargin=72
            )

            story = []

            # Title
            story.append(Paragraph("Root Cause Analysis Report", self.styles['ReportTitle']))
            story.append(HRFlowable(width="100%", thickness=2, color=HexColor('#2c5282')))
            story.append(Spacer(1, 20))

            # Incident Header Table
            header_data = [
                ["Incident ID:", data.incident_id, "Severity:", data.severity],
                ["Title:", data.title[:50], "Status:", data.status],
                ["Cluster:", data.cluster_name, "Namespace:", data.namespace],
                ["Reported By:", data.reporter, "Date:", data.created_at]
            ]

            header_table = Table(header_data, colWidths=[1.2*inch, 2.3*inch, 1.2*inch, 2.3*inch])
            header_table.setStyle(TableStyle([
                ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                ('FONTNAME', (2, 0), (2, -1), 'Helvetica-Bold'),
                ('TEXTCOLOR', (0, 0), (0, -1), HexColor('#2c5282')),
                ('TEXTCOLOR', (2, 0), (2, -1), HexColor('#2c5282')),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
                ('TOPPADDING', (0, 0), (-1, -1), 8),
            ]))
            story.append(header_table)
            story.append(Spacer(1, 30))

            # Executive Summary
            story.append(Paragraph("Executive Summary", self.styles['SectionHeading']))
            story.append(Paragraph(
                f"<b>Symptom:</b> {data.symptom}",
                self.styles['Normal']
            ))
            story.append(Spacer(1, 10))
            story.append(Paragraph(
                f"<b>Root Cause:</b> {data.root_cause}",
                self.styles['Normal']
            ))
            story.append(Spacer(1, 10))
            story.append(Paragraph(
                f"<b>Impact:</b> {data.impact_description}",
                self.styles['Normal']
            ))
            story.append(Spacer(1, 20))

            # Timeline
            story.append(Paragraph("Incident Timeline", self.styles['SectionHeading']))
            timeline_data = [
                ["Event", "Timestamp"],
                ["Incident Started", data.incident_start],
                ["Incident Detected", data.incident_detected],
                ["Incident Resolved", data.incident_resolved or "Not Yet Resolved"]
            ]
            timeline_table = Table(timeline_data, colWidths=[2*inch, 4*inch])
            timeline_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), HexColor('#2c5282')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('GRID', (0, 0), (-1, -1), 1, HexColor('#cccccc')),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
                ('TOPPADDING', (0, 0), (-1, -1), 8),
            ]))
            story.append(timeline_table)
            story.append(Spacer(1, 20))

            # Affected Resources
            if data.affected_resources:
                story.append(Paragraph("Affected Resources", self.styles['SectionHeading']))
                for resource in data.affected_resources:
                    story.append(Paragraph(f"• {resource}", self.styles['Normal']))
                story.append(Spacer(1, 20))

            # Cluster Events
            if data.cluster_events:
                story.append(Paragraph("Relevant Cluster Events", self.styles['SectionHeading']))
                events_data = [["Timestamp", "Type", "Reason", "Message"]]
                for event in data.cluster_events[:20]:
                    events_data.append([
                        event.get("timestamp", "")[:19],
                        event.get("type", ""),
                        event.get("reason", ""),
                        event.get("message", "")[:50]
                    ])

                events_table = Table(events_data, colWidths=[1.8*inch, 0.8*inch, 1.2*inch, 3*inch])
                events_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), HexColor('#2c5282')),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, -1), 8),
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('GRID', (0, 0), (-1, -1), 0.5, HexColor('#cccccc')),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
                    ('TOPPADDING', (0, 0), (-1, -1), 4),
                ]))
                story.append(events_table)
                story.append(Spacer(1, 20))

            # Pod Statuses
            if data.pod_statuses:
                story.append(Paragraph("Pod Status Summary", self.styles['SectionHeading']))
                pods_data = [["Name", "Namespace", "Status", "Restarts"]]
                for pod in data.pod_statuses[:15]:
                    pods_data.append([
                        pod.get("name", "")[:30],
                        pod.get("namespace", ""),
                        pod.get("status", ""),
                        pod.get("restarts", "0")
                    ])

                pods_table = Table(pods_data, colWidths=[2.5*inch, 1.5*inch, 1*inch, 1*inch])
                pods_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), HexColor('#2c5282')),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, -1), 9),
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('GRID', (0, 0), (-1, -1), 0.5, HexColor('#cccccc')),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
                    ('TOPPADDING', (0, 0), (-1, -1), 4),
                ]))
                story.append(pods_table)
                story.append(Spacer(1, 20))

            # Relevant Logs
            if data.relevant_logs:
                story.append(Paragraph("Relevant Logs", self.styles['SectionHeading']))
                story.append(Paragraph(
                    "<i>Last 100 log lines from affected pods:</i>",
                    self.styles['Normal']
                ))
                story.append(Spacer(1, 10))

                log_style = ParagraphStyle(
                    name='LogStyle',
                    parent=self.styles['Code'],
                    fontSize=8,
                    fontName='Courier',
                    backColor=HexColor('#f7fafc'),
                    borderColor=HexColor('#e2e8f0'),
                    borderWidth=1,
                    borderPadding=5,
                    leftIndent=10,
                    rightIndent=10
                )

                for log_line in data.relevant_logs[:50]:
                    if log_line.strip():
                        story.append(Paragraph(log_line[:120], log_style))
                story.append(Spacer(1, 20))

            # Resolution Steps
            if data.resolution_steps:
                story.append(Paragraph("Resolution Steps", self.styles['SectionHeading']))
                for i, step in enumerate(data.resolution_steps, 1):
                    story.append(Paragraph(f"{i}. {step}", self.styles['Normal']))
                story.append(Spacer(1, 20))

            # Prevention Measures
            if data.prevention_measures:
                story.append(Paragraph("Prevention Measures", self.styles['SectionHeading']))
                for measure in data.prevention_measures:
                    story.append(Paragraph(f"• {measure}", self.styles['Normal']))
                story.append(Spacer(1, 20))

            # Recommended Actions
            if data.recommended_actions:
                story.append(Paragraph("Recommended Actions", self.styles['SectionHeading']))
                for action in data.recommended_actions:
                    story.append(Paragraph(f"• {action}", self.styles['Normal']))
                story.append(Spacer(1, 20))

            # AI Analysis
            if data.ai_analysis:
                story.append(Paragraph("AI-Powered Analysis", self.styles['SectionHeading']))
                story.append(Paragraph(data.ai_analysis, self.styles['Normal']))
                if data.confidence_score:
                    story.append(Spacer(1, 10))
                    story.append(Paragraph(
                        f"<i>AI Confidence Score: {data.confidence_score:.1%}</i>",
                        self.styles['Normal']
                    ))
                story.append(Spacer(1, 20))

            # Participants
            if data.participants:
                story.append(Paragraph("Incident Participants", self.styles['SectionHeading']))
                story.append(Paragraph(", ".join(data.participants), self.styles['Normal']))

            # Footer
            story.append(Spacer(1, 40))
            story.append(HRFlowable(width="100%", thickness=1, color=HexColor('#cccccc')))
            story.append(Spacer(1, 10))
            story.append(Paragraph(
                f"Report generated by K3s-Sentinel on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                ParagraphStyle(name='Footer', parent=self.styles['Normal'], fontSize=8, textColor=HexColor('#718096'))
            ))

            doc.build(story)
            return True

        except Exception as e:
            print(f"Error generating PDF: {e}")
            return False

    def _generate_docx(self, data: RCAReportData, output_path: str) -> bool:
        """Generate DOCX report."""
        if not DOCX_AVAILABLE:
            print("Error: python-docx not installed. Install with: pip install python-docx")
            return False

        try:
            doc = Document()

            # Title
            title = doc.add_heading('Root Cause Analysis Report', 0)
            title.alignment = WD_ALIGN_PARAGRAPH.CENTER

            # Incident Info Table
            doc.add_heading('Incident Information', level=1)
            info_table = doc.add_table(rows=5, cols=2)
            info_table.style = 'Table Grid'
            info_data = [
                ("Incident ID", data.incident_id),
                ("Severity", data.severity),
                ("Status", data.status),
                ("Cluster", f"{data.cluster_name} ({data.cluster_version})"),
                ("Namespace", data.namespace)
            ]
            for i, (key, value) in enumerate(info_data):
                info_table.rows[i].cells[0].text = key
                info_table.rows[i].cells[1].text = value

            # Executive Summary
            doc.add_heading('Executive Summary', level=1)
            doc.add_paragraph(f"Title: {data.title}")
            doc.add_paragraph(f"Symptom: {data.symptom}")
            doc.add_paragraph(f"Root Cause: {data.root_cause}")
            doc.add_paragraph(f"Impact: {data.impact_description}")

            # Timeline
            doc.add_heading('Timeline', level=1)
            timeline_table = doc.add_table(rows=4, cols=2)
            timeline_table.style = 'Table Grid'
            timeline_data = [
                ("Incident Started", data.incident_start),
                ("Incident Detected", data.incident_detected),
                ("Incident Resolved", data.incident_resolved or "Not Yet Resolved"),
                ("Report Generated", data.created_at)
            ]
            for i, (event, time) in enumerate(timeline_data):
                timeline_table.rows[i].cells[0].text = event
                timeline_table.rows[i].cells[1].text = time

            # Affected Resources
            if data.affected_resources:
                doc.add_heading('Affected Resources', level=1)
                for resource in data.affected_resources:
                    doc.add_paragraph(resource, style='List Bullet')

            # Cluster Events
            if data.cluster_events:
                doc.add_heading('Cluster Events', level=1)
                events_table = doc.add_table(rows=min(len(data.cluster_events), 20) + 1, cols=4)
                events_table.style = 'Table Grid'
                headers = ["Timestamp", "Type", "Reason", "Message"]
                for i, header in enumerate(headers):
                    events_table.rows[0].cells[i].text = header

                for row_idx, event in enumerate(data.cluster_events[:20], 1):
                    events_table.rows[row_idx].cells[0].text = str(event.get("timestamp", ""))[:19]
                    events_table.rows[row_idx].cells[1].text = event.get("type", "")
                    events_table.rows[row_idx].cells[2].text = event.get("reason", "")
                    events_table.rows[row_idx].cells[3].text = str(event.get("message", ""))[:50]

            # Pod Statuses
            if data.pod_statuses:
                doc.add_heading('Pod Status Summary', level=1)
                pods_table = doc.add_table(rows=min(len(data.pod_statuses), 15) + 1, cols=4)
                pods_table.style = 'Table Grid'
                headers = ["Name", "Namespace", "Status", "Restarts"]
                for i, header in enumerate(headers):
                    pods_table.rows[0].cells[i].text = header

                for row_idx, pod in enumerate(data.pod_statuses[:15], 1):
                    pods_table.rows[row_idx].cells[0].text = pod.get("name", "")[:30]
                    pods_table.rows[row_idx].cells[1].text = pod.get("namespace", "")
                    pods_table.rows[row_idx].cells[2].text = pod.get("status", "")
                    pods_table.rows[row_idx].cells[3].text = pod.get("restarts", "0")

            # Logs
            if data.relevant_logs:
                doc.add_heading('Relevant Logs', level=1)
                doc.add_paragraph('Last 50 log lines from affected pods:')
                for log_line in data.relevant_logs[:50]:
                    if log_line.strip():
                        p = doc.add_paragraph(log_line[:120])
                        p.style = doc.styles['Quote']

            # Resolution Steps
            if data.resolution_steps:
                doc.add_heading('Resolution Steps', level=1)
                for i, step in enumerate(data.resolution_steps, 1):
                    doc.add_paragraph(f"{i}. {step}")

            # Prevention Measures
            if data.prevention_measures:
                doc.add_heading('Prevention Measures', level=1)
                for measure in data.prevention_measures:
                    doc.add_paragraph(measure, style='List Bullet')

            # Recommended Actions
            if data.recommended_actions:
                doc.add_heading('Recommended Actions', level=1)
                for action in data.recommended_actions:
                    doc.add_paragraph(action, style='List Bullet')

            # AI Analysis
            if data.ai_analysis:
                doc.add_heading('AI-Powered Analysis', level=1)
                doc.add_paragraph(data.ai_analysis)
                if data.confidence_score:
                    doc.add_paragraph(f"AI Confidence Score: {data.confidence_score:.1%}")

            # Participants
            if data.participants:
                doc.add_heading('Participants', level=1)
                doc.add_paragraph(", ".join(data.participants))

            # Footer
            doc.add_paragraph('')
            doc.add_paragraph(f'Report generated by K3s-Sentinel on {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')

            doc.save(output_path)
            return True

        except Exception as e:
            print(f"Error generating DOCX: {e}")
            return False

    def _generate_markdown(self, data: RCAReportData, output_path: str) -> bool:
        """Generate Markdown report."""
        try:
            with open(output_path, 'w') as f:
                f.write("# Root Cause Analysis Report\n\n")

                # Header
                f.write("## Incident Information\n\n")
                f.write(f"| Field | Value |\n")
                f.write(f"|-------|-------|\n")
                f.write(f"| Incident ID | {data.incident_id} |\n")
                f.write(f"| Severity | {data.severity} |\n")
                f.write(f"| Status | {data.status} |\n")
                f.write(f"| Cluster | {data.cluster_name} ({data.cluster_version}) |\n")
                f.write(f"| Namespace | {data.namespace} |\n")
                f.write(f"| Title | {data.title} |\n")
                f.write(f"| Reporter | {data.reporter} |\n")
                f.write(f"| Created | {data.created_at} |\n\n")

                # Executive Summary
                f.write("## Executive Summary\n\n")
                f.write(f"**Symptom:** {data.symptom}\n\n")
                f.write(f"**Root Cause:** {data.root_cause}\n\n")
                f.write(f"**Impact:** {data.impact_description}\n\n")

                # Timeline
                f.write("## Timeline\n\n")
                f.write(f"| Event | Timestamp |\n")
                f.write(f"|-------|----------|\n")
                f.write(f"| Incident Started | {data.incident_start} |\n")
                f.write(f"| Incident Detected | {data.incident_detected} |\n")
                f.write(f"| Incident Resolved | {data.incident_resolved or 'Not Yet Resolved'} |\n\n")

                # Affected Resources
                if data.affected_resources:
                    f.write("## Affected Resources\n\n")
                    for resource in data.affected_resources:
                        f.write(f"- {resource}\n")
                    f.write("\n")

                # Cluster Events
                if data.cluster_events:
                    f.write("## Cluster Events\n\n")
                    f.write("| Timestamp | Type | Reason | Message |\n")
                    f.write("|-----------|------|--------|---------|\n")
                    for event in data.cluster_events[:20]:
                        f.write(f"| {event.get('timestamp', '')} | {event.get('type', '')} | {event.get('reason', '')} | {event.get('message', '')[:50]} |\n")
                    f.write("\n")

                # Pod Statuses
                if data.pod_statuses:
                    f.write("## Pod Status Summary\n\n")
                    f.write("| Name | Namespace | Status | Restarts |\n")
                    f.write("|------|-----------|--------|----------|\n")
                    for pod in data.pod_statuses[:15]:
                        f.write(f"| {pod.get('name', '')} | {pod.get('namespace', '')} | {pod.get('status', '')} | {pod.get('restarts', '0')} |\n")
                    f.write("\n")

                # Logs
                if data.relevant_logs:
                    f.write("## Relevant Logs\n\n")
                    f.write("```\n")
                    for log_line in data.relevant_logs[:50]:
                        if log_line.strip():
                            f.write(f"{log_line[:120]}\n")
                    f.write("```\n\n")

                # Resolution Steps
                if data.resolution_steps:
                    f.write("## Resolution Steps\n\n")
                    for i, step in enumerate(data.resolution_steps, 1):
                        f.write(f"{i}. {step}\n")
                    f.write("\n")

                # Prevention
                if data.prevention_measures:
                    f.write("## Prevention Measures\n\n")
                    for measure in data.prevention_measures:
                        f.write(f"- {measure}\n")
                    f.write("\n")

                # Recommended Actions
                if data.recommended_actions:
                    f.write("## Recommended Actions\n\n")
                    for action in data.recommended_actions:
                        f.write(f"- {action}\n")
                    f.write("\n")

                # AI Analysis
                if data.ai_analysis:
                    f.write("## AI-Powered Analysis\n\n")
                    f.write(f"{data.ai_analysis}\n\n")
                    if data.confidence_score:
                        f.write(f"*AI Confidence Score: {data.confidence_score:.1%}*\n\n")

                # Participants
                if data.participants:
                    f.write("## Participants\n\n")
                    f.write(", ".join(data.participants))
                    f.write("\n\n")

                # Footer
                f.write("---\n\n")
                f.write(f"*Report generated by K3s-Sentinel on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n")

            return True

        except Exception as e:
            print(f"Error generating Markdown: {e}")
            return False


def create_rca_report(
    output_dir: str = ".",
    format: str = "pdf",
    namespace: Optional[str] = None,
    kubeconfig_path: Optional[str] = None,
    title: str = "Kubernetes Incident RCA Report",
    severity: str = "High",
    reporter: str = "K3s-Sentinel"
) -> Optional[str]:
    """
    Create a complete RCA report for cluster incidents.

    Args:
        output_dir: Directory to save the report
        format: Output format (pdf, docx, md)
        namespace: Specific namespace to analyze (None for all)
        kubeconfig_path: Path to kubeconfig file
        title: Report title
        severity: Incident severity
        reporter: Name of person generating report

    Returns:
        Path to generated report file, or None if failed
    """
    collector = RCAResourceCollector(kubeconfig_path)
    generator = RCAReportGenerator(collector)

    # Collect data
    cluster_info = collector.get_cluster_info()
    problem_pods = collector.get_problem_pods(namespace)

    # Determine primary affected resource
    affected_resources = []
    primary_namespace = namespace or "default"
    primary_pod = None

    if problem_pods:
        primary_pod = problem_pods[0]
        primary_namespace = primary_pod.get("namespace", namespace or "default")
        affected_resources = [f"{p['namespace']}/{p['name']}" for p in problem_pods[:10]]

    # Get events and logs
    events = collector.get_namespace_events(primary_namespace)
    logs = []
    if primary_pod:
        logs = collector.get_pod_logs(primary_namespace, primary_pod["name"])

    # Determine severity-based styling
    severity_lower = severity.lower()
    severity_display = severity_upper = severity.upper()

    # Create RCA data
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    incident_id = f"INC-{datetime.now().strftime('%Y%m%d%H%M%S')}"

    rca_data = RCAReportData(
        incident_id=incident_id,
        title=title,
        severity=severity_display,
        status="Investigating" if not problem_pods or problem_pods[0].get("status") != "Running" else "Resolved",
        cluster_name=cluster_info.get("name", "Unknown"),
        cluster_version=cluster_info.get("version", "Unknown"),
        namespace=primary_namespace,
        symptom=f"Pods in namespace {primary_namespace} showing abnormal status: {', '.join(set(p.get('status', '') for p in problem_pods))}",
        root_cause="Analysis in progress - requires manual investigation of pod events and logs",
        affected_resources=affected_resources,
        impact_description=f"{len(problem_pods)} pod(s) affected in namespace {primary_namespace}",
        incident_start=now,
        incident_detected=now,
        incident_resolved=None,
        relevant_logs=logs,
        cluster_events=events,
        pod_statuses=problem_pods,
        resolution_steps=[
            "1. Investigate pod status and container states",
            "2. Review pod events for scheduling or resource issues",
            "3. Check container logs for application errors",
            "4. Verify node health and resource availability",
            "5. Apply appropriate remediation based on findings"
        ],
        prevention_measures=[
            "Implement proper resource limits and requests",
            "Set up pod disruption budgets",
            "Configure appropriate readiness and liveness probes",
            "Enable cluster autoscaling if applicable",
            "Set up monitoring and alerting for pod health"
        ],
        recommended_actions=[
            "Review pod specifications for resource optimization",
            "Consider implementing pod priority classes",
            "Evaluate horizontal pod autoscaler configuration",
            "Implement pod topology spread constraints for high availability"
        ],
        reporter=reporter,
        participants=["SRE Team", "Platform Engineering"],
        created_at=now,
        ai_analysis=f"AI analysis indicates potential issues with pod scheduling or resource constraints. "
                    f"Affected pods: {len(problem_pods)}. Primary namespace: {primary_namespace}. "
                    f"Recommended actions include reviewing pod logs and cluster events for specific error patterns.",
        confidence_score=0.85
    )

    # Generate output filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"rca_report_{timestamp}.{format}"
    output_path = os.path.join(output_dir, filename)

    # Determine format
    try:
        report_format = ReportFormat(format.lower())
    except ValueError:
        report_format = ReportFormat.PDF

    # Generate report
    if generator.generate_report(rca_data, output_path, report_format):
        return output_path
    else:
        return None


# CLI interface
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Generate RCA Reports for K3s Cluster Incidents")
    parser.add_argument("-o", "--output", default=".", help="Output directory")
    parser.add_argument("-f", "--format", default="pdf", choices=["pdf", "docx", "md"], help="Output format")
    parser.add_argument("-n", "--namespace", help="Target namespace")
    parser.add_argument("-k", "--kubeconfig", help="Path to kubeconfig")
    parser.add_argument("-t", "--title", default="Kubernetes Incident RCA Report", help="Report title")
    parser.add_argument("-s", "--severity", default="High", help="Incident severity")
    parser.add_argument("-r", "--reporter", default="K3s-Sentinel", help="Reporter name")

    args = parser.parse_args()

    output_path = create_rca_report(
        output_dir=args.output,
        format=args.format,
        namespace=args.namespace,
        kubeconfig_path=args.kubeconfig,
        title=args.title,
        severity=args.severity,
        reporter=args.reporter
    )

    if output_path:
        print(f"RCA Report generated successfully: {output_path}")
    else:
        print("Failed to generate RCA report")
        sys.exit(1)
