import base64
from datetime import datetime
from io import BytesIO
from typing import Any

from xhtml2pdf import pisa
from jinja2 import Environment, FileSystemLoader, select_autoescape
from app.core.logging import get_logger
from app.models.schemas import AnalysisReport
from pathlib import Path


logger = get_logger(__name__)


class PDFService:
    """Generador de PDFs clínicos para reportes de microbiota usando xhtml2pdf."""

    def __init__(self, templates_dir: str = "templates/pdf"):
        """Inicializa el servicio con Jinja2 usando rutas absolutas absolutas."""

        base_dir = Path(__file__).resolve().parent.parent
        template_path = base_dir / templates_dir
        logger.info(f"Loading Jinja templates from: {template_path}")

        self.env = Environment(
            loader=FileSystemLoader(str(template_path)),  # <-- Pasamos la ruta absoluta como string
            autoescape=select_autoescape(['html', 'xml']),
            trim_blocks=True,
            lstrip_blocks=True,
        )


    def generate_microbiota_pdf(
        self, 
        report: AnalysisReport,
        patient_info: dict[str, Any] | None = None,
        nutricionist_info: dict[str, Any] | None = None,
    ) -> BytesIO:
        """
        Genera PDF visual completo desde AnalysisReport.
        
        Args:
            report: Reporte completo (data + interpretation)
            patient_info: Datos adicionales del paciente (opcional)
            nutricionist_info: Datos del nutricionista (opcional)
        
        Returns:
            BytesIO con el PDF generado
        """
        logger.info(f"🖨️ Generating PDF for study: {report.study_code} (using xhtml2pdf)")

        # Preparar contexto para el template
        context = self._prepare_template_context(
            report=report,
            patient_info=patient_info or {},
            nutricionist_info=nutricionist_info or {},
        )

        # Renderizar HTML con Jinja2
        template = self.env.get_template("microbiota_report.html")
        html_content = template.render(**context)

        # Generar PDF con xhtml2pdf
        pdf_buffer = BytesIO()
        pisa_status = pisa.CreatePDF(
            src=html_content,
            dest=pdf_buffer,
            encoding='utf-8'
        )

        if pisa_status.err:
            logger.error(f"❌ Error generating PDF for {report.study_code}")
            raise RuntimeError("PDF generation failed via xhtml2pdf")

        logger.info(f"✅ PDF generated for {report.study_code} ({len(pdf_buffer.getvalue())} bytes)")
        pdf_buffer.seek(0)
        return pdf_buffer

    def _prepare_template_context(
        self, 
        report: AnalysisReport,
        patient_info: dict[str, Any],
        nutricionist_info: dict[str, Any],
    ) -> dict[str, Any]:
        """Prepara datos limpios para el template Jinja."""

        context = {
            "study_code": report.study_code,
            "patient_id": report.patient_id,
            "nutricionist_id": report.nutricionist_id,
            "study_date": report.study_date.strftime("%d/%m/%Y"),
            "generated_at": datetime.now().strftime("%d/%m/%Y %H:%M"),
            "patient_info": patient_info,
            "nutricionist_info": nutricionist_info,
        }

        interpretation = report.interpretation.model_dump()
        context.update({
            "interpretation": interpretation,
            "general_summary": interpretation.get("general_summary", {}),
            "bacterial_composition": interpretation.get("bacterial_composition", []),
            "bacterial_diversity": interpretation.get("bacterial_diversity", []),
            "opportunistic_microorganisms": interpretation.get("opportunistic_microorganisms", []),
            "inferred_metabolic_functions": interpretation.get("inferred_metabolic_functions", []),
            "final_observations": interpretation.get("final_observations", {}),
        })

        # Colores hex para compatibilidad pura con xhtml2pdf
        context["risk_color_bg"] = self._get_risk_bg_color(context["final_observations"].get("risk_score", 0))
        context["risk_color_text"] = self._get_risk_text_color(context["final_observations"].get("risk_score", 0))

        return context

    def _get_risk_bg_color(self, risk_score: int | float) -> str:
        if risk_score < 30: return "#d4edda"
        elif risk_score < 60: return "#fff3cd"
        elif risk_score < 80: return "#ffe8cc"
        else: return "#f8d7da"

    def _get_risk_text_color(self, risk_score: int | float) -> str:
        if risk_score < 30: return "#155724"
        elif risk_score < 60: return "#856404"
        elif risk_score < 80: return "#c45a11"
        else: return "#721c24"


# Instancia global
pdf_service = PDFService()