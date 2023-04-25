from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi_utils.inferring_router import InferringRouter
from fastapi_utils.cbv import cbv
from dataclasses import dataclass
from typing import Dict, Optional, Type
import uvicorn
import asyncio

responses = {
    400: {"message":"Время ожидания привязки оплаты закончилось"},
    404: {"message":"Транзакций открытых нет"},
    405: {"message":"Идентификаторы не сходятся"},
    200: {"message":"Оплата прошла успешно"}
}

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

    def validate(self, id:str)->Transaction:
        if id in self.transactions:
            return self.transactions[id]
    
    def is_empty(self) -> bool:
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
            return JSONResponse(status_code=400, content={"transaction_id": id, "status": responses[400]})
        
        if invoice.event.is_set():
            self.invoices.remove(invoice)
            invoice.event.clear()
            return JSONResponse(status_code=200, content={"transaction_id": id, "status": responses[200]})

    @router.get("/pay/{id}")
    async def get_pay(self,id:str):
        if self.invoices.is_empty():
            return JSONResponse(status_code=404, content={"pay_id": id, "status": responses[404]})
        invoice = self.invoices.validate(id)
        if invoice:
            invoice.event.set()
            return JSONResponse(status_code=200, content={"pay_id": id, "status": responses[200]})
        else: 
            return JSONResponse(status_code=405, content={"pay_id": id, "status": responses[405]})

app.include_router(router)

if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)

