import asyncio
import logging
from contextlib import asynccontextmanager
from dataclasses import dataclass
import aiohttp
from typing import List , AsyncIterator , Optional , Dict
 
logger = logging.getLogger(__name__)

@dataclass(frozen=True)
class ProxySession:
    id:str
    proxy: str
    session: aiohttp.ClientSession
    
    @property
    def proxy_url(self) -> str | None:
        return self.proxy
    
    @property
    def proxy_id(self) -> str | None:
        return self.id

class ProxyPool:
    def __init__(
        self,
        proxies: Optional[List[str]] = None,
    )->None:
        self.proxies: asyncio.Queue[ProxySession]= asyncio.Queue()
        self.proxies_map: Dict[str,ProxySession] = {}   

        if proxies:
            for i,proxy in enumerate(proxies):
                self.proxies.put_nowait(
                    ProxySession(
                        id=str(i+1),
                        proxy=proxy,
                        session=aiohttp.ClientSession(proxy=proxy)
                    )
                )
        else:
            self.proxies.put_nowait(
                ProxySession(
                    id="1",
                    proxy=None,
                    session=aiohttp.ClientSession()
                )
            )

    @asynccontextmanager
    async def get_proxy(self) -> AsyncIterator[ProxySession]:
        session=await self.proxies.get()
        try:
            yield session
        finally:
            self.proxies.put_nowait(session)

    async def close(self):
        sessions=[]
        while not self.proxies.empty():
            sessions.append(self.proxies.get_nowait())
        logger.warning(
            f"Closing {len(sessions)} proxy sessions"
        )
        await asyncio.gather(*[s.session.close() for s in sessions])