"""
Vertex AI - PaaS (Product as a Service)
Gemini Flash shopping assistant and TimesFM zero-shot demand forecasting over BigQuery history (mock provider, keyless mode).
"""

from typing import Dict, Any, List
import datetime

from vertex_ai import gemini

ACTIONS = {"shopping": ["Explore the catalog", "Check delivery options", "Start a return"], "bidding": ["Open the bidding room", "See greener options"],
           "delivery": ["Track my order", "See delivery options"], "support": ["Start a return", "Open a ticket"], "account and login": ["Open my profile"]}

class VertexAIPaaS:
    def __init__(self):
        self.provider_status = "Mock Driver (Offline / Keyless Mode)"

    def chat_assistant(self, message: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """The assistant's answer. Gemini answers in the person's language from the shop's own facts; when it cannot be reached
        the fixed replies below are used, so an assistant never leaves a screen empty."""
        ctx = context or {}
        topic = ctx.get("topic", "shopping")
        text = gemini.reply(topic, message, ctx.get("language", "en"), ctx.get("facts", ""))
        if text:
            return {"source": "Gemini", "reply": text, "suggested_actions": ACTIONS.get(topic, []), "intent": "AI_ANSWER"}
        msg_lower = message.lower()

        if "return" in msg_lower or "refund" in msg_lower:
            return {
                "source": "AI Assistant",
                "reply": "I can help you initiate a return or trade-in for your item. Would you like to upload a photo for AI condition grading, or receive an instant trade-in quote?",
                "suggested_actions": ["Upload Return Photo", "Check Guaranteed Buy-Back", "Chat with Support Agent"],
                "intent": "RETURN_INITIATION"
            }
        elif "bid" in msg_lower or "price" in msg_lower or "buy" in msg_lower:
            return {
                "source": "AI Assistant",
                "reply": "I can open a bidding room for this item so sellers can make you offers. Tell me your maximum budget to start.",
                "suggested_actions": ["Open Live Bidding Room", "Filter by Carbon Impact", "View Refurbished Options"],
                "intent": "BIDDING_SEARCH"
            }
        elif "forecast" in msg_lower or "demand" in msg_lower:
            return {
                "source": "AI Assistant",
                "reply": "A demand forecast needs sales history for the product. Once sales are recorded I can forecast the next 14 days and suggest a reorder point.",
                "suggested_actions": ["Trigger Stock Rebalance", "Open Surplus Auction"],
                "intent": "FORECAST_QUERY"
            }
        else:
            return {
                "source": "AI Assistant",
                "reply": "Welcome to Lakshmi! I am your AI Shopping & Circularity Assistant. How can I assist you with products, multi-seller bidding, or circular returns today?",
                "suggested_actions": ["Explore Product Catalog", "Check Active Bids", "Track Reverse Shipment"],
                "intent": "GENERAL_ASSISTANCE"
            }

    def predict_demand_timesfm(self, sku: str, history: List[Dict[str, Any]] = None, days: int = 14) -> List[Dict[str, Any]]:
        """A demand forecast from the sales history: the recent level, shaped by how each weekday usually sells, with a small
        trend. A stand-in for the TimesFM model, but it only uses the real history and gives the same answer every time."""
        if not history:
            return []  # nothing has been sold yet, so there is nothing to forecast from
        today = datetime.date.today()
        units = [h["units_sold"] for h in history]
        level = sum(units[-14:]) / len(units[-14:])
        overall = sum(units) / len(units)
        by_weekday: Dict[int, List[int]] = {}
        for h in history:
            by_weekday.setdefault(datetime.date.fromisoformat(h["date"]).weekday(), []).append(h["units_sold"])
        factor = {d: (sum(v) / len(v)) / overall if overall else 1.0 for d, v in by_weekday.items()}
        half = max(1, len(units) // 2)
        trend = ((sum(units[half:]) / len(units[half:])) / (sum(units[:half]) / len(units[:half])) - 1) / max(1, len(units)) if sum(units[:half]) else 0.0
        forecast = []
        for i in range(days):
            day = today + datetime.timedelta(days=i)
            value = max(0, round(level * factor.get(day.weekday(), 1.0) * (1 + trend * i)))
            forecast.append({"date": day.strftime("%Y-%m-%d"), "predicted_demand": value,
                             "lower_bound": max(0, round(value * 0.85)), "upper_bound": round(value * 1.15) + 1})
        return forecast

vertex_paas = VertexAIPaaS()
