import requests

from app.core.config import settings


class MercadoPagoService:

    BASE_URL = "https://api.mercadopago.com"

    def __init__(self):
        self.headers = {
            "Authorization": f"Bearer {settings.MERCADO_PAGO_ACCESS_TOKEN}",
            "Content-Type": "application/json"
        }

        self.headers = {
            "Authorization": f"Bearer {settings.MERCADO_PAGO_ACCESS_TOKEN}",
            "Content-Type": "application/json"
        }

    def create_plan(
        self,
        name: str,
        price: float,
        duration_days: int
    ):

        if duration_days == 30:
            frequency = 1
            frequency_type = "months"

        elif duration_days == 365:
            frequency = 1
            frequency_type = "years"

        else:
            frequency = duration_days
            frequency_type = "days"

        payload = {
            "reason": name,

            "back_url": "https://google.com",

            "auto_recurring": {
            "frequency": frequency,
            "frequency_type": frequency_type,
            "transaction_amount": price,
            "currency_id": "BRL"
        }
    }

        

        response = requests.post(
            f"{self.BASE_URL}/preapproval_plan",
            headers=self.headers,
            json=payload,
            timeout=30
        )


        return response.json()


    def create_subscription(
    self,
    plan_id: str,
    payer_email: str
):
        payload = {
            "preapproval_plan_id": plan_id,
            "payer_email": payer_email,
            "back_url": settings.MERCADO_PAGO_BACK_URL,
            "status": "pending"
    }

        

        response = requests.post(
            f"{self.BASE_URL}/preapproval",
            headers=self.headers,
            json=payload)

        return response.json()

mercado_pago_service = MercadoPagoService()