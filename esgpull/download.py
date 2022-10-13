# from math import ceil
from typing import AsyncIterator

# import asyncio
# from urllib.parse import urlsplit
from httpx import AsyncClient

# from esgpull.auth import Auth
# from esgpull.context import Context
# from esgpull.settings import Settings
from esgpull.types import File, DownloadKind


class BaseDownloader:
    def stream(self, client: AsyncClient, file: File) -> AsyncIterator[bytes]:
        raise NotImplementedError


class Simple(BaseDownloader):
    """
    Simple chunked async downloader.
    """

    async def stream(
        self, client: AsyncClient, file: File
    ) -> AsyncIterator[bytes]:
        async with client.stream("GET", file.url) as resp:
            resp.raise_for_status()
            async for chunk in resp.aiter_bytes():
                yield chunk


class Distributed(BaseDownloader):
    """
    Distributed chunked async downloader.
    Fetches chunks from multiple URLs pointing to the same file.
    """

    # def __init__(
    #     self,
    #     auth: Auth,
    #     *,
    #     file: File | None = None,
    #     url: str | None = None,
    #     settings: Settings | None = None,
    #     max_ping: float = 5.0,
    # ) -> None:
    #     super().__init__(auth, file=file, url=url, settings=settings)
    #     self.max_ping = max_ping

    # async def try_url(self, url: str, client: AsyncClient) -> str | None:
    #     result = None
    #     node = urlsplit(url).netloc
    #     print(f"trying url on '{node}'")
    #     try:
    #         resp = await client.head(url)
    #         print(f"got response on '{node}'")
    #         resp.raise_for_status()
    #         accept_ranges = resp.headers.get("Accept-Ranges")
    #         content_length = resp.headers.get("Content-Length")
    #         if (
    #             accept_ranges == "bytes"
    #             and int(content_length) == self.file.size
    #         ):
    #             result = str(resp.url)
    #         else:
    #             print(dict(resp.headers))
    #     except HTTPError as err:
    #         print(type(err))
    #         print(err.request.headers)
    #     return result

    # async def process_queue(
    #     self, url: str, queue: asyncio.Queue
    # ) -> tuple[list[tuple[int, bytes]], str]:
    #     node = urlsplit(url).netloc
    #     print(f"starting process on '{node}'")
    #     chunks: list[tuple[int, bytes]] = []
    #     async with self.make_client() as client:
    #         final_url = await self.try_url(url, client)
    #         if final_url is None:
    #             print(f"no url found for '{node}'")
    #             return chunks, url
    #         else:
    #             url = final_url
    #         while not queue.empty():
    #             chunk_idx = await queue.get()
    #             print(f"processing chunk {chunk_idx} on '{node}'")
    #             start = chunk_idx * self.settings.download.chunk_size
    #             end = min(
    #                 self.file.size,
    #                 (chunk_idx + 1) * self.settings.download.chunk_size - 1,
    #             )
    #             headers = {"Range": f"bytes={start}-{end}"}
    #             resp = await client.get(url, headers=headers)
    #             queue.task_done()
    #             if resp.status_code == 206:
    #                 chunks.append((chunk_idx, resp.content))
    #             else:
    #                 await queue.put(chunk_idx)
    #                 print(f"error status {resp.status_code} on '{node}'")
    #                 break
    #     return chunks, url

    # async def fetch_urls(self) -> list[str]:
    #     ctx = Context(distrib=True)
    #     ctx.query.instance_id = self.file.file_id
    #     results = await ctx._search(file=True)
    #     files = [File.from_dict(item) for item in results]
    #     return [file.url for file in files]

    # async def aget(self) -> bytes:
    #     nb_chunks = ceil(self.file.size / self.settings.download.chunk_size)
    #     queue: asyncio.Queue[int] = asyncio.Queue(nb_chunks)
    #     for chunk_idx in range(nb_chunks):
    #         queue.put_nowait(chunk_idx)
    #     completed: list[bool] = [False for _ in range(nb_chunks)]
    #     chunks: list[bytes] = [bytes() for _ in range(nb_chunks)]
    #     urls = await self.fetch_urls()
    #     workers = [self.process_queue(url, queue) for url in urls]
    #     for future in asyncio.as_completed(workers):
    #         some_chunks, url = await future
    #         print(f"got {len(some_chunks)} chunks from {url}")
    #         for chunk_idx, chunk in some_chunks:
    #             completed[chunk_idx] = True
    #             chunks[chunk_idx] = chunk
    #     if not all(completed):
    #         raise ValueError("TODO: progressive write (with .part file)")
    #     return b"".join(chunks)


Downloaders = {
    DownloadKind.Simple: Simple,
    DownloadKind.Distributed: Distributed,
}


__all__ = ["BaseDownloader", "Downloaders"]
