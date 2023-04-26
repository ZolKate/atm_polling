from fastapi import FastAPI
import uvicorn
from dataclasses import dataclass
from typing import Dict, Optional, Type
import asyncio


app = FastAPI()

@dataclass
class Transaction:
    id_invoice: str
    event: Type[asyncio.Event]

class TransactionController:
    transactions: Optional[Dict[str, Transaction]]

    def __init__(self) -> None:
        self.transactions = dict()

    def add(self, invoice: Transaction):
        self.transactions[invoice.id_invoice] = invoice

    def remove(self, invoice: Transaction):
        del self.transactions[invoice.id_invoice]

    def validate(self, id:str):
        if id in self.transactions:
            return self.transactions[id]
    
    def is_empty(self):
        return len(self.transactions) == 0
        

invoices = TransactionController()

@app.get("/new_invoice/{id}")
async def get_new_invoice(id:str):
    try:
        invoice = Transaction(id, asyncio.Event())
        invoices.add(invoice)
        await asyncio.wait_for(invoice.event.wait(), timeout=30)
        invoices.remove(invoice)
        return "Оплата прошла"
    except asyncio.TimeoutError:
        invoices.remove(invoice)
        return "Время ожидания привязки оплаты закончилось"

@app.get("/pay/{id}")
async def get_pay(id:str):
    invoice = invoices.validate(id)
    if invoice:
        invoice.event.set()
    else: 
        return "Идентификаторы не сходятся"

if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)

