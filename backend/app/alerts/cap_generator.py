"""
VARSHAAI - CAP 1.2 XML Generator

Generates CAP-oriented XML from VARSHAAI flood-risk assessments.
The alert levels GREEN/YELLOW/ORANGE/RED are internal prototype
risk levels and are mapped to standardized CAP severity values.

Operational deployment must use an authorized sender identity and
follow the responsible authority's official alert workflow.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path
from xml.etree import ElementTree as ET


class CAPGenerator:
    """Generate Common Alerting Protocol 1.2 XML documents."""

    CAP_NAMESPACE = "urn:oasis:names:tc:emergency:cap:1.2"

    # VARSHAAI branding for the prototype.
    VARSHAII_PREFIX = "VARSHAI"
    DEFAULT_SENDER = "VARSHAAI"
    DEFAULT_SENDER_NAME = "VARSHAAI"

    RISK_TO_CAP_SEVERITY = {
        "GREEN": "Minor",
        "YELLOW": "Moderate",
        "ORANGE": "Severe",
        "RED": "Extreme",
    }

    RISK_TO_CAP_URGENCY = {
        "GREEN": "Future",
        "YELLOW": "Expected",
        "ORANGE": "Expected",
        "RED": "Immediate",
    }

    RISK_TO_CAP_CERTAINTY = {
        "GREEN": "Possible",
        "YELLOW": "Likely",
        "ORANGE": "Likely",
        "RED": "Likely",
    }

    def __init__(
        self,
        sender: str = DEFAULT_SENDER,
        sender_name: str = DEFAULT_SENDER_NAME,
    ):
        if not str(sender).strip():
            raise ValueError("sender cannot be empty.")
        if not str(sender_name).strip():
            raise ValueError("sender_name cannot be empty.")

        self.sender = str(sender).strip()
        self.sender_name = str(sender_name).strip()

        ET.register_namespace("", self.CAP_NAMESPACE)

    @staticmethod
    def _utc_now() -> datetime:
        return datetime.now(timezone.utc)

    @staticmethod
    def _format_datetime(value: datetime) -> str:
        if value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc).isoformat()

    @staticmethod
    def _escape_text(value: object) -> str:
        return str(value)

    def _add_text(
        self,
        parent: ET.Element,
        tag: str,
        value: object,
    ) -> ET.Element:
        element = ET.SubElement(
            parent,
            f"{{{self.CAP_NAMESPACE}}}{tag}",
        )
        element.text = self._escape_text(value)
        return element

    def _validate_risk_level(self, risk_level: str) -> str:
        level = str(risk_level).strip().upper()

        if level not in self.RISK_TO_CAP_SEVERITY:
            raise ValueError(
                f"Unsupported VARSHAAI risk level: {risk_level}"
            )

        return level

    def generate(
        self,
        area_name: str,
        risk_level: str,
        headline: str,
        description: str,
        instruction: str,
        effective: datetime | None = None,
        expires: datetime | None = None,
        identifier: str | None = None,
        event: str = "Heavy Rainfall / Flood Inundation",
        category: str = "Met",
        source: str = DEFAULT_SENDER,
        maximum_depth_m: float | None = None,
        flooded_fraction: float | None = None,
        confidence: float | None = None,
    ) -> str:
        """
        Generate a CAP 1.2 XML alert.

        If no expiry is supplied, the prototype alert remains valid
        for two hours from its effective time.
        """

        if not str(area_name).strip():
            raise ValueError("area_name cannot be empty.")
        if not str(headline).strip():
            raise ValueError("headline cannot be empty.")
        if not str(description).strip():
            raise ValueError("description cannot be empty.")
        if not str(instruction).strip():
            raise ValueError("instruction cannot be empty.")

        level = self._validate_risk_level(risk_level)

        cap_severity = self.RISK_TO_CAP_SEVERITY[level]
        cap_urgency = self.RISK_TO_CAP_URGENCY[level]
        cap_certainty = self.RISK_TO_CAP_CERTAINTY[level]

        now = self._utc_now()

        if effective is None:
            effective = now

        if expires is None:
            expires = effective + timedelta(hours=2)

        if identifier is None:
            identifier = (
                f"{self.VARSHAII_PREFIX}-"
                f"{now.strftime('%Y%m%d%H%M%S')}"
            )

        if expires < effective:
            raise ValueError(
                "expires cannot be earlier than effective."
            )

        alert = ET.Element(
            f"{{{self.CAP_NAMESPACE}}}alert"
        )

        # CAP alert-level fields.
        self._add_text(alert, "identifier", identifier)
        self._add_text(alert, "sender", self.sender)
        self._add_text(alert, "sent", self._format_datetime(now))
        self._add_text(alert, "status", "Actual")
        self._add_text(alert, "msgType", "Alert")
        self._add_text(alert, "scope", "Public")

        info = ET.SubElement(
            alert,
            f"{{{self.CAP_NAMESPACE}}}info",
        )

        self._add_text(info, "language", "en-IN")
        self._add_text(info, "category", category)
        self._add_text(info, "event", event)
        self._add_text(info, "urgency", cap_urgency)
        self._add_text(info, "severity", cap_severity)
        self._add_text(info, "certainty", cap_certainty)
        self._add_text(info, "senderName", self.sender_name)
        self._add_text(info, "headline", headline)
        self._add_text(info, "description", description)
        self._add_text(info, "instruction", instruction)
        self._add_text(
            info,
            "effective",
            self._format_datetime(effective),
        )
        self._add_text(
            info,
            "expires",
            self._format_datetime(expires),
        )

        if maximum_depth_m is not None:
            self._add_text(
                info,
                "parameter",
                f"Maximum Flood Depth;{float(maximum_depth_m):.3f} m",
            )

        if flooded_fraction is not None:
            self._add_text(
                info,
                "parameter",
                f"Flooded Area Fraction;{float(flooded_fraction):.1%}",
            )

        if confidence is not None:
            self._add_text(
                info,
                "parameter",
                f"VARSHAAI Evidence Score;{float(confidence):.3f}",
            )

        area = ET.SubElement(
            info,
            f"{{{self.CAP_NAMESPACE}}}area",
        )

        self._add_text(area, "areaDesc", area_name)

        tree = ET.ElementTree(alert)
        ET.indent(tree, space="  ")

        xml_bytes = ET.tostring(
            alert,
            encoding="utf-8",
            xml_declaration=True,
        )

        return xml_bytes.decode("utf-8")

    def generate_from_assessment(
        self,
        assessment,
        area_name: str,
        effective: datetime | None = None,
        expires: datetime | None = None,
    ) -> str:
        """Generate CAP XML directly from a RiskAssessment object."""

        risk_level = str(assessment.alert_level).upper()

        headline = (
            f"{risk_level}: Flood Risk for {area_name}"
        )

        description = (
            "VARSHAAI estimates a maximum flood depth of "
            f"{assessment.maximum_depth_m:.2f} m and a flooded "
            "spatial fraction of "
            f"{assessment.flooded_fraction:.1%}."
        )

        instruction = (
            "Follow official emergency guidance and local authority instructions."
        )

        return self.generate(
            area_name=area_name,
            risk_level=risk_level,
            headline=headline,
            description=description,
            instruction=instruction,
            effective=effective,
            expires=expires,
            maximum_depth_m=assessment.maximum_depth_m,
            flooded_fraction=assessment.flooded_fraction,
            confidence=assessment.confidence,
            source=self.DEFAULT_SENDER,
        )

    @staticmethod
    def save(
        xml_content: str,
        output_path: str | Path,
    ) -> Path:
        """Save CAP XML to disk."""

        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(xml_content, encoding="utf-8")
        return path


if __name__ == "__main__":
    print("\nVARSHAAI CAP XML Generator")
    print("==========================")

    generator = CAPGenerator()

    effective = datetime(
        2026,
        9,
        16,
        12,
        0,
        tzinfo=timezone.utc,
    )

    expires = datetime(
        2026,
        9,
        16,
        14,
        0,
        tzinfo=timezone.utc,
    )

    xml = generator.generate(
        area_name="Chennai",
        risk_level="ORANGE",
        headline="ORANGE: Flood Risk for Chennai",
        description=(
            "VARSHAAI estimates heavy rainfall and flood "
            "inundation risk."
        ),
        instruction=(
            "Follow official emergency guidance and local "
            "authority instructions."
        ),
        effective=effective,
        expires=expires,
        maximum_depth_m=0.147,
        flooded_fraction=0.3125,
        confidence=0.7805,
    )

    print("\nGenerated CAP XML")
    print("-----------------")
    print(xml)

    root = ET.fromstring(xml)

    assert root.tag == (
        f"{{{generator.CAP_NAMESPACE}}}alert"
    )

    namespace = {"cap": generator.CAP_NAMESPACE}

    assert root.find("cap:identifier", namespace) is not None
    assert root.find("cap:sender", namespace).text == "VARSHAAI"
    assert root.find("cap:status", namespace).text == "Actual"
    assert root.find("cap:msgType", namespace).text == "Alert"
    assert root.find("cap:scope", namespace).text == "Public"

    info = root.find("cap:info", namespace)
    assert info is not None

    assert info.find("cap:senderName", namespace).text == "VARSHAAI"
    assert info.find("cap:severity", namespace).text == "Severe"
    assert info.find("cap:urgency", namespace).text == "Expected"
    assert info.find("cap:certainty", namespace).text == "Likely"

    print("\nCAP XML validation: PASSED")
