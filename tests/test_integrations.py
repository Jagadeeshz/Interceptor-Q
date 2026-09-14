"""Tests for Interceptor integrations."""

import pytest
from unittest.mock import patch, MagicMock

# Test Apollo enrichment
def test_enrich_apollo_stub():
    """Test that the Apollo enrichment stub returns expected data structure."""
    from integrations.enrich_apollo import enrich_company_with_apollo
    
    # Mock the database session and upsert_enrichment function
    with patch('integrations.enrich_apollo.get_session') as mock_get_session, \
         patch('integrations.enrich_apollo.upsert_enrichment') as mock_upsert:
        
        # Setup mock session context manager
        mock_session = MagicMock()
        mock_get_session.return_value.__enter__.return_value = mock_session
        mock_get_session.return_value.__exit__.return_value = None
        
        # Call the function
        result = enrich_company_with_apollo("test-company-id")
        
        # Verify the result structure
        assert isinstance(result, dict)
        assert "funding_stage" in result
        assert "employee_count" in result
        assert "technologies" in result
        assert result["funding_stage"] == "Series B"
        assert result["employee_count"] == 150
        
        # Verify that upsert_enrichment was called with correct args
        mock_upsert.assert_called_once_with(
            mock_session, 
            "test-company-id", 
            {
                "funding_stage": "Series B",
                "employee_count": 150,
                "technologies": ["Python", "React", "AWS"],
                "revenue": "$10M",
                "apollo_id": "apo_12345"
            },
            source="apollo"
        )

# Test LinkedIn enrichment
def test_enrich_linkedin_stub():
    """Test that the LinkedIn enrichment stub returns expected data structure."""
    from integrations.enrich_linkedin import enrich_company_with_linkedin
    
    # Mock the database session and upsert_enrichment function
    with patch('integrations.enrich_linkedin.get_session') as mock_get_session, \
         patch('integrations.enrich_linkedin.upsert_enrichment') as mock_upsert:
        
        # Setup mock session context manager
        mock_session = MagicMock()
        mock_get_session.return_value.__enter__.return_value = mock_session
        mock_get_session.return_value.__exit__.return_value = None
        
        # Call the function
        result = enrich_company_with_linkedin("test-company-id")
        
        # Verify the result structure
        assert isinstance(result, dict)
        assert "company_size" in result
        assert "industry" in result
        assert "linkedin_followers" in result
        assert result["company_size"] == "51-200"
        assert result["industry"] == "Software"
        assert result["linkedin_followers"] == 5000
        
        # Verify that upsert_enrichment was called with correct args
        mock_upsert.assert_called_once_with(
            mock_session, 
            "test-company-id", 
            {
                "company_size": "51-200",
                "industry": "Software",
                "linkedin_followers": 5000,
                "recent_hires": 5,
                "linkedin_id": "li_67890"
            },
            source="linkedin"
        )

# Test Mautic client
def test_send_email_sequence():
    """Test that the Mautic client creates a funnel record."""
    from integrations.mautic_client import send_email_sequence
    
    # Mock the database session and upsert_funnel function
    with patch('integrations.mautic_client.get_session') as mock_get_session, \
         patch('integrations.mautic_client.upsert_funnel') as mock_upsert:
        
        # Setup mock session context manager
        mock_session = MagicMock()
        mock_get_session.return_value.__enter__.return_value = mock_session
        mock_get_session.return_value.__exit__.return_value = None
        
        # Call the function
        result = send_email_sequence("test-opportunity-id", "welcome_series")
        
        # Verify return value
        assert result is True
        
        # Verify that upsert_funnel was called with correct args
        mock_upsert.assert_called_once_with(
            mock_session,
            name=f"Mautic sequence for opportunity test-opportunity-id",
            description=f"Automated email sequence triggered by opportunity test-opportunity-id",
            channel="email",
            campaign_id=f"mautic_test-opportunity-id",
            sequence_json=[{"step": 1, "type": "email", "template": "welcome_series"}],
            status="active"
        )

# Test Calendly client
def test_create_meeting():
    """Test that the Calendly client returns a UUID-like string."""
    from integrations.calendly_client import create_meeting
    
    # Call the function
    result = create_meeting("test-opportunity-id", "2026-09-20T10:00:00Z", "2026-09-20T11:00:00Z")
    
    # Verify it returns a string that looks like a UUID
    assert isinstance(result, str)
    assert len(result) == 36  # Standard UUID length
    assert result.count("-") == 4  # UUID has 4 hyphens

# Test Twilio webhook (basic structure)
def test_twilio_webhook_import():
    """Test that the Twilio webhook module can be imported and has the expected app."""
    from integrations.twilio_webhook import webhook_app
    assert webhook_app is not None
    assert webhook_app.title == "Twilio Webhook"