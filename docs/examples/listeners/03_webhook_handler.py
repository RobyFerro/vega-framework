"""
Webhook Handler Listener - Processa webhook da servizi esterni

Gestisce webhook da:
- Stripe (pagamenti)
- GitHub (repository events)
- SendGrid (email events)
- Custom webhooks

Formato messaggio atteso:
{
    "source": "stripe",  # stripe|github|sendgrid|custom
    "event_type": "payment_intent.succeeded",
    "event_id": "evt_123",
    "timestamp": "2025-01-01T12:00:00Z",
    "data": {
        # Event-specific payload
    }
}
"""
from vega.listeners import JobListener, job_listener, Message
from vega.di import bind
from domain.repositories import PaymentRepository, UserRepository
from domain.services import NotificationService
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)


@job_listener(
    queue="webhook-events",
    workers=3,
    retry_on_error=False,  # No retry per webhook (idempotency)
    visibility_timeout=60
)
class WebhookHandlerListener(JobListener):
    """
    Listener per processing webhook esterni.

    Features:
    - Multi-source support (Stripe, GitHub, etc.)
    - Idempotent processing
    - Event routing automatico
    - No retry (webhook deve essere idempotente)

    Important:
    - Webhook possono essere riprocessati → handler deve essere idempotente!
    - Usa event_id per deduplicazione
    """

    async def on_startup(self) -> None:
        """Inizializza handler registry"""
        logger.info("webhook_handler_started")

    async def on_error(self, message: Message, error: Exception) -> None:
        """
        Alert immediato per webhook falliti.

        Webhook falliti sono critici perché non possono essere
        re-inviati facilmente.
        """
        logger.critical(
            "webhook_processing_failed",
            source=message.body.get('source'),
            event_type=message.body.get('event_type'),
            event_id=message.body.get('event_id'),
            error=str(error)
        )

        # Alert team (PagerDuty, Slack, etc.)
        # await self.alert_on_call_engineer(message, error)

    @bind
    async def handle(
        self,
        message: Message,
        payment_repo: PaymentRepository,
        user_repo: UserRepository,
        notification_service: NotificationService
    ) -> None:
        """
        Processa webhook routing all'handler specifico.

        Args:
            message: Webhook event data
            payment_repo: Repository pagamenti
            user_repo: Repository utenti
            notification_service: Servizio notifiche
        """
        source = message.body.get('source')
        event_type = message.body.get('event_type')
        event_id = message.body.get('event_id')
        data = message.body.get('data', {})

        logger.info(
            "processing_webhook",
            source=source,
            event_type=event_type,
            event_id=event_id
        )

        # Route to appropriate handler
        if source == 'stripe':
            await self._handle_stripe_webhook(
                event_type,
                event_id,
                data,
                payment_repo,
                user_repo,
                notification_service
            )
        elif source == 'github':
            await self._handle_github_webhook(
                event_type,
                event_id,
                data
            )
        elif source == 'sendgrid':
            await self._handle_sendgrid_webhook(
                event_type,
                event_id,
                data
            )
        else:
            logger.warning(f"Unknown webhook source: {source}")

        logger.info(
            "webhook_processed",
            source=source,
            event_type=event_type,
            event_id=event_id
        )

    async def _handle_stripe_webhook(
        self,
        event_type: str,
        event_id: str,
        data: Dict[str, Any],
        payment_repo: PaymentRepository,
        user_repo: UserRepository,
        notification_service: NotificationService
    ) -> None:
        """Gestisce webhook Stripe"""

        if event_type == 'payment_intent.succeeded':
            await self._handle_payment_success(
                data,
                payment_repo,
                user_repo,
                notification_service
            )

        elif event_type == 'payment_intent.payment_failed':
            await self._handle_payment_failed(
                data,
                payment_repo,
                user_repo,
                notification_service
            )

        elif event_type == 'customer.subscription.created':
            await self._handle_subscription_created(
                data,
                user_repo
            )

        elif event_type == 'customer.subscription.deleted':
            await self._handle_subscription_cancelled(
                data,
                user_repo,
                notification_service
            )

        else:
            logger.debug(f"Unhandled Stripe event: {event_type}")

    async def _handle_payment_success(
        self,
        data: Dict[str, Any],
        payment_repo: PaymentRepository,
        user_repo: UserRepository,
        notification_service: NotificationService
    ) -> None:
        """
        Gestisce pagamento riuscito.

        IMPORTANTE: Deve essere idempotente!
        """
        payment_intent_id = data['id']

        # Controlla se già processato (idempotency)
        payment = await payment_repo.get_by_stripe_id(payment_intent_id)
        if payment and payment.status == 'succeeded':
            logger.info(
                "payment_already_processed",
                payment_intent_id=payment_intent_id
            )
            return  # Già processato!

        # Aggiorna stato pagamento
        payment.status = 'succeeded'
        payment.stripe_payment_intent_id = payment_intent_id
        await payment_repo.save(payment)

        # Attiva servizio utente
        user = await user_repo.get(payment.user_id)
        user.subscription_active = True
        await user_repo.save(user)

        # Invia ricevuta via email
        await notification_service.send_payment_receipt(
            user.email,
            payment
        )

        logger.info(
            "payment_processed",
            payment_id=payment.id,
            user_id=user.id,
            amount=payment.amount
        )

    async def _handle_payment_failed(
        self,
        data: Dict[str, Any],
        payment_repo: PaymentRepository,
        user_repo: UserRepository,
        notification_service: NotificationService
    ) -> None:
        """Gestisce pagamento fallito"""
        payment_intent_id = data['id']
        error_message = data.get('last_payment_error', {}).get('message', 'Unknown error')

        payment = await payment_repo.get_by_stripe_id(payment_intent_id)
        if not payment:
            logger.warning(f"Payment not found: {payment_intent_id}")
            return

        # Aggiorna stato
        payment.status = 'failed'
        payment.error_message = error_message
        await payment_repo.save(payment)

        # Notifica utente
        user = await user_repo.get(payment.user_id)
        await notification_service.send_payment_failed_notification(
            user.email,
            error_message
        )

        logger.info(
            "payment_failed_handled",
            payment_id=payment.id,
            error=error_message
        )

    async def _handle_subscription_created(
        self,
        data: Dict[str, Any],
        user_repo: UserRepository
    ) -> None:
        """Gestisce nuova subscription"""
        customer_id = data['customer']
        subscription_id = data['id']

        # Trova utente da Stripe customer ID
        user = await user_repo.get_by_stripe_customer_id(customer_id)
        if not user:
            logger.warning(f"User not found for customer: {customer_id}")
            return

        # Aggiorna utente
        user.subscription_id = subscription_id
        user.subscription_active = True
        user.subscription_plan = data.get('plan', {}).get('id')
        await user_repo.save(user)

        logger.info(
            "subscription_created",
            user_id=user.id,
            subscription_id=subscription_id
        )

    async def _handle_subscription_cancelled(
        self,
        data: Dict[str, Any],
        user_repo: UserRepository,
        notification_service: NotificationService
    ) -> None:
        """Gestisce cancellazione subscription"""
        subscription_id = data['id']

        user = await user_repo.get_by_subscription_id(subscription_id)
        if not user:
            logger.warning(f"User not found for subscription: {subscription_id}")
            return

        # Disattiva subscription
        user.subscription_active = False
        await user_repo.save(user)

        # Notifica utente
        await notification_service.send_subscription_cancelled(user.email)

        logger.info(
            "subscription_cancelled",
            user_id=user.id,
            subscription_id=subscription_id
        )

    async def _handle_github_webhook(
        self,
        event_type: str,
        event_id: str,
        data: Dict[str, Any]
    ) -> None:
        """Gestisce webhook GitHub"""
        # Esempio: Deploy automatico su push
        if event_type == 'push':
            branch = data.get('ref', '').replace('refs/heads/', '')
            if branch == 'main':
                logger.info("Triggering deployment for main branch")
                # await self.trigger_deployment()

    async def _handle_sendgrid_webhook(
        self,
        event_type: str,
        event_id: str,
        data: Dict[str, Any]
    ) -> None:
        """Gestisce webhook SendGrid"""
        # Track email delivery events
        email = data.get('email')

        if event_type == 'bounce':
            logger.warning(f"Email bounced: {email}")
            # await self.mark_email_invalid(email)

        elif event_type == 'delivered':
            logger.info(f"Email delivered: {email}")
            # await self.track_email_delivered(email)


# Esempio integrazione con API endpoint
"""
# presentation/web/routes/webhooks.py
from vega.web import Router
from starlette.requests import Request
import boto3
import json

router = Router(prefix="/webhooks", tags=["webhooks"])

@router.post("/stripe")
async def stripe_webhook(request: Request):
    # Verifica signature Stripe
    payload = await request.body()
    sig_header = request.headers.get('stripe-signature')

    # Valida webhook (importante per sicurezza!)
    # event = stripe.Webhook.construct_event(payload, sig_header, webhook_secret)

    # Pubblica su SQS per processing asincrono
    sqs = boto3.client('sqs')
    sqs.send_message(
        QueueUrl='https://sqs.us-east-1.amazonaws.com/123/webhook-events',
        MessageBody=json.dumps({
            'source': 'stripe',
            'event_type': event['type'],
            'event_id': event['id'],
            'timestamp': event['created'],
            'data': event['data']['object']
        })
    )

    return {"status": "received"}
"""
