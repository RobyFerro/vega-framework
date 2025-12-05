"""
Email Notification Listener - Sistema di notifiche email asincrone

Questo listener gestisce l'invio di email transazionali come:
- Email di benvenuto
- Reset password
- Conferme ordini
- Notifiche sistema

Formato messaggio atteso:
{
    "to": "user@example.com",
    "subject": "Welcome to MyApp",
    "template": "welcome",  # Nome template
    "context": {            # Variabili per il template
        "name": "John Doe",
        "activation_url": "https://..."
    }
}
"""
from vega.listeners import JobListener, job_listener, Message
from vega.di import bind
from domain.services import EmailService
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)


@job_listener(
    queue="email-notifications",
    workers=5,  # 5 worker concorrenti per throughput alto
    retry_on_error=True,  # Retry su errori temporanei
    max_retries=3,  # Max 3 tentativi
    visibility_timeout=60  # 1 minuto per invio email
)
class EmailNotificationListener(JobListener):
    """
    Listener per invio email asincrone.

    Utilizza un servizio di terze parti (Sendgrid, Mailgun, SES)
    per inviare email con retry automatico in caso di errori temporanei.

    Features:
    - Template email personalizzabili
    - Retry automatico con exponential backoff
    - Logging strutturato per debugging
    - Error tracking su Sentry
    """

    async def on_startup(self) -> None:
        """Inizializza template cache"""
        logger.info(
            "email_listener_started",
            workers=5,
            queue="email-notifications"
        )

    async def on_shutdown(self) -> None:
        """Cleanup finale"""
        logger.info("email_listener_stopped")

    async def on_error(self, message: Message, error: Exception) -> None:
        """
        Log errori critici su Sentry.

        Chiamato dopo tutti i retry falliti.
        """
        try:
            import sentry_sdk
            sentry_sdk.capture_exception(error)
        except ImportError:
            pass

        logger.error(
            "email_send_failed",
            recipient=message.body.get('to'),
            subject=message.body.get('subject'),
            error=str(error),
            message_id=message.id,
            retry_count=message.received_count
        )

    @bind
    async def handle(
        self,
        message: Message,
        email_service: EmailService
    ) -> None:
        """
        Invia email usando il servizio configurato.

        Args:
            message: Messaggio con dati email
            email_service: Servizio email iniettato

        Raises:
            ValueError: Se dati messaggio non validi
            EmailServiceError: Se invio fallisce (triggera retry)
        """
        # Estrai dati messaggio
        to = message.body.get('to')
        subject = message.body.get('subject')
        template = message.body.get('template')
        context = message.body.get('context', {})

        # Validazione
        if not to or not subject:
            raise ValueError("Missing required fields: to, subject")

        # Log inizio processing
        logger.info(
            "sending_email",
            to=to,
            subject=subject,
            template=template,
            message_id=message.id
        )

        # Invia email
        await email_service.send_templated(
            to=to,
            subject=subject,
            template=template,
            context=context
        )

        # Log successo
        logger.info(
            "email_sent",
            to=to,
            subject=subject,
            message_id=message.id
        )


# Esempio di utilizzo da un Interactor
"""
from vega.patterns import Interactor
from vega.di import bind
import boto3
import json

class RegisterUser(Interactor[User]):
    @bind
    async def call(
        self,
        email: str,
        name: str,
        user_repo: UserRepository
    ) -> User:
        # Crea utente
        user = await user_repo.create(email=email, name=name)

        # Pubblica messaggio SQS per email asincrona
        sqs = boto3.client('sqs')
        sqs.send_message(
            QueueUrl='https://sqs.us-east-1.amazonaws.com/123/email-notifications',
            MessageBody=json.dumps({
                'to': user.email,
                'subject': 'Welcome to MyApp!',
                'template': 'welcome',
                'context': {
                    'name': user.name,
                    'activation_url': f'https://myapp.com/activate/{user.token}'
                }
            })
        )

        return user
"""
