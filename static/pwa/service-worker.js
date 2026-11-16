/* OPERA HUB: não interceptar requisições nem guardar conteúdos de clientes offline. */
self.addEventListener("install",()=>self.skipWaiting());
self.addEventListener("activate",e=>e.waitUntil(self.clients.claim()));
