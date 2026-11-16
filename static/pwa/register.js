/* OPERA HUB PWA — sem cache dos dados operacionais. */
(()=>{if(!("serviceWorker"in navigator)||!window.isSecureContext)return;
window.addEventListener("load",()=>navigator.serviceWorker.register("/service-worker.js",{scope:"/"}).catch(()=>{}),{once:true});})();
