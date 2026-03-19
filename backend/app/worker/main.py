import asyncio
import logging
import signal

from app.worker.queue import dequeue_job
from app.worker.executor import execute_task_step
from app.worker.retry_scheduler import create_scheduler

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

shutdown_event = asyncio.Event()


def handle_sigterm():
    logger.info("SIGTERM received. Shutting down worker...")
    shutdown_event.set()


async def main():
    loop = asyncio.get_running_loop()
    loop.add_signal_handler(signal.SIGTERM, handle_sigterm)
    loop.add_signal_handler(signal.SIGINT, handle_sigterm)

    scheduler = create_scheduler()
    scheduler.start()
    logger.info("Worker started. Waiting for jobs...")

    while not shutdown_event.is_set():
        job = await dequeue_job(timeout=5)
        if job is None:
            continue  # timeout, loop again to check shutdown_event

        logger.info(
            "Processing job: execution_id=%s, step=%s",
            job.task_execution_id,
            job.step_index,
        )
        try:
            await execute_task_step(job)
        except Exception as e:
            logger.exception("Unhandled error processing job %s: %s", job, e)

    scheduler.shutdown()
    logger.info("Worker shutdown complete.")


if __name__ == "__main__":
    asyncio.run(main())
