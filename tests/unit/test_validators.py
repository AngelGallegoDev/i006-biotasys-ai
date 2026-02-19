from app.models.schemas import TaxonomicComposition, TaxonomicAbundance

def test_calculate_fb_ratio_automatically():
    """Verify that F/B ratio is calculated if missing but phyla data exists."""
    composition = TaxonomicComposition(
        phyla=[
            TaxonomicAbundance(name="Firmicutes", abundance=60.0),
            TaxonomicAbundance(name="Bacteroidetes", abundance=40.0)
        ],
        firmicutes_bacteroidetes_ratio=0.0
    )
    
    # After Pydantic initialization, the validator should have run
    assert composition.firmicutes_bacteroidetes_ratio == 1.5

def test_do_not_overwrite_existing_fb_ratio():
    """Verify that if a ratio is provided, it is not overwritten."""
    composition = TaxonomicComposition(
        phyla=[
            TaxonomicAbundance(name="Firmicutes", abundance=60.0),
            TaxonomicAbundance(name="Bacteroidetes", abundance=40.0)
        ],
        firmicutes_bacteroidetes_ratio=2.0
    )
    
    assert composition.firmicutes_bacteroidetes_ratio == 2.0

def test_handle_zero_bacteroidetes():
    """Verify that it handles division by zero gracefully by keeping 0.0."""
    composition = TaxonomicComposition(
        phyla=[
            TaxonomicAbundance(name="Firmicutes", abundance=60.0),
            TaxonomicAbundance(name="Bacteroidetes", abundance=0.0)
        ],
        firmicutes_bacteroidetes_ratio=0.0
    )
    
    assert composition.firmicutes_bacteroidetes_ratio == 0.0
