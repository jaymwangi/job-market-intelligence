# dashboard/components/charts.py
"""Reusable Plotly chart components."""
import plotly.graph_objects as go
import plotly.express as px
from typing import Optional, List, Dict, Any
import logging

from dashboard.schemas.chart_data import (
    BarChartData, HorizontalBarChartData,
    PieChartData, DonutChartData, LineChartData, HistogramData
)

logger = logging.getLogger(__name__)


def create_bar_chart(data: BarChartData) -> go.Figure:
    """Create a bar chart from chart model."""
    fig = go.Figure()
    
    if data.x_values and data.y_values:
        fig.add_trace(go.Bar(
            x=data.x_values,
            y=data.y_values,
            marker_color=data.color or '#1f77b4',
            text=data.y_values if data.show_values else None,
            textposition='outside' if data.show_values else None,
            hovertemplate='%{x}<br>%{y}<extra></extra>'
        ))
        
        fig.update_layout(
            title=data.title,
            xaxis_title=data.x_label,
            yaxis_title=data.y_label,
            showlegend=False,
            template='plotly_white',
            height=400,
            font=dict(family="Inter, sans-serif", size=12),
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
        )
    else:
        fig.update_layout(
            title=data.title,
            annotations=[{
                'text': 'No data available',
                'xref': 'paper',
                'yref': 'paper',
                'x': 0.5,
                'y': 0.5,
                'showarrow': False,
                'font': {'size': 14}
            }]
        )
    
    return fig


def create_horizontal_bar_chart(data: HorizontalBarChartData) -> go.Figure:
    """Create a horizontal bar chart from chart model."""
    fig = go.Figure()
    
    if data.x_values and data.y_values:
        fig.add_trace(go.Bar(
            y=data.x_values,
            x=data.y_values,
            marker_color=data.color or '#1f77b4',
            orientation='h',
            text=data.y_values if data.show_values else None,
            textposition='outside' if data.show_values else None,
            hovertemplate='%{y}<br>%{x}<extra></extra>'
        ))
        
        fig.update_layout(
            title=data.title,
            xaxis_title=data.x_label,
            yaxis_title=data.y_label,
            showlegend=False,
            template='plotly_white',
            height=max(400, len(data.x_values) * 30 + 100),
            yaxis={'categoryorder': 'total ascending'} if data.sort_by == 'value' else None,
            font=dict(family="Inter, sans-serif", size=12),
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
        )
    else:
        fig.update_layout(
            title=data.title,
            annotations=[{
                'text': 'No data available',
                'xref': 'paper',
                'yref': 'paper',
                'x': 0.5,
                'y': 0.5,
                'showarrow': False,
                'font': {'size': 14}
            }]
        )
    
    return fig


def create_pie_chart(data: PieChartData) -> go.Figure:
    """Create a pie chart from chart model."""
    fig = go.Figure()
    
    if data.labels and data.values:
        fig.add_trace(go.Pie(
            labels=data.labels,
            values=data.values,
            textinfo='label+percent' if data.show_percentage else 'label',
            textposition='auto',
            marker=dict(colors=data.color_sequence or px.colors.qualitative.Set3),
            hovertemplate='%{label}<br>%{value}<br>%{percent}<extra></extra>'
        ))
        
        fig.update_layout(
            title=data.title,
            template='plotly_white',
            height=400,
            showlegend=True,
            legend={'orientation': 'v', 'yanchor': 'top', 'xanchor': 'left'},
            font=dict(family="Inter, sans-serif", size=12),
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
        )
    else:
        fig.update_layout(
            title=data.title,
            annotations=[{
                'text': 'No data available',
                'xref': 'paper',
                'yref': 'paper',
                'x': 0.5,
                'y': 0.5,
                'showarrow': False,
                'font': {'size': 14}
            }]
        )
    
    return fig


def create_donut_chart(data: DonutChartData) -> go.Figure:
    """Create a donut chart from chart model."""
    fig = go.Figure()
    
    if data.labels and data.values:
        fig.add_trace(go.Pie(
            labels=data.labels,
            values=data.values,
            textinfo='label+percent' if data.show_percentage else 'label',
            textposition='auto',
            hole=data.hole_size,
            marker=dict(colors=data.color_sequence or px.colors.qualitative.Set3),
            hovertemplate='%{label}<br>%{value}<br>%{percent}<extra></extra>'
        ))
        
        fig.update_layout(
            title=data.title,
            template='plotly_white',
            height=400,
            showlegend=True,
            legend={'orientation': 'v', 'yanchor': 'top', 'xanchor': 'left'},
            font=dict(family="Inter, sans-serif", size=12),
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
        )
    else:
        fig.update_layout(
            title=data.title,
            annotations=[{
                'text': 'No data available',
                'xref': 'paper',
                'yref': 'paper',
                'x': 0.5,
                'y': 0.5,
                'showarrow': False,
                'font': {'size': 14}
            }]
        )
    
    return fig


def create_line_chart(data: LineChartData) -> go.Figure:
    """Create a line chart from chart model."""
    fig = go.Figure()
    
    if data.x_values and data.y_values:
        fig.add_trace(go.Scatter(
            x=data.x_values,
            y=data.y_values,
            mode='lines+markers' if data.show_markers else 'lines',
            fill='tozeroy' if data.fill_area else None,
            line=dict(color=data.color or '#1f77b4', width=2),
            marker=dict(size=6, color=data.color or '#1f77b4'),
            hovertemplate='%{x}<br>%{y}<extra></extra>'
        ))
        
        fig.update_layout(
            title=data.title,
            xaxis_title=data.x_label,
            yaxis_title=data.y_label,
            template='plotly_white',
            height=400,
            hovermode='x unified',
            font=dict(family="Inter, sans-serif", size=12),
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
        )
    else:
        fig.update_layout(
            title=data.title,
            annotations=[{
                'text': 'No data available',
                'xref': 'paper',
                'yref': 'paper',
                'x': 0.5,
                'y': 0.5,
                'showarrow': False,
                'font': {'size': 14}
            }]
        )
    
    return fig


def create_histogram(data: HistogramData) -> go.Figure:
    """Create a histogram from chart model."""
    fig = go.Figure()
    
    if data.bins and data.counts:
        fig.add_trace(go.Bar(
            x=data.bins,
            y=data.counts,
            marker_color=data.color or '#1f77b4',
            hovertemplate='%{x}<br>%{y}<extra></extra>'
        ))
        
        fig.update_layout(
            title=data.title,
            xaxis_title=data.x_label,
            yaxis_title=data.y_label,
            template='plotly_white',
            height=400,
            bargap=0.05,
            font=dict(family="Inter, sans-serif", size=12),
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
        )
    else:
        fig.update_layout(
            title=data.title,
            annotations=[{
                'text': 'No data available',
                'xref': 'paper',
                'yref': 'paper',
                'x': 0.5,
                'y': 0.5,
                'showarrow': False,
                'font': {'size': 14}
            }]
        )
    
    return fig