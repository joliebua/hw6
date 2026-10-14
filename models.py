"""Data shapes for the Campus Customs vendor desk agent."""
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field


class ExtractedQuote(BaseModel):
    """Facts only, no decision. With the design defense on, this is all the model is allowed to return."""

    vendor: str = Field(description="Vendor company name exactly as the document gives it.")
    sku: str | None = Field(
        description="Campus Customs SKU (format CC-XX-000) from the document, or null if not stated."
    )
    unit_price: float | None = Field(
        description="The unit price exactly as printed on the quote's price line (no currency conversion), or null if not stated."
    )
    lead_time_days: int | None = Field(
        description="Lead time in days as quoted (business days count as days), or null if not stated."
    )
    min_order: int | None = Field(
        description="The minimum order number exactly as printed on the quote's minimum order line (no unit conversion), or null if not stated."
    )


class VendorDecision(ExtractedQuote):
    """The agent's final answer for one vendor document (handbook section 13)."""

    decision: Literal["recommend", "do_not_recommend"] = Field(
        description="recommend only if all four purchasing checks pass; otherwise do_not_recommend."
    )
    reason: str = Field(
        description="One sentence naming the purchasing check that decided the outcome."
    )


@dataclass
class VendorDeskDeps:
    """Run context handed to every tool: which document this run may read, and where logs go."""

    doc_path: Path
    output_dir: Path
    sanitize: bool = False                                  # code defense on/off
    removed: list[str] = field(default_factory=list)        # what the code defense stripped out
