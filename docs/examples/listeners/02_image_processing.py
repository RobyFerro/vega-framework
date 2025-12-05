"""
Image Processing Listener - Pipeline automatica per processing immagini

Processa immagini caricate dagli utenti:
- Resize multipli (thumbnail, medium, large)
- Ottimizzazione qualità
- Watermark (opzionale)
- Upload su storage (S3/CDN)

Formato messaggio atteso:
{
    "image_url": "s3://bucket/uploads/original/photo.jpg",
    "user_id": "user_123",
    "sizes": [
        {"width": 150, "height": 150, "name": "thumbnail"},
        {"width": 800, "height": 600, "name": "medium"},
        {"width": 1920, "height": 1080, "name": "large"}
    ],
    "watermark": true,
    "output_bucket": "s3://bucket/processed/"
}
"""
from vega.listeners import JobListener, job_listener, Message, MessageContext
from vega.di import bind
from domain.services import StorageService
from PIL import Image, ImageDraw, ImageFont
from typing import Dict, List
import io
import logging

logger = logging.getLogger(__name__)


@job_listener(
    queue="image-processing",
    workers=3,  # CPU intensive - pochi worker
    auto_ack=False,  # Controllo manuale ack
    visibility_timeout=300  # 5 minuti per processing
)
class ImageProcessingListener(JobListener):
    """
    Listener per processing immagini in background.

    Features:
    - Resize multipli paralleli
    - Ottimizzazione qualità automatica
    - Watermark opzionale
    - Manual acknowledgment per controllo fine-grained
    """

    async def on_startup(self) -> None:
        """Carica font per watermark"""
        logger.info("image_processing_listener_started")
        # Pre-carica risorse se necessario

    async def on_error(self, message: Message, error: Exception) -> None:
        """Alert team per immagini che falliscono"""
        logger.error(
            "image_processing_failed",
            image_url=message.body.get('image_url'),
            user_id=message.body.get('user_id'),
            error=str(error)
        )

        # Notifica utente che upload fallito
        # await self.notify_user_upload_failed(message.body['user_id'])

    @bind
    async def handle(
        self,
        message: Message,
        context: MessageContext,
        storage: StorageService
    ) -> None:
        """
        Processa immagine creando resize multipli.

        Args:
            message: Dati immagine da processare
            context: Context per manual ack
            storage: Servizio storage iniettato

        Workflow:
        1. Download immagine originale
        2. Resize per ogni dimensione richiesta
        3. Applica watermark se richiesto
        4. Upload versioni processate
        5. Acknowledge messaggio
        """
        data = message.body
        image_url = data['image_url']
        sizes = data.get('sizes', [])
        add_watermark = data.get('watermark', False)
        output_bucket = data.get('output_bucket')

        try:
            # Estendi timeout per processing lungo
            await context.extend_visibility(600)  # 10 minuti totali

            logger.info(
                "processing_image",
                image_url=image_url,
                sizes_count=len(sizes),
                watermark=add_watermark
            )

            # Download immagine originale
            image_data = await storage.download(image_url)
            image = Image.open(io.BytesIO(image_data))

            # Processa ogni dimensione
            processed_urls = []
            for size_config in sizes:
                url = await self._process_size(
                    image=image,
                    size_config=size_config,
                    add_watermark=add_watermark,
                    output_bucket=output_bucket,
                    storage=storage
                )
                processed_urls.append(url)

            logger.info(
                "image_processed",
                image_url=image_url,
                processed_count=len(processed_urls)
            )

            # Successo completo
            await context.ack()

        except StorageError as e:
            # Errore storage temporaneo - retry tra 5 minuti
            logger.warning(f"Storage error, retrying: {e}")
            await context.reject(requeue=True, visibility_timeout=300)

        except Exception as e:
            # Errore processing - non retry (immagine corrotta?)
            logger.error(f"Processing error: {e}")
            await context.reject(requeue=False)

    async def _process_size(
        self,
        image: Image.Image,
        size_config: Dict,
        add_watermark: bool,
        output_bucket: str,
        storage: StorageService
    ) -> str:
        """
        Processa singola dimensione.

        Returns:
            URL immagine processata
        """
        width = size_config['width']
        height = size_config['height']
        name = size_config['name']

        # Resize mantenendo aspect ratio
        image.thumbnail((width, height), Image.Resampling.LANCZOS)

        # Applica watermark se richiesto
        if add_watermark:
            self._add_watermark(image)

        # Converti a bytes con ottimizzazione
        output = io.BytesIO()
        image.save(
            output,
            format='JPEG',
            quality=85,  # Qualità ottimizzata
            optimize=True
        )
        output.seek(0)

        # Upload
        filename = f"{name}_{width}x{height}.jpg"
        url = await storage.upload(
            bucket=output_bucket,
            filename=filename,
            data=output.getvalue(),
            content_type='image/jpeg'
        )

        logger.debug(f"Processed size {name}: {url}")
        return url

    def _add_watermark(self, image: Image.Image) -> None:
        """Aggiunge watermark all'immagine"""
        draw = ImageDraw.Draw(image)

        # Watermark semplice in basso a destra
        text = "© MyApp"
        width, height = image.size

        # Posizione
        x = width - 100
        y = height - 30

        # Disegna con trasparenza
        draw.text(
            (x, y),
            text,
            fill=(255, 255, 255, 128)  # Bianco semi-trasparente
        )


# Esempio messaggio SQS
"""
import boto3
import json

sqs = boto3.client('sqs')
sqs.send_message(
    QueueUrl='https://sqs.us-east-1.amazonaws.com/123/image-processing',
    MessageBody=json.dumps({
        'image_url': 's3://my-bucket/uploads/photo123.jpg',
        'user_id': 'user_456',
        'sizes': [
            {'width': 150, 'height': 150, 'name': 'thumbnail'},
            {'width': 800, 'height': 600, 'name': 'medium'}
        ],
        'watermark': True,
        'output_bucket': 's3://my-bucket/processed/'
    })
)
"""
