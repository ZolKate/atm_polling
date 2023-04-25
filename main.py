from fastapi import FastAPI
from fastapi_utils.inferring_router import InferringRouter
from fastapi_utils.cbv import cbv
import uvicorn
from dataclasses import dataclass
from typing import Dict, Optional, Type
import asyncio

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
        
app = FastAPI()
router = InferringRouter()

@cbv(router)
class App:
    invoices = TransactionController()

    @router.get("/new_invoice/{id}")
    async def get_new_invoice(self,id:str):
        try:
            invoice = Transaction(id, asyncio.Event())
            self.invoices.add(invoice)
            await asyncio.wait_for(invoice.event.wait(), timeout=30)
        except asyncio.TimeoutError:
            return "Время ожидания привязки оплаты закончилось"
        
        if invoice.event.is_set():
            self.invoices.remove(invoice)
            invoice.event.clear()
            return "Оплата прошла"

    @router.get("/pay/{id}")
    async def get_pay(self,id:str):
        if self.invoices.is_empty():
            return "Транзакций открытых нет"
        invoice = self.invoices.validate(id)
        if invoice:
            invoice.event.set()
        else: 
            return "Идентификаторы не сходятся"

app.include_router(router)

if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)

