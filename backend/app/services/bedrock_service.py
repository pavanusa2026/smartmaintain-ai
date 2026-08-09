"""AI explanation and maintenance assistant services."""

import logging
from typing import Optional

from app.core.config import get_settings

logger = logging.getLogger(__name__)

MAINTENANCE_DOCS = [
    {
        "title": "Motor Maintenance Manual - Section 4.2",
        "section": "Bearing Inspection Procedures",
        "revisionDate": "2025-11-01",
        "content": (
            "When motor vibration increases above baseline: 1) Shut down motor safely. "
            "2) Inspect bearing housing for heat discoloration. 3) Check lubrication levels "
            "and grease condition. 4) Measure bearing clearance with feeler gauge. "
            "5) Listen for grinding or rattling sounds during slow rotation. "
            "Replace bearings if clearance exceeds 0.005 inches."
        ),
        "keywords": ["vibration", "motor", "bearing", "lubrication"],
    },
    {
        "title": "Pump Maintenance Guide - Section 3.1",
        "section": "Seal and Leak Inspection",
        "revisionDate": "2025-09-15",
        "content": (
            "For cooling pump seal leaks: 1) Check mechanical seal faces for scoring. "
            "2) Verify seal flush system pressure. 3) Inspect coupling alignment. "
            "4) Monitor suction pressure for cavitation signs. "
            "5) Replace seal kit if leakage exceeds 5 drops per minute."
        ),
        "keywords": ["pump", "seal", "leak", "cooling", "pressure"],
    },
    {
        "title": "Conveyor Belt Maintenance - Section 2.4",
        "section": "Belt Alignment and Tension",
        "revisionDate": "2026-01-20",
        "content": (
            "For conveyor belt misalignment: 1) Check tracking rollers and idlers. "
            "2) Verify belt tension is within manufacturer specs. "
            "3) Inspect drive pulley lagging condition. "
            "4) Clean debris from belt path. "
            "5) Adjust take-up unit if belt sag exceeds 2% of span length."
        ),
        "keywords": ["conveyor", "belt", "alignment", "packaging", "vibration"],
    },
    {
        "title": "CNC Spindle Maintenance - Section 5.0",
        "section": "Spindle Wear Assessment",
        "revisionDate": "2025-12-10",
        "content": (
            "For CNC spindle wear indicators: 1) Run spindle warm-up cycle. "
            "2) Measure runout with dial indicator at tool holder. "
            "3) Check coolant flow to spindle bearings. "
            "4) Review recent tool breakage frequency. "
            "5) Schedule spindle rebuild if runout exceeds 0.0005 inches."
        ),
        "keywords": ["cnc", "spindle", "mill", "tool", "wear"],
    },
    {
        "title": "General Safety Procedures - Section 1.0",
        "section": "Lockout/Tagout Requirements",
        "revisionDate": "2026-02-01",
        "content": (
            "Before any maintenance: 1) Follow LOTO procedures per OSHA 1910.147. "
            "2) Verify zero energy state with test equipment. "
            "3) Use appropriate PPE: safety glasses, gloves, steel-toe boots. "
            "4) Never bypass safety interlocks. "
            "5) Document all maintenance actions in the work order system."
        ),
        "keywords": ["safety", "lockout", "tagout", "maintenance", "inspect"],
    },
]


def _retrieve_docs(question: str, machine_id: Optional[str] = None) -> list[dict]:
    q = question.lower()
    scored = []
    for doc in MAINTENANCE_DOCS:
        score = sum(1 for kw in doc["keywords"] if kw in q)
        if machine_id:
            mid = machine_id.lower()
            if any(kw in mid for kw in doc["keywords"]):
                score += 2
        if score > 0:
            scored.append((score, doc))
    scored.sort(key=lambda x: x[0], reverse=True)
    if not scored:
        return [MAINTENANCE_DOCS[4]]
    return [doc for _, doc in scored[:3]]


class BedrockService:
    """Generates explanations using Bedrock or local fallback."""

    def __init__(self) -> None:
        self.settings = get_settings()

    def generate_alert_explanation(
        self,
        machine_name: str,
        machine_type: str,
        prediction: dict,
        recent_readings: list[dict],
    ) -> str:
        fp = prediction.get("failureProbability", 0)
        anomaly = prediction.get("anomalyScore", 0)
        failure_type = prediction.get("likelyFailureType", "unknown").replace("_", " ")

        vib_change = 0
        temp_change = 0
        if len(recent_readings) >= 2:
            vib_change = recent_readings[-1].get("vibration", 0) - recent_readings[0].get("vibration", 0)
            temp_change = recent_readings[-1].get("temperature", 0) - recent_readings[0].get("temperature", 0)

        if self.settings.use_local_model or not self._bedrock_available():
            return self._local_explanation(
                machine_name, failure_type, fp, anomaly, vib_change, temp_change
            )

        return self._bedrock_explanation(
            machine_name, machine_type, prediction, vib_change, temp_change
        )

    def _bedrock_available(self) -> bool:
        try:
            import boto3

            boto3.client("bedrock-runtime", region_name=self.settings.aws_region)
            return True
        except Exception:
            return False

    def _local_explanation(
        self,
        machine_name: str,
        failure_type: str,
        fp: float,
        anomaly: float,
        vib_change: float,
        temp_change: float,
    ) -> str:
        parts = [f"{machine_name} is showing unusual operating patterns."]
        if vib_change > 0.2:
            parts.append(
                f"Vibration has increased by {vib_change:.1f} units over the monitoring window."
            )
        if temp_change > 2:
            parts.append(f"Temperature has risen by {temp_change:.1f}°C.")
        if fp > 0.5:
            parts.append(
                f"The failure prediction model estimates a {fp * 100:.0f}% probability of "
                f"{failure_type} within 7 days (anomaly score: {anomaly:.2f})."
            )
        parts.append(
            "Similar patterns in historical records were associated with developing mechanical wear. "
            "Human review and physical inspection are recommended before taking corrective action."
        )
        return " ".join(parts)

    def _bedrock_explanation(
        self, machine_name: str, machine_type: str, prediction: dict, vib_change: float, temp_change: float
    ) -> str:
        import json

        import boto3

        prompt = (
            f"You are a manufacturing maintenance assistant. Explain this alert in plain language.\n"
            f"Machine: {machine_name} ({machine_type})\n"
            f"Failure probability: {prediction.get('failureProbability')}\n"
            f"Anomaly score: {prediction.get('anomalyScore')}\n"
            f"Vibration change: {vib_change:.2f}\n"
            f"Temperature change: {temp_change:.2f}\n"
            f"Use only the provided data. Do not invent repair procedures. "
            f"Recommend human review. Keep response under 150 words."
        )
        try:
            client = boto3.client("bedrock-runtime", region_name=self.settings.aws_region)
            body = json.dumps(
                {
                    "anthropic_version": "bedrock-2023-05-31",
                    "max_tokens": 300,
                    "messages": [{"role": "user", "content": prompt}],
                }
            )
            response = client.invoke_model(
                modelId=self.settings.bedrock_model_id,
                body=body,
                contentType="application/json",
                accept="application/json",
            )
            result = json.loads(response["body"].read())
            return result["content"][0]["text"]
        except Exception as exc:
            logger.warning("Bedrock call failed, using local fallback: %s", exc)
            return self._local_explanation(
                machine_name,
                prediction.get("likelyFailureType", "unknown").replace("_", " "),
                prediction.get("failureProbability", 0),
                prediction.get("anomalyScore", 0),
                vib_change,
                temp_change,
            )

    def query_assistant(self, question: str, machine_id: Optional[str] = None) -> dict:
        docs = _retrieve_docs(question, machine_id)

        if self.settings.use_local_model or not self._bedrock_available():
            answer = self._local_assistant_answer(question, docs)
        else:
            context = "\n\n".join(f"[{d['title']} - {d['section']}]\n{d['content']}" for d in docs)
            answer = self._bedrock_assistant_answer(question, context)

        return {
            "answer": answer,
            "sources": [
                {"title": d["title"], "section": d["section"], "revisionDate": d["revisionDate"]}
                for d in docs
            ],
            "safetyNotice": "Always follow lockout/tagout procedures before performing maintenance.",
            "humanReviewReminder": (
                "This AI-generated guidance is for decision support only. "
                "Verify all recommendations with qualified maintenance personnel."
            ),
            "urgencyLevel": self._compute_urgency(docs, question),
        }

    def _compute_urgency(self, docs: list[dict], question: str) -> str:
        q = question.lower()
        if any(w in q for w in ("emergency", "critical", "immediate", "urgent")):
            return "critical"
        if any(w in q for w in ("vibration", "bearing", "failure", "leak")):
            return "high"
        return "medium"

    def _local_assistant_answer(self, question: str, docs: list[dict]) -> str:
        lines = ["Based on approved maintenance documentation:\n"]
        for doc in docs:
            lines.append(f"**{doc['section']}** ({doc['title']}):")
            lines.append(doc["content"])
            lines.append("")
        return "\n".join(lines)

    def _bedrock_assistant_answer(self, question: str, context: str) -> str:
        import json

        import boto3

        prompt = (
            f"Answer this maintenance question using ONLY the provided documentation.\n\n"
            f"Documentation:\n{context}\n\nQuestion: {question}\n\n"
            f"Include inspection steps and safety warnings. Do not invent procedures."
        )
        try:
            client = boto3.client("bedrock-runtime", region_name=self.settings.aws_region)
            body = json.dumps(
                {
                    "anthropic_version": "bedrock-2023-05-31",
                    "max_tokens": 500,
                    "messages": [{"role": "user", "content": prompt}],
                }
            )
            response = client.invoke_model(
                modelId=self.settings.bedrock_model_id,
                body=body,
                contentType="application/json",
                accept="application/json",
            )
            result = json.loads(response["body"].read())
            return result["content"][0]["text"]
        except Exception as exc:
            logger.warning("Bedrock assistant failed: %s", exc)
            return self._local_assistant_answer(question, _retrieve_docs(question))


class InspectionService:
    """Computer vision inspection using local heuristics or SageMaker."""

    def analyze_image(self, image_bytes: bytes, filename: str) -> dict:
        import io

        from PIL import Image

        try:
            img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
            width, height = img.size
            pixels = list(img.getdata())
            avg_brightness = sum(sum(p) for p in pixels) / (len(pixels) * 3)
            variance = sum((sum(p) / 3 - avg_brightness) ** 2 for p in pixels) / len(pixels)

            is_defect = variance > 800 or avg_brightness < 80 or avg_brightness > 220
            confidence = min(0.95, 0.5 + variance / 2000)

            defect_type = "none"
            if is_defect:
                if variance > 1500:
                    defect_type = "scratch"
                elif avg_brightness < 80:
                    defect_type = "crack"
                elif avg_brightness > 220:
                    defect_type = "contamination"
                else:
                    defect_type = "misalignment"

            return {
                "predictedResult": "fail" if is_defect else "pass",
                "defectType": defect_type,
                "confidence": round(confidence, 3),
                "imageWidth": width,
                "imageHeight": height,
            }
        except Exception as exc:
            logger.error("Image analysis failed: %s", exc)
            return {
                "predictedResult": "pass",
                "defectType": "none",
                "confidence": 0.5,
            }


class NotificationService:
    def send_alert_notification(self, alert: dict, machine_name: str) -> bool:
        settings = get_settings()
        if not settings.sns_topic_arn:
            logger.info(
                "Alert notification (local): [%s] %s - %s",
                alert.get("severity"),
                machine_name,
                alert.get("title"),
            )
            return True
        try:
            import boto3

            sns = boto3.client("sns", region_name=settings.aws_region)
            message = (
                f"SmartMaintain AI Alert\n"
                f"Severity: {alert.get('severity')}\n"
                f"Machine: {machine_name}\n"
                f"Title: {alert.get('title')}\n"
                f"Action: {alert.get('recommendedAction', 'Review in dashboard')}"
            )
            sns.publish(
                TopicArn=settings.sns_topic_arn,
                Subject=f"Alert: {alert.get('title')}",
                Message=message,
            )
            return True
        except Exception as exc:
            logger.error("SNS notification failed: %s", exc)
            return False
