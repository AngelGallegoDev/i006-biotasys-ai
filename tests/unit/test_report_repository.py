from unittest.mock import MagicMock
import pytest
from app.repositories.report_repository import ReportRepository
from app.models.schemas import MicrobiotaReport, AnalysisRequest
from app.core.exceptions import DatabaseError

@pytest.fixture
def mock_supabase():
    """Mock the Supabase client."""
    return MagicMock()

@pytest.fixture
def repository(mock_supabase):
    """Repository instance with mocked client."""
    return ReportRepository(client=mock_supabase)

@pytest.mark.asyncio
async def test_save_report_success(repository, mock_supabase):
    """Test successful report persistence."""
    mock_report = MagicMock(spec=MicrobiotaReport)
    mock_report.model_dump.return_value = {"foo": "bar"}
    
    mock_request = MagicMock(spec=AnalysisRequest)
    mock_request.documento_id = "DOC123"
    mock_request.empresa_id = "EMP1"
    mock_request.doctor_id = "DR1"
    mock_request.file_url = "https://fake.url"
    
    # Mock the chain: table().insert().execute()
    mock_insert_chain = mock_supabase.table.return_value.insert.return_value.execute
    mock_insert_chain.return_value = MagicMock(data=[{"id": "new-uuid"}])

    result = await repository.save_report(mock_report, mock_request)

    assert result["id"] == "new-uuid"
    mock_supabase.table.assert_called_with("microbiota_reports")

@pytest.mark.asyncio
async def test_save_report_failure_raises_database_error(repository, mock_supabase):
    """Test that persistence errors are wrapped in DatabaseError."""
    mock_supabase.table.side_effect = Exception("DB Connection Timeout")
    
    with pytest.raises(DatabaseError) as exc:
        await repository.save_report(MagicMock(), MagicMock())
    
    assert "Failed to save report in Supabase" in str(exc.value)
