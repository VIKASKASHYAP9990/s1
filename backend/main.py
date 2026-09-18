"""FastAPI demo service for InvestGuard."""
from datetime import date, datetime
from typing import Literal
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

app = FastAPI(title="InvestGuard API", version="0.1.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

holdings = [
    {"symbol":"NVDA","company":"NVIDIA Corp.","quantity":18,"average_buy_price":742.5,"current_price":880.2,"sector":"Technology"},
    {"symbol":"AAPL","company":"Apple Inc.","quantity":24,"average_buy_price":168.4,"current_price":181.7,"sector":"Technology"},
    {"symbol":"MSFT","company":"Microsoft","quantity":12,"average_buy_price":352.2,"current_price":398.6,"sector":"Technology"},
]
transactions, alerts, journal = [], [], []
planner = {"monthly_income":85000,"monthly_expenses":52000,"monthly_contribution":12000,"horizon_years":5}

class TransactionIn(BaseModel):
    symbol: str = Field(min_length=1, max_length=12)
    company: str = "Demo company"
    type: Literal["BUY", "SELL"]
    quantity: float = Field(gt=0)
    price: float = Field(gt=0)
    date: date = Field(default_factory=date.today)
    reason: str = "Not recorded"
    expected_holding_period: str = "Unclear"

class JournalIn(BaseModel):
    symbol: str
    thesis: str
    holding_period: str
    reconsider_condition: str
    reflection: str = ""

class PlannerIn(BaseModel):
    monthly_income: float = Field(ge=0)
    monthly_expenses: float = Field(ge=0)
    existing_savings: float = Field(ge=0, default=0)
    monthly_contribution: float = Field(ge=0)
    horizon_years: int = Field(ge=1, le=50)

@app.get("/api/health")
def health(): return {"status":"ok","mode":"demo","timestamp":datetime.utcnow().isoformat()}

@app.get("/api/portfolio")
def portfolio():
    value = sum(h["quantity"] * h["current_price"] for h in holdings)
    return {"currency":"INR","value":value,"holdings":len(holdings),"change_today":1250}

@app.get("/api/holdings")
def get_holdings(): return holdings

@app.get("/api/transactions")
def get_transactions(): return transactions

@app.post("/api/transactions", status_code=201)
def create_transaction(payload: TransactionIn):
    item = {"id":len(transactions)+1, **payload.model_dump(), "date":payload.date.isoformat()}
    transactions.insert(0,item)
    return item

@app.delete("/api/transactions/{transaction_id}")
def delete_transaction(transaction_id: int):
    for i, item in enumerate(transactions):
        if item["id"] == transaction_id: return {"deleted":transactions.pop(i)}
    raise HTTPException(status_code=404, detail="Transaction not found")

def signals():
    return [
        {"pattern_type":"overtrading","severity":"high","title":"Potential overtrading pattern","evidence":f"You made {len(transactions)} transactions in this session compared with a recent average of 2.","reflection_question":"Was each transaction part of a predefined strategy?"},
        {"pattern_type":"concentration","severity":"moderate","title":"Concentration alert","evidence":"NVDA represents 34.8% of current portfolio value, above the 30% review threshold.","reflection_question":"Does this allocation match your intended portfolio strategy?"},
    ]

@app.get("/api/behavior-analysis")
def behavior_analysis():
    return {"features":{"trades_per_week":8,"average_holding_period_days":43,"portfolio_concentration":0.348,"short_term_trade_ratio":0.42},"patterns":signals()}

@app.post("/api/behavior-analysis/run")
def run_behavior_analysis():
    global alerts
    alerts = [{"id":i+1,"created_at":datetime.utcnow().isoformat(),**signal,"status":"open"} for i, signal in enumerate(signals())]
    return {"status":"complete","patterns":alerts,"model":"Isolation Forest (demo features)"}

@app.get("/api/alerts")
def get_alerts(): return alerts

@app.patch("/api/alerts/{alert_id}")
def patch_alert(alert_id: int, status: Literal["open","reviewed","dismissed"]):
    for alert in alerts:
        if alert["id"] == alert_id:
            alert["status"] = status
            return alert
    raise HTTPException(status_code=404, detail="Alert not found")

@app.get("/api/journal")
def get_journal(): return journal

@app.post("/api/journal", status_code=201)
def create_journal(payload: JournalIn):
    item = {"id":len(journal)+1,"created_at":datetime.utcnow().isoformat(),**payload.model_dump()}
    journal.insert(0,item)
    return item

@app.get("/api/planner")
def get_planner(): return planner

@app.post("/api/planner")
def save_planner(payload: PlannerIn):
    planner.update(payload.model_dump())
    monthly = payload.monthly_contribution
    return {**planner,"available_amount":payload.monthly_income-payload.monthly_expenses,"contributions":{"one_year":monthly*12,"three_years":monthly*36,"five_years":monthly*60}}

@app.get("/api/market/{symbol}")
def market(symbol: str):
    known = {"AAPL":181.7,"MSFT":398.6,"NVDA":880.2,"TSLA":255.4,"AMZN":192.3,"GOOGL":176.8}
    return {"symbol":symbol.upper(),"price":known.get(symbol.upper(),100.0),"change_percent":1.02,"volume":1240000,"source":"demo-fallback"}

@app.get("/api/news/{symbol}")
def news(symbol: str): return {"symbol":symbol.upper(),"items":[],"source":"disabled-in-demo"}

@app.post("/api/ai/explain")
def explain(payload: dict):
    evidence = payload.get("evidence","The account activity differs from the recent baseline.")
    return {"explanation":f"Your recent activity contains an observable {payload.get('pattern','activity')} signal. {evidence} Transaction data cannot establish why the trades occurred.","reflection_question":payload.get("reflection_question","Was this action part of your predefined strategy?")}
