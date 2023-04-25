from fastapi import FastAPI
import uvicorn
from dataclasses import dataclass
from typing import Set, Optional
import asyncio
from pydantic import BaseModel


app = FastAPI()
event = asyncio.Event()

@dataclass
class Transaction:
    transactions: Optional[Set[str]]

    def add(self, id:str):
        self.transactions.add(id)
    
    def remove(self, id: str):
        self.transactions.remove(id)
    
    def validate(self, id: str):
        return id in self.transactions
    
    def is_empty(self):
        return len(self.transactions) == 0
    
id_set = Transaction(set())

@app.get("/new_invoice/{id}")
async def get_new_invoice(id:str):
    print("Ожидание оплаты...")
    try:
        id_set.add(id)
        await asyncio.wait_for(event.wait(), timeout=30)
    except asyncio.TimeoutError:
        return "Время ожидания привязки оплаты закончилось"
    if event.is_set():
        id_set.remove(id)
        event.clear()
        return "Оплата прошла"

@app.get("/pay/{id}")
async def get_pay(id:str):
    print("Происходит оплата ...")
    if id_set.is_empty():
        return "Транзакций открытых нет"
    if id_set.validate(id):
        event.set()
    else: 
        return "Идентификаторы не сходятся"

if __name__ == "__main__":
    
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)

